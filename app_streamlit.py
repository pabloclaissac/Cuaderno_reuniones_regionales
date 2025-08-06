import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import re
import openpyxl
from openpyxl.utils import get_column_letter
import numpy as np

# Configuración de la página
st.set_page_config(layout="wide", page_title="Editor de Cuadernos Regionales")

# Constantes y estilos
BURDEOS = "#800020"
AZUL_OSCURO = "#003366"
GRIS_OSCURO = "#333333"
EXCEL_FILE = "Planificación 2025.xlsx"
SHEET_NAME = "Hoja3"
DB_FILE = "cuadernos.db"

# Estilos CSS personalizados mejorados
st.markdown(f"""
    <style>
    /* Estilos generales de la barra lateral */
    [data-testid="stSidebar"] {{
        background-color: {BURDEOS};
        color: white;
    }}
    
    /* Título principal de la barra lateral */
    .sidebar-title {{
        font-size: 1.4rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 0.5rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.2);
    }}
    
    /* Contenedor de botones */
    .tomo-container {{
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 0 0.5rem;
        max-height: calc(100vh - 150px);
        overflow-y: auto;
    }}
    
    /* Botones de regiones */
    .tomo-button {{
        background-color: {BURDEOS};
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 4px;
        padding: 0.7rem 0.5rem;
        text-align: center;
        font-size: 0.95rem;
        font-weight: bold;
        transition: all 0.3s ease;
        margin: 0;
    }}
    
    .tomo-button:hover {{
        background-color: #a04060;
        transform: translateY(-1px);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }}
    
    .active-tomo {{
        background-color: #a04060 !important;
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }}
    
    /* Área del editor */
    .editor-container {{
        background-image: url('https://i.imgur.com/hoja_fondo.png');
        background-size: contain;
        background-repeat: no-repeat;
        padding: 125px 54px 64px 54px;
        min-height: 940px;
    }}
    
    /* Barra de herramientas */
    .toolbar-section {{
        margin-bottom: 1.2rem;
    }}
    
    /* Botones de búsqueda */
    .search-buttons {{
        display: flex;
        gap: 0.8rem;
        margin-top: 1.5rem;
        justify-content: flex-end;
    }}
    
    .search-button {{
        flex: 1;
    }}
    
    /* Textarea del editor */
    .stTextArea textarea {{
        background-color: transparent !important;
        line-height: 1.5;
        font-size: 1.05rem;
    }}
    
    /* Encabezado principal */
    .main-header {{
        margin-bottom: 1.5rem;
        border-bottom: 2px solid {BURDEOS};
        padding-bottom: 0.8rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# Clase para manejar Excel
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

# Clase para manejar la base de datos (conexión por hilo)
class DatabaseManager:
    def __init__(self, db_name=DB_FILE):
        self.db_name = db_name
        self.create_tables()
    
    def get_connection(self):
        """Crea una nueva conexión para cada operación"""
        return sqlite3.connect(self.db_name)
    
    def create_tables(self):
        """Crea las tablas si no existen"""
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
        """Obtiene el ID de un cuaderno, creándolo si no existe"""
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
        """Guarda una hoja en la base de datos"""
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
        """Carga una hoja desde la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT contenido FROM hojas WHERE cuaderno_id = (SELECT id FROM cuadernos WHERE nombre = ?)",
            (cuaderno_nombre,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else ""

# Inicialización de la aplicación
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

# Interfaz principal
def main():
    init_session()
    
    # Barra lateral mejorada
    with st.sidebar:
        # Título con estilo mejorado
        st.markdown('<div class="sidebar-title">CUADERNOS DE NOTAS</div>', unsafe_allow_html=True)
        
        # Contenedor para los botones con scroll
        with st.container():
            st.markdown('<div class="tomo-container">', unsafe_allow_html=True)
            
            for tomo in st.session_state.tomo_names:
                # Botones con estilo mejorado
                if st.button(
                    tomo, 
                    key=f"btn_{tomo}", 
                    use_container_width=True,
                    type="primary" if tomo == st.session_state.current_tomo else "secondary"
                ):
                    st.session_state.current_tomo = tomo
                    st.session_state.contenido_tomo = st.session_state.db_manager.cargar_hoja(tomo)
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Área principal
    st.markdown(f'<div class="main-header">Editor de Cuadernos Regionales - {st.session_state.current_tomo}</div>', 
               unsafe_allow_html=True)
    
    # Barra de herramientas
    with st.container():
        col1, col2, col3 = st.columns([4, 3, 2])
        
        with col1:
            st.markdown('<div class="toolbar-section">', unsafe_allow_html=True)
            st.session_state.search_term = st.text_input(
                "Buscar:", 
                st.session_state.search_term, 
                key="search_input",
                placeholder="Buscar en el documento..."
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="toolbar-section">', unsafe_allow_html=True)
            st.selectbox("Temas", st.session_state.temas, key="selected_theme", index=0)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div class="toolbar-section">', unsafe_allow_html=True)
            st.button("➕ Comentario", key="btn_comment", use_container_width=True)
            st.button("🔍 Buscar Comentarios", key="btn_search_comments", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Editor de texto
    with st.container():
        st.markdown('<div class="editor-container">', unsafe_allow_html=True)
        new_content = st.text_area(
            "Contenido:", 
            st.session_state.contenido_tomo, 
            height=700,
            key="editor_area",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if new_content != st.session_state.contenido_tomo:
            st.session_state.contenido_tomo = new_content
            st.session_state.db_manager.guardar_hoja(
                st.session_state.current_tomo, 
                st.session_state.contenido_tomo)
    
    # Botones de búsqueda con mejor diseño
    st.markdown('<div class="search-buttons">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("◄ Anterior", key="btn_prev", use_container_width=True, 
                    help="Ir a la coincidencia anterior"):
            search_text("prev")
    
    with col2:
        if st.button("Siguiente ►", key="btn_next", use_container_width=True,
                    help="Ir a la siguiente coincidencia"):
            search_text("next")
    
    with col3:
        if st.button("✕ Limpiar búsqueda", key="btn_clear", use_container_width=True,
                    help="Limpiar resultados de búsqueda"):
            st.session_state.search_term = ""
            st.session_state.search_results = []
            st.session_state.current_search_index = 0
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón para insertar tema
    if st.button("📝 Insertar Tema", key="btn_insert_theme", use_container_width=True,
                help="Insertar el tema seleccionado en el editor"):
        insert_theme()

# Funciones de búsqueda
def search_text(direction):
    if not st.session_state.search_term:
        return
    
    content = st.session_state.contenido_tomo
    search_term = st.session_state.search_term.lower()
    matches = [m.start() for m in re.finditer(re.escape(search_term), content.lower())]
    
    if not matches:
        st.warning("No se encontraron coincidencias")
        return
    
    if direction == "next":
        if st.session_state.current_search_index < len(matches) - 1:
            st.session_state.current_search_index += 1
        else:
            st.session_state.current_search_index = 0
    else:  # prev
        if st.session_state.current_search_index > 0:
            st.session_state.current_search_index -= 1
        else:
            st.session_state.current_search_index = len(matches) - 1
    
    # Actualizar el editor para mostrar la coincidencia
    start_pos = matches[st.session_state.current_search_index]
    end_pos = start_pos + len(st.session_state.search_term)
    st.session_state.editor_area = content
    st.experimental_rerun()

# Función para insertar temas
def insert_theme():
    theme = st.session_state.selected_theme
    if not theme:
        return
    
    # Insertar el tema en el contenido
    new_content = st.session_state.contenido_tomo + f"\n{theme}\n"
    st.session_state.contenido_tomo = new_content
    
    # Guardar en Excel
    ExcelManager.save_to_excel(
        st.session_state.current_tomo,
        theme,
        new_content)
    
    # Actualizar la base de datos
    st.session_state.db_manager.guardar_hoja(
        st.session_state.current_tomo, 
        new_content)
    
    st.rerun()

if __name__ == "__main__":
    main()