import streamlit as st
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# ===== CONFIGURAÇÃO DA PÁGINA =====
st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== ESTILOS CUSTOMIZADOS =====
st.markdown("""
<style>
    .main { padding: 2rem; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# ===== DADOS INICIAIS =====
BULLS_FILE = "bulls_data.json"
USERS_FILE = "users_data.json"

initial_bulls = [
    {
        "id": 1,
        "name": "Super Bull 001",
        "code": "SB001",
        "breed": "Holandês",
        "category": "Leite",
        "description": "Excelente produção de leite e conformação.",
        "bullImage": "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=900&q=80",
        "daughters": [
            {
                "id": 101,
                "cowName": "Vaca 4021",
                "farm": "Fazenda Boa Vista",
                "location": "Varginha / MG",
                "milk": "42 kg/dia",
                "lactation": "2ª lactação",
                "image": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?auto=format&fit=crop&w=1200&q=80"
            }
        ]
    },
    {
        "id": 2,
        "name": "Alta Prime 245",
        "code": "AP245",
        "breed": "Jersey",
        "category": "Sólidos",
        "description": "Destaque para sólidos, fertilidade e vacas funcionais.",
        "bullImage": "https://images.unsplash.com/photo-1493962853295-0fd70327578a?auto=format&fit=crop&w=900&q=80",
        "daughters": []
    }
]

# ===== FUNÇÕES DE ARMAZENAMENTO =====
def load_bulls():
    try:
        if Path(BULLS_FILE).exists():
            with open(BULLS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Erro ao carregar touros: {e}")
    return initial_bulls

def save_bulls():
    try:
        with open(BULLS_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.bulls, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar touros: {e}")

def load_users():
    try:
        if Path(USERS_FILE).exists():
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Erro ao carregar usuários: {e}")
    return []

def save_users():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {e}")

# ===== INICIALIZAR SESSION STATE =====
if "bulls" not in st.session_state:
    st.session_state.bulls = load_bulls()

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.user_role = "viewer"

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "breed_filter" not in st.session_state:
    st.session_state.breed_filter = "Todas as raças"

# ===== FUNÇÕES AUXILIARES =====
def get_breeds():
    breeds = set(bull["breed"] for bull in st.session_state.bulls)
    return ["Todas as raças"] + sorted(list(breeds))

def get_filtered_bulls():
    filtered = st.session_state.bulls

    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        filtered = [b for b in filtered if query in b["name"].lower() or query in b["code"].lower()]

    if st.session_state.breed_filter != "Todas as raças":
        filtered = [b for b in filtered if b["breed"] == st.session_state.breed_filter]

    return filtered

def can_edit():
    return st.session_state.user_role in ["editor", "admin"]

def can_manage_users():
    return st.session_state.user_role == "admin"

# ===== SIDEBAR - LOGIN ADMIN =====
with st.sidebar:
    st.markdown("## 🔐 Área do Administrador")

    if not st.session_state.logged_in:
        st.markdown("**Login para gerenciar dados**")

        with st.form("admin_login"):
            email = st.text_input("E-mail corporativo", placeholder="seu.nome@altagenetics.com")
            password = st.text_input("Senha", type="password")

            if st.form_submit_button("🔓 Acessar como Admin"):
                email = email.strip().lower()

                if not email.endswith("@altagenetics.com"):
                    st.error("Use um e-mail com final @altagenetics.com")
                elif not password:
                    st.error("Preencha a senha")
                else:
                    user = next((u for u in st.session_state.users if u["email"] == email), None)

                    if user and user["password"] != password:
                        st.error("Senha incorreta")
                    elif user:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.user_name = user["name"]
                        st.session_state.user_role = user["role"]
                        st.success("Login realizado!")
                        st.rerun()
                    else:
                        st.info("Usuário não encontrado. Solicite acesso ao administrador.")
    else:
        st.success(f"✅ Conectado como: **{st.session_state.user_name}**")
        st.markdown(f"**Papel:** {st.session_state.user_role.upper()}")

        if st.button("🚪 Sair"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user_name = ""
            st.session_state.user_role = "viewer"
            st.rerun()

# ===== PÁGINA PRINCIPAL =====
st.markdown("# 🐄 Alta Gallery")
st.markdown("Galeria de touros e progênie Alta Genetics")
st.divider()

# Estatísticas (visível para TODOS)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Touros Cadastrados", len(st.session_state.bulls))

with col2:
    breeds = get_breeds()
    st.metric("Raças", len(breeds) - 1)

with col3:
    total_photos = sum(len(bull["daughters"]) for bull in st.session_state.bulls)
    st.metric("Fotos de Filhas", total_photos)

st.divider()

# Filtros (visível para TODOS)
col1, col2 = st.columns([3, 1])
with col1:
    st.session_state.search_query = st.text_input("🔎 Buscar por nome ou código", st.session_state.search_query)
with col2:
    st.session_state.breed_filter = st.selectbox("Filtrar por raça", get_breeds(), index=0)

# ===== ABAS =====
if st.session_state.logged_in and can_edit():
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Galeria", "➕ Adicionar Touro", "📥 Importar", "📤 Exportar", "⚙️ Gerenciar"])
elif st.session_state.logged_in and can_manage_users():
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Galeria", "📥 Importar", "📤 Exportar", "👥 Usuários", "⚙️ Admin"])
else:
    tab1 = st.tabs(["📊 Galeria"])[0]

with tab1:
    st.markdown("## Touros Cadastrados")

    filtered_bulls = get_filtered_bulls()

    if not filtered_bulls:
        st.info("Nenhum touro encontrado com esse filtro.")
    else:
        for bull in filtered_bulls:
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
                    st.markdown(f"**Fotos de filhas:** {len(bull['daughters'])}")

                    col_open, col_edit, col_delete = st.columns(3)

                    with col_open:
                        if st.button(f"📂 Abrir galeria", key=f"open_{bull['id']}"):
                            st.session_state.selected_bull_id = bull["id"]
                            st.rerun()

                    if st.session_state.logged_in and can_edit():
                        with col_edit:
                            if st.button(f"✏️ Editar", key=f"edit_{bull['id']}"):
                                st.session_state.edit_bull_id = bull["id"]
                                st.rerun()

                        with col_delete:
                            if st.button(f"🗑️ Excluir", key=f"delete_{bull['id']}"):
                                st.session_state.bulls = [b for b in st.session_state.bulls if b["id"] != bull["id"]]
                                save_bulls()
                                st.success("Touro excluído!")
                                st.rerun()

if st.session_state.logged_in and can_edit():
    with tab2:
        st.markdown("## Adicionar Novo Touro")

        with st.form("add_bull_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Nome do touro")
                code = st.text_input("Código")
                breed = st.selectbox("Raça", ["Holandês", "Jersey", "Girolando", "Gir Leiteiro"])

            with col2:
                category = st.text_input("Categoria (ex: Leite, Sólidos)")
                description = st.text_area("Descrição genética")

            bull_image_url = st.text_input("URL da foto do touro")

            if st.form_submit_button("💾 Salvar Touro"):
                if name and code:
                    new_bull = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "name": name,
                        "code": code,
                        "breed": breed,
                        "category": category,
                        "description": description,
                        "bullImage": bull_image_url or "https://via.placeholder.com/300",
                        "daughters": []
                    }
                    st.session_state.bulls.insert(0, new_bull)
                    save_bulls()
                    st.success("Touro adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha nome e código do touro")

    with tab3:
        st.markdown("## Importar Base em JSON")

        uploaded_file = st.file_uploader("Selecione um arquivo JSON", type="json")

        if uploaded_file:
            try:
                imported_data = json.load(uploaded_file)
                if isinstance(imported_data, list):
                    st.session_state.bulls = imported_data
                    save_bulls()
                    st.success("Base importada com sucesso!")
                    st.rerun()
                else:
                    st.error("Arquivo JSON inválido. Deve ser uma lista de touros.")
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

    with tab4:
        st.markdown("## Exportar Base")

        col1, col2 = st.columns(2)

        with col1:
            json_str = json.dumps(st.session_state.bulls, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 Exportar Base Completa (JSON)",
                json_str,
                "alta-gallery-dados.json",
                "application/json"
            )

        with col2:
            bulls_df = pd.DataFrame([
                {
                    "Nome": bull["name"],
                    "Código": bull["code"],
                    "Raça": bull["breed"],
                    "Categoria": bull["category"],
                    "Fotos": len(bull["daughters"])
                }
                for bull in st.session_state.bulls
            ])
            csv = bulls_df.to_csv(index=False)
            st.download_button(
                "📊 Exportar como CSV",
                csv,
                "alta-gallery-dados.csv",
                "text/csv"
            )

    with tab5:
        st.markdown("## Gerenciar Dados")

        if st.button("🔄 Resetar todos os dados"):
            if st.checkbox("Confirmar reset"):
                st.session_state.bulls = initial_bulls
                save_bulls()
                st.success("Dados resetados!")
                st.rerun()

if st.session_state.logged_in and can_manage_users():
    with tab4:
        st.markdown("## Gerenciar Usuários")

        st.markdown("### Usuários Cadastrados")

        for user in st.session_state.users:
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**{user['name']}** ({user['email']})")

            with col2:
                new_role = st.selectbox(
                    "Papel",
                    ["viewer", "editor", "admin"],
                    index=["viewer", "editor", "admin"].index(user["role"]),
                    key=f"role_{user['id']}"
                )
                if new_role != user["role"]:
                    user["role"] = new_role
                    save_users()
                    st.rerun()

            with col3:
                if st.button("🗑️ Remover", key=f"delete_user_{user['id']}"):
                    st.session_state.users = [u for u in st.session_state.users if u["id"] != user["id"]]
                    save_users()
                    st.rerun()

        st.divider()
        st.markdown("### Criar Novo Usuário")

        with st.form("new_user_form"):
            name = st.text_input("Nome completo")
            email = st.text_input("E-mail corporativo", placeholder="seu.nome@altagenetics.com")
            password = st.text_input("Senha", type="password")
            role = st.selectbox("Papel", ["viewer", "editor", "admin"])

            if st.form_submit_button("➕ Criar Usuário"):
                email = email.strip().lower()

                if not name or not email or not password:
                    st.error("Preencha todos os campos")
                elif not email.endswith("@altagenetics.com"):
                    st.error("Use um e-mail com final @altagenetics.com")
                elif any(u["email"] == email for u in st.session_state.users):
                    st.error("Este e-mail já está cadastrado")
                else:
                    st.session_state.users.append({
                        "id": int(datetime.now().timestamp() * 1000),
                        "name": name,
                        "email": email,
                        "password": password,
                        "role": role
                    })
                    save_users()
                    st.success(f"Usuário {name} criado como {role}!")
                    st.rerun()

    with tab5:
        st.markdown("## Painel de Administração")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de Usuários", len(st.session_state.users))

        with col2:
            editors = len([u for u in st.session_state.users if u["role"] == "editor"])
            st.metric("Editores", editors)

        with col3:
            admins = len([u for u in st.session_state.users if u["role"] == "admin"])
            st.metric("Admins", admins)
