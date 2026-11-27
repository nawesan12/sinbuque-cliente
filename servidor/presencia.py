#!/usr/bin/env python3
"""Presencia de SinBuque: quién late, desde dónde, y cuándo se calla.

hbbs sólo deja en su log los cambios de IP. Si una compu deja de latir, no queda
nada escrito, y el 2026-11-25 eso costó una noche entera: la 7432715 se calló y
nadie podía decir a qué hora ni si volvía.

Lee con tcpdump los RegisterPeer que llegan al 21116/udp y escribe una línea por
evento en /var/log/sinbuque/presencia.log:

    2026-11-27T02:10:00Z 7432715 aparece desde 167.60.63.11:59247
    2026-11-27T02:12:40Z 7432715 cambia de 167.60.63.11:59247 a 167.60.63.11:61001
    2026-11-27T02:20:00Z 7432715 se calla (último latido hace 45 s, desde 167.60.63.11:61001)

Y cada hora un resumen con todas las compus que latieron.

Los latidos por TCP o WebSocket (el modo de respaldo por 443) no pasan por acá:
esos los registra el propio cliente en los logs que sube.
"""
import re
import subprocess
import sys
import threading
import time

LOG = "/var/log/sinbuque/presencia.log"
CALLADO = 45  # segundos sin latir: el cliente late cada 12-16 s
lock = threading.Lock()
vistos = {}  # id -> [ultimo_latido, "ip:puerto", callado]


def ahora():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def anotar(texto):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{ahora()} {texto}\n")


def id_de(payload):
    # RendezvousMessage { register_peer (6) = RegisterPeer { id (1), serial (2) } }
    if len(payload) < 4 or payload[0] != 0x32 or payload[2] != 0x0A:
        return None
    n = payload[3]
    ident = payload[4:4 + n]
    if len(ident) != n or not ident.isdigit():
        return None
    return ident.decode()


def latido(ident, origen):
    with lock:
        v = vistos.get(ident)
        if v is None or v[2]:
            anotar(f"{ident} aparece desde {origen}")
            vistos[ident] = [time.monotonic(), origen, False]
            return
        if v[1] != origen:
            anotar(f"{ident} cambia de {v[1]} a {origen}")
        v[0], v[1] = time.monotonic(), origen


def vigilar():
    ultimo_resumen = time.monotonic()
    while True:
        time.sleep(5)
        with lock:
            t = time.monotonic()
            for ident, v in vistos.items():
                if not v[2] and t - v[0] > CALLADO:
                    v[2] = True
                    anotar(f"{ident} se calla (último latido hace {int(t - v[0])} s, desde {v[1]})")
            if t - ultimo_resumen >= 3600:
                ultimo_resumen = t
                vivos = sorted(f"{i}@{v[1]}" for i, v in vistos.items() if not v[2])
                anotar(f"resumen: {len(vivos)} latiendo: {' '.join(vivos) or '-'}")


CABECERA = re.compile(r"^\S+ IP6? (\S+)\.(\d+) > \S+: UDP")


def procesar(origen, crudo):
    if crudo[0] >> 4 == 4:
        ip_len = (crudo[0] & 0x0F) * 4
    else:
        ip_len = 40  # IPv6 sin cabeceras de extensión
    ident = id_de(crudo[ip_len + 8:])
    if ident:
        latido(ident, origen)


def largo_total(crudo):
    """Bytes del paquete según su cabecera IP, o None si todavía no se sabe."""
    if len(crudo) < 6:
        return None
    if crudo[0] >> 4 == 4:
        return int.from_bytes(crudo[2:4], "big")
    return 40 + int.from_bytes(crudo[4:6], "big")


def leer():
    cmd = ["tcpdump", "-l", "-n", "-tt", "-x", "-i", "eth0", "udp dst port 21116"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    origen, crudo = None, b""
    # Cada paquete se procesa apenas está completo: esperar al siguiente dejaría
    # colgado el último latido de una compu que se calla.
    for linea in p.stdout:
        if linea.startswith("\t"):
            if origen is None:
                continue
            crudo += bytes.fromhex("".join(linea.split(":", 1)[1].split()))
            total = largo_total(crudo)
            if total is not None and len(crudo) >= total:
                procesar(origen, crudo)
                origen = None
            continue
        m = CABECERA.match(linea)
        origen = f"{m.group(1)}:{m.group(2)}" if m else None
        crudo = b""
    sys.exit(f"tcpdump terminó con código {p.wait()}")


if __name__ == "__main__":
    anotar("presencia arranca")
    threading.Thread(target=vigilar, daemon=True).start()
    leer()
