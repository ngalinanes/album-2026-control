"""
FIFA 2026 · Mi Álbum Digital
────────────────────────────
Aplicación Streamlit para gestionar tu colección de figuritas del Mundial 2026.
Persistencia: lee y escribe sobre `album.json` en la misma carpeta del script.

Ejecutar:
    streamlit run app.py
"""

import json
import streamlit as st
import requests

# ═══════════════════════════════════════════════════════════════════════════════
# ① CONFIGURACIÓN DE PÁGINA — debe ser la PRIMERA llamada a Streamlit
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="FIFA 2026 · Mi Álbum",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ═══════════════════════════════════════════════════════════════════════════════
# ①.b CONTROL DE ACCESO (LOGIN)
# ═══════════════════════════════════════════════════════════════════════════════

# Inicializamos el estado de autenticación si no existe
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Si no está autenticado, mostramos el login y DETENEMOS la app
if not st.session_state.authenticated:
    # Un diseño centrado y simple para el login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🔒 Acceso Restringido</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-muted);'>Ingresá la contraseña familiar para gestionar el álbum.</p>", unsafe_allow_html=True)
        
        pwd_input = st.text_input("Contraseña", type="password", label_visibility="collapsed")
        
        if st.button("Ingresar", use_container_width=True):
            if pwd_input == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()  # Recarga la página ya autenticado
            else:
                st.error("❌ Contraseña incorrecta.")
    
    st.stop() # <- CLAVE: Esto evita que el resto de app.py se ejecute si no hay login
# ═══════════════════════════════════════════════════════════════════════════════
# ② CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════
ALBUM_PATH = "album.json"
GRID_COLS  = 4  # columnas en la cuadrícula de figuritas

# Mapa de sigla → emoji de bandera
# MEJORA 4: se agrega "CC": "🥤" para la colección Coca-Cola
FLAG_EMOJIS: dict[str, str] = {
    "FWC": "🌍",
    "MEX": "🇲🇽", "RSA": "🇿🇦", "KOR": "🇰🇷", "CZE": "🇨🇿",
    "CAN": "🇨🇦", "BIH": "🇧🇦", "QAT": "🇶🇦", "SUI": "🇨🇭",
    "BRA": "🇧🇷", "MAR": "🇲🇦", "HAI": "🇭🇹", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "USA": "🇺🇸", "PAR": "🇵🇾", "AUS": "🇦🇺", "TUR": "🇹🇷",
    "GER": "🇩🇪", "CUW": "🇨🇼", "CIV": "🇨🇮", "ECU": "🇪🇨",
    "NED": "🇳🇱", "JPN": "🇯🇵", "SWE": "🇸🇪", "TUN": "🇹🇳",
    "BEL": "🇧🇪", "EGY": "🇪🇬", "IRN": "🇮🇷", "NZL": "🇳🇿",
    "ESP": "🇪🇸", "CPV": "🇨🇻", "KSA": "🇸🇦", "URU": "🇺🇾",
    "FRA": "🇫🇷", "SEN": "🇸🇳", "IRQ": "🇮🇶", "NOR": "🇳🇴",
    "ARG": "🇦🇷", "ALG": "🇩🇿", "AUT": "🇦🇹", "JOR": "🇯🇴",
    "POR": "🇵🇹", "COD": "🇨🇩", "UZB": "🇺🇿", "COL": "🇨🇴",
    "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "CRO": "🇭🇷", "GHA": "🇬🇭", "PAN": "🇵🇦",
    "CC":  "🥤",  # MEJORA 4: Colección Coca-Cola
}

# ═══════════════════════════════════════════════════════════════════════════════
# ③ CSS GLOBAL + JS PARA COLOREAR BOTONES
#    Streamlit no permite estilar botones individuales directamente, por eso:
#    • Inyectamos CSS con variables de color y estilos generales.
#    • Un MutationObserver en JS aplica clases CSS según el emoji del label
#      (✅ → verde, ❌ → rojo/oscuro) cada vez que el DOM cambia.
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    /* ── Importar fuente ── */
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;900&family=Barlow:wght@400;500;600&display=swap');

    /* ── Variables de color ── */
    :root {
        --green-dark:  #0d3b1e;
        --green-mid:   #1a5c30;
        --green-light: #2d8a4a;
        --green-btn:   #1e7a3c;
        --green-hover: #25a050;
        --red-dark:    #3b0d0d;
        --red-mid:     #7a1e1e;
        --red-btn:     #5c1a1a;
        --red-text:    #ff9999;
        --gold:        #f5c518;
        --bg-main:     #0a0f14;
        --bg-card:     #111820;
        --bg-sidebar:  #0d1520;
        --text-main:   #e8edf2;
        --text-muted:  #8899aa;
        --border:      #1e2d3d;
    }

    /* ── Fondo general ── */
    .stApp { background-color: var(--bg-main) !important; }

    /* ── Tipografía global ── */
    html, body, [class*="css"] {
        font-family: "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", 'Barlow', sans-serif !important;
        color: var(--text-main) !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'Barlow Condensed', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em;
    }

    /* ── Título principal ── */
    h1 {
        font-family: 'Barlow Condensed', sans-serif !important;
        font-weight: 900 !important;
        font-size: 2.8rem !important;
        letter-spacing: 0.03em;
        color: var(--text-main) !important;
    }

    /* ── Subtítulos ── */
    h2, h3 {
        font-family: 'Barlow Condensed', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em;
        color: var(--text-main) !important;
    }

    /* ── Métricas ── */
    [data-testid="stMetric"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Barlow Condensed', sans-serif !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: var(--gold) !important;
    }

    /* ── Barra de progreso ── */
    [data-testid="stProgressBar"] > div {
        background-color: var(--border) !important;
        border-radius: 99px !important;
        height: 8px !important;
    }
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, var(--green-mid), var(--green-light)) !important;
        border-radius: 99px !important;
    }

    /* ── Selector / selectbox ── */
    [data-testid="stSelectbox"] > div > div {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
    }

    /* ── Toggle / checkbox ── */
    [data-testid="stToggle"] label {
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: var(--text-main) !important;
    }

    /* ── Divider ── */
    hr {
        border-color: var(--border) !important;
    }

    /* ── Caption / textos pequeños ── */
    [data-testid="stCaptionContainer"] p {
        color: var(--text-muted) !important;
        font-size: 0.82rem !important;
    }

    /* ═══ BOTONES BASE (todos los st.button de la cuadrícula) ═══ */
    [data-testid="stButton"] > button {
        width: 100% !important;
        min-height: 64px !important;
        border-radius: 10px !important;
        font-family: 'Barlow Condensed', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        line-height: 1.3 !important;
        letter-spacing: 0.02em;
        transition: all 0.15s ease !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
        text-align: center !important;
    }

    /* ═══ BOTÓN PEGADA (clase aplicada por JS) ═══ */
    [data-testid="stButton"] > button.sticker-pegada {
        background-color: var(--green-btn)    !important;
        border: 1.5px solid var(--green-light) !important;
        color: #ffffff                          !important;
        box-shadow: 0 2px 8px rgba(29, 122, 60, 0.4) !important;
    }
    [data-testid="stButton"] > button.sticker-pegada:hover {
        background-color: var(--green-hover)   !important;
        box-shadow: 0 4px 14px rgba(29, 122, 60, 0.65) !important;
        transform: translateY(-1px) !important;
    }

    /* ═══ BOTÓN FALTANTE (clase aplicada por JS) ═══ */
    [data-testid="stButton"] > button.sticker-faltante {
        background-color: var(--red-btn)      !important;
        border: 1.5px solid var(--red-mid)    !important;
        color: var(--red-text)                !important;
        box-shadow: 0 2px 8px rgba(92, 26, 26, 0.35) !important;
    }
    [data-testid="stButton"] > button.sticker-faltante:hover {
        background-color: var(--red-mid)      !important;
        box-shadow: 0 4px 14px rgba(122, 30, 30, 0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Info / success box ── */
    [data-testid="stAlert"] {
        background-color: var(--green-dark) !important;
        border: 1px solid var(--green-mid) !important;
        color: #a8ffc8 !important;
        border-radius: 10px !important;
    }

    /* ── Ocultar decoraciones innecesarias ── */
    #MainMenu, footer, header { visibility: hidden !important; }
    .block-container { padding-top: 1.5rem !important; }
    </style>

    <script>
    /**
     * Aplica clases CSS (sticker-pegada / sticker-faltante) a los botones
     * basándose en el emoji del label. Se ejecuta al inicio y cada vez
     * que el DOM muta (Streamlit hace rerender completo en cada interacción).
     */
    function colorizeButtons() {
        document.querySelectorAll('[data-testid="stButton"] > button').forEach(btn => {
            const txt = btn.innerText || '';
            // Limpiamos clases anteriores para evitar state stale
            btn.classList.remove('sticker-pegada', 'sticker-faltante');
            if (txt.startsWith('✅')) {
                btn.classList.add('sticker-pegada');
            } else if (txt.startsWith('❌')) {
                btn.classList.add('sticker-faltante');
            }
        });
    }

    // Ejecutar inmediatamente
    colorizeButtons();

    // Observer: re-ejecuta cuando el DOM cambia (ej: Streamlit reemplaza botones)
    const observer = new MutationObserver(() => colorizeButtons());
    observer.observe(document.body, { childList: true, subtree: true });

    // Seguro de red: polling cada 300ms por si el observer falla en algún navegador
    setInterval(colorizeButtons, 300);
    </script>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# ④ FUNCIONES DE PERSISTENCIA
# ═══════════════════════════════════════════════════════════════════════════════

#def load_album() -> dict:
#    """Carga el archivo album.json desde disco."""
#    with open(ALBUM_PATH, "r", encoding="utf-8") as f:
#        return json.load(f)


#def save_album(data: dict) -> None:
#    """Serializa y sobreescribe album.json con el estado actual."""
#    with open(ALBUM_PATH, "w", encoding="utf-8") as f:
#        json.dump(data, f, ensure_ascii=False, indent=4)

# Obtenemos las credenciales de forma segura desde Streamlit Secrets
BIN_ID = st.secrets["JSONBIN_ID"]
API_KEY = st.secrets["JSONBIN_KEY"]
BIN_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"

def load_album() -> dict:
    """Carga el archivo album.json desde JSONBin."""
    headers = {"X-Master-Key": API_KEY}
    respuesta = requests.get(BIN_URL, headers=headers)
    return respuesta.json()["record"]

def save_album(data: dict) -> None:
    """Sobreescribe el JSONBin con el estado actual."""
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": API_KEY
    }
    requests.put(BIN_URL, json=data, headers=headers)

# ═══════════════════════════════════════════════════════════════════════════════
# ⑤ FUNCIONES DE INYECCIÓN DE DATOS FALTANTES
#    Estas funciones se ejecutan UNA sola vez al inicio (antes de guardar en
#    session_state) para garantizar que el JSON esté siempre completo.
#    Retornan True si realizaron algún cambio (para saber si hay que guardar).
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_fwc00(data: dict) -> bool:
    """
    MEJORA 3: Verifica si FWC00 existe en la sección 'FWC'.
    Si no existe, la inyecta al INICIO del dict 'FWC' y retorna True.
    Python 3.7+ garantiza el orden de inserción en los dicts.
    """
    if "FWC" not in data:
        return False  # Sección FWC inexistente, no hace nada
    if "FWC00" in data["FWC"]:
        return False  # Ya existe, nada que hacer

    sticker_00 = {
        "FWC00": {
            "pegada": False,
            "nombre": "Panini Logo",
            "pais":   "FIFA World Cup History",
        }
    }
    # Reconstruimos el dict FWC con FWC00 primero, luego el resto
    data["FWC"] = {**sticker_00, **data["FWC"]}
    return True


def ensure_cc_collection(data: dict) -> bool:
    """
    MEJORA 4: Verifica si la sección 'CC' (Coca-Cola) existe en el JSON.
    Si no existe, la crea con CC1..CC14 al FINAL del álbum y retorna True.
    """
    if "CC" in data:
        return False  # Ya existe, nada que hacer

    data["CC"] = {
        f"CC{i}": {
            "pegada": False,
            "nombre": "Coca-Cola Extra",
            "pais":   "Coca-Cola",
        }
        for i in range(1, 15)  # CC1 a CC14 inclusive
    }
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# ⑥ INICIALIZACIÓN DEL SESSION STATE
#    • Carga el JSON desde disco.
#    • Corre las inyecciones de datos faltantes (FWC00 y CC).
#    • Persiste el JSON si hubo cambios.
#    • Todo esto ocurre UNA sola vez por sesión.
# ═══════════════════════════════════════════════════════════════════════════════

if "album" not in st.session_state:
    raw = load_album()

    # Inyecciones: acumulamos si alguna modificó el dict
    changed = ensure_fwc00(raw)
    changed = ensure_cc_collection(raw) or changed

    if changed:
        save_album(raw)  # Persistir sólo si hubo modificaciones

    st.session_state.album = raw

# Lista ordenada de claves de secciones reales
section_keys_real: list[str] = list(st.session_state.album.keys())
# Lista de navegación incluyendo el Resumen
NAV_OPTIONS = ["📊 Resumen General"] + section_keys_real

# Sección seleccionada por defecto: la primera del JSON
if "selected_section" not in st.session_state:
    st.session_state.selected_section = NAV_OPTIONS[0]

# Estado del filtro "mostrar solo faltantes"
if "show_missing_only" not in st.session_state:
    st.session_state.show_missing_only = False

# Referencia corta al álbum en memoria
album: dict = st.session_state.album

# ═══════════════════════════════════════════════════════════════════════════════
# ⑦ CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

def toggle_sticker(section_key: str, sticker_key: str) -> None:
    """
    Invierte el estado `pegada` de una figurita en session_state
    y persiste inmediatamente el álbum completo en album.json.
    Usamos on_click para que Streamlit ejecute esto ANTES del rerender,
    evitando parpadeos o inconsistencias visuales.
    """
    fig = st.session_state.album[section_key][sticker_key]
    fig["pegada"] = not fig["pegada"]
    save_album(st.session_state.album)


def go_to_prev_section() -> None:
    """MEJORA 2: Navega a la sección anterior en el orden del JSON."""
    current_idx = NAV_OPTIONS.index(st.session_state.selected_section)
    if current_idx > 0:
        st.session_state.selected_section = NAV_OPTIONS[current_idx - 1]


def go_to_next_section() -> None:
    """MEJORA 2: Navega a la sección siguiente en el orden del JSON."""
    current_idx = NAV_OPTIONS.index(st.session_state.selected_section)
    if current_idx < len(NAV_OPTIONS) - 1:
        st.session_state.selected_section = NAV_OPTIONS[current_idx + 1]

def set_section(section_name: str) -> None:
    st.session_state.selected_section = section_name

# ═══════════════════════════════════════════════════════════════════════════════
# ⑧ CONSTRUIR OPCIONES DEL SELECTOR
#    MEJORA 1: Formato limpio "[Emoji] [Sigla] — [Nombre del País]"
#    Se agregan las opciones de navegación al mapeo.
# ═══════════════════════════════════════════════════════════════════════════════

section_options: dict[str, str] = {}
for code, stickers in album.items():
    first_sticker = next(iter(stickers.values()))
    pais_label    = first_sticker["pais"]
    flag          = FLAG_EMOJIS.get(code, "🏳")
    # MEJORA 1: formato explícito y limpio, sin doble espacio
    section_options[code] = f"{flag} {code} — {pais_label}"
section_options["📊 Resumen General"] = "📊 Resumen General"


# ═══════════════════════════════════════════════════════════════════════════════
# ⑨ SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:

    st.markdown("## ⚽ FIFA 2026")
    st.markdown("### Mi Álbum Digital")
    st.divider()

    # ── Selector de sección ──────────────────────────────────────────────────
    # `key="selected_section"` sincroniza automáticamente con session_state.
    # `format_func` garantiza que la etiqueta visible sea el string pre-formateado
    # de `section_options`, con el formato "[Emoji] [Sigla] — [País]".
    st.selectbox(
        label="🌎 Selecciona una sección:",
        options=NAV_OPTIONS,
        format_func=lambda code: section_options[code],  # MEJORA 1: label formateado
        key="selected_section",
    )

    st.text_input("🔍 Buscar jugador o ID (ej: ARG2):", key="search_query")

    st.divider()

    # ── Estadísticas Globales ────────────────────────────────────────────────
    total_figuritas = sum(len(v) for v in album.values())
    total_pegadas   = sum(
        1 for sec in album.values()
          for fig in sec.values()
          if fig["pegada"]
    )
    total_faltantes = total_figuritas - total_pegadas
    progreso_global = total_pegadas / total_figuritas if total_figuritas else 0.0

    st.markdown("### 📊 Estadísticas Globales")

    col_a, col_b = st.columns(2)
    col_a.metric("✅ Pegadas",   total_pegadas)
    col_b.metric("❌ Faltantes", total_faltantes)

    st.progress(progreso_global)
    st.caption(
        f"Progreso global: **{progreso_global * 100:.1f}%**  "
        f"({total_pegadas} de {total_figuritas})"
    )

    st.divider()

    # ── Ranking rápido: Selecciones con más completitud ────────────────────────
    st.markdown("### 🏆 Top 10 Selecciones")
    ranking = sorted(
        [
            (
                code,
                FLAG_EMOJIS.get(code, "🏳"),
                sum(1 for f in stks.values() if f["pegada"]),
                len(stks),
            )
            for code, stks in album.items()
        ],
        key=lambda x: x[2] / x[3] if x[3] else 0,
        reverse=True,
    )[:10]

    for code, flag, peg, tot in ranking:
        pct_rank = peg / tot if tot else 0
        st.caption(f"{flag} **{code}** — {peg}/{tot} ({pct_rank * 100:.0f}%)")


# ═══════════════════════════════════════════════════════════════════════════════
# ⑩ ÁREA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

# ── Lógica de Búsqueda Global ────────────────────────────────────────────────
search_query = st.session_state.get("search_query", "").strip().lower()

if search_query:
    st.title(f"🔍 Resultados: '{search_query}'")
    
    matches = []
    for s_code, s_dict in album.items():
        for sid, sdata in s_dict.items():
            # Buscamos coincidencias en el ID o en el nombre del jugador
            if search_query in sid.lower() or search_query in sdata["nombre"].lower():
                matches.append((s_code, sid, sdata))
    
    if not matches:
        st.info("No se encontraron figuritas que coincidan con la búsqueda.")
    else:
        st.write(f"Se encontraron **{len(matches)}** coincidencias:")
        columnas = st.columns(GRID_COLS)
        
        for idx, (s_code, sid, sdata) in enumerate(matches):
            col = columnas[idx % GRID_COLS]
            with col:
                pegada = sdata["pegada"]
                icono = "✅" if pegada else "❌"
                nombre = sdata["nombre"]
                label = f"{icono} {sid}\n{nombre}"
                
                st.button(
                    label=label,
                    key=f"search_btn_{s_code}_{sid}",
                    on_click=toggle_sticker,
                    args=(s_code, sid),
                    use_container_width=True,
                )
                # Mostramos a qué país/sección pertenece
                st.caption(f"{FLAG_EMOJIS.get(s_code, '🏳')} {s_code}")
    
    st.stop()  # Detenemos la ejecución aquí para no mostrar la sección actual

# Datos de la sección activa
selected_code:   str  = st.session_state.selected_section

# ── Lógica de Resumen General ────────────────────────────────────────────────
if selected_code == "📊 Resumen General":
    st.title("📊 Resumen del Álbum")
    
    # Métricas Globales (ya calculadas arriba)
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Total Álbum", total_figuritas)
    c2.metric("✅ Pegadas", total_pegadas)
    c3.metric("❌ Faltantes", total_faltantes)
    
    st.progress(progreso_global)
    st.write(f"Has completado el **{progreso_global*100:.1f}%** de tu colección.")
    
    st.divider()
    st.subheader("🚩 Progreso por Sección")
    
    # Grid de países para ver progreso individual
    cols_summary = st.columns(4)
    for idx, (code, stickers) in enumerate(album.items()):
        col_idx = idx % 4
        with cols_summary[col_idx]:
            peg = sum(1 for f in stickers.values() if f["pegada"])
            tot = len(stickers)
            pct = peg/tot if tot else 0
            flag = FLAG_EMOJIS.get(code, "🏳")
            
            # Card visual con botón para saltar a la sección
            st.markdown(f"""
                <div class="section-card">
                    <div style="font-size: 1.5rem;">{flag}</div>
                    <div style="font-weight: bold; margin: 5px 0;">{code}</div>
                    <div style="color: var(--text-muted); font-size: 0.8rem;">{peg} / {tot}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.button(
                f"Ver {code}", 
                key=f"goto_{code}", 
                on_click=set_section, 
                args=(code,), 
                use_container_width=True
            )

    # Paginación especial para el resumen (solo Siguiente)
    st.divider()
    st.button(
        "Empezar a revisar secciones ➡️", 
        on_click=set_section, 
        args=(section_keys_real[0],), 
        use_container_width=True
    )
        
    st.stop()

# ── Vista de Sección Individual ──────────────────────────────────────────────

current_section: dict = album[selected_code]
flag_main:       str  = FLAG_EMOJIS.get(selected_code, "🏳")
pais_nombre:     str  = next(iter(current_section.values()))["pais"]

# Índice actual para la lógica de paginación (MEJORA 2)
current_idx: int = NAV_OPTIONS.index(selected_code)
is_first:   bool = current_idx == 0
is_last:    bool = current_idx == len(NAV_OPTIONS) - 1

# ── Título ───────────────────────────────────────────────────────────────────
st.title(f"{flag_main} {pais_nombre}")

# ── Estadísticas de la sección ───────────────────────────────────────────────
sec_total     = len(current_section)
sec_pegadas   = sum(1 for f in current_section.values() if f["pegada"])
sec_faltantes = sec_total - sec_pegadas
sec_progreso  = sec_pegadas / sec_total if sec_total else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("🃏 Total",     sec_total)
m2.metric("✅ Pegadas",   sec_pegadas)
m3.metric("❌ Faltantes", sec_faltantes)

st.progress(sec_progreso)
st.caption(
    f"Progreso: **{sec_progreso * 100:.1f}%** "
    f"({sec_pegadas} de {sec_total} figuritas)"
)

st.divider()

# ── Filtro "Mostrar solo faltantes" ─────────────────────────────────────────
st.toggle(
    "🔍 Mostrar solo faltantes",
    key="show_missing_only",
)
show_missing_only: bool = st.session_state.show_missing_only

# ── Filtrar figuritas según el toggle ───────────────────────────────────────
stickers_a_mostrar: dict = {
    sid: sdata
    for sid, sdata in current_section.items()
    if not show_missing_only or not sdata["pegada"]
}

# ── Mensaje si no hay figuritas para mostrar ─────────────────────────────────
if not stickers_a_mostrar:
    st.success(
        "🎉 ¡Felicitaciones! Tenés **todas las figuritas** de esta sección pegadas. "
        "¡Sección completa!"
    )
else:
    # ── Cuadrícula de botones ────────────────────────────────────────────────
    # Creamos las columnas UNA sola vez y las reutilizamos en el loop.
    # on_click=toggle_sticker ejecuta el callback ANTES del rerender,
    # manteniendo el estado consistente y sin parpadeos.
    columnas = st.columns(GRID_COLS)

    for idx, (sticker_id, sticker_data) in enumerate(stickers_a_mostrar.items()):
        col = columnas[idx % GRID_COLS]
        with col:
            pegada: bool = sticker_data["pegada"]
            icono:  str  = "✅" if pegada else "❌"
            nombre: str  = sticker_data["nombre"]
            # Dos líneas: ID arriba, nombre abajo
            label = f"{icono} {sticker_id}\n{nombre}"

            st.button(
                label=label,
                key=f"btn_{selected_code}_{sticker_id}",
                on_click=toggle_sticker,
                args=(selected_code, sticker_id),
                use_container_width=True,
            )

# ── Paginación: Anterior / Siguiente ────────────────────────────────────────
# MEJORA 2: Botones de navegación entre secciones debajo del grid.
# Se ubican SIEMPRE al final del área principal, independientemente del filtro.
# Los callbacks go_to_prev/next_section actualizan selected_section en
# session_state ANTES del rerender, igual que toggle_sticker.
st.divider()

prev_label = "⬅️ Anterior"
next_label = "Siguiente ➡️"

# Construimos el label contextual con el nombre de la sección vecina
if not is_first:
    prev_code  = NAV_OPTIONS[current_idx - 1]
    if prev_code == "📊 Resumen General":
        prev_label = "⬅️ Resumen"
    else:
        prev_flag  = FLAG_EMOJIS.get(prev_code, "🏳")
        prev_label = f"⬅️ {prev_flag} {prev_code}"

if not is_last:
    next_code  = NAV_OPTIONS[current_idx + 1]
    next_flag  = FLAG_EMOJIS.get(next_code, "🏳")
    next_label = f"{next_flag} {next_code} ➡️"

col_prev, col_counter, col_next = st.columns([2, 1, 2])

with col_prev:
    st.button(
        label=prev_label,
        on_click=go_to_prev_section,
        disabled=is_first,           # deshabilitado en la primera sección
        use_container_width=True,
        key="btn_nav_prev",
    )

with col_counter:
    # Indicador de posición: "5 / 51"
    st.markdown(
        f"<p style='text-align:center; color:var(--text-muted); "
        f"font-family:Barlow Condensed,sans-serif; font-size:1rem; "
        f"margin-top:8px;'>{current_idx + 1} / {len(NAV_OPTIONS)}</p>",
        unsafe_allow_html=True,
    )

with col_next:
    st.button(
        label=next_label,
        on_click=go_to_next_section,
        disabled=is_last,            # deshabilitado en la última sección
        use_container_width=True,
        key="btn_nav_next",
    )