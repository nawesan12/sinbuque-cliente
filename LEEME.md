# SinBuque

Control remoto de escritorio para uso interno, con **servidor propio**: el cliente no habla
con ninguna nube de terceros.

Está construido sobre [RustDesk](https://github.com/rustdesk/rustdesk) **1.4.9**
(commit `6c57829`), que es software libre bajo **AGPL-3.0**. Esta versión mantiene esa
licencia, y el archivo [`LICENCE`](LICENCE) y los avisos de copyright del autor original están
intactos. Este repositorio es público justamente por eso: la AGPL pide que quien reciba el
programa pueda ver el código con el que se hizo, y acá está.

## Qué le cambiamos

| | |
|---|---|
| **Nombre** | `SinBuque` en la ventana, el servicio de Windows, `C:\Program Files\SinBuque`, el ejecutable instalado y las carpetas de configuración. Todo sale de `APP_NAME`. |
| **Servidor** | `sinbuque.online` y su clave pública **compilados adentro** (`libs/hbb_common/src/config.rs`). Recién instalado ya apunta a donde tiene que apuntar: nadie configura nada. |
| **La sesión no se corta** | La desconexión por inactividad queda apagada **y trabada** (`OVERWRITE_SETTINGS`): estas máquinas se manejan durante jornadas enteras. |
| **Menos cosas** | Sin libreta de direcciones, sin cuenta, sin favoritos, sin descubrimiento por red y sin chat. Lo que quedó es lo que usamos. |
| **Marca** | Ícono y logotipo propios, generados por los scripts de [`res/`](res). |

## Cómo se compila

El de Windows sale de GitHub Actions: pestaña **Actions** → *SinBuque · publicar una versión*
→ **Run workflow**. No hace falta ningún secreto; la firma de código se saltea sola cuando no
está configurada. El resultado queda publicado como *release*.

No se puede compilar en un servidor Linux: la interfaz es Flutter y `flutter build windows`
sólo corre sobre Windows.
