# auth.py
# Login simples com senha em texto puro armazenada nos secrets.
# Os secrets do Streamlit Cloud são criptografados e seguros.
import streamlit as st
from typing import Tuple, Optional


def render_admin_login() -> Tuple[bool, Optional[str]]:
    """
    Renderiza formulário de login na sidebar.
    Compara senha diretamente com o valor nos secrets (sem hash).
    Retorna (is_admin: bool, username: str | None).
    """

    # ── Inicializa session_state ─────────────────────────────────────────────
    for key, default in {
        "is_admin":       False,
        "admin_user":     None,
        "login_attempts": 0,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Já autenticado ───────────────────────────────────────────────────────
    if st.session_state.is_admin:
        return True, st.session_state.admin_user

    # ── Bloco admin não configurado = modo somente leitura público ───────────
    if "admin_credentials" not in st.secrets:
        return False, None

    # ── Formulário de login ──────────────────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.subheader("🔐 Área Administrativa")

        MAX_TENTATIVAS = 5
        if st.session_state.login_attempts >= MAX_TENTATIVAS:
            st.error("🔒 Muitas tentativas. Recarregue a página.")
            return False, None

        with st.form(key="form_login_admin", clear_on_submit=True):
            username = st.text_input(
                label       = "Usuário",
                placeholder = "Administrador",
            )
            password = st.text_input(
                label       = "Senha",
                type        = "password",
                placeholder = "••••••••",
            )
            entrar = st.form_submit_button(
                "🔑 Entrar",
                use_container_width=True,
            )

        # ── Processa o submit ────────────────────────────────────────────────
        if entrar:
            if not username.strip() or not password.strip():
                st.sidebar.warning("⚠️ Preencha usuário e senha.")
                return False, None

            # Carrega usuários dos secrets
            try:
                users = st.secrets["admin_credentials"]["usernames"]
            except KeyError:
                st.sidebar.error("❌ Configuração de admin ausente nos secrets.")
                return False, None

            # Verifica usuário e senha
            if username in users:
                senha_correta = str(users[username].get("password", ""))

                if password == senha_correta:
                    # ✅ Login bem-sucedido
                    st.session_state.is_admin       = True
                    st.session_state.admin_user     = username
                    st.session_state.login_attempts = 0
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    restantes = MAX_TENTATIVAS - st.session_state.login_attempts
                    st.sidebar.error(
                        f"❌ Senha incorreta. "
                        f"{restantes} tentativa(s) restante(s)."
                    )
            else:
                st.session_state.login_attempts += 1
                st.sidebar.error("❌ Usuário não encontrado.")

    return False, None


def render_admin_logout():
    """
    Botão de logout na sidebar para admin autenticado.
    """
    with st.sidebar:
        st.divider()
        nome = st.session_state.get("admin_user", "Admin")
        st.success(f"👤 **{nome}**")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.is_admin       = False
            st.session_state.admin_user     = None
            st.session_state.login_attempts = 0
            st.rerun()
