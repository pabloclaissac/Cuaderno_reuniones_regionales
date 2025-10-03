# app_encabezado.py 
# -*- coding: utf-8 -*-
import os
import sqlite3
import io
import base64
import secrets
import string
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================
# Configuración base
# =========================
st.set_page_config(page_title="SEGUIMIENTO REGIONAL 2025", layout="wide")

# =========================
# Base de datos de usuarios
# =========================
USER_DB_PATH = Path("usuarios.db")

def init_user_db():
    """Inicializa la base de datos de usuarios"""
    with sqlite3.connect(USER_DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS usuarios(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                secret_word TEXT NOT NULL
            );
        """)
        
        # Insertar usuarios por defecto si no existen
        usuarios_por_defecto = [
            ("dcostar@isl.gob.cl", "123456", "seguridad"),
            ("pclaissacs@isl.gob.cl", "123456", "prevencion")
        ]
        
        for email, password, secret_word in usuarios_por_defecto:
            try:
                con.execute(
                    "INSERT OR IGNORE INTO usuarios (email, password, secret_word) VALUES (?, ?, ?)",
                    (email, password, secret_word)
                )
            except Exception as e:
                st.error(f"Error al insertar usuario {email}: {str(e)}")
        con.commit()

def get_user(email):
    """Obtiene un usuario por email"""
    with sqlite3.connect(USER_DB_PATH) as con:
        cur = con.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        result = cur.fetchone()
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "password": result[2],
                "secret_word": result[3]
            }
        return None

def update_user_password(email, new_password):
    """Actualiza la contraseña de un usuario"""
    with sqlite3.connect(USER_DB_PATH) as con:
        con.execute(
            "UPDATE usuarios SET password = ? WHERE email = ?",
            (new_password, email)
        )
        con.commit()
        return True

# =========================
# Sistema de autenticación
# =========================
def generate_temp_password(length=8):
    """Genera una contraseña temporal"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_user = None
    
    if not st.session_state.authenticated:
        # Inicializar base de datos de usuarios
        init_user_db()
        
        # Mostrar formulario de login en 5 columnas → todo en la central
        col1, col2, col_center, col4, col5 = st.columns([1,1,2,1,1])
        with col_center:
            st.title("🔐 Acceso al Sistema")

            tab1, tab2, tab3 = st.tabs(["Iniciar Sesión", "Recuperar Contraseña", "Cambiar Contraseña"])
            
            with tab1:
                email = st.text_input("Correo electrónico", key="login_email")
                password = st.text_input("Contraseña", type="password", key="login_password")
                
                if st.button("Ingresar", key="login_btn", use_container_width=True):
                    user = get_user(email)
                    if user and password == user["password"]:
                        st.session_state.authenticated = True
                        st.session_state.current_user = email
                        st.success("✅ Credenciales correctas. Redirigiendo...")
                        st.rerun()
                    else:
                        st.error("❌ Correo o contraseña incorrectos")
            
            with tab2:
                st.subheader("Recuperar Contraseña")
                recovery_email = st.text_input("Correo electrónico", key="recovery_email")
                secret_word = st.text_input("Palabra secreta", type="password", key="secret_word")
                
                if st.button("Generar Clave Temporal", key="recover_btn", use_container_width=True):
                    user = get_user(recovery_email)
                    if user and secret_word == user["secret_word"]:
                        temp_password = generate_temp_password()
                        update_user_password(recovery_email, temp_password)
                        st.success(f"✅ Clave temporal generada: **{temp_password}**")
                        st.info("Por seguridad, cambie su contraseña después de ingresar al sistema.")
                    else:
                        st.error("❌ Correo o palabra secreta incorrectos")
            
            with tab3:
                st.subheader("Cambiar Contraseña")
                change_email = st.text_input("Correo electrónico", key="change_email")
                current_password = st.text_input("Contraseña actual", type="password", key="current_password")
                new_password = st.text_input("Nueva contraseña", type="password", key="new_password")
                confirm_password = st.text_input("Confirmar nueva contraseña", type="password", key="confirm_password")
                
                if st.button("Cambiar Contraseña", key="change_btn", use_container_width=True):
                    user = get_user(change_email)
                    if not user:
                        st.error("❌ Correo electrónico no válido")
                    elif current_password != user["password"]:
                        st.error("❌ Contraseña actual incorrecta")
                    elif new_password != confirm_password:
                        st.error("❌ Las contraseñas no coinciden")
                    else:
                        update_user_password(change_email, new_password)
                        st.success("✅ Contraseña cambiada exitosamente")
        
        st.stop()  # Detener la ejecución hasta que se autentique

# Verificar autenticación
check_authentication()

# =========================
# VARIABLES DE COLOR
# =========================
PRIMARY = "#0F69B4"
BG = "#ffffff"
BTN_PRIMARY_BG = "#0F69B4"
BTN_PRIMARY_TEXT = "#ffffff"
BTN_PRIMARY_HOVER = "#DDEFFB"
BTN_DELETE_BG = "#0F69B4"
BTN_DELETE_TEXT = "#333"
BTN_DELETE_HOVER = "#EA7A85"
BTN_SECONDARY_BG = "#0F69B4"
BTN_SECONDARY_TEXT = "#ffffff"  
BTN_SECONDARY_HOVER = "#DDEFFB"

DB_PATH = Path("seguimiento_regional.db")
TABLE = "registros"
EXCEL_FILE = "registros.xlsx"  # Archivo fijo para importación

REGIONES = [
    "Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo",
    "Valparaíso", "Metropolitana", "O'Higgins", "Maule", "Ñuble",
    "Biobío", "La Araucanía", "Los Ríos", "Los Lagos", "Aysén", "Magallanes"
]

ITEMS_MONITOREO = [
    "Indicadores de desempeño","Ejecución Presupuestaria","Clima Laboral", "Infraestructura",
    "Plan de SSPP", "Político Institucional",
    "Temas Dpto. Personas", "Informática", "Otros"
]

ESTADOS = ["Pendiente", "En progreso", "Completado", "Cancelado"]

# =========================
# CONVERTIR IMAGEN LOCAL A BASE64
# =========================
def image_to_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Archivo de imagen no encontrado: {path}")
        return None

# Cargar imagen
IMAGEN_LOCAL = "LOGO-PROPIO-ISL-2023-CMYK-01.png"
img_base64 = image_to_base64(IMAGEN_LOCAL)
img_src = f"data:image/png;base64,{img_base64}" if img_base64 else None

# =========================
# Funciones de la base de datos
# =========================
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                direccion_regional TEXT NOT NULL,
                item_monitoreo TEXT NOT NULL,
                detalle TEXT NOT NULL,
                estado TEXT,
                plazo_dias INTEGER,
                fecha_reunion TEXT
            );
        """)
        con.commit()

def delete_record(record_id):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(f"DELETE FROM {TABLE} WHERE id = ?", (record_id,))
        con.commit()

def get_record(record_id):
    """Obtiene un registro específico por ID"""
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(f"SELECT * FROM {TABLE} WHERE id = ?", (record_id,))
        result = cur.fetchone()
        if result:
            return {
                "id": result[0],
                "direccion_regional": result[1],
                "item_monitoreo": result[2],
                "detalle": result[3],
                "estado": result[4],
                "plazo_dias": result[5],
                "fecha_reunion": result[6]
            }
        return None

def update_record(record_id, reg):
    """Actualiza un registro existente"""
    with sqlite3.connect(DB_PATH) as con:
        con.execute(f"""
            UPDATE {TABLE} 
            SET direccion_regional = ?, item_monitoreo = ?, detalle = ?, 
                estado = ?, plazo_dias = ?, fecha_reunion = ?
            WHERE id = ?
        """, (
            reg["direccion_regional"], reg["item_monitoreo"], reg["detalle"],
            reg["estado"], reg["plazo_dias"], reg["fecha_reunion"], record_id
        ))
        con.commit()
        return True

def get_count():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(f"SELECT COUNT(*) FROM {TABLE}")
        return int(cur.fetchone()[0])

def insert_record(reg):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(f"""
            INSERT INTO {TABLE}
            (direccion_regional, item_monitoreo, detalle, estado, plazo_dias, fecha_reunion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            reg["direccion_regional"], reg["item_monitoreo"], reg["detalle"],
            reg["estado"], reg["plazo_dias"], reg["fecha_reunion"]
        ))
        con.commit()
        return cur.lastrowid

def get_all_records():
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql_query(f"""
            SELECT
                id,
                direccion_regional AS "Dirección Regional",
                item_monitoreo AS "Ítem Monitoreo",
                detalle AS "Detalle",
                estado AS "Estado",
                plazo_dias AS "Plazo (días)",
                strftime('%d-%m-%Y', fecha_reunion) AS "Fecha Reunión"
            FROM {TABLE}
            ORDER BY id ASC
        """, con)
    df.insert(0, " ", False)
    return df

def export_to_excel():
    """Exporta todos los registros a un archivo Excel fijo"""
    df = get_all_records().drop(columns=[" "])
    df.to_excel(EXCEL_FILE, index=False)
    return True

def import_from_fixed_excel():
    """Importa registros desde el archivo Excel fijo"""
    try:
        if not os.path.exists(EXCEL_FILE):
            return False, f"Archivo {EXCEL_FILE} no encontrado"
        
        df = pd.read_excel(EXCEL_FILE)

        rename_map = {
            "N° Registro": "id",
            "Dirección Regional": "direccion_regional",
            "Ítem Monitoreo": "item_monitoreo",
            "Detalle": "detalle",
            "Estado": "estado",
            "Plazo (días)": "plazo_dias",
            "Fecha Reunión": "fecha_reunion"
        }
        df = df.rename(columns=rename_map)

        with sqlite3.connect(DB_PATH) as con:
            con.execute(f"DROP TABLE IF EXISTS {TABLE}")
            con.commit()
        init_db()

        with sqlite3.connect(DB_PATH) as con:
            for _, row in df.iterrows():
                plazo = row.get("plazo_dias", 0)
                plazo = 0 if pd.isna(plazo) else int(plazo)

                fecha_reunion = row.get("fecha_reunion", None)
                if pd.isna(fecha_reunion) or fecha_reunion is None:
                    fecha_reunion = date.today().strftime("%Y-%m-%d")
                else:
                    # Especificar explícitamente el formato de fecha
                    fecha_reunion = pd.to_datetime(
                        fecha_reunion, 
                        format='%d-%m-%Y'  # Especificar formato día-mes-año
                    ).strftime("%Y-%m-%d")

                con.execute(f"""
                    INSERT INTO {TABLE} (direccion_regional, item_monitoreo, detalle, estado, plazo_dias, fecha_reunion)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row.get("direccion_regional", ""),
                    row.get("item_monitoreo", ""),
                    str(row.get("detalle", "")),
                    row.get("estado", ""),
                    plazo,
                    fecha_reunion
                ))
            con.commit()
        
        return True, "Registros importados correctamente"
    except Exception as e:
        return False, f"Error al importar: {str(e)}"

# =========================
# Estilos CSS (mejorados)
# =========================
st.markdown(f"""
<style>
.stApp {{
    background: {BG};
}}
.header-container {{
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: {PRIMARY};
    height: 85px;
    width: 100%;
    color: white;
    position: relative;
    margin: -1rem -1rem 1.2rem -1rem;
}}
.header-logo {{
    position: absolute;
    left: 20px;
    top: 5px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}}
.header-logo img {{
    height: 60px;
}}
.header-subtitle {{
    position: absolute;
    bottom: 5px;
    left: 20px;
    font-size: 10px;
}}
.header-title {{
    font-size: 20px;
    font-weight: bold;
}}
.section-title {{
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 12px;
    color: #333;
}}
.form-container {{
    background: transparent;
    padding: 15px 0;
}}
.form-row {{
    display: flex;
    align-items: center;
    margin-bottom: 12px;
}}
.form-label {{
    width: 120px;
    text-align: left;
    font-size: 12px;
    font-weight: 500;
}}
.form-input {{
    flex: 1;
}}
.input-field {{
    background-color: white;
    border: 1px solid #cccccc;
    border-radius: 4px;
    box-shadow: inset -2px -2px 4px rgba(0,0,0,0.05);
    padding: 8px;
    height: 35px;
    display: flex;
    align-items: center;
}}
.stTextInput>div>div>input, 
.stNumberInput>div>div>input,
.stSelectbox>div>div>div,
.stDateInput>div>div>input {{
    background-color: white !important;
    border: 1px solid #cccccc !important;
    border-radius: 4px !important;
    box-shadow: inset -2px -2px 4px rgba(0,0,0,0.05) !important;
    padding: 8px !important;
    font-size: 12px !important;
    height: 35px !important;
}}
.stTextArea>div>div>textarea {{
    height: 500px !important;
    resize: none;
    font-size: 12px;
    background-color: white !important;
    border: 1px solid #cccccc !important;
    border-radius: 4px;
    box-shadow: inset -2px -2px 4px rgba(0,0,0,0.05);
    padding: 8px;
}}
.button-container {{
    display: flex;
    gap: 10px;
    margin-top: 15px;
}}
.button-container button {{
    flex: 1;
}}
/* BOTÓN PRIMARIO (REGISTRAR) */
div[data-testid="stButton"] button[kind="primary"] {{
    background-color: {BTN_PRIMARY_BG} !important;
    border-color: {BTN_PRIMARY_BG} !important;
    color: {BTN_PRIMARY_TEXT} !important;
}}
div[data-testid="stButton"] button[kind="primary"]:hover {{
    background-color: {BTN_PRIMARY_HOVER} !important;
    border-color: {BTN_PRIMARY_HOVER} !important;
}}
/* BOTÓN ELIMINAR */
.stButton>button:not([kind]) {{
    background-color: {BTN_PRIMARY_BG} !important;
    border-color: {BTN_PRIMARY_BG} !important;
    color: {BTN_PRIMARY_TEXT} !important;
}}
.stButton>button:not([kind]):hover {{
    background-color: {BTN_DELETE_HOVER} !important;
    border-color: {BTN_DELETE_HOVER} !important;
}}
/* BOTONES SECUNDARIOS (EXPORTAR/IMPORTAR) */
.stButton>button[kind="secondary"] {{
    background-color: {BTN_SECONDARY_BG} !important;
    border-color: {BTN_SECONDARY_BG} !important;
    color: {BTN_SECONDARY_TEXT} !important;
}}
.stButton>button[kind="secondary"]:hover {{
    background-color: {BTN_SECONDARY_HOVER} !important;
    border-color: {BTN_SECONDARY_HOVER} !important;
}}
.st-emotion-cache-1p1nwyz {{
    visibility: hidden;
    height: 0;
    margin: 0;
    padding: 0;
}}
/* CHECKBOXES */
.stCheckbox>div>div>label>div:first-child {{
    margin-right: 8px;
}}
/* ESTILOS UNIFICADOS PARA BOTONES */
/* Asegurar que todos los botones tengan el mismo tamaño */
.col-button button {{
    width: 100% !important;
    min-height: 35px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    white-space: nowrap;
}}
/* Botón de descarga con estilo secundario */
.stDownloadButton button {{
    background-color: {BTN_SECONDARY_BG} !important;
    border-color: {BTN_SECONDARY_BG} !important;
    color: {BTN_SECONDARY_TEXT} !important;
    width: 100% !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}}
.stDownloadButton button:hover {{
    background-color: {BTN_SECONDARY_HOVER} !important;
    border-color: {BTN_SECONDARY_HOVER} !important;
}}

/* ======================== */
/* ESTILOS MEJORADOS TABLA  */
/* ======================== */
.stDataFrame {{
    border: 1px solid #cccccc !important;
    border-top: 3px solid {PRIMARY} !important;
    box-shadow: 3px 3px 5px rgba(0,0,0,0.1) !important;
    border-radius: 4px !important;
}}

/* Cabecera de la tabla */
.stDataFrame thead tr th {{
    background-color: #f0f0f0 !important;
    color: #333 !important;
    font-weight: bold !important;
}}

/* Filas alternadas */
.stDataFrame tbody tr:nth-child(even) {{
    background-color: #f9f9f9 !important;
}}

/* Hover en filas */
.stDataFrame tbody tr:hover {{
    background-color: #f0f8ff !important;
}}

/* Contenedor de botones con mismo ancho */
.button-column-container {{
    display: flex;
    justify-content: center;
}}

/* Estilos para las pestañas de autenticación */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
}}

.stTabs [data-baseweb="tab"] {{
    height: 40px;
    white-space: pre-wrap;
    background-color: #f0f2f6;
    border-radius: 4px 4px 0px 0px;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
}}

.stTabs [aria-selected="true"] {{
    background-color: {PRIMARY};
    color: white;
}}
</style>
""", unsafe_allow_html=True)

# =========================
# Encabezado con logo
# =========================
if img_src:
    st.markdown(f"""
    <div class="header-container">
        <div class="header-logo">
            <img src="{img_src}" alt="Logo">
        </div>
        <div class="header-subtitle">Coordinación Territorial</div>
        <div class="header-title">SEGUIMIENTO REGIONAL 2025</div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Fallback al diseño original si no hay imagen
    st.markdown(f"""
    <div class="topbar">
        <div class="logo">
            ISL
            <small>Coordinación Territorial</small>
        </div>
        <div class="title">SEGUIMIENTO REGIONAL 2025</div>
    </div>
    """, unsafe_allow_html=True)

init_db()

# Exportar inicialmente si no existe el archivo
if not os.path.exists(EXCEL_FILE):
    export_to_excel()

# Inicializar variables de sesión para edición
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None
if 'is_editing' not in st.session_state:
    st.session_state.is_editing = False
if 'record_to_edit' not in st.session_state:
    st.session_state.record_to_edit = None

# =========================
# Layout principal
# =========================
col_left, col_middle, col_right = st.columns([0.4, 0.6, 1.0], gap="large")

# Obtener el registro a editar si existe
record_to_edit = None
if st.session_state.record_to_edit:
    record_to_edit = get_record(st.session_state.record_to_edit)

with col_left:
    st.markdown('<div class="section-title">Registro de datos</div>', unsafe_allow_html=True)
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    total_registros = get_count()
    st.markdown(f"""
        <div class="form-row">
            <div class="form-label">N° Registros:</div>
            <div class="form-input"><div class="input-field">{total_registros}</div></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="form-row"><div class="form-label">Dirección Regional:</div></div>', unsafe_allow_html=True)
    
    # Determinar el valor inicial basado en si estamos editando
    default_dr_index = REGIONES.index("Magallanes")
    if record_to_edit:
        default_dr_index = REGIONES.index(record_to_edit["direccion_regional"])
    
    direccion = st.selectbox("Dirección Regional", REGIONES, index=default_dr_index, label_visibility="collapsed", key="dr")

    st.markdown('<div class="form-row"><div class="form-label">Ítem Monitoreo:</div></div>', unsafe_allow_html=True)
    
    # Determinar el valor inicial basado en si estamos editando
    default_im_index = 0
    if record_to_edit:
        default_im_index = ITEMS_MONITOREO.index(record_to_edit["item_monitoreo"])
    
    item = st.selectbox("Ítem Monitoreo", ITEMS_MONITOREO, index=default_im_index, label_visibility="collapsed", key="im")

    st.markdown('<div class="form-row"><div class="form-label">Estado:</div></div>', unsafe_allow_html=True)
    
    # Determinar el valor inicial basado en si estamos editando
    default_est_index = 0
    if record_to_edit:
        default_est_index = ESTADOS.index(record_to_edit["estado"])
    
    estado = st.selectbox("Estado", ESTADOS, index=default_est_index, label_visibility="collapsed", key="est")

    st.markdown('<div class="form-row"><div class="form-label">Plazo (Días):</div></div>', unsafe_allow_html=True)
    
    # Determinar el valor inicial basado en si estamos editando
    default_plz = 0
    if record_to_edit:
        default_plz = record_to_edit["plazo_dias"]
    
    plazo = st.number_input("Plazo (Días)", min_value=0, step=1, value=default_plz, format="%d", label_visibility="collapsed", key="plz")

    st.markdown('<div class="form-row"><div class="form-label">Fecha Reunión:</div></div>', unsafe_allow_html=True)
    
    # Determinar el valor inicial basado en si estamos editando
    default_fec = date.today()
    if record_to_edit:
        default_fec = pd.to_datetime(record_to_edit["fecha_reunion"]).date()
    
    fecha = st.date_input("Fecha Reunión", value=default_fec, format="DD-MM-YYYY", label_visibility="collapsed", key="fec")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_middle:
    st.markdown('<div class="section-title">Observaciones</div>', unsafe_allow_html=True)
    
    # Determinar el valor inicial basado en si estamos editando
    default_detalle = ""
    if record_to_edit:
        default_detalle = record_to_edit["detalle"]
    
    detalle = st.text_area("Observaciones", value=default_detalle, key="detalle", label_visibility="collapsed", height=500)

with col_right:
    st.markdown('<div class="section-title">Registros guardados</div>', unsafe_allow_html=True)
    df_all = get_all_records()
    
    edited_df = st.data_editor(
        df_all,
        use_container_width=True,
        height=500,
        key="data_editor",
        column_config={
            " ": st.column_config.CheckboxColumn(
                "Seleccionar",
                help="Selecciona registros para eliminar",
                default=False,
            ),
            "id": None
        },
        disabled=["Dirección Regional", "Ítem Monitoreo", "Detalle", "Estado", "Plazo (días)", "Fecha Reunión"],
        hide_index=True
    )
    
    selected_ids = edited_df[edited_df[" "]]["id"].tolist()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Botón de exportación
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_all.drop(columns=[" "]).to_excel(writer, index=False)
        
        st.markdown('<div class="col-button">', unsafe_allow_html=True)
        st.download_button(
            "Exportar Excel",
            data=excel_buffer.getvalue(),
            file_name=EXCEL_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Botón de importación
        st.markdown('<div class="col-button">', unsafe_allow_html=True)
        if st.button("Importar Excel", type="secondary", key="import_btn", use_container_width=True):
            success, message = import_from_fixed_excel()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        # Botón de registro
        st.markdown('<div class="col-button">', unsafe_allow_html=True)
        submitted = st.button("Registrar", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        # Botón de modificación
        st.markdown('<div class="col-button">', unsafe_allow_html=True)
        modify_clicked = st.button("Modificar", type="secondary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        # Botón de eliminación
        st.markdown('<div class="col-button">', unsafe_allow_html=True)
        if st.button("Eliminar selección", use_container_width=True):
            if not selected_ids:
                st.warning("Por favor, selecciona al menos un registro")
            else:
                for record_id in selected_ids:
                    try:
                        delete_record(record_id)
                    except Exception as e:
                        st.error(f"Error al eliminar registro {record_id}: {str(e)}")
                        break
                else:
                    st.success(f"{len(selected_ids)} registro(s) eliminado(s) correctamente")
                    # Actualizar el archivo Excel después de eliminar
                    export_to_excel()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Manejar clic en botón Modificar
if modify_clicked:
    if len(selected_ids) == 0:
        st.warning("Por favor, selecciona un registro para modificar")
    elif len(selected_ids) > 1:
        st.warning("Por favor, selecciona solo un registro para modificar")
    else:
        record_id = selected_ids[0]
        st.session_state.record_to_edit = record_id
        st.session_state.is_editing = True
        st.success(f"Registro #{record_id} cargado para modificación")
        st.rerun()

# Manejar envío del formulario (Registrar o Actualizar)
if submitted:
    detalle_content = detalle
    
    if not detalle_content.strip():
        st.warning("Por favor, escribe las observaciones antes de registrar.")
        st.stop()

    reg = {
        "direccion_regional": direccion,
        "item_monitoreo": item,
        "detalle": detalle_content.strip(),
        "estado": estado.strip(),
        "plazo_dias": int(plazo) if plazo else 0,
        "fecha_reunion": fecha.strftime("%Y-%m-%d"),
    }

    if st.session_state.is_editing and st.session_state.record_to_edit:
        # Modo edición: actualizar registro existente
        update_record(st.session_state.record_to_edit, reg)
        st.success(f"Registro #{st.session_state.record_to_edit} actualizado correctamente.")
        # Resetear estado de edición
        st.session_state.editing_id = None
        st.session_state.is_editing = False
        st.session_state.record_to_edit = None
    else:
        # Modo nuevo: insertar registro
        new_id = insert_record(reg)
        st.success(f"Registro #{new_id} guardado correctamente.")
    
    # Actualizar el archivo Excel después de insertar/actualizar
    export_to_excel()
    st.rerun()

# Mostrar indicador de modo edición
if st.session_state.is_editing and st.session_state.record_to_edit:
    st.info(f"Modo edición: Modificando registro #{st.session_state.record_to_edit}")

