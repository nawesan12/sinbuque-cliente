//! SinBuque: sube los logs de este proceso al servidor a medida que crecen.
//!
//! El 2026-11-25 una compu en Uruguay dejó de responder y nadie allá podía buscar
//! carpetas de logs: sin ellos no hubo forma de saber por qué. Ahora cada proceso
//! manda lo que escribe a https://sinbuque.online/registro/subir, y los archivos
//! locales siguen como siempre.
//!
//! Cada archivo se identifica por su primera línea, no por el nombre: flexi_logger
//! renombra `_rCURRENT.log` al rotar, y la primera línea (con fecha al
//! microsegundo) no cambia. Así una rotación no duplica nada, y si la compu pasó
//! días sin internet, al volver sube lo que faltaba de cada archivo.
//!
//! El servidor contesta cuántos bytes tiene de cada archivo, y de ahí se sigue: un
//! reintento nunca duplica y un hueco se rellena solo.
use hbb_common::{config::Config, log};
use std::{
    collections::{HashMap, HashSet},
    fs::{self, File, OpenOptions},
    io::{Read, Seek, SeekFrom},
    os::windows::fs::OpenOptionsExt,
    path::{Path, PathBuf},
    time::{Duration, Instant, SystemTime},
};

const URL: &str = "https://sinbuque.online/registro/subir";
const TOKEN: Option<&str> = option_env!("SINBUQUE_REGISTRO_TOKEN");
const CADA: Duration = Duration::from_secs(20);
const PEDAZO: u64 = 512 * 1024;
// La primera vez que corre no sube un mes de historia: sólo lo de la última semana.
const VIEJO: Duration = Duration::from_secs(7 * 24 * 3600);
const ESTADO: &str = "subido.json";
const CANDADO: &str = "subiendo.lock";

pub fn start(proceso: &str) {
    let Some(token) = TOKEN.filter(|t| !t.is_empty()) else {
        return;
    };
    log::info!(
        "SinBuque build {}",
        option_env!("GITHUB_SHA").unwrap_or("local")
    );
    let proceso = proceso.to_owned();
    let mut dir = Config::log_path();
    if !proceso.is_empty() {
        dir.push(&proceso);
    }
    std::thread::spawn(move || {
        // Un solo proceso por carpeta: si otro ya la sube, este no hace nada.
        let Some(_candado) = tomar_candado(&dir) else {
            return;
        };
        let mut estado = cargar_estado(&dir);
        let mut ultimo_aviso: Option<Instant> = None;
        loop {
            std::thread::sleep(CADA);
            let id = Config::get_id();
            if id.is_empty() {
                continue;
            }
            if let Err(err) = ronda(&dir, &proceso, &id, token, &mut estado) {
                // Sin internet esto falla cada 20 s: avisar una vez por hora alcanza.
                if ultimo_aviso.map_or(true, |t| t.elapsed() > Duration::from_secs(3600)) {
                    log::warn!("log upload: {err}");
                    ultimo_aviso = Some(Instant::now());
                }
            }
        }
    });
}

fn tomar_candado(dir: &Path) -> Option<File> {
    fs::create_dir_all(dir).ok()?;
    OpenOptions::new()
        .create(true)
        .write(true)
        .share_mode(0)
        .open(dir.join(CANDADO))
        .ok()
}

fn cargar_estado(dir: &Path) -> HashMap<String, u64> {
    fs::read(dir.join(ESTADO))
        .ok()
        .and_then(|b| serde_json::from_slice(&b).ok())
        .unwrap_or_default()
}

fn guardar_estado(dir: &Path, estado: &HashMap<String, u64>) {
    let Ok(datos) = serde_json::to_vec(estado) else {
        return;
    };
    let tmp = dir.join(format!("{ESTADO}.tmp"));
    if fs::write(&tmp, datos).is_ok() {
        fs::rename(&tmp, dir.join(ESTADO)).ok();
    }
}

// FNV-1a: estable entre versiones, a diferencia de DefaultHasher.
fn fnv1a(datos: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in datos {
        h ^= *b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

/// El nombre con que el archivo se guarda en el servidor, o None si todavía no
/// tiene una primera línea completa.
fn clave_de(ruta: &Path) -> Option<String> {
    let mut cabeza = vec![0u8; 4096];
    let n = File::open(ruta).ok()?.read(&mut cabeza).ok()?;
    let fin = cabeza[..n].iter().position(|b| *b == b'\n')?;
    let linea = &cabeza[..fin];
    // Las líneas empiezan con «[2026-11-26 01:51:06.726686 …».
    let dia = std::str::from_utf8(linea.get(1..11)?)
        .ok()
        .filter(|d| d.bytes().all(|b| b.is_ascii_digit() || b == b'-'))
        .unwrap_or("sin-fecha");
    Some(format!("{dia}_{:016x}.log", fnv1a(linea)))
}

fn leer_pedazo(ruta: &Path, desde: u64, largo: u64) -> std::io::Result<Vec<u8>> {
    let mut f = File::open(ruta)?;
    f.seek(SeekFrom::Start(desde))?;
    let mut buf = Vec::with_capacity(largo as usize);
    f.take(largo).read_to_end(&mut buf)?;
    Ok(buf)
}

fn ronda(
    dir: &Path,
    proceso: &str,
    id: &str,
    token: &str,
    estado: &mut HashMap<String, u64>,
) -> Result<(), String> {
    let mut archivos: Vec<(PathBuf, u64, SystemTime)> = fs::read_dir(dir)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().map_or(false, |x| x == "log"))
        .filter_map(|p| {
            let m = fs::metadata(&p).ok()?;
            Some((p, m.len(), m.modified().ok()?))
        })
        .collect();
    // Los más viejos primero: si se corta a la mitad, lo que falta es lo más nuevo.
    archivos.sort_by_key(|a| a.2);

    let cliente = crate::hbbs_http::create_http_client_with_url(URL);
    let mut vistos = HashSet::new();
    for (ruta, largo, modificado) in archivos {
        let Some(clave) = clave_de(&ruta) else {
            continue;
        };
        vistos.insert(clave.clone());
        let viejo = modificado.elapsed().map_or(false, |e| e > VIEJO);
        let mut desde = *estado
            .entry(clave.clone())
            .or_insert(if viejo { largo } else { 0 });
        while desde < largo {
            let cuerpo = leer_pedazo(&ruta, desde, PEDAZO.min(largo - desde))
                .map_err(|e| e.to_string())?;
            if cuerpo.is_empty() {
                break;
            }
            let resp = cliente
                .post(URL)
                .bearer_auth(token)
                .header("X-SinBuque-Id", id)
                .header("X-SinBuque-Proceso", proceso)
                .header("X-SinBuque-Archivo", &clave)
                .header("X-SinBuque-Desde", desde.to_string())
                .body(cuerpo)
                .timeout(Duration::from_secs(60))
                .send()
                .map_err(|e| e.to_string())?;
            let codigo = resp.status().as_u16();
            let texto = resp.text().unwrap_or_default();
            let tengo: Option<u64> = texto.trim().parse().ok();
            match (codigo, tengo) {
                // 409: al servidor le falta algo antes de `desde`; se retoma desde ahí.
                (200, Some(t)) | (409, Some(t)) => {
                    if codigo == 200 && t <= desde {
                        return Err(format!("server did not advance on {clave}"));
                    }
                    desde = t;
                    estado.insert(clave.clone(), desde);
                    guardar_estado(dir, estado);
                }
                _ => return Err(format!("{codigo} {}", texto.trim())),
            }
        }
    }
    let antes = estado.len();
    estado.retain(|k, _| vistos.contains(k));
    if estado.len() != antes {
        guardar_estado(dir, estado);
    }
    Ok(())
}
