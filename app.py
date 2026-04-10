# app.py
import streamlit as st
from auth import render_admin_login
from drive_utils import (
    load_touros, load_progenies,
    get_image_from_drive, get_pdf_bytes_from_drive
)
from config.breed_indices import get_breed_config

# ── Configuração da Página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="🐂 Galeria de Touros",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="auto"
)

# ── CSS Global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Remove padding padrão */
    .block-container { padding-top: 1rem; }

    /* Cards */
    .bull-card {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
        transition: box-shadow 0.2s;
    }
    .bull-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.15); }

    /* Badge de raça */
    .breed-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
    }

    /* Índice principal destacado */
    .index-highlight {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1565C0;
        line-height: 1;
    }

    /* Valores de produção */
    .prod-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2E7D32;
    }
    .prod-value.negative { color: #C62828; }
</style>
""", unsafe_allow_html=True)

# ── Sessão ────────────────────────────────────────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "galeria"
if "touro_sel" not in st.session_state:
    st.session_state.touro_sel = None
if "filtro_raca" not in st.session_state:
    st.session_state.filtro_raca = "Todas"
if "filtro_busca" not in st.session_state:
    st.session_state.filtro_busca = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x80?text=Logo+Fazenda", use_container_width=True)
    st.markdown("---")

    # Filtros (visíveis a todos)
    st.markdown("### 🔍 Filtros")
    st.session_state.filtro_busca = st.text_input("Buscar touro", placeholder="Nome ou registro...")
    st.session_state.filtro_raca  = st.selectbox(
        "Raça",
        options=["Todas", "HO - Holandês", "JE - Jersey", "GI - Girolando", "GIR - Gir Leiteiro"]
    )

    if st.button("🏠 Galeria Principal", use_container_width=True):
        st.session_state.pagina = "galeria"
        st.rerun()

    # Login Admin
    is_admin, admin_user = render_admin_login()
    if is_admin:
        st.markdown("---")
        if st.button("📤 Painel de Upload", use_container_width=True):
            st.session_state.pagina = "admin"
            st.rerun()

# ── Roteamento ────────────────────────────────────────────────────────────────
if st.session_state.pagina == "galeria":
    render_galeria()

elif st.session_state.pagina == "touro":
    render_touro_detail()

elif st.session_state.pagina == "progenies":
    render_progenies()

elif st.session_state.pagina == "admin" and is_admin:
    from pages.admin_upload import render_admin_panel
    render_admin_panel()


# ════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE RENDERIZAÇÃO
# ════════════════════════════════════════════════════════════════════════════

def render_galeria():
    """Galeria principal com todos os touros e filtros."""
    st.markdown("# 🐂 Galeria de Touros")
    st.markdown("Clique em um touro para ver sua prova completa e galeria de filhas.")
    st.markdown("---")

    df = load_touros()
    if df.empty:
        st.info("Nenhum touro cadastrado ainda.")
        return

    # ── Aplicar filtros ──────────────────────────────────────────────────────
    busca = st.session_state.filtro_busca.strip().lower()
    raca_filtro = st.session_state.filtro_raca

    if busca:
        df = df[
            df["nome_curto"].str.lower().str.contains(busca, na=False) |
            df["registro"].str.lower().str.contains(busca, na=False)
        ]

    if raca_filtro != "Todas":
        codigo_raca = raca_filtro.split(" - ")[0]
        df = df[df["raca"] == codigo_raca]

    st.markdown(f"**{len(df)} touro(s) encontrado(s)**")

    # ── Grid: 3 colunas ──────────────────────────────────────────────────────
    cols = st.columns(3)
    for idx, (_, touro) in enumerate(df.iterrows()):
        breed_cfg = get_breed_config(touro.get("raca", "HO"))
        cor = breed_cfg["cor_tema"]

        with cols[idx % 3]:
            with st.container(border=True):
                # Foto do touro
                imagem = get_image_from_drive(touro.get("foto_drive_id", ""))
                if imagem:
                    st.image(imagem, use_container_width=True)
                else:
                    st.image(
                        "https://via.placeholder.com/300x250?text=Sem+Foto",
                        use_container_width=True
                    )

                # Cabeçalho do card
                st.markdown(
                    f"<span class='breed-badge' style='background:{cor}'>"
                    f"{touro.get('raca','?')}</span>",
                    unsafe_allow_html=True
                )
                st.markdown(f"### {touro.get('nome_curto','')}")
                st.caption(touro.get("nome_completo",""))

                # Índice principal em destaque
                idx_principal = breed_cfg["indice_principal"]
                valor_idx = touro.get(idx_principal, "—")
                st.markdown(
                    f"<div class='index-highlight'>{idx_principal}: {valor_idx}</div>",
                    unsafe_allow_html=True
                )

                # Produção resumida
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("🥛 Leite", f"{touro.get('leite_lbs','—')} lbs")
                col_b.metric("🧈 Gord.", f"{touro.get('gordura_lbs','—')} lbs")
                col_c.metric("🔬 Prot.", f"{touro.get('proteina_lbs','—')} lbs")

                st.markdown("---")
                if st.button(
                    f"🔍 Ver Prova & Filhas",
                    key=f"btn_touro_{touro['id_touro']}",
                    use_container_width=True
                ):
                    st.session_state.touro_sel = touro.to_dict()
                    st.session_state.pagina = "touro"
                    st.rerun()


def render_touro_detail():
    """Página de detalhe do touro com abas."""
    touro = st.session_state.touro_sel
    if not touro:
        st.session_state.pagina = "galeria"
        st.rerun()

    breed_cfg = get_breed_config(touro.get("raca", "HO"))

    # Navegação
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "galeria"
            st.rerun()
    with col_title:
        st.markdown(f"# {breed_cfg['icone']} {touro.get('nome_curto','')}")

    st.caption(f"{touro.get('nome_completo','')}  |  {touro.get('registro','')}  |  Prova: {touro.get('prova_atual','')}")
    st.markdown("---")

    # ── Hero: foto + índices principais ─────────────────────────────────────
    col_foto, col_indices = st.columns([1, 2])
    with col_foto:
        img = get_image_from_drive(touro.get("foto_drive_id",""))
        if img:
            st.image(img, use_container_width=True)
        else:
            st.image("https://via.placeholder.com/300x350?text=Sem+Foto",
                     use_container_width=True)

        # Download do PDF da prova
        pdf_id = touro.get("pdf_drive_id","")
        if pdf_id:
            pdf_bytes = get_pdf_bytes_from_drive(pdf_id)
            if pdf_bytes:
                st.download_button(
                    label="📥 Baixar Prova (PDF)",
                    data=pdf_bytes,
                    file_name=f"{touro.get('id_touro','touro')}_prova.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    with col_indices:
        # Índices econômicos em destaque
        idx_cols = st.columns(len(breed_cfg["indices_economicos"]) + 1)

        idx_cols[0].metric(
            breed_cfg["indice_principal"],
            touro.get(breed_cfg["indice_principal"], "—")
        )
        for i, idx_name in enumerate(breed_cfg["indices_economicos"]):
            idx_cols[i+1].metric(idx_name, f"${touro.get(idx_name,'—')}")

        st.markdown("---")
        st.markdown(f"**Raça:** {breed_cfg['nome_completo']}")
        st.markdown(f"**Nascimento:** {touro.get('data_nascimento','—')}")
        st.markdown(f"**Cruzamento:** {touro.get('cruzamento','—')}")
        st.markdown(f"**Kappa-Caseína:** {touro.get('kappa_caseina','—')}  |  **Beta-Caseína:** {touro.get('beta_caseina','—')}")
        st.markdown(f"**EFI:** {touro.get('EFI','—')}%  |  **RHA:** {touro.get('RHA','—')}%")

    st.markdown("---")

    # ── Abas de informações ──────────────────────────────────────────────────
    tab_prod, tab_saude, tab_parto, tab_conf, tab_ped = st.tabs([
        "🥛 Produção", "❤️ Saúde & Eficiência",
        "🤱 Facilidade de Parto", "🦵 Conformação", "🧬 Pedigree"
    ])

    with tab_prod:
        c1, c2, c3 = st.columns(3)
        c1.metric("🥛 Leite (Lbs)",    touro.get("leite_lbs","—"), help=f"Rel: {touro.get('leite_rel','—')}%")
        c2.metric("🧈 Gordura (Lbs)",  touro.get("gordura_lbs","—"), delta=f"{touro.get('gordura_pct','—')}%")
        c3.metric("🔬 Proteína (Lbs)", touro.get("proteina_lbs","—"), delta=f"{touro.get('proteina_pct','—')}%")

    with tab_saude:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vida Produtiva",  touro.get("vida_produtiva","—"))
        c2.metric("Livab. Vaca",     touro.get("livabilidade_vaca","—"))
        c3.metric("Livab. Novilha",  touro.get("livabilidade_novilha","—"))
        c4.metric("Cél. Somáticas",  touro.get("celulas_somaticas","—"))

        st.markdown("**Doenças (%)**")
        dc1, dc2, dc3, dc4, dc5 = st.columns(5)
        dc1.metric("MAST", f"{touro.get('MAST','—')}%")
        dc2.metric("METR", f"{touro.get('METR','—')}%")
        dc3.metric("DA",   f"{touro.get('DA','—')}%")
        dc4.metric("KETO", f"{touro.get('KETO','—')}%")
        dc5.metric("RP",   f"{touro.get('RP','—')}%")

        st.markdown("**Reprodução & Eficiência**")
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("DPR",  touro.get("DPR","—"))
        rc2.metric("CCR",  touro.get("CCR","—"))
        rc3.metric("HCR",  touro.get("HCR","—"))
        rc4.metric("DWP$", f"${touro.get('DWP$','—')}")

    with tab_parto:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ease Parto Touro", f"{touro.get('ease_parto_touro_pct','—')}%",
                  help=f"Rel: {touro.get('ease_parto_touro_rel','—')}%")
        c2.metric("Mortinato Touro",  f"{touro.get('mortinato_touro_pct','—')}%",
                  help=f"Rel: {touro.get('mortinato_touro_rel','—')}%")
        c3.metric("Ease Parto Filha", f"{touro.get('ease_parto_filha_pct','—')}%",
                  help=f"Rel: {touro.get('ease_parto_filha_rel','—')}%")
        c4.metric("Mortinato Filha",  f"{touro.get('mortinato_filha_pct','—')}%",
                  help=f"Rel: {touro.get('ease_parto_filha_rel','—')}%")

    with tab_conf:
        c1, c2, c3 = st.columns(3)
        c1.metric("PTAT", touro.get("PTAT","—"))
        c2.metric("UDC",  touro.get("UDC","—"))
        c3.metric("FLC",  touro.get("FLC","—"))
        c1.metric("MUI",  touro.get("MUI","—"))
        c2.metric("BWC",  touro.get("BWC","—"))

        with st.expander("📋 Conformação Detalhada"):
            conf_data = {
                "Estatura": touro.get("estatura","—"),
                "Força": touro.get("forca","—"),
                "Prof. Corporal": touro.get("prof_corporal","—"),
                "Forma Leiteira": touro.get("forma_leiteira","—"),
                "Ângulo Garupa": touro.get("angulo_garupa","—"),
                "Largura Garupa": touro.get("largura_garupa","—"),
                "Pernas (lateral)": touro.get("pernas_lateral","—"),
                "Pernas (posterior)": touro.get("pernas_post","—"),
                "Ângulo Casco": touro.get("angulo_casco","—"),
                "Lig. Ubere Ant.": touro.get("lig_ub_ant","—"),
                "Alt. Ubere Post.": touro.get("alt_ub_post","—"),
                "Larg. Ubere Post.": touro.get("larg_ub_post","—"),
                "Lig. Central": touro.get("lig_central","—"),
                "Prof. Úbere": touro.get("prof_ubere","—"),
                "Posição Tetos Ant.": touro.get("posic_tetos_ant","—"),
                "Posição Tetos Post.": touro.get("posic_tetos_post","—"),
                "Comprimento Teto": touro.get("comp_teto","—"),
            }
            import pandas as pd
            st.dataframe(
                pd.DataFrame(conf_data.items(), columns=["Característica", "Valor"]),
                use_container_width=True,
                hide_index=True
            )

    with tab_ped:
        ped_data = {
            "Pai": touro.get("pai","—"),
            "Mãe": touro.get("mae","—"),
            "Avô Materno": touro.get("avo_mat","—"),
            "Avó Materna": touro.get("avo_mae","—"),
            "Bisavô Materno": touro.get("bisavo_mat","—"),
            "Bisavó Materna": touro.get("bisavo_mae","—"),
        }
        for label, value in ped_data.items():
            st.markdown(f"**{label}:** {value}")

    st.markdown("---")

    # Botão para galeria de filhas
    if st.button("🐄 Ver Galeria de Filhas", use_container_width=True, type="primary"):
        st.session_state.pagina = "progenies"
        st.rerun()


def render_progenies():
    """Galeria de filhas de um touro específico."""
    touro = st.session_state.touro_sel
    if not touro:
        st.session_state.pagina = "galeria"
        st.rerun()

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "touro"
            st.rerun()
    with col_title:
        st.markdown(f"# 🐄 Filhas de {touro.get('nome_curto','')}")

    st.markdown("---")

    df_prog = load_progenies(touro["id_touro"])

    if df_prog.empty:
        st.info("ℹ️ Nenhuma filha cadastrada para este touro ainda.")
        return

    st.markdown(f"**{len(df_prog)} filha(s) encontrada(s)**")

    # Grid de filhas: 4 por linha

