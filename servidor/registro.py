#!/usr/bin/env python3
"""Receptor de logs de SinBuque.

Cada cliente sube sus archivos de log a medida que crecen, para que una falla en
una compu lejana se pueda leer acá sin que nadie de allá tenga que buscar
carpetas. Caddy lo publica en https://sinbuque.online/registro/subir.

El cliente manda un pedazo de un archivo y dónde empieza:

    POST /registro/subir
    Authorization: Bearer <token>
    X-SinBuque-Id: 7432715          (sólo dígitos)
    X-SinBuque-Proceso: server       (minúsculas, puede ir vacío)
    X-SinBuque-Archivo: 2026-11-26_9f3c0a1b2c3d4e5f.log
    X-SinBuque-Desde: 81920          (byte del archivo donde empieza el cuerpo)

y la respuesta es el tamaño que quedó guardado acá. Así un reintento nunca
duplica: si el pedazo ya estaba se ignora lo repetido, y si falta algo en el
medio el cliente retoma desde lo que el servidor dice tener.

Se guarda en /var/log/sinbuque/clientes/<id>/<proceso>/<archivo>. El nombre lo
arma el cliente con la fecha y un hash de la primera línea del archivo
(2026-11-26_9f3c….log), que no cambia cuando el log rota. Se borra a los 90 días
(cron de limpieza).
"""
import hmac
import os
import re
import shutil
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.environ.get("REGISTRO_RAIZ", "/var/log/sinbuque/clientes")
TOKEN = open(os.environ.get("REGISTRO_TOKEN", "/opt/sinbuque/registro.token")).read().strip()
PUERTO = int(os.environ.get("REGISTRO_PUERTO", "21190"))
MAX_PEDAZO = 1 << 20          # 1 MiB por pedido
MAX_ARCHIVO = 200 << 20       # 200 MiB por archivo guardado
MIN_LIBRE = int(os.environ.get("REGISTRO_MIN_LIBRE", 2 << 30))          # con menos de 2 GiB libres no se guarda nada

ID = re.compile(r"^[0-9]{6,12}$")
PROCESO = re.compile(r"^[a-z_-]{0,16}$")
ARCHIVO = re.compile(r"^[A-Za-z0-9_.-]{1,96}\.log$")

# Dos pedidos sobre el mismo archivo no pueden intercalarse.
candados = {}
candados_lock = threading.Lock()


def candado(ruta):
    with candados_lock:
        return candados.setdefault(ruta, threading.Lock())


class Receptor(BaseHTTPRequestHandler):
    server_version = "registro"
    sys_version = ""

    def responder(self, codigo, texto=""):
        cuerpo = texto.encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        if self.path != "/registro/subir":
            return self.responder(404)
        clave = self.headers.get("Authorization", "")
        if not hmac.compare_digest(clave.encode(), f"Bearer {TOKEN}".encode()):
            return self.responder(401)
        ident = self.headers.get("X-SinBuque-Id", "")
        proceso = self.headers.get("X-SinBuque-Proceso", "")
        archivo = self.headers.get("X-SinBuque-Archivo", "")
        try:
            desde = int(self.headers.get("X-SinBuque-Desde", ""))
            largo = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.responder(400, "desde/largo")
        if not (ID.match(ident) and PROCESO.match(proceso) and ARCHIVO.match(archivo)):
            return self.responder(400, "nombres")
        if desde < 0 or largo < 0 or largo > MAX_PEDAZO:
            return self.responder(413 if largo > MAX_PEDAZO else 400, "largo")
        cuerpo = self.rfile.read(largo)
        if len(cuerpo) != largo:
            return self.responder(400, "cuerpo cortado")

        carpeta = os.path.join(RAIZ, ident, proceso or "app")
        os.makedirs(carpeta, mode=0o700, exist_ok=True)
        destino = os.path.join(carpeta, archivo)
        with candado(destino):
            return self.guardar(destino, desde, cuerpo)

    def guardar(self, destino, desde, cuerpo):
        tengo = os.path.getsize(destino) if os.path.exists(destino) else 0

        if desde > tengo:
            # Falta un pedazo del medio: que el cliente retome desde acá.
            return self.responder(409, str(tengo))
        nuevo = cuerpo[tengo - desde:]
        if nuevo:
            if tengo + len(nuevo) > MAX_ARCHIVO:
                return self.responder(507, str(tengo))
            if shutil.disk_usage(RAIZ).free < MIN_LIBRE:
                return self.responder(507, str(tengo))
            with open(destino, "ab") as f:
                f.write(nuevo)
            tengo += len(nuevo)
        self.responder(200, str(tengo))

    def do_GET(self):
        self.responder(404)

    def log_message(self, formato, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), formato % args))


if __name__ == "__main__":
    os.makedirs(RAIZ, mode=0o700, exist_ok=True)
    os.umask(0o077)
    ThreadingHTTPServer(("0.0.0.0", PUERTO), Receptor).serve_forever()
