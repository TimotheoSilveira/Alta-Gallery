# auth.py — versão simplificada compatível com secrets.toml sem Service Account
import streamlit as st
import bcrypt
from typing import Tuple

def _verify_password(plain: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            hashed.encode("utf-8")
        )
    except Exception:
        return False


def render_admin_login() -> Tuple[bool, Optional[str]]:
    """
    Renderiza login admin na sidebar.
    Retorna (is_admin, username).
    """
    # Inicializa session_state
    if "is_admin"       not in st.session_state:
        st.session_state.is_admin = False
    if "admin_user"     not in st.session_state:
        st.session_state.admin_user = None
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    # Já autenticado
    if st.session_state.is_admin:
        return True, st.session_state.admin_user

    # Verifica se admin_credentials existe nos secrets
    if "admin_credentials" not in st.secrets:
        # Sem bloco admin nos secrets = sem login admin
        # O app funciona normalmente em modo público
        return False, None

    with st.sidebar:
        st.divider()
        st.subheader("🔐 Área Administrativa")

        MAX = 5
        if st.session_state.login_attempts >= MAX:
            st.error("🔒 Muitas tentativas. Recarregue a página.")
            return False, None

        with st.form("form_login", clear_on_submit=True):
            username = st.text_input("Usuário", placeholder="admin1")
            password = st.text_input("Senha", type="password")
            entrar   = st.form_submit_button("🔑 Entrar", use_container_width=True)

        if entrar:
            if not username or not password:
                st.warning("Preencha usuário e senha.")
                return False, None

            try:
                users = st.secrets["admin_credentials"]["usernames"]
            except KeyError:
                st.error("❌ Configuração de admin inválida no secrets.")
                return False, None

            if username in users:
                stored_hash = users[username].get("password", "")

                if _verify_password(password, stored_hash):
                    st.session_state.is_admin   = True
                    st.session_state.admin_user  = username
                    st.session_state.login_attempts = 0
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    restantes = MAX - st.session_state.login_attempts
                    st.error(f"❌ Senha incorreta. {restantes} tentativa(s) restantes.")
            else:
                st.session_state.login_attempts += 1
                st.error("❌ Usuário não encontrado.")

    return False, None


def render_admin_logout():
    """Botão de logout para sidebar."""
    with st.sidebar:
        st.divider()
        user = st.session_state.get("admin_user", "admin")
        st.caption(f"👤 Logado como: **{user}**")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.is_admin   = False
            st.session_state.admin_user = None
            st.session_state.login_attempts = 0
            st.rerun()
