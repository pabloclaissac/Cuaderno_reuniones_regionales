import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import re
import openpyxl
import numpy as np

# === CONFIGURACIÓN DE PÁGINA (DEBE SER LA PRIMERA INVOCACIÓN) ===
st.set_page_config(layout="wide", page_title="Editor de Cuadernos Regionales")

# === CONSTANTES Y ARCHIVOS ===
BURDEOS = "#ac042b"
EXCEL_FILE = "Planificación 2025.xlsx"
SHEET_NAME = "Hoja3"
DB_FILE = "cuadernos.db"

# Anchos configurables (ajusta si quieres)
REGION_BUTTON_WIDTH = "150px"  # ancho de botones en la barra lateral
TOOLBAR_GAP_PX = 10  # espaciado vertical pedido

# === CSS GLOBAL ===
# - estilos para la sidebar (botones más angostos)
# - estilos generales del layout del editor
st.markdown(f"""
    <style>
    /* Sidebar: fondo y estilo */
    [data-testid="stSidebar"] {{
        background-color: {BURDEOS};
        color: white;
        padding-top: 8px;
    }}
    .sidebar-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: white;
        text-align: center;
        margin-bottom: 8px;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }}

    /* Limitar ancho de botones SOLO dentro de la sidebar */
    [data-testid="stSidebar"] div.stButton > button {{
        width: {REGION_BUTTON_WIDTH} !important;
        height: 36px !important;
        font-size: 0.9rem !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        margin: 4px auto !important;
        display: block !important;
        background-color: #ffffff10 !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }}
    [data-testid="stSidebar"] div.stButton > button:hover {{
        background-color: rgba(255,255,255,0.06) !important;
        transform: translateY(-1px);
    }}

    /* Contenedores principales */
    .main-header {{
        font-size: 1.1rem;
        font-weight: 700;
        padding-bottom: 8px;
        border-bottom: 2px solid {BURDEOS};
        margin-bottom: 6px;
    }}

    .toolbar-container {{
        background-color: #ffffff;
        padding: 8px;
        border-radius: 6px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}

    /* Espaciado utilizable */
    .spacer-vertical {{
        height: {TOOLBAR_GAP_PX}px;
    }}

    /* Ajuste del textarea (editor) */
    .stTextArea > div > textarea {{
        line-height: 1.4 !important;
        font-size: 1rem !important;
    }}
    </style>
""", unsafe_allow_html=True)

# === CLASES DE SOPORTE (Excel y DB) ===
class ExcelManager:
    @staticmethod
    def get_next_empty_row(worksheet):
        row = 1
        while worksheet.cell(row=row, column=1).value is not None:
            row += 1
        return row

    @staticmethod
    def save_to_excel(tomo_name, tema, detalle):
        try:
            if not os.path.exists(EXCEL_FILE):
                wb = openpyxl.Workbook()
                # borrar sheet "Sheet" si existe y crear la hoja deseada
                if "Sheet" in wb.sheetnames:
                    del wb["Sheet"]
                sheet = wb.create_sheet(SHEET_NAME)
                sheet['A1'] = "Dirección Regional"
                sheet['B1'] = "Fecha de Reunión"
                sheet['C1'] = "Ítem de monitoreo"
                sheet['D1'] = "Detalle"
            else:
                wb = openpyxl.load_workbook(EXCEL_FILE)
                if SHEET_NAME in wb.sheetnames:
                    sheet = wb[SHEET_NAME]
                else:
                    sheet = wb.create_sheet(SHEET_NAME)
                    sheet['A1'] = "Dirección Regional"
                    sheet['B1'] = "Fecha de Reunión"
                    sheet['C1'] = "Ítem de monitoreo"
                    sheet['D1'] = "Detalle"

            next_row = ExcelManager.get_next_empty_row(sheet)
            sheet[f'A{next_row}'] = tomo_name
            sheet[f'B{next_row}'] = datetime.now().strftime("%d/%m/%Y")
            sheet[f'C{next_row}'] = tema
            sheet[f'D{next_row}'] = detalle
            wb.save(EXCEL_FILE)
            return True
        except Exception as e:
            st.error(f"Error al guardar en Excel: {e}")
            return False

class DatabaseManager:
    def __init__(self, db_name=DB_FILE):
        self.db_name = db_name
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cuadernos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                fecha_creacion TEXT,
                fecha_modificacion TEXT
            )
        ''')
        cursor.execute('''
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
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cuadernos WHERE nombre = ?", (nombre,))
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]
        else:
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO cuadernos (nombre, fecha_creacion, fecha_modificacion) VALUES (?, ?, ?)",
                (nombre, now, now)
            )
            id = cursor.lastrowid
            conn.commit()
            conn.close()
            return id

    def guardar_hoja(self, cuaderno_nombre, contenido):
        cuaderno_id = self.get_cuaderno_id(cuaderno_nombre)
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("SELECT id FROM hojas WHERE cuaderno_id = ?", (cuaderno_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "UPDATE hojas SET contenido = ?, fecha_modificacion = ? WHERE id = ?",
                (contenido, now, existing[0])
            )
        else:
            cursor.execute(
                "INSERT INTO hojas (cuaderno_id, contenido, fecha_creacion, fecha_modificacion) VALUES (?, ?, ?, ?)",
                (cuaderno_id, contenido, now, now)
            )
        conn.commit()
        conn.close()

    def cargar_hoja(self, cuaderno_nombre):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT contenido FROM hojas WHERE cuaderno_id = (SELECT id FROM cuadernos WHERE nombre = ?)",
            (cuaderno_nombre,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else ""

# === INICIALIZACIÓN DE ESTADO DE SESIÓN ===
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
        st.session_state.contenido_tomo = st.session_state.db_manager.cargar_hoja(
            st.session_state.current_tomo)
    if "search_term" not in st.session_state:
        st.session_state.search_term = ""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "current_search_index" not in st.session_state:
        st.session_state.current_search_index = 0

# === FUNCIONES: BÚSQUEDA E INSERCIÓN ===
def search_text(direction):
    # No hacer nada si no hay término
    if not st.session_state.search_term:
        return

    content = st.session_state.contenido_tomo or ""
    search_term = st.session_state.search_term.lower()
    matches = [m.start() for m in re.finditer(re.escape(search_term), content.lower())]

    if not matches:
        st.warning("No se encontraron coincidencias")
        return

    if direction == "next":
        st.session_state.current_search_index = (st.session_state.current_search_index + 1) % len(matches)
    else:  # prev
        st.session_state.current_search_index = (st.session_state.current_search_index - 1) % len(matches)

    # opcional: centramos el editor mostrando todo el contenido (no hay highlight nativo)
    st.session_state.editor_area = content
    st.rerun()

def insert_theme():
    theme = st.session_state.get("selected_theme", "")
    if not theme:
        return

    # Insertar el tema al final del contenido
    new_content = (st.session_state.contenido_tomo or "") + f"\n{theme}\n"
    st.session_state.contenido_tomo = new_content

    # Guardar en Excel y DB
    ExcelManager.save_to_excel(st.session_state.current_tomo, theme, new_content)
    st.session_state.db_manager.guardar_hoja(st.session_state.current_tomo, new_content)
    st.rerun()

# === INTERFAZ PRINCIPAL ===
def main():
    init_session()

    # ----------- BARRA LATERAL (CUADERNOS/TOMOS) -----------
    with st.sidebar:
        st.markdown('<div class="sidebar-title">CUADERNOS DE NOTAS</div>', unsafe_allow_html=True)
        st.markdown('<div style="padding:6px 8px 12px 8px;">', unsafe_allow_html=True)

        for tomo in st.session_state.tomo_names:
            # usamos botones típicos; CSS dirigirá a los botones de la sidebar
            if st.button(tomo, key=f"btn_tomo_{tomo}"):
                st.session_state.current_tomo = tomo
                st.session_state.contenido_tomo = st.session_state.db_manager.cargar_hoja(tomo)
                # reset búsqueda
                st.session_state.search_term = ""
                st.session_state.search_results = []
                st.session_state.current_search_index = 0
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ----------- ÁREA PRINCIPAL (CABECERA + TOOLBAR + EDITOR) -----------
    st.markdown(f'<div class="main-header">Editor de Cuadernos Regionales - {st.session_state.current_tomo}</div>', unsafe_allow_html=True)

    # TOOLBAR superior dividida en 5 columnas (1, espacio, 3, espacio, 5)
    with st.container():
        st.markdown('<div class="toolbar-container">', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns([1, 0.06, 1, 0.06, 1])

        # --- Columna 1: caja búsqueda + botones (fila) ---
        with col1:
            st.session_state.search_term = st.text_input(
                "Buscar:", st.session_state.search_term, key="search_input",
                placeholder="Buscar en el documento..."
            )
            st.markdown('<div class="spacer-vertical"></div>', unsafe_allow_html=True)

            bprev, bnext, bclear = st.columns([1,1,1])
            with bprev:
                if st.button("◄ Anterior", key="btn_prev"):
                    search_text("prev")
            with bnext:
                if st.button("Siguiente ►", key="btn_next"):
                    search_text("next")
            with bclear:
                if st.button("✕ Limpiar", key="btn_clear"):
                    st.session_state.search_term = ""
                    st.session_state.search_results = []
                    st.session_state.current_search_index = 0
                    st.rerun()

        # --- Columna 3: selectbox de temas + botón insertar ---
        with col3:
            st.selectbox("Temas", st.session_state.temas, key="selected_theme", index=0)
            st.markdown('<div class="spacer-vertical"></div>', unsafe_allow_html=True)
            if st.button("📝 Insertar Tema", key="btn_insert_theme"):
                insert_theme()

        # --- Columna 5: Comentarios / Buscar Comentarios / Guardar (vertical con 10px) ---
        with col5:
            if st.button("➕ Comentario", key="btn_comment"):
                # Aquí podrías abrir modal o desplegar un input para crear comentario
                # por ahora conservamos funcionalidad placeholder (sin mensaje innecesario)
                st.session_state._last_action = "abrir_comentario"  # marca interna si necesitas
            st.markdown('<div class="spacer-vertical"></div>', unsafe_allow_html=True)

            if st.button("🔍 Buscar Comentarios", key="btn_search_comments"):
                st.session_state._last_action = "buscar_comentarios"
            st.markdown('<div class="spacer-vertical"></div>', unsafe_allow_html=True)

            if st.button("💾 Guardar", key="btn_save"):
                st.session_state.db_manager.guardar_hoja(
                    st.session_state.current_tomo,
                    st.session_state.contenido_tomo or ""
                )
                st.success("Documento guardado correctamente")

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- EDITOR: textarea que muestra y guarda contenido ----------
    with st.container():
        st.markdown('<div style="margin-top:8px;">', unsafe_allow_html=True)
        new_content = st.text_area(
            "Contenido:",
            value=st.session_state.contenido_tomo or "",
            height=520,
            key="editor_area",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Guardar cambios automáticamente si hay edición (y actualizar DB)
        if new_content != (st.session_state.contenido_tomo or ""):
            st.session_state.contenido_tomo = new_content
            st.session_state.db_manager.guardar_hoja(
                st.session_state.current_tomo,
                st.session_state.contenido_tomo
            )

# === EJECUCIÓN ===
if __name__ == "__main__":
    main()



