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

    if seleccionados.empty():
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
        pdf.set_font("Arial", "B", 16)
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

        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, fecha_formal, ln=True, align="C")

        pdf.ln(10)

        # Encabezados de tabla
        pdf.set_font("Arial", "B", 12)
        pdf.cell(130, 10, "Producto", border=1, align="C")
        pdf.cell(60, 10, "Lugar", border=1, align="C", ln=True)

        # Contenido
        pdf.set_font("Arial", "", 11)

        for _, fila in orden_compra.iterrows():
            pdf.cell(130, 8, str(fila["producto"]), border=1)
            pdf.cell(60, 8, str(fila["lugar"]), border=1, ln=True)

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
