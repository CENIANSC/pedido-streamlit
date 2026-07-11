import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from supabase import create_client

# ==========================
# Supabase
# ==========================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# ==========================
# Leer archivo Excel
# ==========================
df = pd.read_excel("Pedido.xlsx", sheet_name="Hoja1")

col1, col2 = st.columns([4, 1])

with col1:
    st.title("Compras Cafetería UPPE")

with col2:
    generar_orden = st.button(
        "📄 Generar Orden de Compra",
        use_container_width=True
    )
# Diccionario para almacenar selecciones
selecciones = {}

# Obtener categorías únicas y convertirlas a lista
categorias = (
    df["categoría"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

# Crear pestañas por categoría
tabs = st.tabs(categorias)

for tab, categoria in zip(tabs, categorias):

    with tab:

        df_categoria = df[df["categoría"].astype(str) == categoria]

        productos = df_categoria.to_dict("records")

        # Mostrar 4 productos por fila
        for fila_inicio in range(0, len(productos), 4):

            columnas = st.columns(4)

            for col, producto in zip(
                columnas,
                productos[fila_inicio:fila_inicio + 4]
            ):

                with col:

                    st.markdown(
                        f"""
                        <div style="text-align:center; font-size:16px; font-weight:bold;">
                            {producto['producto']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    seleccion = st.radio(
                        "",
                        ["NO", "SÍ"],
                        index=0,
                        horizontal=True,
                        key=f"prod_{producto['producto']}",
                        label_visibility="collapsed"
                    )

                    selecciones[producto["producto"]] = seleccion

            # Espacio entre filas
            st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# Generar orden de compra
# ==========================
if generar_orden:

    # Agregar selecciones al DataFrame
    df["Seleccion"] = df["producto"].map(selecciones)

    # Filtrar productos seleccionados
    seleccionados = df[df["Seleccion"] == "SÍ"]

    if seleccionados.empty:
        st.warning("No se seleccionó ningún producto.")

    else:

        # Mantener únicamente las columnas requeridas
        orden_compra = seleccionados[
            ["producto", "lugar"]
        ].reset_index(drop=True)

        # ==========================
        # Crear PDF
        # ==========================
        pdf = FPDF()
        pdf.add_page()

        # Título
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "ORDEN DE COMPRA", ln=True, align="C")

        # Fecha
        meses = {
            1: "enero",
            2: "febrero",
            3: "marzo",
            4: "abril",
            5: "mayo",
            6: "junio",
            7: "julio",
            8: "agosto",
            9: "septiembre",
            10: "octubre",
            11: "noviembre",
            12: "diciembre"
        }

        hoy = datetime.now()
        fecha_formal = f"{hoy.day} de {meses[hoy.month]} de {hoy.year}"

        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, fecha_formal, ln=True, align="C")

        pdf.ln(10)

# Agrupar productos por lugar
lugares = list(orden_compra.groupby("lugar"))

# Configuración de columnas del PDF
ancho_columna = 90
alto_renglon = 8
margen_izquierdo = 10
separacion_columnas = 10

for i in range(0, len(lugares), 2):

    grupo_izq = lugares[i]

    grupo_der = lugares[i + 1] if i + 1 < len(lugares) else None

    nombre_izq, productos_izq = grupo_izq
    max_filas = len(productos_izq)

    if grupo_der:
        nombre_der, productos_der = grupo_der
        max_filas = max(max_filas, len(productos_der))

    y_inicio = pdf.get_y()

    # -------------------
    # Encabezado izquierda
    # -------------------
    pdf.set_xy(margen_izquierdo, y_inicio)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(
        ancho_columna,
        alto_renglon,
        nombre_izq,
        border=1,
        align="C"
    )

    # -------------------
    # Encabezado derecha
    # -------------------
    if grupo_der:
        pdf.set_xy(
            margen_izquierdo + ancho_columna + separacion_columnas,
            y_inicio
        )

        pdf.cell(
            ancho_columna,
            alto_renglon,
            nombre_der,
            border=1,
            align="C"
        )

    pdf.set_font("Arial", "", 11)

    # -------------------
    # Productos
    # -------------------
    for fila in range(max_filas):

        y_actual = y_inicio + alto_renglon * (fila + 1)

        # Columna izquierda
        pdf.set_xy(margen_izquierdo, y_actual)

        texto_izq = ""
        if fila < len(productos_izq):
            texto_izq = str(
                productos_izq.iloc[fila]["producto"]
            )

        pdf.cell(
            ancho_columna,
            alto_renglon,
            texto_izq,
            border=1
        )

        # Columna derecha
        if grupo_der:

            pdf.set_xy(
                margen_izquierdo + ancho_columna + separacion_columnas,
                y_actual
            )

            texto_der = ""
            if fila < len(productos_der):
                texto_der = str(
                    productos_der.iloc[fila]["producto"]
                )

            pdf.cell(
                ancho_columna,
                alto_renglon,
                texto_der,
                border=1
            )

    # Posicionar el cursor debajo del bloque
    pdf.set_y(
        y_inicio + alto_renglon * (max_filas + 2)
    )

        # Convertir PDF a bytes
        pdf_bytes = pdf.output(dest="S").encode("latin1")

        st.success("Orden de compra generada correctamente.")

        # Descargar PDF
        st.download_button(
            label="Descargar Orden de Compra PDF",
            data=pdf_bytes,
            file_name="OrdenCompra.pdf",
            mime="application/pdf"
        )

        # Mostrar vista previa
        st.subheader("Orden de Compra")

        st.dataframe(
            orden_compra,
            use_container_width=True
        )
