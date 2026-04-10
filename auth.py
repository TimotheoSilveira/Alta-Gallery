# auth.py
import streamlit as st
import streamlit_authenticator as stauth
from typing import Tuple

def get_authenticator():
    """
    Cria e retorna o objeto autenticador com credenciais do secrets.toml.
    Suporta múltiplos administradores.
    """
    usernames = st.secrets["admin_credentials"]["usernames"]
    names     = st.secrets["admin_credentials"]["names"]
    hashes    = st.secrets["admin_credentials"]["passwords_hash"]

    credentials = {
        "usernames": {
            uname: {"name": name, "password": pwd}
            for uname, name, pwd in zip(usernames, names, hashes)
        }
    }

    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name="galeria_touros_admin",
        key="auth_key_super_secreto",
        cookie_expiry_days=1,  # Sessão expira em 1 dia
    )
    return authenticator


def render_admin_login() -> Tuple[bool, str]:
    """
    Renderiza o formulário de login na sidebar e retorna
    (is_authenticated, username).
    """
    authenticator = get_authenticator()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔐 Área Administrativa")

        name, auth_status, username = authenticator.login(
            location="sidebar",
            fields={
                "Form name": "Login Admin",
                "Username": "Usuário",
                "Password": "Senha",
                "Login": "Entrar",
            }
        )

        if auth_status is False:
            st.error("❌ Usuário ou senha incorretos!")
        elif auth_status is None:
            st.info("ℹ️ Insira suas credenciais para acessar o painel admin.")
        elif auth_status:
            st.success(f"✅ Bem-vindo, {name}!")
            authenticator.logout("Sair", location="sidebar")

    return bool(auth_status), username or ""


def generate_password_hash(password: str) -> str:
    """
    Utilitário para gerar hash de senha (use offline para gerar hashes).
    Execute: python -c "from auth import generate_password_hash; print(generate_password_hash('suasenha'))"
    """
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
