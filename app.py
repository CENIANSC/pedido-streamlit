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
col1, col2 = st.columns([4, 1])

with col1:
    st.title("Compras Cafetería UPPE")

with col2:
    generar_orden = st.button(
        "📄 Generar Orden de Compra",
        use_container_width=True
    )

# ==========================
# Selecciones
# ==========================
selecciones = {}

categorias = (
    df["categoría"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

tabs = st.tabs(categorias)

for tab, categoria in zip(tabs, categorias):

    with tab:

        df_categoria = df[
            df["categoría"].astype(str) == categoria
        ]

        productos = df_categoria.to_dict("records")

        # 4 productos por fila
        for fila_inicio in range(0, len(productos), 4):

            columnas = st.columns(4)

            for col, producto in zip(
                columnas,
                productos[fila_inicio:fila_inicio + 4]
            ):

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
                            {producto['producto']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    seleccion = st.radio(
                        "",
                        ["NO", "SÍ"],
                        horizontal=True,
                        index=0,
                        key=f"prod_{producto['producto']}",
                        label_visibility="collapsed"
                    )

                    selecciones[
                        producto["producto"]
                    ] = seleccion

            st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# Generar Orden de Compra
# ==========================
if generar_orden:

    df["Seleccion"] = df["producto"].map(selecciones)

    seleccionados = df[
        df["Seleccion"] == "SÍ"
    ]

    if seleccionados.empty:

        st.warning(
            "No se seleccionó ningún producto."
        )

    else:

        orden_compra = seleccionados[
            ["producto", "lugar"]
        ].reset_index(drop=True)

        # ==========================
        # Crear PDF
        # ==========================
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font(
            "Arial",
            "B",
            14
        )

        pdf.cell(
            0,
            10,
            "ORDEN DE COMPRA",
            ln=True,
            align="C"
        )

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

        fecha_formal = (
            f"{hoy.day} de "
            f"{meses[hoy.month]} de "
            f"{hoy.year}"
        )

        pdf.set_font(
            "Arial",
            "",
            10
        )

        pdf.cell(
            0,
            8,
            fecha_formal,
            ln=True,
            align="C"
        )

        pdf.ln(5)

        # ==========================
        # Configuración columnas
        # ==========================
        lugares = list(
            orden_compra.groupby("lugar")
        )

        margen_superior = pdf.get_y()

        ancho_columna = 90
        alto_renglon = 7

        separacion_tablas = 5

        x_col1 = 10
        x_col2 = 110

        columna_actual = 1
        x_actual = x_col1
        y_actual = margen_superior

        for lugar, productos_lugar in lugares:

            altura_tabla = (
                len(productos_lugar) + 1
            ) * alto_renglon

            # ¿Cabe la tabla?
            if y_actual + altura_tabla > 270:

                # Cambiar a columna derecha
                if columna_actual == 1:

                    columna_actual = 2
                    x_actual = x_col2
                    y_actual = margen_superior

                # Nueva página
                else:

                    pdf.add_page()

                    pdf.set_font(
                        "Arial",
                        "B",
                        14
                    )

                    pdf.cell(
                        0,
                        10,
                        "ORDEN DE COMPRA",
                        ln=True,
                        align="C"
                    )

                    pdf.set_font(
                        "Arial",
                        "",
                        10
                    )

                    pdf.cell(
                        0,
                        8,
                        fecha_formal,
                        ln=True,
                        align="C"
                    )

                    pdf.ln(5)

                    margen_superior = pdf.get_y()

                    columna_actual = 1
                    x_actual = x_col1
                    y_actual = margen_superior

            # ==========================
            # Encabezado tabla
            # ==========================
            pdf.set_xy(
                x_actual,
                y_actual
            )

            pdf.set_font(
                "Arial",
                "B",
                11
            )

            pdf.cell(
                ancho_columna,
                alto_renglon,
                str(lugar),
                border=1,
                align="C"
            )

            pdf.set_font(
                "Arial",
                "",
                10
            )

            # ==========================
            # Productos
            # ==========================
            for idx, (_, fila) in enumerate(
                productos_lugar.iterrows()
            ):

                pdf.set_xy(
                    x_actual,
                    y_actual +
                    alto_renglon *
                    (idx + 1)
                )

                pdf.cell(
                    ancho_columna,
                    alto_renglon,
                    str(
                        fila["producto"]
                    ),
                    border=1
                )

            y_actual += (
                altura_tabla +
                separacion_tablas
            )

        # ==========================
        # Descargar PDF
        # ==========================
        pdf_bytes = (
            pdf.output(dest="S")
            .encode("latin1")
        )

        st.success(
            "Orden de compra generada correctamente."
        )

        st.download_button(
            label="Descargar Orden de Compra PDF",
            data=pdf_bytes,
            file_name="OrdenCompra.pdf",
            mime="application/pdf"
        )

        st.subheader(
            "Vista previa"
        )

        st.dataframe(
            orden_compra,
            use_container_width=True
        )
