import streamlit as st
import json
from datetime import datetime
from pathlib import Path

# ===== CONFIGURAÇÃO =====
st.set_page_config(page_title="Alta Gallery", page_icon="🐄", layout="wide")

BULLS_FILE = "bulls_data.json"
USERS_FILE = "users_data.json"

# ===== CARREGAR DADOS =====
def load_bulls():
    if Path(BULLS_FILE).exists():
        with open(BULLS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_bulls():
    with open(BULLS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.bulls, f, ensure_ascii=False, indent=2)

def load_users():
    if Path(USERS_FILE).exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [{"id": 1, "name": "Admin", "email": "timotheo@altagenetics.com", "password": "admin123", "role": "admin"}]

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.users, f, ensure_ascii=False, indent=2)

# ===== SESSION STATE =====
if "bulls" not in st.session_state:
    st.session_state.bulls = load_bulls()

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.user_role = "viewer"

# ===== SIDEBAR =====
with st.sidebar:
    st.title("🔐 Login")

    if not st.session_state.logged_in:
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            user = next((u for u in st.session_state.users if u["email"] == email), None)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_name = user["name"]
                st.session_state.user_role = user["role"]
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos")
    else:
        st.write(f"**Bem-vindo, {st.session_state.user_name}!**")
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()

# ===== PÁGINA PRINCIPAL =====
st.title("🐄 Alta Gallery")
st.write("Galeria de touros Alta Genetics")

if st.session_state.logged_in and st.session_state.user_role == "admin":
    tab1, tab2 = st.tabs(["Galeria", "Adicionar Touro"])
else:
    tab1 = st.tabs(["Galeria"])[0]

# ===== TAB 1: GALERIA =====
with tab1:
    st.subheader("Touros Cadastrados")

    if len(st.session_state.bulls) == 0:
        st.info("Nenhum touro cadastrado")
    else:
        for bull in st.session_state.bulls:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if bull.get("image"):
                        st.image(bull["image"], width=200)
                    else:
                        st.write("Sem foto")

                with col2:
                    st.write(f"### {bull['name']}")
                    st.write(f"**Código:** {bull['code']}")
                    st.write(f"**Raça:** {bull['breed']}")
                    st.write(f"**Descrição:** {bull['description']}")

# ===== TAB 2: ADICIONAR TOURO =====
if st.session_state.logged_in and st.session_state.user_role == "admin":
    with tab2:
        st.subheader("Adicionar Novo Touro")

        with st.form("form_touro"):
            name = st.text_input("Nome do touro")
            code = st.text_input("Código")
            breed = st.text_input("Raça")
            description = st.text_area("Descrição")
            image_url = st.text_input("URL da foto (GitHub)")

            if st.form_submit_button("Salvar"):
                if name and code:
                    new_bull = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "name": name,
                        "code": code,
                        "breed": breed,
                        "description": description,
                        "image": image_url
                    }
                    st.session_state.bulls.append(new_bull)
                    save_bulls()
                    st.success("Touro adicionado!")
                    st.rerun()
                else:
                    st.error("Preencha nome e código")

        st.divider()
        st.subheader("Como adicionar fotos")
        st.write("""
        1. Acesse: https://github.com/TimotheoSilveira/Alta-Gallery
        2. Clique em "fotos"
        3. Clique em "Add file" → "Upload files"
        4. Selecione a foto
        5. Clique em "Commit changes"
        6. Copie a URL: https://raw.githubusercontent.com/TimotheoSilveira/Alta-Gallery/main/fotos/NOME_DA_FOTO.jpg
        7. Cole a URL no campo acima
        """)
