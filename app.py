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

        # =====================================
# Configuración tipo periódico
# =====================================
margen_superior = pdf.get_y()
ancho_columna = 90
alto_renglon = 7
separacion_columnas = 10
separacion_tablas = 5

x_columna_1 = 10
x_columna_2 = 110

columna_actual = 1
x_actual = x_columna_1
y_actual = margen_superior

for lugar, productos_lugar in lugares:

    altura_tabla = (len(productos_lugar) + 1) * alto_renglon

    # ¿Cabe en la columna actual?
    if y_actual + altura_tabla > 270:

        # Si estábamos en la columna izquierda, mover a la derecha
        if columna_actual == 1:
            columna_actual = 2
            x_actual = x_columna_2
            y_actual = margen_superior

        # Si ya estábamos en la derecha, nueva página
        else:
            pdf.add_page()

            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "ORDEN DE COMPRA", ln=True, align="C")

            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, fecha_formal, ln=True, align="C")
            pdf.ln(10)

            margen_superior = pdf.get_y()

            columna_actual = 1
            x_actual = x_columna_1
            y_actual = margen_superior

    # ======================
    # Encabezado
    # ======================
    pdf.set_xy(x_actual, y_actual)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(
        ancho_columna,
        alto_renglon,
        str(lugar),
        border=1,
        align="C"
    )

    # ======================
    # Productos
    # ======================
    pdf.set_font("Arial", "", 10)

    for i, (_, fila) in enumerate(productos_lugar.iterrows()):

        pdf.set_xy(
            x_actual,
            y_actual + alto_renglon * (i + 1)
        )

        pdf.cell(
            ancho_columna,
            alto_renglon,
            str(fila["producto"]),
            border=1
        )

    # Posición para la siguiente tabla
    y_actual += altura_tabla + separacion_tablas

        # Convertir PDF a bytes
        pdf_bytes = pdf.output(dest="S").encode("latin1")

        st.success("Orden de compra generada correctamente.")

        st.download_button(
            label="Descargar Orden de Compra PDF",
            data=pdf_bytes,
            file_name="OrdenCompra.pdf",
            mime="application/pdf"
        )

        st.subheader("Orden de Compra")

        st.dataframe(
            orden_compra,
            use_container_width=True
        )
