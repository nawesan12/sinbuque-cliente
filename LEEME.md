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

En Android, además, cambian el nombre de la aplicación, el del servicio de accesibilidad, el
de la notificación, los íconos y el `applicationId`, que pasa a `online.sinbuque.cliente`. El
enlace profundo es `sinbuque://`, no `rustdesk://`.

Los textos de la interfaz **no** están traducidos a mano: `src/lang.rs` ya reemplaza
«RustDesk» por `APP_NAME` en los 49 idiomas cuando el cliente no es el oficial. La única
excepción es el nombre del servicio de accesibilidad en
`android_input_permission_tip2`, que tiene que coincidir letra por letra con el
`android:label` del manifiesto.

## La página de descarga

[`web/descargar.html`](web/descargar.html) es lo que ve alguien a quien le dijeron «entrá acá
y bajate esto». Se despliega a mano en el VPS, **con otro nombre**:

```bash
scp web/descargar.html root@179.199.147.216:/opt/puente/server/deploy/descargas/index.html
```

No tiene JavaScript a propósito: elegir entre Windows y Android es un `radio` y un `:checked`.
La puede estar abriendo un navegador viejo en una máquina que anda mal, que es exactamente el
motivo por el que la persona llegó hasta ahí.

## Cómo se compila

Las dos plataformas salen de GitHub Actions, del mismo workflow: pestaña **Actions** →
*SinBuque · publicar una versión* → **Run workflow**. El resultado queda publicado como
*release*.

**Windows** no necesita ningún secreto: la firma de código se saltea sola cuando no está
configurada.

**Android** sí necesita cuatro, y sin ellos el job falla a propósito en los primeros
segundos en vez de entregar un APK que no se puede instalar:

| | |
|---|---|
| `ANDROID_SIGNING_KEY` | el keystore en base64 (`openssl base64 -A -in sinbuque.jks`) |
| `ANDROID_ALIAS` | `sinbuque` |
| `ANDROID_KEY_STORE_PASSWORD` | alfanumérica: `key.properties` es un `.properties` de Java y `\`, `:` y `=` tienen significado ahí |
| `ANDROID_KEY_PASSWORD` | la misma |

**El keystore no se puede perder.** Android rechaza una actualización firmada con otra clave,
así que perderlo obliga a desinstalar la app de cada equipo para poder actualizarla.

El APK sale sólo para **arm64-v8a**. Antes de repartirlo conviene confirmar que el equipo
destino es de 64 bits, porque si no ni siquiera instala:

```bash
adb shell getprop ro.product.cpu.abi     # tiene que decir arm64-v8a
```

Para sumar otra arquitectura alcanza con agregar una entrada a la matriz del job
`build-for-android`; los pasos ya están parametrizados.

No se puede compilar en un servidor Linux: la interfaz es Flutter y `flutter build windows`
sólo corre sobre Windows. El APK sí se podría, pero no hay motivo: Actions ya lo hace.
