import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Leer archivo Excel
df = pd.read_excel("Pedido.xlsx", sheet_name="Hoja1")

st.title("Revisión de Pedido")

# Crear opciones de selección
selecciones = []
for i, row in df.iterrows():
    decision = st.radio(
        f"{row['producto']} ({row['lugar']})",
        ["NO", "SÍ"],
        index=0,
        key=i
    )
    selecciones.append(decision)

# Generar orden de compra
if st.button("Generar Orden de Compra"):

    # Agregar selecciones al DataFrame
    df["Seleccion"] = selecciones

    # Filtrar únicamente los productos seleccionados
    seleccionados = df[df["Seleccion"] == "SÍ"]

    if seleccionados.empty:
        st.warning("No se seleccionó ningún producto.")
    else:
        # --------------------------
        # Crear PDF
        # --------------------------
        pdf = FPDF()
        pdf.add_page()

        # Título
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ORDEN DE COMPRA", ln=True, align="C")

        # Fecha en formato formal
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

        # Productos agrupados por lugar
        for lugar, grupo in seleccionados.groupby("lugar"):

            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"Lugar: {lugar}", ln=True)

            pdf.set_font("Arial", "", 12)
            for _, r in grupo.iterrows():
                pdf.cell(0, 8, f"- {r['producto']}", ln=True)

            pdf.ln(5)

        # Convertir PDF a bytes para descarga
        pdf_bytes = pdf.output(dest="S").encode("latin1")

        st.success("Orden de compra generada correctamente.")

        # Botón de descarga
        st.download_button(
            label="Descargar Orden de Compra PDF",
            data=pdf_bytes,
            file_name="OrdenCompra.pdf",
            mime="application/pdf"
        )

        # Mostrar tabla sin categoría ni selección
        st.subheader("Orden de Compra")
        st.dataframe(
            seleccionados[["producto", "lugar"]].reset_index(drop=True)
        )
