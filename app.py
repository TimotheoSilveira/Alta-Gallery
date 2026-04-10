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
# CORES POR RAÇA
# ══════════════════════════════════════════════════════════════
BREED_CONFIG = {
    "HO":  {"cor": "#1565C0", "nome": "Holandês"},
    "JE":  {"cor": "#6A1B9A", "nome": "Jersey"},
    "GI":  {"cor": "#2E7D32", "nome": "Girolando"},
    "GIR": {"cor": "#E65100", "nome": "Gir Leiteiro"},
}

def get_breed_color(raca: str) -> str:
    return BREED_CONFIG.get(str(raca).strip().upper(), {}).get("cor", "#37474F")

def get_breed_name(raca: str) -> str:
    return BREED_CONFIG.get(str(raca).strip().upper(), {}).get("nome", raca)

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
# HELPERS
# ══════════════════════════════════════════════════════════════
def _placeholder() -> str:
    return "https://placehold.co/300x280/EEE/999?text=Sem+Foto"

def _val(dados: dict, campo: str) -> str:
    """Retorna valor do campo ou traço se vazio/nulo."""
    v = dados.get(campo, "")
    if v is None or str(v).strip() in ("", "nan", "None"):
        return "—"
    return str(v).strip()

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
        options=[
            "Todas",
            "HO - Holandês",
            "JE - Jersey",
            "GI - Girolando",
            "GIR - Gir Leiteiro",
        ],
        index=[
            "Todas",
            "HO - Holandês",
            "JE - Jersey",
            "GI - Girolando",
            "GIR - Gir Leiteiro",
        ].index(st.session_state.filtro_raca)
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
        if st.button("📤 Painel Admin", use_container_width=True):
            st.session_state.pagina = "admin"
            st.rerun()

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
              .astype(str).str.lower().str.contains(busca, na=False)
            |
            df.get("InterRegNumber", pd.Series(dtype=str))
              .astype(str).str.lower().str.contains(busca, na=False)
        )
        df = df[mask]

    if raca_sel != "Todas":
        codigo_raca = raca_sel.split(" - ")[0]
        df = df[df["Raça"].astype(str).str.strip() == codigo_raca]

    if df.empty:
        st.warning("Nenhum touro encontrado com os filtros aplicados.")
        return

    st.markdown(f"**{len(df)} touro(s) encontrado(s)**")
    st.divider()

    # ── Grid 3 colunas ────────────────────────────────────────
    cols = st.columns(3, gap="medium")

    for idx, (_, touro) in enumerate(df.iterrows()):
        raca_code = str(touro.get("Raça", "HO")).strip()
        cor       = get_breed_color(raca_code)

        with cols[idx % 3]:
            with st.container(border=True):

                # Foto
                foto_id = str(touro.get("foto_id", "")).strip()
                if foto_id and foto_id not in ("", "nan", "None"):
                    img = get_image_from_drive(foto_id)
                    st.image(
                        img if img else _placeholder(),
                        use_container_width=True
                    )
                else:
                    st.image(_placeholder(), use_container_width=True)

                # Badge raça
                st.markdown(
                    f"<span class='breed-badge' style='background:{cor}'>"
                    f"&nbsp;{raca_code}&nbsp;</span>",
                    unsafe_allow_html=True
                )

                # Nome e nome completo
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
                    key=f"btn_{touro.get('Código NAAB', idx)}_{idx}",
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

    cor = get_breed_color(str(touro.get("Raça", "HO")))

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
        f"{touro.get('Nome completo', '')}  ·  "
        f"Registro: {touro.get('InterRegNumber', '')}  ·  "
        f"Código NAAB: {touro.get('Código NAAB', '')}  ·  "
        f"Prova: {touro.get('Prova', '')}  ·  "
        f"Raça: {get_breed_name(str(touro.get('Raça', '')))}"
    )
    st.divider()

    # ── Hero: foto + índices principais ──────────────────────
    col_foto, col_info = st.columns([1, 2], gap="large")

    with col_foto:
        foto_id = str(touro.get("foto_id", "")).strip()
        img = get_image_from_drive(foto_id) \
              if foto_id not in ("", "nan", "None") else None
        st.image(img if img else _placeholder(), use_container_width=True)

        # Download PDF da prova
        prova_id = str(touro.get("prova_id", "")).strip()
        if prova_id and prova_id not in ("", "nan", "None"):
            with st.spinner("Preparando PDF..."):
                pdf_bytes = get_pdf_bytes_from_drive(prova_id)
            if pdf_bytes:
                st.download_button(
                    label="📥 Baixar Prova (PDF)",
                    data=pdf_bytes,
                    file_name=(
                        f"{touro.get('Código NAAB','touro')}_prova.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )

    with col_info:
        # Índices econômicos
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("TPI", _val(touro, "TPI"))
        c2.metric("NM$", f"${_val(touro, 'NM$')}")
        c3.metric("CM$", f"${_val(touro, 'CM$')}")
        c4.metric("FM$", f"${_val(touro, 'FM$')}")
        c5.metric("GM$", f"${_val(touro, 'GM$')}")

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

    # ── Aba Produção ──────────────────────────────────────────
    with tab_prod:
        st.markdown("##### 🥛 Produção Leiteira")
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Leite (Lbs)",    _val(touro, "Leite"))
        p2.metric("Gordura (Lbs)",  _val(touro, "Gordura"))
        p3.metric("% Gordura",      _val(touro, "% Gordura"))
        p4.metric("Proteína (Lbs)", _val(touro, "Proteína"))
        p5.metric("% Proteína",     _val(touro, "Prot%"))

        st.divider()

        st.markdown("##### 📊 Índices Complementares")
        p6, p7, p8, p9 = st.columns(4)
        p6.metric("CGP", _val(touro, "CGP"))
        p7.metric("VP",  _val(touro, "VP"))
        p8.metric("CUB", _val(touro, "CUB"))
        p9.metric("EFI", f"{_val(touro, 'EFI')}%")

    # ── Aba Saúde & Eficiência ────────────────────────────────
    with tab_saude:
        st.markdown("##### ❤️ Saúde & Eficiência Reprodutiva")
        s1, s2, s3 = st.columns(3)
        s1.metric("REI", _val(touro, "REI"))
        s2.metric("IF",  _val(touro, "IF"))
        s3.metric("VP",  _val(touro, "VP"))

    # ── Aba Conformação ───────────────────────────────────────
    with tab_conf:
        st.markdown("##### 📐 Índices Gerais")
        t1, t2, t3 = st.columns(3)
        t1.metric("PTAT", _val(touro, "PTAT"))
        t2.metric("MUI",  _val(touro, "MUI"))
        t3.metric("CUB",  _val(touro, "CUB"))

        st.divider()

        st.markdown("##### 🦵 Pernas & Pés")
        u1, u2, u3 = st.columns(3)
        u1.metric("Pernas Lateral", _val(touro, "RLSV"))
        u2.metric("Pernas Post.",   _val(touro, "RLRV"))
        u3.metric("Ângulo Pé",      _val(touro, "Ângulo Pé"))

        st.divider()

        st.markdown("##### 🐄 Úbere")
        v1, v2, v3, v4, v5 = st.columns(5)
        v1.metric("Lig. Úb. Ant.",   _val(touro, "Lig. Úbere Ant."))
        v2.metric("Alt. Úb. Post.",  _val(touro, "R Udder Height"))
        v3.metric("Larg. Úb. Post.", _val(touro, "Larg. Úbere Post."))
        v4.metric("Lig. Susp.",      _val(touro, "Ligamento Susp."))
        v5.metric("Prof. Úbere",     _val(touro, "Prof Úbere"))

        st.divider()

        st.markdown("##### 🔬 Tetos")
        w1, w2, w3 = st.columns(3)
        w1.metric("Pos. Teto Ant.",  _val(touro, "FTP"))
        w2.metric("Pos. Teto Post.", _val(touro, "RTP"))
        w3.metric("Comp. Tetos",     _val(touro, "Comp. Tetos"))

    st.divider()

    # ── Botão galeria de filhas ───────────────────────────────
    if st.button(
        "🐄 Ver Galeria de Filhas",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.pagina = "progenies"
        st.rerun()


# ══════════════════════════════════════════════════════════════
# GALERIA DE FILHAS (PROGENIES)
# Colunas da aba progenies:
#   id_progenie | id_touro_pai | nome | data_nascimento |
#   proprietario | leite_lts | Classificação | fotos_ids
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
        st.markdown(f"# 🐄 Filhas de {touro.get('Nome', '')}")

    st.caption(
        f"Pai: {touro.get('Nome completo', '')}  ·  "
        f"Registro: {touro.get('InterRegNumber', '')}  ·  "
        f"Raça: {get_breed_name(str(touro.get('Raça', '')))}"
    )
    st.divider()

    with st.spinner("Carregando filhas..."):
        try:
            df_prog = load_progenies(
                str(touro.get("Código NAAB", ""))
            )
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

                # ── Fotos ─────────────────────────────────────
                fotos_raw = str(prog.get("fotos_ids", "")).strip()
                fotos_ids = [
                    f.strip() for f in fotos_raw.split(",")
                    if f.strip() and f.strip() not in ("", "nan", "None")
                ]

                if fotos_ids:
                    img = get_image_from_drive(fotos_ids[0])
                    st.image(
                        img if img else _placeholder(),
                        use_container_width=True
                    )
                    if len(fotos_ids) > 1:
                        st.caption(f"📷 +{len(fotos_ids)-1} foto(s)")
                else:
                    st.image(_placeholder(), use_container_width=True)

                # ── Dados básicos ─────────────────────────────
                st.markdown(
                    f"**{_val(prog, 'nome')}**"
                )
                st.caption(
                    f"📅 {_val(prog, 'data_nascimento')}  ·  "
                    f"🏠 {_val(prog, 'proprietario')}"
                )

                # Produção
                leite = _val(prog, "leite_lts")
                if leite != "—":
                    st.markdown(f"🥛 **{leite} L/Lact.**")

                # Classificação
                clf = _val(prog, "Classificação")
                if clf != "—":
                    st.markdown(f"📋 **Classificação:** {clf}")

                # ── Download foto ─────────────────────────────
                if fotos_ids:
                    img_dl = get_image_from_drive(fotos_ids[0])
                    if img_dl:
                        buf = BytesIO()
                        img_dl.save(buf, format="JPEG", quality=90)
                        st.download_button(
                            label="⬇️ Baixar Foto",
                            data=buf.getvalue(),
                            file_name=(
                                f"{_val(prog, 'nome')}.jpg"
                            ),
                            mime="image/jpeg",
                            key=(
                                f"dl_{_val(prog, 'id_progenie')}_{idx}"
                            ),
                            use_container_width=True,
                        )


# ══════════════════════════════════════════════════════════════
# PAINEL ADMIN
# ══════════════════════════════════════════════════════════════
def render_admin():
    st.markdown("## ⚙️ Painel Administrativo")
    st.divider()

    nome_admin = st.session_state.get("admin_user", "Admin")
    st.info(
        f"👋 Bem-vindo, **{nome_admin}**! "
        "Para adicionar ou editar touros e filhas, "
        "acesse diretamente a planilha e as pastas do Drive abaixo."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Planilha Google Sheets")
        sheet_id = st.secrets.get("sheets", {}).get("sheet_id", "")
        if sheet_id:
            url_sheet = (
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            )
            st.link_button(
                "📝 Abrir Planilha",
                url_sheet,
                use_container_width=True
            )
        else:
            st.warning("⚠️ sheet_id não configurado nos secrets.")

    with col2:
        st.markdown("### 📁 Pastas Google Drive")
        try:
            pasta_touros = st.secrets["drive"].get("pasta_touros", "")
            pasta_pdfs   = st.secrets["drive"].get("pasta_pdfs", "")

            if pasta_touros:
                st.link_button(
                    "🐂 Pasta de Fotos (Touros)",
                    f"https://drive.google.com/drive/folders/{pasta_touros}",
                    use_container_width=True
                )
            if pasta_pdfs:
                st.link_button(
                    "📄 Pasta de PDFs",
                    f"https://drive.google.com/drive/folders/{pasta_pdfs}",
                    use_container_width=True
                )
        except Exception:
            st.warning("⚠️ Pastas do Drive não configuradas nos secrets.")

    st.divider()

    st.markdown("### 🔄 Cache")
    st.caption(
        "Após adicionar dados na planilha, limpe o cache "
        "para ver as atualizações imediatamente."
    )
    if st.button("🧹 Limpar Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Cache limpo! Recarregue a página.")

    st.divider()
    st.markdown("### 📋 Estrutura das Abas")

    with st.expander("📄 Colunas da aba **touros**"):
        st.code(
            "Código NAAB | InterRegNumber | Nome | Nome completo | Raça | "
            "foto_id | prova_id | TPI | NM$ | CM$ | FM$ | GM$ | Leite | "
            "Proteína | Prot% | Gordura | % Gordura | CGP | VP | REI | IF | "
            "PTAT | MUI | CUB | Kapa-Caseína | Beta-Caseína | EFI | "
            "Birth Date | Prova",
            language="text"
        )

    with st.expander("📄 Colunas da aba **progenies**"):
        st.code(
            "id_progenie | id_touro_pai | nome | data_nascimento | "
            "proprietario | leite_lts | Classificação | fotos_ids",
            language="text"
        )


# ══════════════════════════════════════════════════════════════
# ROTEADOR DE PÁGINAS
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
        render_admin()
    else:
        st.session_state.pagina = "galeria"
        st.rerun()

else:
    st.session_state.pagina = "galeria"
    st.rerun()
