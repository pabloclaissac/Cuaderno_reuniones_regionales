# app_streamlit.py
import streamlit as st
import sqlite3
import json
from datetime import datetime
import re
import streamlit.components.v1 as components

# -------------------------
# Configuración (estética)
# -------------------------
DB_FILE = "cuadernos.db"

COLOR_PRIMARIO = "#88001b"
COLOR_PRIMARIO_TEXTO = "#ffffff"
COLOR_SECUNDARIO = "#a83232"
COLOR_FONDO = "#f5f5f5"
COLOR_BORDE = "#dcdcdc"
COLOR_BOTON_HOVER = "#e6e6e6"
COLOR_BOTON_ACTIVO = "#6a0f1a"

ANCHO_SIDEBAR = "250px"
ANCHO_BOTON_REGION = "150px"
ANCHO_BOTON_UNICO = "160px"

ALTURA_EDITOR = "calc(100vh - 250px)"
TAMANO_FUENTE_EDITOR = "0.75rem"
ALTURA_BOTONES = "38px"

st.set_page_config(layout="wide", page_title="Editor de Cuadernos Regionales", page_icon="📘")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; }}
    [data-testid="stSidebar"] {{
        background-color: {COLOR_PRIMARIO};
        color: {COLOR_PRIMARIO_TEXTO};
        min-width: {ANCHO_SIDEBAR};
        max-width: {ANCHO_SIDEBAR};
    }}
    .sidebar-title {{
        font-size: 1rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        padding: 0.5rem;
        color: {COLOR_PRIMARIO_TEXTO};
        border-bottom: 2px solid rgba(255,255,255,0.2);
    }}
    .stButton button {{
        background-color: {COLOR_PRIMARIO};
        color: {COLOR_PRIMARIO_TEXTO} !important;
        border: 0px solid rgba(255,255,255,0.3);
        border-radius: 4px;
        padding: 0.6rem 0.6rem;
        font-size: 0.1rem;
        font-weight: bold;
        transition: all 0.3s ease;
        width: {ANCHO_BOTON_REGION};
        margin: 0.1rem auto;
    }}
    .stButton button:hover {{
        background-color: {COLOR_SECUNDARIO};
        transform: translateY(-1px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    .stButton button[kind="primary"] {{
        background-color: {COLOR_BOTON_ACTIVO} !important;
    }}
    .main-container {{ background-color: transparent; padding: 0; }}
    .main-header {{
        color: {COLOR_PRIMARIO};
        font-size: 1rem;
        font-weight: bold;
        margin: 0.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {COLOR_PRIMARIO};
    }}
    .toolbar-container {{
        background-color: transparent;
        padding: 0.5rem 0;
        margin-bottom: 0.5rem;
        display: flex;
        gap: 1rem;
        align-items: center;
        border-bottom: 1px solid {COLOR_BORDE};
    }}
    .editor-container {{
        background-color: {COLOR_FONDO};
        padding: 1rem;
        border-radius: 6px;
    }}
    .stTextArea textarea {{
        background-color: white !important;
        line-height: 1.5;
        font-size: {TAMANO_FUENTE_EDITOR};
        height: {ALTURA_EDITOR} !important;
        border: 1px solid {COLOR_BORDE} !important;
        border-radius: 4px !important;
    }}
    .stTextInput input, .stSelectbox select {{
        line-height: 1.5;
        height: {ALTURA_BOTONES} !important;
        border: 1px solid {COLOR_BORDE} !important;
        border-radius: 4px !important;
    }}
    .stButton button:not([kind="primary"]):not([kind="secondary"]) {{
        background-color: white;
        color: #333 !important;
        border: 1.5px solid {COLOR_BORDE};
        height: {ALTURA_BOTONES} !important;
    }}
    .stButton button:not([kind="primary"]):not([kind="secondary"]):hover {{
        background-color: {COLOR_BOTON_HOVER} !important;
    }}
    div[data-testid="column"]:has(button) button {{
        width: {ANCHO_BOTON_UNICO} !important;
        min-width: {ANCHO_BOTON_UNICO} !important;
    }}
    .stTextInput > label, .stSelectbox > label {{ display: none !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 0.5rem; padding: 0; margin-bottom: 1rem; }}
    .stTabs [data-baseweb="tab"] {{
        padding: 0.5rem 1rem;
        border-radius: 4px 4px 0 0;
        background-color: #f0f0f0;
        border: 1px solid #dcdcdc;
        margin-right: 0 !important;
    }}
    .stTabs [data-baseweb="tab"]:hover {{ background-color: #e6e6e6; }}
    .stTabs [aria-selected="true"] {{
        background-color: white;
        border-bottom: 2px solid {COLOR_PRIMARIO};
        color: {COLOR_PRIMARIO};
    }}
    </style>
""", unsafe_allow_html=True)

# -------------------------
# Base de datos
# -------------------------
class DatabaseManager:
    def __init__(self, db_name=DB_FILE):
        self.db_name = db_name
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS cuadernos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                fecha_creacion TEXT,
                fecha_modificacion TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS hojas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cuaderno_id INTEGER NOT NULL,
                contenido TEXT,
                fecha_creacion TEXT,
                fecha_modificacion TEXT,
                FOREIGN KEY (cuaderno_id) REFERENCES cuadernos (id)
            )
        ''')
        conn.commit()
        conn.close()

    def get_cuaderno_id(self, nombre):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM cuadernos WHERE nombre = ?", (nombre,))
        r = c.fetchone()
        if r:
            conn.close()
            return r[0]
        now = datetime.now().isoformat()
        c.execute("INSERT INTO cuadernos (nombre, fecha_creacion, fecha_modificacion) VALUES (?, ?, ?)",
                  (nombre, now, now))
        cid = c.lastrowid
        conn.commit()
        conn.close()
        return cid

    def guardar_hoja(self, cuaderno_nombre, contenido):
        cuaderno_id = self.get_cuaderno_id(cuaderno_nombre)
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute("SELECT id FROM hojas WHERE cuaderno_id = ?", (cuaderno_id,))
        existing = c.fetchone()
        if existing:
            c.execute("UPDATE hojas SET contenido = ?, fecha_modificacion = ? WHERE id = ?",
                      (contenido, now, existing[0]))
        else:
            c.execute("INSERT INTO hojas (cuaderno_id, contenido, fecha_creacion, fecha_modificacion) VALUES (?, ?, ?, ?)",
                      (cuaderno_id, contenido, now, now))
        conn.commit()
        conn.close()

    def cargar_hoja(self, cuaderno_nombre):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT contenido FROM hojas WHERE cuaderno_id = (SELECT id FROM cuadernos WHERE nombre = ?)",
                  (cuaderno_nombre,))
        r = c.fetchone()
        conn.close()
        return r[0] if r else ""

# -------------------------
# Session init
# -------------------------
def init_session():
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    if "tomo_names" not in st.session_state:
        st.session_state.tomo_names = [
            "Arica", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo",
            "Valparaíso", "R. Metropolitana", "O'Higgins", "Maule", "Ñuble",
            "Bío-Bío", "Araucanía", "Los Ríos", "Los Lagos", "Aysén",
            "Magallanes", "General"
        ]
    if "temas" not in st.session_state:
        st.session_state.temas = [
            "Clima Laboral", "Ejecución Presupuestaria", "Indicadores de desempeño",
            "Informática", "Infraestructura", "Planificación", "Plan de SSPP",
            "Político Institucional", "Otros", "Temas Dpto. Personas"
        ]
    if "current_tomo" not in st.session_state:
        st.session_state.current_tomo = st.session_state.tomo_names[0]
    if "contenido_tomo" not in st.session_state:
        st.session_state.contenido_tomo = st.session_state.db_manager.cargar_hoja(st.session_state.current_tomo)
    if "search_input" not in st.session_state:
        st.session_state.search_input = ""
    if "search_term" not in st.session_state:
        st.session_state.search_term = ""
    if "current_search_index" not in st.session_state:
        st.session_state.current_search_index = -1
    if "editor_update_id" not in st.session_state:
        st.session_state.editor_update_id = 0
    if "focus_end" not in st.session_state:
        st.session_state.focus_end = False

# -------------------------
# Generador HTML del editor (CodeMirror)
# -------------------------
def generate_editor_html(initial_content: str, search_term: str, search_index: int, editor_update_id: int, focus_end: bool):
    """
    Devuelve HTML/JS que ejecuta CodeMirror.
    initial_content: string raw
    search_term: string raw (puede estar vacio)
    search_index: integer (0-based) o -1
    editor_update_id: entero pasado de servidor -> el cliente lo devuelve al postear
    focus_end: bool -> si True coloca cursor al final en la inicialización
    """
    safe_content = json.dumps(initial_content)   # produce cadena JS segura
    safe_search = json.dumps(search_term)
    # search_index and editor_update_id are numbers; pass directly
    html_code = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8"/>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/codemirror.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/codemirror.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.15/mode/markdown/markdown.min.js"></script>
        <style>
          html, body {{ margin:0; padding:0; height:100%; }}
          .CodeMirror {{ height:100%; font-size:12px; line-height:1.4; }}
          .CodeMirror {{ background: white; border: 1px solid #dcdcdc; border-radius:4px; padding:6px; box-sizing:border-box; }}
          .cm-match {{ background: yellow; }}
          .cm-active-match {{ background: orange; }}
          .CodeMirror pre {{ white-space: pre-wrap; word-break: break-word; }}
        </style>
      </head>
      <body>
        <textarea id="editor_textarea"></textarea>
        <script>
        (function(){{
          const initialContent = {safe_content};
          const searchTerm = {safe_search};
          const serverSearchIndex = {search_index};
          const serverEditorUpdateId = {editor_update_id};
          const focusEnd = {str(focus_end).lower()};

          // Init CodeMirror
          var editor = CodeMirror.fromTextArea(document.getElementById('editor_textarea'), {{
            lineNumbers: false,
            lineWrapping: true,
            viewportMargin: Infinity,
            mode: "markdown"
          }});

          editor.setValue(initialContent);

          // place cursor at end if asked
          if (focusEnd) {{
            const doc = editor.getDoc();
            const endPos = doc.posFromIndex(doc.getValue().length);
            doc.setCursor(endPos);
            editor.focus();
            // ensure visible
            setTimeout(function() {{
              editor.scrollIntoView(endPos, 100);
            }}, 80);
          }}

          // Helpers for marking matches
          var marks = [];
          function clearMarks() {{
            for (let m of marks) {{
              try {{ m.clear(); }} catch(e){{}}
            }}
            marks = [];
          }}

          function markAll(term, activeIndex) {{
            clearMarks();
            if (!term || !term.length) return 0;
            const doc = editor.getDoc();
            const content = doc.getValue();
            const re = new RegExp(term.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&'), 'ig');
            let m;
            let idx = 0;
            const matches = [];
            while ((m = re.exec(content)) !== null) {{
              matches.push({{start: m.index, end: m.index + m[0].length}});
            }}
            for (let i=0; i<matches.length; i++) {{
              const startIndex = matches[i].start;
              const endIndex = matches[i].end;
              const from = doc.posFromIndex(startIndex);
              const to = doc.posFromIndex(endIndex);
              if (i === activeIndex) {{
                marks.push(doc.markText(from, to, {{className: 'cm-active-match'}}));
              }} else {{
                marks.push(doc.markText(from, to, {{className: 'cm-match'}}));
              }}
            }}
            // scroll to active if present
            if (activeIndex !== -1 && activeIndex < matches.length) {{
              const pos = doc.posFromIndex(matches[activeIndex].start);
              setTimeout(function(){{ editor.scrollIntoView(pos, 150); }}, 60);
            }}
            return matches.length;
          }}

          // Debounced sender (save)
          var sendTimeout = null;
          function postToStreamlit(obj) {{
            // streamlit expects messages shaped like this:
            window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', value: JSON.stringify(obj)}}, '*');
          }}
          function scheduleSend() {{
            if (sendTimeout) clearTimeout(sendTimeout);
            sendTimeout = setTimeout(function() {{
              try {{
                var content = editor.getValue();
                var cursorIndex = editor.getDoc().indexFromPos(editor.getDoc().getCursor());
                var scrollInfo = editor.getScrollInfo();
                postToStreamlit({{content: content, cursor_index: cursorIndex, scroll_top: scrollInfo.top, editor_update_id: serverEditorUpdateId}});
              }} catch(e) {{ console.error(e); }}
            }}, 600);
          }}

          editor.on('change', function() {{
            scheduleSend();
          }});

          // initial highlight per server values
          var matchCount = markAll(searchTerm, serverSearchIndex >= 0 ? serverSearchIndex : -1);

          // Send initial content once so server can sync if necessary
          setTimeout(function(){{
            try {{
              postToStreamlit({{content: editor.getValue(), cursor_index: editor.getDoc().indexFromPos(editor.getDoc().getCursor()), editor_update_id: serverEditorUpdateId}});
            }} catch(e){{}}
          }}, 250);

        }})();
        </script>
      </body>
    </html>
    """
    return html_code

# -------------------------
# Lógica de búsqueda / helpers
# -------------------------
def _count_matches(content: str, term: str) -> int:
    if not term or not term.strip():
        return 0
    return len(list(re.finditer(re.escape(term), content, re.IGNORECASE)))

def start_search_from_input():
    # called on Enter in input
    st.session_state.search_term = st.session_state.search_input
    if st.session_state.search_term.strip():
        count = _count_matches(st.session_state.contenido_tomo or "", st.session_state.search_term)
        if count:
            st.session_state.current_search_index = 0
        else:
            st.session_state.current_search_index = -1
    else:
        st.session_state.current_search_index = -1
    st.session_state.editor_update_id += 1

# -------------------------
# Interfaz principal
# -------------------------
def main():
    init_session()

    # Sidebar (tomos)
    with st.sidebar:
        st.markdown('<div class="sidebar-title">CUADERNOS REGIONALES</div>', unsafe_allow_html=True)
        for tomo in st.session_state.tomo_names:
            if st.button(tomo, key=f"btn_{tomo}", use_container_width=True,
                         type="primary" if tomo == st.session_state.current_tomo else "secondary"):
                st.session_state.current_tomo = tomo
                st.session_state.contenido_tomo = st.session_state.db_manager.cargar_hoja(tomo)
                # reset search and force cursor to end
                st.session_state.search_input = ""
                st.session_state.search_term = ""
                st.session_state.current_search_index = -1
                st.session_state.focus_end = True
                st.session_state.editor_update_id += 1

    # Header
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="main-header">Editor de Cuaderno - Región de {st.session_state.current_tomo}</div>', unsafe_allow_html=True)

    # Tabs (Busqueda / Temas / Acciones)
    with st.container():
        tab1, tab2, tab3 = st.tabs(["🔍 Búsqueda", "📝 Temas", "⚙️ Acciones"])

        with tab1:
            col_buscar, col_prev, col_next, col_clear = st.columns([4, 1, 1, 1])
            with col_buscar:
                st.text_input("Buscar:", value=st.session_state.search_input, key="search_input",
                              placeholder="Buscar en el documento...", label_visibility="collapsed",
                              on_change=start_search_from_input)
            with col_prev:
                if st.button("◄ Anterior", key="btn_prev", use_container_width=True):
                    # ensure search_term exists
                    if not st.session_state.search_term and st.session_state.search_input:
                        start_search_from_input()
                    term = st.session_state.search_term.strip()
                    if term:
                        count = _count_matches(st.session_state.contenido_tomo or "", term)
                        if count == 0:
                            st.warning("No se encontraron coincidencias")
                            st.session_state.current_search_index = -1
                        else:
                            if st.session_state.current_search_index == -1:
                                st.session_state.current_search_index = count - 1
                            else:
                                st.session_state.current_search_index = (st.session_state.current_search_index - 1) % count
                    st.session_state.editor_update_id += 1
            with col_next:
                if st.button("Siguiente ►", key="btn_next", use_container_width=True):
                    if not st.session_state.search_term and st.session_state.search_input:
                        start_search_from_input()
                    term = st.session_state.search_term.strip()
                    if term:
                        count = _count_matches(st.session_state.contenido_tomo or "", term)
                        if count == 0:
                            st.warning("No se encontraron coincidencias")
                            st.session_state.current_search_index = -1
                        else:
                            if st.session_state.current_search_index == -1:
                                st.session_state.current_search_index = 0
                            else:
                                st.session_state.current_search_index = (st.session_state.current_search_index + 1) % count
                    st.session_state.editor_update_id += 1
            with col_clear:
                if st.button("Limpiar", key="btn_clear", use_container_width=True):
                    for k in ("search_input", "search_term", "current_search_index"):
                        if k in st.session_state:
                            del st.session_state[k]
                    st.session_state.editor_update_id += 1
                    st.rerun()

        with tab2:
            col_tema, col_insertar = st.columns([3, 1])
            with col_tema:
                st.selectbox("Temas:", options=st.session_state.temas, key="selected_theme", index=0, label_visibility="collapsed")
            with col_insertar:
                if st.button("Insertar Tema", key="btn_insert_theme", use_container_width=True):
                    theme = st.session_state.selected_theme
                    if theme:
                        st.session_state.contenido_tomo = (st.session_state.contenido_tomo or "") + "\n" + theme + "\n"
                        st.session_state.db_manager.guardar_hoja(st.session_state.current_tomo, st.session_state.contenido_tomo)
                        st.session_state.editor_update_id += 1

        with tab3:
            col_comentario, col_buscar_com, col_guardar = st.columns([1, 1, 1])
            with col_comentario:
                if st.button("➕", key="btn_comment", help="Agregar comentario", use_container_width=True):
                    pass
            with col_buscar_com:
                if st.button("🔍", key="btn_search_comments", help="Buscar comentarios", use_container_width=True):
                    pass
            with col_guardar:
                if st.button("💾", key="btn_save", help="Guardar documento", use_container_width=True):
                    st.session_state.db_manager.guardar_hoja(st.session_state.current_tomo, st.session_state.contenido_tomo)
                    st.success("Documento guardado correctamente")

    # Editor area (CodeMirror)
    with st.container():
        st.markdown('<div class="editor-container">', unsafe_allow_html=True)

        initial_content = st.session_state.contenido_tomo or ""
        # choose search term - prefer executed term, fallback to input
        search_term = st.session_state.search_term or st.session_state.search_input or ""
        search_index = st.session_state.current_search_index if (search_term and search_term.strip()) else -1

        # Build editor HTML and render (editor_update_id forces new iframe when changed)
        editor_html = generate_editor_html(initial_content=initial_content,
                                           search_term=search_term,
                                           search_index=search_index,
                                           editor_update_id=st.session_state.editor_update_id,
                                           focus_end=st.session_state.focus_end)

        posted = components.html(editor_html, height=520, scrolling=True)

        # focus_end used once
        st.session_state.focus_end = False

        # If iframe returned a posted value (JSON string), parse and save changes in real time
        if posted:
            try:
                data = json.loads(posted)
                content = data.get("content")
                posted_update_id = data.get("editor_update_id", None)
                # Only accept posted content (save) if content changed
                if content is not None and content != st.session_state.contenido_tomo:
                    st.session_state.contenido_tomo = content
                    st.session_state.db_manager.guardar_hoja(st.session_state.current_tomo, content)
                # store last cursor if needed
                if "cursor_index" in data:
                    st.session_state.last_cursor = data.get("cursor_index")
            except Exception:
                # ignore parse errors
                pass

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()





