# pages/admin_upload.py
import streamlit as st
from drive_utils import upload_file_to_drive, insert_touro, insert_progenie
from pdf_parser import parse_proof
import uuid

def render_admin_panel():
    st.markdown("## 📤 Painel Administrativo")

    tab_touro, tab_progenie = st.tabs(["🐂 Cadastrar Touro", "🐄 Cadastrar Filha"])

    # ── ABA: Cadastrar Touro ─────────────────────────────────────────────────
    with tab_touro:
        st.markdown("### 1️⃣ Upload da Prova (PDF)")
        raca = st.selectbox(
            "Raça do Touro",
            options=["HO", "JE", "GI", "GIR"],
            format_func=lambda x: {
                "HO": "🐄 Holandês",
                "JE": "🐄 Jersey",
                "GI": "🐄 Girolando",
                "GIR": "🐄 Gir Leiteiro"
            }[x]
        )

        pdf_file = st.file_uploader(
            "Envie a prova em PDF",
            type=["pdf"],
            key="pdf_touro"
        )

        dados_extraidos = {}

        if pdf_file:
            pdf_bytes = pdf_file.read()
            with st.spinner("🔍 Analisando PDF..."):
                dados_extraidos = parse_proof(pdf_bytes, raca) or {}

            if dados_extraidos:
                st.success("✅ Dados extraídos com sucesso! Revise abaixo:")
            else:
                st.warning("⚠️ Não foi possível extrair dados automaticamente. Preencha manualmente.")

        # ── Formulário (pré-preenchido com dados do PDF) ─────────────────────
        with st.form("form_touro"):
            st.markdown("### 2️⃣ Dados do Touro")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Identificação**")
                id_touro       = st.text_input("Código", dados_extraidos.get("id_touro", ""))
                nome_curto     = st.text_input("Nome Curto", dados_extraidos.get("nome_curto", ""))
                nome_completo  = st.text_input("Nome Completo", dados_extraidos.get("nome_completo", ""))
                registro       = st.text_input("Registro", dados_extraidos.get("registro", ""))
                data_nasc      = st.text_input("Data Nasc.", dados_extraidos.get("data_nascimento", ""))
                cruzamento     = st.text_input("Cruzamento", dados_extraidos.get("cruzamento", ""))
                kappa          = st.text_input("Kappa-Caseína", dados_extraidos.get("kappa_caseina", ""))
                beta           = st.text_input("Beta-Caseína", dados_extraidos.get("beta_caseina", ""))
                efi            = st.text_input("EFI (%)", dados_extraidos.get("EFI", ""))
                rha            = st.text_input("RHA (%)", dados_extraidos.get("RHA", ""))
                prova_atual    = st.text_input("Prova Atual", dados_extraidos.get("prova_atual", ""))

            with col2:
                st.markdown("**Índices & Produção**")
                TPI  = st.text_input("TPI",      dados_extraidos.get("TPI", ""))
                NM   = st.text_input("NM$",      dados_extraidos.get("NM$", ""))
                CM   = st.text_input("CM$",      dados_extraidos.get("CM$", ""))
                FM   = st.text_input("FM$",      dados_extraidos.get("FM$", ""))
                GM   = st.text_input("GM$",      dados_extraidos.get("GM$", ""))
                leite_lbs = st.text_input("Leite (Lbs)",   dados_extraidos.get("leite_lbs", ""))
                leite_rel = st.text_input("Leite Rel (%)", dados_extraidos.get("leite_rel", ""))
                prot_lbs  = st.text_input("Proteína (Lbs)",dados_extraidos.get("proteina_lbs", ""))
                prot_pct  = st.text_input("Proteína (%)",  dados_extraidos.get("proteina_pct", ""))
                gord_lbs  = st.text_input("Gordura (Lbs)", dados_extraidos.get("gordura_lbs", ""))
                gord_pct  = st.text_input("Gordura (%)",   dados_extraidos.get("gordura_pct", ""))

            with col3:
                st.markdown("**Saúde & Parto**")
                PL    = st.text_input("Vida Produtiva", dados_extraidos.get("vida_produtiva", ""))
                SCS   = st.text_input("Cell. Somáticas", dados_extraidos.get("celulas_somaticas", ""))
                DPR   = st.text_input("DPR", dados_extraidos.get("DPR", ""))
                CCR   = st.text_input("CCR", dados_extraidos.get("CCR", ""))
                PTAT  = st.text_input("PTAT", dados_extraidos.get("PTAT", ""))
                UDC   = st.text_input("UDC",  dados_extraidos.get("UDC", ""))
                FLC   = st.text_input("FLC",  dados_extraidos.get("FLC", ""))
                ease_t= st.text_input("Ease Parto Touro (%)", dados_extraidos.get("ease_parto_touro_pct", ""))
                ease_f= st.text_input("Ease Parto Filha (%)", dados_extraidos.get("ease_parto_filha_pct", ""))
                pai   = st.text_input("Pai",  dados_extraidos.get("pai", ""))
                mae   = st.text_input("Mãe",  dados_extraidos.get("mae", ""))

            st.markdown("### 3️⃣ Foto do Touro")
            foto_file = st.file_uploader("Foto principal (JPG/PNG)", type=["jpg","jpeg","png"], key="foto_touro")

            submitted = st.form_submit_button("💾 Salvar Touro", use_container_width=True)

        if submitted:
            with st.spinner("Salvando..."):
                foto_id = ""
                pdf_id  = ""

                # Upload foto
                if foto_file:
                    foto_id = upload_file_to_drive(
                        foto_file.read(),
                        f"{id_touro}_foto.jpg",
                        st.secrets["drive"]["pasta_touros"]
                    )

                # Upload PDF original
                if pdf_file:
                    pdf_id = upload_file_to_drive(
                        pdf_bytes,
                        f"{id_touro}_prova.pdf",
                        st.secrets["drive"]["pasta_pdfs"],
                        mimetype="application/pdf"
                    )

                # Monta dicionário completo para o Sheets
                registro_touro = {
                    "id_touro": id_touro, "nome_curto": nome_curto,
                    "nome_completo": nome_completo, "raca": raca,
                    "registro": registro, "data_nascimento": data_nasc,
                    "cruzamento": cruzamento, "kappa_caseina": kappa,
                    "beta_caseina": beta, "EFI": efi, "RHA": rha,
                    "prova_atual": prova_atual, "TPI": TPI, "NM$": NM,
                    "CM$": CM, "FM$": FM, "GM$": GM,
                    "leite_lbs": leite_lbs, "leite_rel": leite_rel,
                    "proteina_lbs": prot_lbs, "proteina_pct": prot_pct,
                    "gordura_lbs": gord_lbs, "gordura_pct": gord_pct,
                    "vida_produtiva": PL, "celulas_somaticas": SCS,
                    "DPR": DPR, "CCR": CCR, "PTAT": PTAT,
                    "UDC": UDC, "FLC": FLC,
                    "ease_parto_touro_pct": ease_t,
                    "ease_parto_filha_pct": ease_f,
                    "pai": pai, "mae": mae,
                    "foto_drive_id": foto_id,
                    "pdf_drive_id": pdf_id,
                    # Campos completos do parser (todos os 50+ campos)
                    **{k: v for k, v in dados_extraidos.items()
                       if k not in registro_touro}
                }

                if insert_touro(registro_touro):
                    st.success(f"✅ Touro **{nome_curto}** cadastrado com sucesso!")
                    st.balloons()

    # ── ABA: Cadastrar Filha ─────────────────────────────────────────────────
    with tab_progenie:
        st.markdown("### Cadastrar Nova Filha")

        with st.form("form_progenie"):
            col1, col2 = st.columns(2)

            with col1:
                id_prog     = st.text_input("ID da Filha")
                id_pai      = st.text_input("Código do Touro Pai")
                nome_prog   = st.text_input("Nome da Filha")
                registro_p  = st.text_input("Registro")
                data_nasc_p = st.text_input("Data de Nascimento")
                proprietario= st.text_input("Proprietário / Fazenda")

            with col2:
                st.markdown("**Produção**")
                leite_prog  = st.text_input("Produção de Leite (Lts/Lactação)")
                gordura_prog= st.text_input("Gordura (%)")
                proteina_p  = st.text_input("Proteína (%)")
                st.markdown("**Conformação**")
                PTAT_prog   = st.text_input("PTAT")
                UDC_prog    = st.text_input("UDC")
                FLC_prog    = st.text_input("FLC")
                observacoes = st.text_area("Observações")

            st.markdown("### Fotos da Filha")
            fotos_prog = st.file_uploader(
                "Envie as fotos (múltiplas permitidas)",
                type=["jpg","jpeg","png"],
                accept_multiple_files=True,
                key="fotos_prog"
            )

            submitted_prog = st.form_submit_button("💾 Salvar Filha", use_container_width=True)

        if submitted_prog:
            with st.spinner("Salvando filha..."):
                fotos_ids = []

                for foto in fotos_prog:
                    fid = upload_file_to_drive(
                        foto.read(),
                        f"{id_prog}_{foto.name}",
                        st.secrets["drive"]["pasta_progenies"]
                    )
                    if fid:
                        fotos_ids.append(fid)

                registro_prog = {
                    "id_progenie": id_prog or str(uuid.uuid4())[:8],
                    "id_touro_pai": id_pai,
                    "nome": nome_prog,
                    "registro": registro_p,
                    "data_nascimento": data_nasc_p,
                    "proprietario": proprietario,
                    "leite_lts": leite_prog,
                    "gordura_pct": gordura_prog,
                    "proteina_pct": proteina_p,
                    "PTAT": PTAT_prog,
                    "UDC": UDC_prog,
                    "FLC": FLC_prog,
                    "observacoes": observacoes,
                    "fotos_drive_ids": ",".join(fotos_ids),  # IDs separados por vírgula
                }

                if insert_progenie(registro_prog):
                    st.success(f"✅ Filha **{nome_prog}** cadastrada com sucesso!")
