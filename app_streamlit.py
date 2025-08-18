# app.py
# -*- coding: utf-8 -*-
import os
import sqlite3
import io
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================
# Configuración base
# =========================
st.set_page_config(page_title="SEGUIMIENTO REGIONAL 2025", layout="wide")

# =========================
# VARIABLES DE COLOR
# =========================
PRIMARY = "#1165a6"
BG = "#f2f2f2"
BTN_PRIMARY_BG = "#e1fbff"
BTN_PRIMARY_TEXT = "#333"
BTN_PRIMARY_HOVER = "#c8f1f5"
BTN_DELETE_BG = "#ffebee"
BTN_DELETE_TEXT = "#c62828"
BTN_DELETE_HOVER = "#ffcdd2"
BTN_SECONDARY_BG = "#eeeeee"
BTN_SECONDARY_TEXT = "#333"
BTN_SECONDARY_HOVER = "#dddddd"

DB_PATH = Path("seguimiento_regional.db")
TABLE = "registros"

REGIONES = [
    "Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo",
    "Valparaíso", "Metropolitana", "O'Higgins", "Maule", "Ñuble",
    "Biobío", "La Araucanía", "Los Ríos", "Los Lagos", "Aysén", "Magallanes"
]

ITEMS_MONITOREO = [
    "Indicadores de desempeño","Ejecución Presupuestaria","Clima Laboral", "Infraestructura",
    "Plan de SSPP", "Político Institucional",
    "Temas de Personas", "Informática", "Otros"
]

ESTADOS = ["Pendiente", "En progreso", "Completado", "Cancelado"]

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

def import_from_excel(uploaded_file):
    """Importar registros desde un Excel, reemplazando completamente la tabla"""
    try:
        df = pd.read_excel(uploaded_file)

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
                    fecha_reunion = pd.to_datetime(fecha_reunion).strftime("%Y-%m-%d")

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
# Estilos CSS
# =========================
st.markdown(f"""
<style>
.stApp {{
    background: {BG};
}}
.topbar {{
    width: 100%;
    background: {PRIMARY};
    height: 82px;
    display: flex;
    align-items: center;
    position: relative;
    margin: -1rem -1rem 1.2rem -1rem;
}}
.logo {{
    position: absolute;
    left: 18px;
    top: 10px;
    color: white;
    font-weight: 700;
    font-size: 18px;
}}
.logo small {{
    display:block;
    font-weight: 400;
    font-size: 12px;
}}
.title {{
    width: 100%;
    text-align: center;
    color: white;
    font-weight: 700;
    font-size: 16px;
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
    background-color: {BTN_DELETE_BG} !important;
    border-color: {BTN_DELETE_BG} !important;
    color: {BTN_DELETE_TEXT} !important;
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
</style>
""", unsafe_allow_html=True)

# =========================
# Barra superior
# =========================
st.markdown("""
<div class="topbar">
    <div class="logo">
        ISL
        <small>Coordinación Territorial</small>
    </div>
    <div class="title">SEGUIMIENTO REGIONAL 2025</div>
</div>
""", unsafe_allow_html=True)

init_db()

# =========================
# Layout principal
# =========================
col_left, col_middle, col_right = st.columns([0.4, 0.6, 1.0], gap="large")

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
    direccion = st.selectbox("Dirección Regional", REGIONES, index=REGIONES.index("Magallanes"), label_visibility="collapsed", key="dr")

    st.markdown('<div class="form-row"><div class="form-label">Ítem Monitoreo:</div></div>', unsafe_allow_html=True)
    item = st.selectbox("Ítem Monitoreo", ITEMS_MONITOREO, index=0, label_visibility="collapsed", key="im")

    st.markdown('<div class="form-row"><div class="form-label">Estado:</div></div>', unsafe_allow_html=True)
    estado = st.selectbox("Estado", ESTADOS, index=0, label_visibility="collapsed", key="est")

    st.markdown('<div class="form-row"><div class="form-label">Plazo (Días):</div></div>', unsafe_allow_html=True)
    plazo = st.number_input("Plazo (Días)", min_value=0, step=1, value=0, format="%d", label_visibility="collapsed", key="plz")

    st.markdown('<div class="form-row"><div class="form-label">Fecha Reunión:</div></div>', unsafe_allow_html=True)
    fecha = st.date_input("Fecha Reunión", value=date.today(), format="DD-MM-YYYY", label_visibility="collapsed", key="fec")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_middle:
    st.markdown('<div class="section-title">Observaciones</div>', unsafe_allow_html=True)
    detalle = st.text_area("Observaciones", key="detalle", label_visibility="collapsed", height=500)

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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_all.drop(columns=[" "]).to_excel(writer, index=False)
        st.download_button(
            "📤 Exportar Excel",
            data=excel_buffer.getvalue(),
            file_name="registros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary"
        )
    
    with col2:
        uploaded_file = st.file_uploader(
            "📥 Importar Excel", 
            type=["xlsx"],
            accept_multiple_files=False,
            key="excel_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            success, message = import_from_excel(uploaded_file)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with col3:
        submitted = st.button("💾 Registrar", type="primary")

    with col4:
        if st.button("🗑️ Eliminar selección"):
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
                    st.rerun()

if submitted:
    detalle_content = st.session_state.detalle if "detalle" in st.session_state else ""
    
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

    new_id = insert_record(reg)
    st.success(f"Registro #{new_id} guardado correctamente.")
    st.rerun()