import streamlit as st
import pandas as pd
from fpdf import FPDF

# Leer Excel
df = pd.read_excel("Pedido.xlsx", sheet_name="Hoja1")

st.title("Revisión de Pedido")

selecciones = []
for i, row in df.iterrows():
    decision = st.radio(
        f"{row['producto']} ({row['lugar']})",
        ["NO", "SÍ"],
        index=0,
        key=i
    )
    selecciones.append(decision)

if st.button("Generar Orden de Compra"):
    df["Seleccion"] = selecciones
    seleccionados = df[df["Seleccion"] == "SÍ"]

    # Crear PDF agrupado por lugar
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "ORDEN DE COMPRA", ln=True, align="C")
    pdf.ln(5)

    for lugar, grupo in seleccionados.groupby("lugar"):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, f"Lugar: {lugar}", ln=True)

        pdf.set_font("Arial", size=12)
        for _, r in grupo.iterrows():
            # Solo mostrar producto
            pdf.cell(200, 8, f"- {r['producto']}", ln=True)

        pdf.ln(5)

    # Generar PDF en memoria
    pdf_bytes = pdf.output(dest="S").encode("latin1")

    st.success("Orden de compra generada correctamente.")

    # Botón para descargar PDF
    st.download_button(
        label="Descargar Orden de Compra PDF",
        data=pdf_bytes,
        file_name="OrdenCompra.pdf",
        mime="application/pdf"
    )

    st.subheader("Orden de Compra")

    # Mostrar únicamente las columnas deseadas
    columnas_mostrar = ["producto", "lugar"]
    st.dataframe(seleccionados[columnas_mostrar])
