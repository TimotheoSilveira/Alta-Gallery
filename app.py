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

    /* Card compacto de progenie */
    .prog-nome {
        font-size: 0.85rem;
        font-weight: 700;
        margin: 4px 0 2px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .prog-info {
        font-size: 0.72rem;
        color: #666;
        margin: 0;
    }
    .prog-badge {
        font-size: 0.70rem;
        color: #444;
        margin: 2px 0;
    }

    /* Miniatura de vídeo YouTube */
    .yt-thumb-wrap {
        position: relative;
        display: inline-block;
        width: 100%;
        cursor: pointer;
    }
    .yt-thumb-wrap img {
        width: 100%;
        border-radius: 6px;
    }
    .yt-play-btn {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(255,0,0,0.85);
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: none;
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
    return BREED_CONFIG.get(
        str(raca).strip().upper(), {}
    ).get("cor", "#37474F")

def get_breed_name(raca: str) -> str:
    return BREED_CONFIG.get(
        str(raca).strip().upper(), {}
    ).get("nome", raca)

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
    _racas = [
        "Todas",
        "HO - Holandês",
        "JE - Jersey",
        "GI - Girolando",
        "GIR - Gir Leiteiro",
    ]
    st.session_state.filtro_raca = st.selectbox(
        "Filtrar por raça",
        options=_racas,
        index=_racas.index(st.session_state.filtro_raca),
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

def _parse_ids(raw) -> list:
    """
    Converte string de IDs/URLs separados por vírgula em lista limpa.
    Ex: "id1, id2" → ["id1", "id2"]
    """
    return [
        i.strip() for i in str(raw).split(",")
        if i.strip() and i.strip() not in ("nan", "None", "")
    ]

def _yt_video_id(url: str) -> str:
    """
    Extrai o ID do vídeo de uma URL do YouTube.
    Suporta:
      https://www.youtube.com/watch?v=XXXXXXXXXXX
      https://youtu.be/XXXXXXXXXXX
    """
    url = url.strip()
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    if "watch?v=" in url:
        return url.split("watch?v=")[-1.split("&")[0]
    return url  # já pode ser só o ID

def _yt_thumbnail(video_id: str) -> str:
    """URL da miniatura HD do YouTube."""
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

def _yt_embed(video_id: str) -> str:
    """URL de embed do YouTube."""
    return f"https://www.youtube.com/embed/{video_id}"

def _yt_watch(video_id: str) -> str:
    """URL de watch do YouTube."""
    return f"https://www.youtube.com/watch?v={video_id}"

# ══════════════════════════════════════════════════════════════
# GALERIA PRINCIPAL
# ══════════════════════════════════════════════════════════════
def render_galeria():
    st.markdown("# 🐂 Alta Gallery")
    st.caption(
        "Selecione um touro para ver a prova completa "
        "e a galeria de filhas."
    )
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
        df = df[
            df["Raça"].astype(str).str.strip() == codigo_raca
        ]

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
                    f"<span class='breed-badge' "
                    f"style='background:{cor}'>"
                    f"&nbsp;{raca_code}&nbsp;</span>",
                    unsafe_allow_html=True
                )

                # Nome
                st.markdown(f"### {touro.get('Nome', 'Sem nome')}")
                st.caption(str(touro.get("Nome completo", "")))

                # TPI em destaque
                st.markdown(
                    f"<div class='index-highlight' style='color:{cor}'>"
                    f"TPI: {_val(touro, 'TPI')}</div>",
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

    # ── Hero: foto + índices ──────────────────────────────────
    col_foto, col_info = st.columns([1, 2], gap="large")

    with col_foto:
        foto_id = str(touro.get("foto_id", "")).strip()
        img = get_image_from_drive(foto_id) \
              if foto_id not in ("", "nan", "None") else None
        st.image(img if img else _placeholder(),
                 use_container_width=True)

        # Download PDF
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
            st.markdown(
                f"**📅 Nascimento:** {_val(touro, 'Birth Date')}"
            )
            st.markdown(
                f"**🧬 Kapa-Caseína:** {_val(touro, 'Kapa-Caseína')}"
            )
            st.markdown(
                f"**🧬 Beta-Caseína:** {_val(touro, 'Beta-Caseína')}"
            )
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

    with tab_saude:
        st.markdown("##### ❤️ Saúde & Eficiência Reprodutiva")
        s1, s2, s3 = st.columns(3)
        s1.metric("REI", _val(touro, "REI"))
        s2.metric("IF",  _val(touro, "IF"))
        s3.metric("VP",  _val(touro, "VP"))

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

    if st.button(
        "🐄 Ver Galeria de Filhas",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.pagina = "progenies"
        st.rerun()


# ══════════════════════════════════════════════════════════════
# GALERIA DE FILHAS — COMPACTA
# Planilha progenies:
#   id_progenie | id_touro_pai | nome | data_nascimento |
#   proprietario | leite_lts | Classificação |
#   fotos_ids | youtube_urls
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

    # ── Grid 4 colunas — cards compactos ─────────────────────
    COLUNAS = 4
    cols = st.columns(COLUNAS, gap="small")

    for idx, (_, prog) in enumerate(df_prog.iterrows()):
        fotos_ids   = _parse_ids(prog.get("fotos_ids", ""))
        yt_urls     = _parse_ids(prog.get("youtube_urls", ""))
        yt_ids      = [_yt_video_id(u) for u in yt_urls if u]

        with cols[idx % COLUNAS]:
            with st.container(border=True):

                # ── Mídia: fotos pequenas + thumb YouTube ─────
                # Monta lista de mídias: primeiro fotos, depois YT
                total_midias = len(fotos_ids) + len(yt_ids)

                if total_midias > 0:
                    # Exibe até 2 itens por card para não ficar gigante
                    # Se tiver mais, mostra contador
                    midias_exibir = []

                    for fid in fotos_ids:
                        midias_exibir.append(("foto", fid))
                    for yid in yt_ids:
                        midias_exibir.append(("youtube", yid))

                    # Primeira mídia ocupa largura total do card
                    tipo, mid = midias_exibir[0]

                    if tipo == "foto":
                        img = get_image_from_drive(mid)
                        st.image(
                            img if img else _placeholder(),
                            use_container_width=True
                        )
                    else:
                        # Miniatura YouTube clicável
                        thumb_url = _yt_thumbnail(mid)
                        watch_url = _yt_watch(mid)
                        st.markdown(
                            f"""
                            <a href="{watch_url}" target="_blank"
                               title="▶ Assistir no YouTube">
                              <div class="yt-thumb-wrap">
                                <img src="{thumb_url}"
                                     style="width:100%;border-radius:6px"/>
                                <div class="yt-play-btn">
                                  <span style="color:white;font-size:14px;
                                               margin-left:3px;">▶</span>
                                </div>
                              </div>
                            </a>
                            """,
                            unsafe_allow_html=True
                        )

                    # Se tiver mais de 1 mídia, exibe miniaturas extras
                    # em linha pequena
                    if len(midias_exibir) > 1:
                        extras = midias_exibir[1:]
                        n_ext  = min(len(extras), 3)
                        ext_cols = st.columns(n_ext)

                        for i, (etipo, emid) in enumerate(
                            extras[:n_ext]
                        ):
                            with ext_cols[i]:
                                if etipo == "foto":
                                    img2 = get_image_from_drive(emid)
                                    if img2:
                                        st.image(
                                            img2,
                                            use_container_width=True
                                        )
                                else:
                                    thumb2   = _yt_thumbnail(emid)
                                    watch2   = _yt_watch(emid)
                                    st.markdown(
                                        f"""
                                        <a href="{watch2}"
                                           target="_blank">
                                          <img src="{thumb2}"
                                               style="width:100%;
                                               border-radius:4px"/>
                                        </a>
                                        """,
                                        unsafe_allow_html=True
                                    )

                        # Contador de mídias extras além das exibidas
                        total_extras = total_midias - 1 - n_ext
                        if total_extras > 0:
                            st.caption(
                                f"📷 +{total_extras} mídia(s)"
                            )

                else:
                    # Sem mídia
                    st.image(_placeholder(), use_container_width=True)

                # ── Dados da progenie ─────────────────────────
                st.markdown(
                    f"<p class='prog-nome'>"
                    f"{_val(prog, 'nome')}</p>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p class='prog-info'>"
                    f"📅 {_val(prog, 'data_nascimento')}  "
                    f"🏠 {_val(prog, 'proprietario')}</p>",
                    unsafe_allow_html=True
                )

                leite = _val(prog, "leite_lts")
                clf   = _val(prog, "Classificação")

                if leite != "—":
                    st.markdown(
                        f"<p class='prog-badge'>"
                        f"🥛 {leite} L/Lact.</p>",
                        unsafe_allow_html=True
                    )
                if clf != "—":
                    st.markdown(
                        f"<p class='prog-badge'>"
                        f"📋 Class.: {clf}</p>",
                        unsafe_allow_html=True
                    )

                # Botão assistir vídeo completo (se tiver YT)
                if yt_ids:
                    st.link_button(
                        "▶ Ver vídeo",
                        _yt_watch(yt_ids[0]),
                        use_container_width=True,
                    )


# ══════════════════════════════════════════════════════════════
# PAINEL ADMIN
# ══════════════════════════════════════════════════════════════
def render_admin():
    st.markdown("## ⚙️ Painel Administrativo")
    st.divider()

    st.info(
        f"👋 Bem-vindo, "
        f"**{st.session_state.get('admin_user', 'Admin')}**!  \n"
        "Para adicionar ou editar dados, acesse a planilha "
        "e as pastas do Drive abaixo."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Planilha Google Sheets")
        sheet_id = st.secrets.get("sheets", {}).get("sheet_id", "")
        if sheet_id:
            st.link_button(
                "📝 Abrir Planilha",
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
                use_container_width=True,
            )
        else:
            st.warning("⚠️ sheet_id não configurado.")

    with col2:
        st.markdown("### 📁 Pastas Google Drive")
        try:
            drive = st.secrets.get("drive", {})
            if drive.get("pasta_touros"):
                st.link_button(
                    "🐂 Fotos de Touros",
                    f"https://drive.google.com/drive/folders/"
                    f"{drive['pasta_touros']}",
                    use_container_width=True,
                )
            if drive.get("pasta_progenies"):
                st.link_button(
                    "🐄 Fotos de Filhas",
                    f"https://drive.google.com/drive/folders/"
                    f"{drive['pasta_progenies']}",
                    use_container_width=True,
                )
            if drive.get("pasta_pdfs"):
                st.link_button(
                    "📄 PDFs das Provas",
                    f"https://drive.google.com/drive/folders/"
                    f"{drive['pasta_pdfs']}",
                    use_container_width=True,
                )
        except Exception:
            st.warning("⚠️ Pastas do Drive não configuradas.")

    st.divider()

    st.markdown("### 🔄 Cache")
    st.caption(
        "Após editar a planilha, limpe o cache para "
        "ver as mudanças imediatamente."
    )
    if st.button("🗑️ Limpar Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Cache limpo! Recarregue a galeria.")

    st.divider()

    st.markdown("### 📋 Estrutura das Abas")

    with st.expander("📄 Colunas da aba **touros**"):
        st.code(
            "Código NAAB | InterRegNumber | Nome | Nome completo | "
            "Raça | foto_id | prova_id | TPI | NM$ | CM$ | FM$ | GM$ | "
            "Leite | Proteína | Prot% | Gordura | % Gordura | CGP | "
            "VP | REI | IF | PTAT | MUI | CUB | Kapa-Caseína | "
            "Beta-Caseína | EFI | Birth Date | Prova",
            language="text"
        )

    with st.expander("📄 Colunas da aba **progenies**"):
        st.code(
            "id_progenie | id_touro_pai | nome | data_nascimento | "
            "proprietario | leite_lts | Classificação | "
            "fotos_ids | youtube_urls",
            language="text"
        )

    with st.expander("💡 Como preencher youtube_urls"):
        st.markdown("""
        Cole o link do YouTube na coluna `youtube_urls`.
        Para múltiplos vídeos, separe por vírgula:

        ```
        https://youtu.be/ABC123, https://youtu.be/XYZ456
        ```

        **Dica:** Use vídeos **não listados** no YouTube para
        que apenas quem tiver o link possa assistir.
        """)


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
        render_admin()
    else:
        st.session_state.pagina = "galeria"
        st.rerun()

else:
    st.session_state.pagina = "galeria"
    st.rerun()
