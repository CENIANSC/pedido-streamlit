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

# ==========================
# Encabezado
# ==========================
col1, col2, col3 = st.columns([4, 1.5, 2])
with col1:
    st.title("Compras Cafetería")
with col2:
    generar_orden = st.button("📄 Generar OC", use_container_width=True)
with col3:
    mensaje_placeholder = st.empty()
    descarga_placeholder = st.empty()

# ==========================
# Selecciones
# ==========================
selecciones = {}
categorias = df["Categoría"].dropna().astype(str).unique().tolist()
tabs = st.tabs(categorias)

for tab, categoria in zip(tabs, categorias):
    with tab:
        df_categoria = df[df["Categoría"].astype(str) == categoria]
        productos = df_categoria.to_dict("records")

        for fila_inicio in range(0, len(productos), 4):
            columnas = st.columns(4)
            for col, producto in zip(columnas, productos[fila_inicio:fila_inicio + 4]):
                with col:
                    st.markdown(
                        f"""
                        <div style="
                            text-align:center;
                            font-size:15px;
                            font-weight:bold;
                            min-height:50px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                        ">
                            {producto['Producto']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    unidad = producto.get("Unidad", "N/A")

                    cantidad = st.number_input(
                        f"Cantidad ({unidad})",
                        min_value=0.0,
                        step=1.0,
                        value=0.0,
                        key=f"cant_{producto['Producto']}"
                    )

                    precio_total = st.number_input(
                        "Precio Total",
                        min_value=0.0,
                        step=0.5,
                        value=0.0,
                        key=f"precio_{producto['Producto']}"
                    )

                    # Consultar último precio registrado en Supabase
                    ultimo_precio = supabase.table("compras") \
                        .select("costo_unitario") \
                        .eq("producto", producto["Producto"]) \
                        .order("fecha", desc=True) \
                        .limit(1) \
                        .execute()

                    if ultimo_precio.data:
                        st.caption(f"Último precio: ${ultimo_precio.data[0]['costo_unitario']} por {unidad}")

                    selecciones[producto["Producto"]] = {
                        "cantidad": cantidad,
                        "precio_total": precio_total,
                        "unidad": unidad,
                        "proveedor": producto.get("Proveedor", "")
                    }

# ==========================
# Generar Orden de Compra
# ==========================
if generar_orden:
    seleccionados = {p: d for p, d in selecciones.items() if d["cantidad"] > 0}
    if not seleccionados:
        st.warning("No se seleccionó ningún producto.")
    else:
        orden_compra = pd.DataFrame([
            {
                "Producto": prod,
                "Unidad": datos["unidad"],
                "Cantidad": datos["cantidad"],
                "Precio Total": datos["precio_total"],
                "Proveedor": datos["proveedor"],
                "Costo Unitario": datos["precio_total"] / datos["cantidad"] if datos["cantidad"] else 0
            }
            for prod, datos in seleccionados.items()
        ])

        # Guardar en Supabase
        for _, fila in orden_compra.iterrows():
            supabase.table("compras").insert({
                "fecha": datetime.now().isoformat(),
                "producto": fila["Producto"],
                "unidad": fila["Unidad"],
                "cantidad": fila["Cantidad"],
                "precio_total": fila["Precio Total"],
                "costo_unitario": fila["Costo Unitario"],
                "proveedor": fila["Proveedor"]
            }).execute()

        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "ORDEN DE COMPRA", ln=True, align="C")

        hoy = datetime.now()
        meses = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}
        fecha_formal = f"{hoy.day} de {meses[hoy.month]} de {hoy.year}"
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, fecha_formal, ln=True, align="C")
        pdf.ln(5)

        for proveedor, grupo in orden_compra.groupby("Proveedor"):
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, f"Proveedor: {proveedor}", ln=True)
            pdf.set_font("Arial", "", 10)
            for _, r in grupo.iterrows():
                pdf.cell(0, 8, f"- {r['Producto']} ({r['Cantidad']} {r['Unidad']})", ln=True)

        pdf_bytes = pdf.output(dest="S").encode("latin1")
        mensaje_placeholder.success("Orden generada")
        descarga_placeholder.download_button(
            label="📥 Descargar PDF",
            data=pdf_bytes,
            file_name="OrdenCompra.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.subheader("Vista previa")
        st.dataframe(orden_compra, use_container_width=True)

