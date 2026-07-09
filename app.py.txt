import streamlit as st
import pandas as pd
from fpdf import FPDF

# Leer Excel
df = pd.read_excel("Pedido.xlsx", sheet_name="Hoja1")

st.title("Revisión de Pedido")

selecciones = []
for i, row in df.iterrows():
    decision = st.radio(f"{row['producto']} ({row['lugar']})", ["NO", "SÍ"], index=0, key=i)
    selecciones.append(decision)

if st.button("Generar Orden de Compra"):
    df["Seleccion"] = selecciones
    seleccionados = df[df["Seleccion"] == "SÍ"]

    # Crear PDF agrupado por lugar
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for lugar, grupo in seleccionados.groupby("lugar"):
        pdf.cell(200, 10, f"Lugar: {lugar}", ln=True, align="L")
        for _, r in grupo.iterrows():
            pdf.cell(200, 10, f"- {r['producto']} ({r['categoría']})", ln=True, align="L")
        pdf.ln(5)

    pdf.output("OrdenCompra.pdf")
    st.success("PDF generado: OrdenCompra.pdf")

    st.subheader("Orden de Compra")
    st.dataframe(seleccionados)
