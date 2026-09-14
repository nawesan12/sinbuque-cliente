#!/usr/bin/env python3
"""Genera el ícono de SinBuque en todos los tamaños que hacen falta.

Queda en el repositorio a propósito: un logo que sólo existe como PNG es un logo que nadie
puede volver a generar cuando cambie el azul o haga falta un tamaño nuevo.

La marca es dos pantallas: una atrás en contorno y otra adelante llena, con un hueco del
color del fondo entre las dos. A 16 píxeles el contorno se pierde y queda un rectángulo
blanco limpio, que es exactamente lo que tiene que pasar — el ícono se sigue reconociendo.
"""

from PIL import Image, ImageDraw

AZUL = (44, 92, 230)        # el mismo de la página de descarga
AZUL_CLARO = (76, 125, 255)
BLANCO = (255, 255, 255, 255)

S = 1024          # se dibuja grande y se achica: es lo que da los bordes suaves
ESCALA = 4        # supermuestreo


def degradado(tam):
    """Un degradado diagonal del azul al azul claro."""
    img = Image.new("RGB", (tam, tam))
    px = img.load()
    for y in range(tam):
        for x in range(tam):
            t = (x + y) / (2 * tam - 2)
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(AZUL, AZUL_CLARO))
    return img


def dibujar(tam, forma="squircle"):
    g = tam * ESCALA
    fondo = degradado(g).convert("RGBA")

    # La máscara del cuadrado redondeado (squircle): sin esto el ícono sería un cuadrado
    # duro, que en una barra de tareas llena de íconos redondeados canta.
    mascara = Image.new("L", (g, g), 0)
    if forma == "circulo":
        # Android pide una variante redonda aparte; en los lanzadores que la usan, un
        # squircle recortado en circulo se veria mordido.
        ImageDraw.Draw(mascara).ellipse([0, 0, g - 1, g - 1], fill=255)
    else:
        ImageDraw.Draw(mascara).rounded_rectangle([0, 0, g - 1, g - 1], radius=int(g * 0.22), fill=255)

    lienzo = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    lienzo.paste(fondo, (0, 0), mascara)
    pantallas(lienzo, g, fondo)

    return lienzo.resize((tam, tam), Image.LANCZOS)


def pantallas(lienzo, g, relleno_hueco):
    """Dibuja las dos pantallas sobre `lienzo`.

    `relleno_hueco` es con qué se rellena el corte que separa una pantalla de la otra: el
    degradado del fondo en el ícono completo, transparencia cuando lo que queremos es la
    silueta sola.
    """
    d = ImageDraw.Draw(lienzo)

    def caja(x0, y0, x1, y1):
        return [x0 * g, y0 * g, x1 * g, y1 * g]

    grosor = max(1, int(g * 0.052))
    radio = int(g * 0.055)

    # La pantalla de atrás, en contorno.
    d.rounded_rectangle(caja(0.20, 0.22, 0.63, 0.57), radius=radio, outline=BLANCO, width=grosor)

    # El hueco: un recorte que separa una pantalla de la otra. Se dibuja con la máscara del
    # degradado para que el corte no sea un azul plano encima del degradado.
    hueco = Image.new("L", (g, g), 0)
    ImageDraw.Draw(hueco).rounded_rectangle(
        caja(0.355 - 0.028, 0.395 - 0.028, 0.815 + 0.028, 0.79 + 0.028),
        radius=radio + grosor, fill=255)
    lienzo.paste(relleno_hueco, (0, 0), hueco)

    # La pantalla de adelante, llena.
    d.rounded_rectangle(caja(0.355, 0.395, 0.815, 0.79), radius=radio, fill=BLANCO)


def silueta(tam=1024):
    """La marca sola: blanca, sobre transparente, recortada a su caja.

    Es lo que necesita Android dos veces — la capa de adelante del ícono adaptativo y el
    ícono de la barra de estado —, y las dos veces lo único que el sistema mira es el alfa.
    """
    g = tam * ESCALA
    lienzo = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    pantallas(lienzo, g, (0, 0, 0, 0))
    lienzo = lienzo.resize((tam, tam), Image.LANCZOS)
    return lienzo.crop(lienzo.getbbox())


def centrada(marca, tam, fraccion):
    """La marca centrada en un lienzo transparente de `tam`, ocupando `fraccion` del ancho."""
    ancho = max(1, round(tam * fraccion))
    alto = max(1, round(marca.height * ancho / marca.width))
    chica = marca.resize((ancho, alto), Image.LANCZOS)
    salida = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    salida.paste(chica, ((tam - ancho) // 2, (tam - alto) // 2), chica)
    return salida


# Android pide el mismo ícono cinco veces, una por densidad de pantalla.
DENSIDADES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
ANDROID = "../flutter/android/app/src/main/res"


def android():
    marca = silueta()
    for nombre, k in DENSIDADES.items():
        carpeta = f"{ANDROID}/mipmap-{nombre}"
        lanzador = round(48 * k)
        dibujar(lanzador).save(f"{carpeta}/ic_launcher.png")
        dibujar(lanzador, forma="circulo").save(f"{carpeta}/ic_launcher_round.png")

        # La capa de adelante del ícono adaptativo. El sistema le recorta los bordes para
        # darle la forma que use el lanzador, así que la marca tiene que vivir en el centro:
        # de los 108 dp del lienzo, sólo los 72 del medio están garantizados. La misma capa
        # se reusa como <monochrome>, y por eso va blanca sobre transparente.
        centrada(marca, round(108 * k), 0.50).save(f"{carpeta}/ic_launcher_foreground.png")

        # El de la barra de estado: Android lo tiñe del color que quiera y descarta el RGB.
        # Si tuviera color, lo aplanaría a un cuadrado blanco.
        centrada(marca, round(24 * k), 0.85).convert("LA").save(f"{carpeta}/ic_stat_logo.png")
    return len(DENSIDADES) * 4


if __name__ == "__main__":
    grande = dibujar(1024)
    grande.save("icon.png")
    for t in (32, 64, 128):
        dibujar(t).save(f"{t}x{t}.png")
    dibujar(256).save("128x128@2x.png")

    tamanios = [16, 32, 48, 64, 128, 256]
    grande.save("icon.ico", sizes=[(t, t) for t in tamanios])
    grande.save("../flutter/windows/runner/resources/app_icon.ico",
                sizes=[(t, t) for t in tamanios])
    print("listo:", ", ".join(str(t) for t in tamanios))
    print("android:", android(), "archivos en", "/".join(DENSIDADES))
