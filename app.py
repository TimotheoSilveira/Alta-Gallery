# app.py
import streamlit as st

st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="auto"
)

import pandas as pd
from io import BytesIO

try:
    from auth import render_admin_login, render_admin_logout
except Exception as e:
    st.error(f"❌ Erro ao importar auth.py: {e}")
    st.stop()

try:
    from drive_utils import (
        load_touros,
        load_progenies,
        get_image_from_drive,
        get_pdf_bytes_from_drive,
    )
except Exception as e:
    st.error(f"❌ Erro ao importar drive_utils.py: {e}")
    st.stop()

try:
    from config.breed_indices import get_breed_config
except Exception as e:
    st.error(f"❌ Erro ao importar breed_indices.py: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .breed-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
        margin-bottom: 6px;
    }
    .index-highlight {
        font-size: 2rem;
        font-weight: 900;
        line-height: 1.1;
        margin: 6px 0;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
_defaults = {
    "pagina":         "galeria",
    "touro_sel":      None,
    "filtro_busca":   "",
    "filtro_raca":    "Todas",
    "is_admin":       False,
    "admin_user":     None,
    "login_attempts": 0,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🐂 Alta Gallery")
    st.caption("Raças leiteiras de elite")
    st.divider()

    st.markdown("### 🔍 Filtros")
    st.session_state.filtro_busca = st.text_input(
        "Buscar por nome ou registro",
        value=st.session_state.filtro_busca,
        placeholder="Ex: AltaGOLDENGATE...",
    )
    st.session_state.filtro_raca = st.selectbox(
        "Filtrar por raça",
        options=["Todas", "HO - Holandês", "JE - Jersey",
                 "GI - Girolando", "GIR - Gir Leiteiro"],
        index=["Todas", "HO - Holandês", "JE - Jersey",
               "GI - Girolando", "GIR - Gir Leiteiro"].index(
            st.session_state.filtro_raca
        )
    )

    st.divider()
    if st.button("🏠 Galeria Principal", use_container_width=True):
        st.session_state.pagina    = "galeria"
        st.session_state.touro_sel = None
        st.rerun()

# ── Autenticação ──────────────────────────────────────────────
is_admin, admin_user = render_admin_login()
st.session_state.is_admin   = is_admin
st.session_state.admin_user = admin_user

if is_admin:
    render_admin_logout()
    with st.sidebar:
        st.divider()
        st.markdown("### ⚙️ Administração")
        if st.button("📤 Painel de Upload", use_container_width=True):
            st.session_state.pagina = "admin"
            st.rerun()

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def _placeholder():
    return "https://placehold.co/300x280/EEE/999?text=Sem+Foto"

def _val(touro: dict, campo: str) -> str:
    """Retorna valor do campo ou traço se vazio/nulo."""
    v = touro.get(campo, "")
    if v is None or str(v).strip() in ("", "nan", "None"):
        return "—"
    return str(v)

# ══════════════════════════════════════════════════════════════
# GALERIA PRINCIPAL
# ══════════════════════════════════════════════════════════════
def render_galeria():
    st.markdown("# 🐂 Alta Gallery")
    st.caption("Selecione um touro para ver a prova completa e a galeria de filhas.")
    st.divider()

    with st.spinner("Carregando touros..."):
        try:
            df = load_touros()
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
            return

    if df.empty:
        st.info("ℹ️ Nenhum touro cadastrado ainda.")
        return

    # ── Filtros ───────────────────────────────────────────────
    busca    = st.session_state.filtro_busca.strip().lower()
    raca_sel = st.session_state.filtro_raca

    if busca:
        mask = (
            df.get("Nome", pd.Series(dtype=str))
              .astype(str).str.lower().str.contains(busca, na=False) |
            df.get("InterRegNumber", pd.Series(dtype=str))
              .astype(str).str.lower().str.contains(busca, na=False)
        )
        df = df[mask]

    if raca_sel != "Todas":
        codigo_raca = raca_sel.split(" - ")[0]
        df = df[df["Raça"].astype(str) == codigo_raca]

    if df.empty:
        st.warning("Nenhum touro encontrado com os filtros aplicados.")
        return

    st.markdown(f"**{len(df)} touro(s) encontrado(s)**")
    st.divider()

    # ── Grid 3 colunas ────────────────────────────────────────
    cols = st.columns(3, gap="medium")

    for idx, (_, touro) in enumerate(df.iterrows()):
        raca_code = str(touro.get("Raça", "HO"))
        breed_cfg = get_breed_config(raca_code)
        cor       = breed_cfg.get("cor_tema", "#37474F")

        with cols[idx % 3]:
            with st.container(border=True):

                # Foto
                foto_id = str(touro.get("foto_id", "")).strip()
                if foto_id and foto_id not in ("", "nan", "None"):
                    img = get_image_from_drive(foto_id)
                    st.image(img if img else _placeholder(),
                             use_container_width=True)
                else:
                    st.image(_placeholder(), use_container_width=True)

                # Badge raça
                st.markdown(
                    f"<span class='breed-badge' style='background:{cor}'>"
                    f"&nbsp;{raca_code}&nbsp;</span>",
                    unsafe_allow_html=True
                )

                # Nome
                st.markdown(f"### {touro.get('Nome', 'Sem nome')}")
                st.caption(str(touro.get("Nome completo", "")))

                # TPI em destaque
                tpi = _val(touro, "TPI")
                st.markdown(
                    f"<div class='index-highlight' style='color:{cor}'>"
                    f"TPI: {tpi}</div>",
                    unsafe_allow_html=True
                )

                # Produção resumida
                c1, c2, c3 = st.columns(3)
                c1.metric("🥛 Leite",   _val(touro, "Leite"))
                c2.metric("🧈 Gordura", _val(touro, "Gordura"))
                c3.metric("🔬 Prot.",   _val(touro, "Proteína"))

                # Botão detalhe
                if st.button(
                    "🔍 Ver Prova & Filhas",
                    key=f"btn_{touro.get('Código NAAB', idx)}",
                    use_container_width=True,
                    type="primary"
                ):
                    st.session_state.touro_sel = touro.to_dict()
                    st.session_state.pagina    = "touro"
                    st.rerun()


# ══════════════════════════════════════════════════════════════
# DETALHE DO TOURO
# ══════════════════════════════════════════════════════════════
def render_touro_detail():
    touro = st.session_state.get("touro_sel")
    if not touro:
        st.session_state.pagina = "galeria"
        st.rerun()
        return

    breed_cfg = get_breed_config(str(touro.get("Raça", "HO")))
    cor       = breed_cfg.get("cor_tema", "#37474F")

    # ── Navegação ─────────────────────────────────────────────
    col_back, col_title = st.columns([1, 7])
    with col_back:
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "galeria"
            st.rerun()
    with col_title:
        st.markdown(
            f"<h1 style='color:{cor}'>🐂 {touro.get('Nome','')}</h1>",
            unsafe_allow_html=True
        )

    st.caption(
        f"{touro.get('Nome completo','')}  ·  "
        f"Registro: {touro.get('InterRegNumber','')}  ·  "
        f"Código NAAB: {touro.get('Código NAAB','')}  ·  "
        f"Prova: {touro.get('Prova','')}  ·  "
        f"Raça: {breed_cfg.get('nome_completo','')}"
    )
    st.divider()

    # ── Hero: foto + índices ──────────────────────────────────
    col_foto, col_info = st.columns([1, 2], gap="large")

    with col_foto:
        foto_id = str(touro.get("foto_id", "")).strip()
        img = get_image_from_drive(foto_id) if foto_id not in ("", "nan", "None") else None
        st.image(img if img else _placeholder(), use_container_width=True)

        # Download PDF
        prova_id = str(touro.get("prova_id", "")).strip()
        if prova_id and prova_id not in ("nan", "None"):
            with st.spinner("Preparando PDF..."):
                pdf_bytes = get_pdf_bytes_from_drive(prova_id)
            if pdf_bytes:
                st.download_button(
                    label="📥 Baixar Prova (PDF)",
                    data=pdf_bytes,
                    file_name=f"{touro.get('Código NAAB','touro')}_prova.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    with col_info:
        # Índices econômicos
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("TPI",  _val(touro, "TPI"))
        c2.metric("NM$",  f"${_val(touro, 'NM$')}")
        c3.metric("CM$",  f"${_val(touro, 'CM$')}")
        c4.metric("FM$",  f"${_val(touro, 'FM$')}")
        c5.metric("GM$",  f"${_val(touro, 'GM$')}")

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**📅 Nascimento:** {_val(touro, 'Birth Date')}")
            st.markdown(f"**🧬 Kapa-Caseína:** {_val(touro, 'Kapa-Caseína')}")
            st.markdown(f"**🧬 Beta-Caseína:** {_val(touro, 'Beta-Caseína')}")
        with col_b:
            st.markdown(f"**📊 EFI:** {_val(touro, 'EFI')}%")
            st.markdown(f"**🏷️ PTAT:** {_val(touro, 'PTAT')}")
            st.markdown(f"**🏷️ MUI:** {_val(touro, 'MUI')}")

    st.divider()

    # ── Abas ──────────────────────────────────────────────────
    tab_prod, tab_saude, tab_conf = st.tabs([
        "🥛 Produção",
        "❤️ Saúde & Eficiência",
        "🦵 Conformação",
    ])

    with tab_prod:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🥛 Leite (Lbs)",   _val(touro, "Leite"))
        c2.metric("🧈 Gordura (Lbs)", _val(touro, "Gordura"))
        c3.metric("% Gordura",        _val(touro, "% Gordura"))
        c4.metric("🔬 Proteína (Lbs)",_val(touro, "Proteína"))
        c5.metric("% Proteína",       _val(touro, "Prot%"))

        st.divider()
        c6 = st.columns(3)
        c6.metric("CGP",  _val(touro, "CGP"))
       
       
    with tab_saude:
        c1, c2, c3, c4 = st.columns(3)
        c1.metric("REI",  _val(touro, "REI"))
        c2.metric("VP",   _val(touro, "VP"))
        c3.metric("IF",   _val(touro, "IF"))
        c4.metric("EFI",  f"{_val(touro, 'EFI')}%")

    with tab_conf:
        c1, c2, c3 = st.columns(3)
        c1.metric("PTAT", _val(touro, "PTAT"))
        c2.metric("MUI",  _val(touro, "MUI"))
        c3.metric("CUB",  _val(touro, "CUB"))

    st.divider()

    # Botão galeria de filhas
    if st.button(
        "🐄 Ver Galeria de Filhas",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.pagina = "progenies"
        st.rerun()


# ══════════════════════════════════════════════════════════════
# GALERIA DE FILHAS
# ══════════════════════════════════════════════════════════════
def render_progenies():
    touro = st.session_state.get("touro_sel")
    if not touro:
        st.session_state.pagina = "galeria"
        st.rerun()
        return

    col_back, col_title = st.columns([1, 7])
    with col_back:
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "touro"
            st.rerun()
    with col_title:
        st.markdown(f"# 🐄 Filhas de {touro.get('Nome','')}")

    st.caption(
        f"Pai: {touro.get('Nome completo','')}  ·  "
        f"Registro: {touro.get('InterRegNumber','')}  ·  "
        f"Raça: {touro.get('Raça','')}"
    )
    st.divider()

    with st.spinner("Carregando filhas..."):
        try:
            df_prog = load_progenies(str(touro.get("Código NAAB", "")))
        except Exception as e:
            st.error(f"❌ Erro ao carregar filhas: {e}")
            return

    if df_prog.empty:
        st.info("ℹ️ Nenhuma filha cadastrada para este touro ainda.")
        return

    st.markdown(f"**{len(df_prog)} filha(s) cadastrada(s)**")
    st.divider()

    cols = st.columns(4, gap="small")
    for idx, (_, prog) in enumerate(df_prog.iterrows()):
        with cols[idx % 4]:
            with st.container(border=True):
                fotos_raw = str(prog.get("fotos_drive_ids", ""))
                fotos_ids = [f.strip() for f in fotos_raw.split(",") if f.strip()]

                if fotos_ids:
                    img = get_image_from_drive(fotos_ids[0])
                    st.image(img if img else _placeholder(),
                             use_container_width=True)
                    if len(fotos_ids) > 1:
                        st.caption(f"📷 +{len(fotos_ids)-1} foto(s)")
                else:
                    st.image(_placeholder(), use_container_width=True)

                st.markdown(f"**{prog.get('nome','Sem nome')}**")
                st.caption(
                    f"📅 {prog.get('data_nascimento','—')}  ·  "
                    f"🏠 {prog.get('proprietario','—')}"
                )

                leite = str(prog.get("leite_lts", "")).strip()
                if leite and leite not in ("nan", "None", ""):
                    st.markdown(f"🥛 **{leite} L/Lact.**")

                if fotos_ids:
                    img_dl = get_image_from_drive(fotos_ids[0])
                    if img_dl:
                        buf = BytesIO()
                        img_dl.save(buf, format="JPEG", quality=90)
                        st.download_button(
                            label="⬇️ Baixar Foto",
                            data=buf.getvalue(),
                            file_name=f"{prog.get('nome','filha')}.jpg",
                            mime="image/jpeg",
                            key=f"dl_{prog.get('id_progenie', idx)}",
                            use_container_width=True,
                        )


# ══════════════════════════════════════════════════════════════
# ROTEADOR
# ══════════════════════════════════════════════════════════════
_pagina = st.session_state.pagina

if _pagina == "galeria":
    render_galeria()

elif _pagina == "touro":
    if st.session_state.touro_sel:
        render_touro_detail()
    else:
        st.session_state.pagina = "galeria"
        st.rerun()

elif _pagina == "progenies":
    if st.session_state.touro_sel:
        render_progenies()
    else:
        st.session_state.pagina = "galeria"
        st.rerun()

elif _pagina == "admin":
    if st.session_state.is_admin:
        st.markdown("## ⚙️ Painel Administrativo")
        st.info("🚧 Painel em construção.")
    else:
        st.session_state.pagina = "galeria"
        st.rerun()

else:
    st.session_state.pagina = "galeria"
    st.rerun()
