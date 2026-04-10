# auth.py
import streamlit as st
import bcrypt

# ── Verificação defensiva dos secrets ────────────────────────────────────────
def _validate_secrets() -> bool:
    """
    Verifica se todos os secrets necessários estão configurados.
    Retorna False com mensagem de erro se algum estiver faltando.
    """
    required_keys = {
        "admin_credentials": ["usernames"],
        "sheets": ["sheet_id"],
        "gcp_service_account": ["type", "project_id", "private_key", "client_email"],
    }

    for section, keys in required_keys.items():
        # Verifica se a seção existe
        if section not in st.secrets:
            st.error(f"❌ Secret ausente: `[{section}]` não encontrado no secrets.toml")
            return False

        # Verifica se as chaves dentro da seção existem
        for key in keys:
            if key not in st.secrets[section]:
                st.error(f"❌ Secret ausente: `[{section}]` → `{key}` não encontrado")
                return False

    return True


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_admin_users() -> dict:
    """
    Retorna dicionário de usuários admin dos secrets.
    Formato esperado no secrets.toml:
        [admin_credentials.usernames.joao]
        name = "João Silva"
        password = "$2b$12$..."
    """
    try:
        return dict(st.secrets["admin_credentials"]["usernames"])
    except KeyError as e:
        st.error(f"❌ Erro ao carregar usuários: {e}")
        return {}


def render_admin_login() -> tuple[bool, str | None]:
    """
    Renderiza o formulário de login na sidebar.

    Returns:
        tuple: (is_admin: bool, username: str | None)
    """
    # Inicializa session_state de forma segura
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "admin_user" not in st.session_state:
        st.session_state.admin_user = None
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    # Se já está autenticado, retorna direto
    if st.session_state.is_admin:
        return True, st.session_state.admin_user

    # Valida secrets antes de tentar qualquer coisa
    if not _validate_secrets():
        st.sidebar.error("⚙️ Secrets não configurados. Contate o administrador.")
        return False, None

    with st.sidebar:
        st.divider()
        st.subheader("🔐 Área Administrativa")

        # Bloqueia após 5 tentativas
        MAX_ATTEMPTS = 5
        if st.session_state.login_attempts >= MAX_ATTEMPTS:
            st.error(f"🔒 Muitas tentativas. Recarregue a página.")
            return False, None

        with st.form(key="login_form", clear_on_submit=True):
            username = st.text_input(
                "Usuário",
                placeholder="seu.usuario",
                autocomplete="username"
            )
            password = st.text_input(
                "Senha",
                type="password",
                placeholder="••••••••",
                autocomplete="current-password"
            )
            submitted = st.form_submit_button(
                "🔑 Entrar",
                use_container_width=True
            )

        if submitted:
            if not username or not password:
                st.warning("⚠️ Preencha usuário e senha.")
                return False, None

            users = get_admin_users()

            if username in users:
                user_data = dict(users[username])
                stored_hash = user_data.get("password", "")

                if _verify_password(password, stored_hash):
                    # Login bem-sucedido
                    st.session_state.is_admin = True
                    st.session_state.admin_user = username
                    st.session_state.login_attempts = 0
                    st.success(f"✅ Bem-vindo, {user_data.get('name', username)}!")
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    remaining = MAX_ATTEMPTS - st.session_state.login_attempts
                    st.error(f"❌ Credenciais inválidas. {remaining} tentativa(s) restantes.")
            else:
                st.session_state.login_attempts += 1
                st.error("❌ Usuário não encontrado.")

    return False, None


def render_admin_logout():
    """Botão de logout para admins autenticados."""
    with st.sidebar:
        st.divider()
        user = st.session_state.get("admin_user", "Admin")
        st.caption(f"👤 Logado como: **{user}**")

        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.is_admin = False
            st.session_state.admin_user = None
            st.session_state.login_attempts = 0
            st.rerun()
