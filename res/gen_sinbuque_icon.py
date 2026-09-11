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


def dibujar(tam):
    g = tam * ESCALA
    fondo = degradado(g).convert("RGBA")

    # La máscara del cuadrado redondeado (squircle): sin esto el ícono sería un cuadrado
    # duro, que en una barra de tareas llena de íconos redondeados canta.
    mascara = Image.new("L", (g, g), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, g - 1, g - 1], radius=int(g * 0.22), fill=255)

    lienzo = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    lienzo.paste(fondo, (0, 0), mascara)
    d = ImageDraw.Draw(lienzo)

    def caja(x0, y0, x1, y1):
        return [x0 * g, y0 * g, x1 * g, y1 * g]

    grosor = max(1, int(g * 0.052))
    radio = int(g * 0.055)

    # La pantalla de atrás, en contorno.
    d.rounded_rectangle(caja(0.20, 0.22, 0.63, 0.57), radius=radio, outline=BLANCO, width=grosor)

    # El hueco: un recorte del color del fondo que separa una pantalla de la otra. Se dibuja
    # con la máscara del degradado para que el corte no sea un azul plano encima del degradado.
    hueco = Image.new("L", (g, g), 0)
    ImageDraw.Draw(hueco).rounded_rectangle(
        caja(0.355 - 0.028, 0.395 - 0.028, 0.815 + 0.028, 0.79 + 0.028),
        radius=radio + grosor, fill=255)
    lienzo.paste(fondo, (0, 0), hueco)

    # La pantalla de adelante, llena.
    d.rounded_rectangle(caja(0.355, 0.395, 0.815, 0.79), radius=radio, fill=BLANCO)

    return lienzo.resize((tam, tam), Image.LANCZOS)


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
