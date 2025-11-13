import re
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from io import BytesIO

# =====================================
# FUNCIONES
# =====================================

def extract_text_with_pages(pdf_file):
    pdf_doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    pages_text = []
    for i, page in enumerate(pdf_doc):
        text = page.get_text("text")
        pages_text.append({"page": i + 1, "text": text})
    return pages_text

def search_in_pdf(pages_text, query):
    results = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for page_info in pages_text:
        text = page_info["text"]
        matches = list(pattern.finditer(text))
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].replace("\n", " ")
            results.append({
                "Página": page_info["page"],
                "Coincidencia": match.group(0),
                "Contexto": context
            })
    return results

def analyze_legal_data(text):
    """Extrae todos los datos legales clave automáticamente."""
    patterns = {
        "Juzgado": r"(Juzgado|Sala|Tribunal)[\s\wº°\d\-\.]*",
        "Expediente": r"(Expediente|T\.|Toca|Juicio|Proceso|Asunto)\s*[A-Z0-9\/\-\.]+",
        "Secretaría": r"(Secretar[ií]a|Despacho)\s*[\w\d\sº°#\-]*",
        "Demandante": r"(Demandante|Actor|Parte\s+Actora)[:\s]+([A-ZÁÉÍÓÚÑa-z\s\.]+)",
        "Demandado": r"(Demandado|Demandada|Parte\s+Demandada)[:\s]+([A-ZÁÉÍÓÚÑa-z\s\.]+)"
    }

    results = []
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                results.append({"Categoría": key, "Valor": m[-1].strip()})
            else:
                results.append({"Categoría": key, "Valor": m.strip()})
    return pd.DataFrame(results).drop_duplicates()

# =====================================
# INTERFAZ
# =====================================

def main():
    st.set_page_config(page_title="Buscador Judicial Inteligente 4.0", page_icon="⚖️", layout="wide")

    # ======= CSS =======
    st.markdown("""
        <style>
        body {background-color: #0d1117; color: #e2e8f0;}
        h1, h2, h3 {font-family: 'Montserrat', sans-serif; color: #00B4D8;}
        .stButton>button {
            background: linear-gradient(90deg, #0077B6, #00B4D8);
            color: white; border: none; border-radius: 10px; font-weight: bold;
        }
        .stDownloadButton>button {background: #22c55e; color: white; border-radius: 10px; font-weight: bold;}
        .footer {text-align: center; color: #9ca3af; font-size: 0.9rem; margin-top: 3rem;}
        </style>
    """, unsafe_allow_html=True)

    # ======= SIDEBAR =======
    st.sidebar.image("https://i.imgur.com/KTJgyZC.png", width=180)
    modo = st.sidebar.radio("🧭 Modo de uso", ["🔍 Búsqueda Específica", "🧠 Análisis Automático Completo"])
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2025 FPA Solutions | Stallum Analytics ⚙️")

    # ======= HEADER =======
    st.title("⚖️ Buscador Judicial Inteligente 4.0")
    st.markdown("Plataforma para búsqueda avanzada y análisis automatizado de documentos judiciales 💼")
    st.markdown("---")

    # ======= APP =======
    uploaded_pdf = st.file_uploader("📂 Sube tu archivo PDF", type=["pdf"])

    if uploaded_pdf:
        with st.spinner("Extrayendo texto del documento... 📖"):
            pages_text = extract_text_with_pages(uploaded_pdf)
            full_text = " ".join([p["text"] for p in pages_text])

        # ---------- MODO 1 ----------
        if modo == "🔍 Búsqueda Específica":
            st.subheader("🔎 Buscar términos dentro del PDF")

            opciones = ["Personalizado", "Juzgado", "Expediente", "Secretaría", "Demandante", "Demandado", "Despacho"]
            tipo_busqueda = st.radio("Tipo de búsqueda:", opciones, horizontal=True)

            if tipo_busqueda == "Personalizado":
                query = st.text_input("Palabra o frase a buscar:")
            else:
                query = tipo_busqueda

            if query:
                with st.spinner("Buscando coincidencias..."):
                    results = search_in_pdf(pages_text, query)

                if results:
                    df = pd.DataFrame(results)
                    st.success(f"✅ {len(df)} coincidencias encontradas para '{query}'.")
                    st.dataframe(df, use_container_width=True)

                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name="Resultados")
                    output.seek(0)
                    st.download_button(
                        label="💾 Descargar Excel",
                        data=output,
                        file_name=f"Resultados_{query}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    for i, row in df.iterrows():
                        highlighted = re.sub(
                            f"(?i)({re.escape(query)})",
                            r"<mark style='background-color:#00B4D8;color:black;'><b>\\1</b></mark>",
                            row["Contexto"]
                        )
                        st.markdown(f"**Página {row['Página']}:** {highlighted}", unsafe_allow_html=True)
                        st.markdown("<hr>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ No se encontraron coincidencias.")

        # ---------- MODO 2 ----------
        else:
            st.subheader("🧠 Análisis Automático Completo")
            st.markdown("El sistema identificará todos los datos relevantes del documento (juzgados, expedientes, demandantes, demandados, etc.)")

            with st.spinner("Analizando texto... 🧠"):
                df_auto = analyze_legal_data(full_text)

            if not df_auto.empty:
                st.success(f"✅ Se identificaron {len(df_auto)} datos legales.")
                st.dataframe(df_auto, use_container_width=True)

                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_auto.to_excel(writer, index=False, sheet_name="Análisis_Completo")
                output.seek(0)

                st.download_button(
                    label="💾 Descargar Análisis Completo en Excel",
                    data=output,
                    file_name="Analisis_Completo_Boletin.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("⚠️ No se detectaron datos legales en este documento.")

    st.markdown("<div class='footer'>© 2025 FPA Solutions | Desarrollado por Stallum Analytics ⚙️</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
