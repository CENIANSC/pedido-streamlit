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

st.title("Revisión de Pedido")

# Diccionario para almacenar las selecciones
selecciones = {}

# Obtener categorías únicas y convertirlas a lista de texto
categorias = (
    df["categoría"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

# Crear pestañas
tabs = st.tabs(categorias)

# Mostrar productos organizados por categoría
for tab, categoria in zip(tabs, categorias):

    with tab:

        df_categoria = df[df["categoría"].astype(str) == categoria]

        productos = df_categoria.to_dict("records")

        # Mostrar 5 productos por fila
        for fila_inicio in range(0, len(productos), 5):

            columnas = st.columns(5)

            for col, producto in zip(
                columnas,
                productos[fila_inicio:fila_inicio + 5]
            ):

                with col:

                    st.markdown(
                        f"**{producto['producto']}**"
                    )

                    if "lugar" in producto:
                        st.caption(producto["lugar"])

                    seleccion = st.radio(
                        "",
                        ["NO", "SÍ"],
                        index=0,
                        horizontal=True,
                        key=f"prod_{producto['producto']}"
                    )

                    selecciones[producto["producto"]] = seleccion

# ==========================
# Generar orden de compra
# ==========================
if st.button("Generar Orden de Compra"):

    # Agregar selecciones al DataFrame
    df["Seleccion"] = df["producto"].map(selecciones)

    # Filtrar productos seleccionados
    seleccionados = df[df["Seleccion"] == "SÍ"]

    if seleccionados.empty:
        st.warning("No se seleccionó ningún producto.")

    else:

        # Crear PDF
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
        pdf.cell(0, 8, f"Fecha: {fecha_formal}", ln=True, align="C")
        pdf.ln(10)

        # Agrupar por lugar
        for lugar, grupo in seleccionados.groupby("lugar"):

            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"Lugar: {lugar}", ln=True)

            pdf.set_font("Arial", "", 12)

            for _, r in grupo.iterrows():
                pdf.cell(0, 8, f"- {r['producto']}", ln=True)

            pdf.ln(5)

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

        # Mostrar tabla
        st.subheader("Orden de Compra")

        st.dataframe(
            seleccionados[["producto", "lugar"]].reset_index(drop=True)
        )
