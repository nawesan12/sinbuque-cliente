#!/usr/bin/env python3
"""El logotipo de SinBuque: la marca más el nombre, para la pantalla principal.

El programa busca `logo_light.png` y `logo_dark.png` y elige según el tema, con `logo.png` de
respaldo. El tope que impone es 300×60; se generan al doble para que no se vean borrosos en
pantallas densas.
"""

import sys

sys.path.insert(0, ".")
from PIL import Image, ImageDraw, ImageFont
from gen_sinbuque_icon import dibujar

ALTO = 120                      # 60 lógicos × 2
TINTA_CLARA = (14, 27, 46)      # sobre fondo claro
TINTA_OSCURA = (255, 255, 255)  # sobre fondo oscuro

FUENTES = [
    ("/System/Library/Fonts/Avenir Next.ttc", 2),   # Demi Bold
    ("/System/Library/Fonts/HelveticaNeue.ttc", 1),
    ("/System/Library/Fonts/Helvetica.ttc", 1),
]


def fuente(tam):
    for ruta, indice in FUENTES:
        try:
            return ImageFont.truetype(ruta, tam, index=indice)
        except Exception:
            continue
    return ImageFont.load_default()


def logo(color):
    marca = dibujar(ALTO - 24)
    f = fuente(52)

    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    caja = tmp.textbbox((0, 0), "SinBuque", font=f)
    ancho_texto = caja[2] - caja[0]

    separacion = 20
    ancho = marca.width + separacion + ancho_texto + 8
    img = Image.new("RGBA", (ancho, ALTO), (0, 0, 0, 0))
    img.paste(marca, (0, (ALTO - marca.height) // 2), marca)

    d = ImageDraw.Draw(img)
    y = (ALTO - (caja[3] - caja[1])) // 2 - caja[1]
    d.text((marca.width + separacion, y), "SinBuque", font=f, fill=color)
    return img


if __name__ == "__main__":
    claro = logo(TINTA_CLARA)
    claro.save("../flutter/assets/logo_light.png")
    oscuro = logo(TINTA_OSCURA)
    oscuro.save("../flutter/assets/logo_dark.png")
    # El respaldo, por si algún día se mira sin tema definido.
    claro.save("../flutter/assets/logo.png")
    print(f"logotipo {claro.width}×{claro.height} (máximo lógico 300×60)")
