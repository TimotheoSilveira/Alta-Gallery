import streamlit as st
import json
from datetime import datetime
from pathlib import Path

# ===== CONFIGURAÇÃO =====
st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐄",
    layout="wide"
)

BULLS_FILE = "bulls_data.json"
USERS_FILE = "users_data.json"

# ===== DADOS INICIAIS =====
initial_bulls = [
    {
        "id": 1,
        "name": "Super Bull 001",
        "code": "SB001",
        "breed": "Holandês",
        "category": "Leite",
        "description": "Excelente produção de leite",
        "bullImage": "",
        "daughters": []
    }
]

# ===== FUNÇÕES =====
def load_bulls():
    try:
        if Path(BULLS_FILE).exists():
            with open(BULLS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return initial_bulls

def save_bulls():
    with open(BULLS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.bulls, f, ensure_ascii=False, indent=2)

def load_users():
    try:
        if Path(USERS_FILE).exists():
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return [
        {
            "id": 1000,
            "name": "Timotheo Admin",
            "email": "timotheo@altagenetics.com",
            "password": "admin123",
            "role": "admin"
        }
    ]

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.users, f, ensure_ascii=False, indent=2)

# ===== INICIALIZAR SESSION STATE =====
if "bulls" not in st.session_state:
    st.session_state.bulls = load_bulls()

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.user_role = "viewer"

# ===== SIDEBAR - LOGIN =====
with st.sidebar:
    st.markdown("## 🔐 Login")

    if not st.session_state.logged_in:
        email = st.text_input("E-mail", placeholder="timotheo@altagenetics.com")
        password = st.text_input("Senha", type="password")

        if st.button("🔓 Acessar", use_container_width=True):
            user = next((u for u in st.session_state.users if u["email"] == email.lower()), None)

            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_name = user["name"]
                st.session_state.user_role = user["role"]
                st.success("✅ Login realizado!")
                st.rerun()
            else:
                st.error("❌ E-mail ou senha incorretos")
    else:
        st.success(f"✅ {st.session_state.user_name}")
        st.markdown(f"**Papel:** {st.session_state.user_role.upper()}")

        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# ===== PÁGINA PRINCIPAL =====
st.markdown("# 🐄 Alta Gallery")
st.markdown("Galeria de touros Alta Genetics")
st.divider()

# ===== ESTATÍSTICAS =====
col1, col2 = st.columns(2)
with col1:
    st.metric("Touros", len(st.session_state.bulls))
with col2:
    st.metric("Raças", len(set(b["breed"] for b in st.session_state.bulls)))

st.divider()

# ===== ABAS =====
if st.session_state.logged_in and st.session_state.user_role in ["editor", "admin"]:
    tab1, tab2 = st.tabs(["📊 Galeria", "➕ Adicionar Touro"])
else:
    tab1 = st.tabs(["📊 Galeria"])[0]

# ===== TAB 1: GALERIA =====
with tab1:
    st.markdown("## Touros Cadastrados")

    if not st.session_state.bulls:
        st.info("Nenhum touro cadastrado.")
    else:
        for bull in st.session_state.bulls:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if bull.get("bullImage"):
                        st.image(bull["bullImage"], use_container_width=True)
                    else:
                        st.info("Sem foto")

                with col2:
                    st.markdown(f"### {bull['name']}")
                    st.markdown(f"**Código:** {bull['code']} | **Raça:** {bull['breed']}")
                    st.markdown(f"**Categoria:** {bull['category']}")
                    st.markdown(f"*{bull['description']}*")

# ===== TAB 2: ADICIONAR TOURO =====
if st.session_state.logged_in and st.session_state.user_role in ["editor", "admin"]:
    with tab2:
        st.markdown("## Adicionar Novo Touro")

        with st.form("add_bull_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Nome do touro")
                code = st.text_input("Código")
                breed = st.selectbox("Raça", ["Holandês", "Jersey", "Girolando", "Gir Leiteiro"])

            with col2:
                category = st.text_input("Categoria")
                description = st.text_area("Descrição")

            st.markdown("**Foto do Touro**")
            bull_image_url = st.text_input("URL da foto (ex: https://...)")

            if st.form_submit_button("💾 Salvar Touro"):
                if name and code:
                    new_bull = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "name": name,
                        "code": code,
                        "breed": breed,
                        "category": category,
                        "description": description,
                        "bullImage": bull_image_url or "",
                        "daughters": []
                    }
                    st.session_state.bulls.insert(0, new_bull)
                    save_bulls()
                    st.success("✅ Touro adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha nome e código")

        st.divider()
        st.markdown("### 📤 Como adicionar fotos no GitHub")

        with st.expander("📖 Ver instruções"):
            st.markdown("""
            1. Acesse: https://github.com/TimotheoSilveira/Alta-Gallery
            2. Clique na pasta **"fotos"**
            3. Clique em **"Add file"** → **"Upload files"**
            4. Selecione a foto do seu computador
            5. Clique em **"Commit changes"**
            6. Copie a URL da foto: `https://raw.githubusercontent.com/TimotheoSilveira/Alta-Gallery/main/fotos/SB001_bull.jpg`
            7. Cole a URL no campo acima
            """)
