# app.py
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA — DEVE SER O PRIMEIRO COMANDO STREAMLIT
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="auto"
)

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTS — após set_page_config
# ══════════════════════════════════════════════════════════════════════════════
import pandas as pd
from io import BytesIO

# ── Importações locais com tratamento de erro ─────────────────────────────────
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

# ══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
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

    .section-divider {
        border: none;
        border-top: 2px solid #8B4513;
        margin: 1rem 0;
    }

    /* Oculta footer padrão do Streamlit */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO DO SESSION STATE — antes de qualquer render
# ══════════════════════════════════════════════════════════════════════════════
_defaults = {
    "pagina":          "galeria",   # galeria | touro | progenies | admin
    "touro_sel":       None,        # dict com dados do touro selecionado
    "filtro_busca":    "",
    "filtro_raca":     "Todas",
    "is_admin":        False,
    "admin_user":      None,
    "login_attempts":  0,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo / título
    st.markdown("## 🐂 Galeria de Touros")
    st.caption("Raças leiteiras de elite")
    st.divider()

    # Filtros públicos
    st.markdown("### 🔍 Filtros")
    st.session_state.filtro_busca = st.text_input(
        "Buscar por nome ou registro",
        value=st.session_state.filtro_busca,
        placeholder="Ex: AltaGOLDENGATE...",
    )
    st.session_state.filtro_raca = st.selectbox(
        "Filtrar por raça",
        options=["Todas", "HO - Holandês", "JE - Jersey", "GI - Girolando", "GIR - Gir Leiteiro"],
        index=["Todas", "HO - Holandês", "JE - Jersey",
               "GI - Girolando", "GIR - Gir Leiteiro"].index(
            st.session_state.filtro_raca
        )
    )

    # Botão voltar para galeria (sempre visível)
    st.divider()
    if st.button("🏠 Galeria Principal", use_container_width=True):
        st.session_state.pagina   = "galeria"
        st.session_state.touro_sel = None
        st.rerun()

# ── Autenticação (fora do bloco `with st.sidebar` para evitar conflito) ───────
is_admin, admin_user = render_admin_login()

# Atualiza estado do admin no session_state
st.session_state.is_admin  = is_admin
st.session_state.admin_user = admin_user

# Controles extras se admin autenticado
if is_admin:
    render_admin_logout()
    with st.sidebar:
        st.divider()
        st.markdown("### ⚙️ Administração")
        # Botão visível apenas para admin autenticado
        if st.session_state.is_admin:
            if st.button("📤 Painel de Upload", use_container_width=True):
                st.session_state.pagina = "admin"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE RENDERIZAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def _placeholder_img():
    """Imagem padrão quando não há foto cadastrada."""
    return "https://placehold.co/300x280/EEE/999?text=Sem+Foto"


# ─────────────────────────────────────────────────────────────────────────────
def render_galeria():
    """Galeria principal com todos os touros cadastrados."""
    st.markdown("# 🐂 Galeria de Touros Leiteiros")
    st.caption("Selecione um touro para ver a prova completa e a galeria de filhas.")
    st.divider()

    # Carrega dados com spinner
    with st.spinner("Carregando touros..."):
        try:
            df = load_touros()
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
            st.info("Verifique se os secrets do Google estão configurados corretamente.")
            return

    if df.empty:
        st.info("ℹ️ Nenhum touro cadastrado ainda. Acesse o painel admin para adicionar.")
        return

    # ── Aplicar filtros ──────────────────────────────────────────────────────
    busca = st.session_state.filtro_busca.strip().lower()
    raca_sel = st.session_state.filtro_raca

    if busca:
        mask = (
            df.get("nome_curto", pd.Series(dtype=str))
              .astype(str).str.lower().str.contains(busca, na=False) |
            df.get("registro", pd.Series(dtype=str))
              .astype(str).str.lower().str.contains(busca, na=False)
        )
        df = df[mask]

    if raca_sel != "Todas":
        codigo_raca = raca_sel.split(" - ")[0]
        df = df[df["raca"].astype(str) == codigo_raca]

    if df.empty:
        st.warning("Nenhum touro encontrado com os filtros aplicados.")
        return

    st.markdown(f"**{len(df)} touro(s) encontrado(s)**")
    st.divider()

    # ── Grid 3 colunas ───────────────────────────────────────────────────────
    cols = st.columns(3, gap="medium")

    for idx, (_, touro) in enumerate(df.iterrows()):
        raca_code  = str(touro.get("raca", "HO"))
        breed_cfg  = get_breed_config(raca_code)
        cor        = breed_cfg.get("cor_tema", "#37474F")
        idx_princ  = breed_cfg.get("indice_principal", "TPI")

        with cols[idx % 3]:
            with st.container(border=True):

                # Foto
                foto_id = str(touro.get("foto_drive_id", ""))
                if foto_id:
                    img = get_image_from_drive(foto_id)
                    if img:
                        st.image(img, use_container_width=True)
                    else:
                        st.image(_placeholder_img(), use_container_width=True)
                else:
                    st.image(_placeholder_img(), use_container_width=True)

                # Badge de raça
                st.markdown(
                    f"<span class='breed-badge' style='background:{cor}'>"
                    f"&nbsp;{raca_code}&nbsp;</span>",
                    unsafe_allow_html=True
                )

                # Nome
                st.markdown(f"### {touro.get('nome_curto', 'Sem nome')}")
                st.caption(str(touro.get("nome_completo", "")))

                # Índice principal em destaque
                val_idx = touro.get(idx_princ, "—")
                st.markdown(
                    f"<div class='index-highlight' style='color:{cor}'>"
                    f"{idx_princ}: {val_idx}</div>",
                    unsafe_allow_html=True
                )

                # Produção resumida
                c1, c2, c3 = st.columns(3)
                c1.metric("🥛 Leite",  f"{touro.get('leite_lbs', '—')}")
                c2.metric("🧈 Gord.",  f"{touro.get('gordura_lbs', '—')}")
                c3.metric("🔬 Prot.",  f"{touro.get('proteina_lbs', '—')}")

                # Botão de detalhe
                if st.button(
                    "🔍 Ver Prova & Filhas",
                    key=f"btn_touro_{touro.get('id_touro', idx)}",
                    use_container_width=True,
                    type="primary"
                ):
                    st.session_state.touro_sel = touro.to_dict()
                    st.session_state.pagina    = "touro"
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
def render_touro_detail():
    """Página de detalhe completo do touro com abas."""

    touro = st.session_state.get("touro_sel")
    if not touro:
        st.warning("Nenhum touro selecionado.")
        st.session_state.pagina = "galeria"
        st.rerun()
        return

    breed_cfg = get_breed_config(str(touro.get("raca", "HO")))
    cor       = breed_cfg.get("cor_tema", "#37474F")
    idx_princ = breed_cfg.get("indice_principal", "TPI")

    # ── Navegação ────────────────────────────────────────────────────────────
    col_back, col_title = st.columns([1, 7])
    with col_back:
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "galeria"
            st.rerun()
    with col_title:
        st.markdown(
            f"<h1 style='color:{cor}'>"
            f"{breed_cfg.get('icone','🐄')} {touro.get('nome_curto','')}"
            f"</h1>",
            unsafe_allow_html=True
        )

    st.caption(
        f"{touro.get('nome_completo','')}  ·  "
        f"Registro: {touro.get('registro','')}  ·  "
        f"Prova: {touro.get('prova_atual','')}  ·  "
        f"Raça: {breed_cfg.get('nome_completo','')}"
    )
    st.divider()

    # ── Hero: foto + índices ──────────────────────────────────────────────────
    col_foto, col_info = st.columns([1, 2], gap="large")

    with col_foto:
        foto_id = str(touro.get("foto_drive_id", ""))
        img = get_image_from_drive(foto_id) if foto_id else None
        st.image(img if img else _placeholder_img(), use_container_width=True)

        # Download PDF da prova
        pdf_id = str(touro.get("pdf_drive_id", ""))
        if pdf_id:
            with st.spinner("Preparando download..."):
                pdf_bytes = get_pdf_bytes_from_drive(pdf_id)
            if pdf_bytes:
                st.download_button(
                    label="📥 Baixar Prova (PDF)",
                    data=pdf_bytes,
                    file_name=f"{touro.get('id_touro','touro')}_prova.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    with col_info:
        # Índices econômicos
        indices_eco = breed_cfg.get("indices_economicos", [])
        num_cols    = min(len(indices_eco) + 1, 5)
        idx_cols    = st.columns(num_cols)

        idx_cols[0].metric(
            label=idx_princ,
            value=str(touro.get(idx_princ, "—"))
        )
        for i, nome_idx in enumerate(indices_eco[:num_cols - 1]):
            val = touro.get(nome_idx, "—")
            idx_cols[i + 1].metric(
                label=nome_idx,
                value=f"${val}" if val != "—" else "—"
            )

        st.divider()

        # Dados gerais
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**📅 Nascimento:** {touro.get('data_nascimento','—')}")
            st.markdown(f"**🔀 Cruzamento:** {touro.get('cruzamento','—')}")
            st.markdown(f"**🧬 Kappa-Caseína:** {touro.get('kappa_caseina','—')}")
            st.markdown(f"**🧬 Beta-Caseína:** {touro.get('beta_caseina','—')}")
        with col_b:
            st.markdown(f"**📊 EFI:** {touro.get('EFI','—')}%")
            st.markdown(f"**📊 RHA:** {touro.get('RHA','—')}%")
            st.markdown(f"**🏷️ Haplótipos:** {touro.get('haplotipos','—')}")
            st.markdown(f"**💻 Cód. Genéticos:** {touro.get('codigos_geneticos','—')}")

    st.divider()

    # ── Abas de dados ─────────────────────────────────────────────────────────
    tab_prod, tab_saude, tab_parto, tab_conf, tab_ped = st.tabs([
        "🥛 Produção",
        "❤️ Saúde & Eficiência",
        "🤱 Facilidade de Parto",
        "🦵 Conformação",
        "🌳 Pedigree",
    ])

    # ── Produção ──────────────────────────────────────────────────────────────
    with tab_prod:
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "🥛 Leite (Lbs)",
            str(touro.get("leite_lbs", "—")),
            help=f"Confiabilidade: {touro.get('leite_rel','—')}%"
        )
        c2.metric(
            "🧈 Gordura (Lbs)",
            str(touro.get("gordura_lbs", "—")),
            delta=str(touro.get("gordura_pct", "")) + "%"
            if touro.get("gordura_pct") else None
        )
        c3.metric(
            "🔬 Proteína (Lbs)",
            str(touro.get("proteina_lbs", "—")),
            delta=str(touro.get("proteina_pct", "")) + "%"
            if touro.get("proteina_pct") else None
        )
        st.caption(
            f"Baseado em {touro.get('conf_filhas','0 filhas em 0 rebanhos')} — "
            f"100% filhas EUA"
        )

    # ── Saúde & Eficiência ────────────────────────────────────────────────────
    with tab_saude:
        st.markdown("#### Longevidade & Células")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vida Produtiva",   str(touro.get("vida_produtiva", "—")))
        c2.metric("Livab. Vaca",      str(touro.get("livabilidade_vaca", "—")))
        c3.metric("Livab. Novilha",   str(touro.get("livabilidade_novilha", "—")))
        c4.metric("Cél. Somáticas",   str(touro.get("celulas_somaticas", "—")))

        st.markdown("#### Doenças (%)")
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("MAST",  f"{touro.get('MAST','—')}%")
        d2.metric("METR",  f"{touro.get('METR','—')}%")
        d3.metric("DA",    f"{touro.get('DA','—')}%")
        d4.metric("KETO",  f"{touro.get('KETO','—')}%")
        d5.metric("RP",    f"{touro.get('RP','—')}%")

        st.markdown("#### Reprodução & Eficiência")
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        r1.metric("DPR",   str(touro.get("DPR",  "—")))
        r2.metric("CCR",   str(touro.get("CCR",  "—")))
        r3.metric("HCR",   str(touro.get("HCR",  "—")))
        r4.metric("EFC",   str(touro.get("EFC",  "—")))
        r5.metric("DWP$",  f"${touro.get('DWP$','—')}")
        r6.metric("WT$",   f"${touro.get('WT$', '—')}")

        st.markdown("#### Índices de Eficiência")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("REI",             str(touro.get("REI",  "—")))
        e2.metric("FI",              str(touro.get("FI",   "—")))
        e3.metric("MFEV",            str(touro.get("MFEV", "—")))
        e4.metric("Vel. Ordenha",    str(touro.get("velocidade_ordenha", "—")))
        st.metric("FSAV", str(touro.get("FSAV", "—")))

    # ── Parto ─────────────────────────────────────────────────────────────────
    with tab_parto:
        st.markdown("#### Facilidade de Parto & Mortinato")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Ease Parto Touro",
            f"{touro.get('ease_parto_touro_pct','—')}%",
            help=f"Confiabilidade: {touro.get('ease_parto_touro_rel','—')}%"
        )
        c2.metric(
            "Mortinato Touro",
            f"{touro.get('mortinato_touro_pct','—')}%",
            help=f"Confiabilidade: {touro.get('mortinato_touro_rel','—')}%"
        )
        c3.metric(
            "Ease Parto Filha",
            f"{touro.get('ease_parto_filha_pct','—')}%",
            help=f"Confiabilidade: {touro.get('ease_parto_filha_rel','—')}%"
        )
        c4.metric(
            "Mortinato Filha",
            f"{touro.get('mortinato_filha_pct','—')}%",
            help=f"Confiabilidade: {touro.get('mortinato_filha_rel','—')}%"
        )

    # ── Conformação ───────────────────────────────────────────────────────────
    with tab_conf:
        st.markdown("#### Índices Compostos")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("PTAT", str(touro.get("PTAT", "—")))
        c2.metric("UDC",  str(touro.get("UDC",  "—")))
        c3.metric("FLC",  str(touro.get("FLC",  "—")))
        c4.metric("MUI",  str(touro.get("MUI",  "—")))
        c5.metric("BWC",  str(touro.get("BWC",  "—")))

        st.caption(f"Conformação: {touro.get('conf_filhas','—')}")

        with st.expander("📋 Lineares Detalhados", expanded=False):
            lineares = {
                "Estatura":             touro.get("estatura",      "—"),
                "Força":                touro.get("forca",         "—"),
                "Prof. Corporal":       touro.get("prof_corporal", "—"),
                "Forma Leiteira":       touro.get("forma_leiteira","—"),
                "Ângulo de Garupa":     touro.get("angulo_garupa", "—"),
                "Largura de Garupa":    touro.get("largura_garupa","—"),
                "Pernas (lateral)":     touro.get("pernas_lateral","—"),
                "Pernas (posterior)":   touro.get("pernas_post",   "—"),
                "Ângulo de Casco":      touro.get("angulo_casco",  "—"),
                "Score F&L":            touro.get("score_FL",      "—"),
                "Lig. Úbere Anterior":  touro.get("lig_ub_ant",    "—"),
                "Alt. Úbere Posterior": touro.get("alt_ub_post",   "—"),
                "Larg. Úbere Post.":    touro.get("larg_ub_post",  "—"),
                "Ligamento Central":    touro.get("lig_central",   "—"),
                "Prof. Úbere":          touro.get("prof_ubere",    "—"),
                "Posição Tetos Ant.":   touro.get("posic_tetos_ant","—"),
                "Posição Tetos Post.":  touro.get("posic_tetos_post","—"),
                "Comprimento de Teto":  touro.get("comp_teto",     "—"),
            }
            df_lin = pd.DataFrame(
                lineares.items(),
                columns=["Característica", "Valor"]
            )
            st.dataframe(df_lin, use_container_width=True, hide_index=True)

    # ── Pedigree ──────────────────────────────────────────────────────────────
    with tab_ped:
        st.markdown("#### Árvore Genealógica")
        ped = {
            "🐂 Pai":              touro.get("pai",         "—"),
            "🐄 Mãe":              touro.get("mae",         "—"),
            "🐂 Avô Materno":      touro.get("avo_mat",     "—"),
            "🐄 Avó Materna":      touro.get("avo_mae",     "—"),
            "🐂 Bisavô Materno":   touro.get("bisavo_mat",  "—"),
            "🐄 Bisavó Materna":   touro.get("bisavo_mae",  "—"),
        }
        for label, value in ped.items():
            col_l, col_v = st.columns([1, 3])
            col_l.markdown(f"**{label}**")
            col_v.markdown(str(value))

    st.divider()

    # Botão para galeria de filhas
    if st.button(
        "🐄 Ver Galeria de Filhas",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.pagina = "progenies"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
def render_progenies():
    """Galeria de filhas de um touro específico."""

    touro = st.session_state.get("touro_sel")
    if not touro:
        st.session_state.pagina = "galeria"
        st.rerun()
        return

    # Navegação
    col_back, col_title = st.columns([1, 7])
    with col_back:
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "touro"
            st.rerun()
    with col_title:
        st.markdown(f"# 🐄 Filhas de {touro.get('nome_curto','')}")

    st.caption(
        f"Pai: {touro.get('nome_completo','')}  ·  "
        f"Registro: {touro.get('registro','')}  ·  "
        f"Raça: {touro.get('raca','')}"
    )
    st.divider()

    # Carrega filhas
    with st.spinner("Carregando filhas..."):
        try:
            df_prog = load_progenies(str(touro.get("id_touro", "")))
        except Exception as e:
            st.error(f"❌ Erro ao carregar filhas: {e}")
            return

    if df_prog.empty:
        st.info("ℹ️ Nenhuma filha cadastrada para este touro ainda.")
        return

    st.markdown(f"**{len(df_prog)} filha(s) cadastrada(s)**")
    st.divider()

    # Grid 4 colunas
    cols = st.columns(4, gap="small")

    for idx, (_, prog) in enumerate(df_prog.iterrows()):
        with cols[idx % 4]:
            with st.container(border=True):

                # Fotos: pode ter múltiplos IDs separados por vírgula
                fotos_raw = str(prog.get("fotos_drive_ids", ""))
                fotos_ids = [f.strip() for f in fotos_raw.split(",") if f.strip()]

                if fotos_ids:
                    img = get_image_from_drive(fotos_ids[0])
                    st.image(img if img else _placeholder_img(),
                             use_container_width=True)
                    if len(fotos_ids) > 1:
                        st.caption(f"📷 +{len(fotos_ids)-1} foto(s)")
                else:
                    st.image(_placeholder_img(), use_container_width=True)

                st.markdown(f"**{prog.get('nome','Sem nome')}**")
                st.caption(
                    f"📅 {prog.get('data_nascimento','—')}  ·  "
                    f"🏠 {prog.get('proprietario','—')}"
                )

                # Produção
                leite = prog.get("leite_lts", "")
                if leite:
                    st.markdown(f"🥛 **{leite} L/Lact.**")

                # Conformação resumida
                ptat_p = prog.get("PTAT", "")
                udc_p  = prog.get("UDC", "")
                if ptat_p or udc_p:
                    st.caption(f"PTAT: {ptat_p}  |  UDC: {udc_p}")

                # Observações
                obs = str(prog.get("observacoes", "")).strip()
                if obs:
                    with st.expander("📝 Obs."):
                        st.write(obs)

                # Download de foto (primeira disponível)
                if fotos_ids:
                    img_dl = get_image_from_drive(fotos_ids[0])
                    if img_dl:
                        buf = BytesIO()
                        img_dl.save(buf, format="JPEG", quality=90)
                        st.download_button(
                            label="⬇️ Baixar Foto",
                            data=buf.getvalue(),
                            file_name=f"{prog.get('nome','filha').replace(' ','_')}.jpg",
                            mime="image/jpeg",
                            key=f"dl_prog_{prog.get('id_progenie', idx)}",
                            use_container_width=True,
                        )


# ══════════════════════════════════════════════════════════════════════════════
# ROTEADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
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
        try:
            from pages.admin_upload import render_admin_panel
            render_admin_panel()
        except Exception as e:
            st.error(f"❌ Erro ao carregar painel admin: {e}")
    else:
        st.warning("🔐 Acesso restrito. Faça login como administrador.")
        st.session_state.pagina = "galeria"
        st.rerun()

else:
    # Fallback seguro para qualquer rota inválida
    st.session_state.pagina = "galeria"
    st.rerun()
