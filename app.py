import streamlit as st
import json
import pandas as pd
from datetime import datetime
from io import BytesIO
import base64
from pathlib import Path
import requests
import os

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS CUSTOMIZADO
# ============================================================================

st.markdown("""
<style>
    :root {
        --blue: #0b57b7;
        --blue-dark: #0a3f8f;
        --blue-light: #2da6ff;
        --bg: #f5f7fb;
        --card: #ffffff;
        --text: #14213a;
        --muted: #65748b;
        --border: #dbe3ee;
        --radius: 20px;
    }

    * {
        box-sizing: border-box;
    }

    body {
        background-color: var(--bg);
        color: var(--text);
        font-family: Inter, Arial, Helvetica, sans-serif;
    }

    .main {
        background-color: var(--bg);
    }

    .stButton > button {
        border-radius: 14px;
        font-weight: 700;
        transition: 0.18s ease;
        border: none;
        padding: 13px 18px;
    }

    .primary-btn {
        background-color: var(--blue);
        color: white;
    }

    .primary-btn:hover {
        background-color: #09489b;
    }

    .secondary-btn {
        background-color: #eef5ff;
        color: var(--blue-dark);
    }

    .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 24px;
        box-shadow: 0 12px 30px rgba(13, 63, 138, 0.08);
    }

    .stat-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 12px 30px rgba(13, 63, 138, 0.08);
        text-align: center;
    }

    .badge {
        background: linear-gradient(135deg, #21a4ff, #0b57b7);
        color: white;
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 14px;
        font-weight: 700;
        display: inline-block;
        white-space: nowrap;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INICIALIZAR SESSION STATE
# ============================================================================

if "loggedIn" not in st.session_state:
    st.session_state.loggedIn = False
    st.session_state.email = ""
    st.session_state.userName = ""
    st.session_state.bulls = []
    st.session_state.users = []
    st.session_state.query = ""
    st.session_state.breedFilter = "Todas as raças"
    st.session_state.selectedBullId = None
    st.session_state.previewPhoto = None
    st.session_state.exportSelection = []
    st.session_state.github_token = ""
    st.session_state.github_repo_owner = ""
    st.session_state.github_repo_name = ""

# ============================================================================
# DADOS INICIAIS
# ============================================================================

INITIAL_BULLS = [
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
            },
            {
                "id": 102,
                "cowName": "Estrela 198",
                "farm": "Fazenda Santa Clara",
                "location": "Carmo do Rio Claro / MG",
                "milk": "38 kg/dia",
                "lactation": "1ª lactação",
                "image": "https://images.unsplash.com/photo-1500595046743-cd271d694d30?auto=format&fit=crop&w=1200&q=80"
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
    },
    {
        "id": 3,
        "name": "Lineage Force 990",
        "code": "LF990",
        "breed": "Girolando",
        "category": "Tropical",
        "description": "Boa adaptação, persistência e excelente tipo leiteiro.",
        "bullImage": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=900&q=80",
        "daughters": []
    }
]

# ============================================================================
# FUNÇÕES DE ARMAZENAMENTO LOCAL
# ============================================================================

def load_data():
    """Carrega dados do arquivo JSON se existir"""
    if Path("alta_gallery_data.json").exists():
        with open("alta_gallery_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return [b.copy() for b in INITIAL_BULLS]

def save_data():
    """Salva dados em arquivo JSON"""
    with open("alta_gallery_data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.bulls, f, indent=2, ensure_ascii=False)

def load_users():
    """Carrega usuários do arquivo JSON"""
    if Path("alta_gallery_users.json").exists():
        with open("alta_gallery_users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_users():
    """Salva usuários em arquivo JSON"""
    with open("alta_gallery_users.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.users, f, indent=2, ensure_ascii=False)

# ============================================================================
# FUNÇÕES DO GITHUB
# ============================================================================

def upload_image_to_github(file_content, filename, github_token, repo_owner, repo_name, folder="images"):
    """
    Faz upload de uma imagem para o GitHub

    Args:
        file_content: bytes da imagem
        filename: nome do arquivo
        github_token: token de autenticação do GitHub
        repo_owner: proprietário do repositório
        repo_name: nome do repositório
        folder: pasta dentro do repositório

    Returns:
        URL raw da imagem ou None se falhar
    """
    try:
        # Codificar a imagem em base64
        encoded_content = base64.b64encode(file_content).decode()

        # Montar a URL da API do GitHub
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{folder}/{filename}"

        # Headers com autenticação
        headers = {
            "Authorization": f"token {github_token}",
            "Content-Type": "application/json"
        }

        # Dados para o upload
        data = {
            "message": f"Upload imagem: {filename}",
            "content": encoded_content,
            "branch": "main"
        }

        # Fazer a requisição
        response = requests.put(url, json=data, headers=headers, timeout=10)

        if response.status_code in [201, 200]:
            # Retorna a URL raw da imagem
            return f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/{folder}/{filename}"
        else:
            st.error(f"Erro ao fazer upload no GitHub: {response.json().get('message', 'Erro desconhecido')}")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar com GitHub: {str(e)}")
        return None

def test_github_connection(github_token, repo_owner, repo_name):
    """Testa a conexão com o repositório do GitHub"""
    try:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        headers = {"Authorization": f"token {github_token}"}
        response = requests.get(url, headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_breeds():
    """Retorna lista de raças disponíveis"""
    breeds = set(bull["breed"] for bull in st.session_state.bulls)
    return ["Todas as raças"] + sorted(list(breeds))

def get_filtered_bulls():
    """Filtra touros por query e raça"""
    filtered = []
    for bull in st.session_state.bulls:
        haystack = f"{bull['name']} {bull['code']} {bull.get('category', '')} {bull['breed']}".lower()
        matches_query = st.session_state.query.lower() in haystack
        matches_breed = (st.session_state.breedFilter == "Todas as raças" or 
                        bull["breed"] == st.session_state.breedFilter)
        if matches_query and matches_breed:
            filtered.append(bull)
    return filtered

def get_selected_bull():
    """Retorna o touro selecionado"""
    for bull in st.session_state.bulls:
        if bull["id"] == st.session_state.selectedBullId:
            return bull
    return None

# ============================================================================
# INICIALIZAR DADOS
# ============================================================================

if not st.session_state.bulls:
    st.session_state.bulls = load_data()
if not st.session_state.users:
    st.session_state.users = load_users()

# ============================================================================
# INTERFACE DE LOGIN
# ============================================================================

if not st.session_state.loggedIn:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🐄 Alta Gallery")
        st.markdown("**Acesso liberado para e-mails com final @altagenetics.com**")

        with st.form("login_form"):
            email = st.text_input("E-mail corporativo", placeholder="seu.nome@altagenetics.com")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Acessar", use_container_width=True)

            if submit:
                email = email.strip().lower()
                if not email.endswith("@altagenetics.com"):
                    st.error("Use um e-mail com final @altagenetics.com")
                elif not password:
                    st.error("Informe uma senha")
                else:
                    registered = next((u for u in st.session_state.users if u["email"] == email), None)
                    if registered and registered["password"] != password:
                        st.error("Senha incorreta para este usuário cadastrado")
                    else:
                        st.session_state.loggedIn = True
                        st.session_state.email = email
                        st.session_state.userName = registered["name"] if registered else email.split("@")[0]
                        st.rerun()

        st.markdown("---")

        if st.button("Criar cadastro", use_container_width=True):
            st.session_state.showRegister = True
            st.rerun()

        # Modal de registro
        if st.session_state.get("showRegister", False):
            st.markdown("### Criar cadastro")
            with st.form("register_form"):
                name = st.text_input("Nome", placeholder="Seu nome")
                reg_email = st.text_input("E-mail corporativo", placeholder="seu.nome@altagenetics.com")
                reg_password = st.text_input("Senha", type="password")
                reg_confirm = st.text_input("Confirmar senha", type="password")
                reg_submit = st.form_submit_button("Salvar cadastro", use_container_width=True)

                if reg_submit:
                    reg_email = reg_email.strip().lower()
                    if not name or not reg_email.endswith("@altagenetics.com") or not reg_password:
                        st.error("Preencha nome, e-mail corporativo e senha")
                    elif reg_password != reg_confirm:
                        st.error("As senhas não conferem")
                    elif any(u["email"] == reg_email for u in st.session_state.users):
                        st.error("Este e-mail já está cadastrado")
                    else:
                        st.session_state.users.append({
                            "id": int(datetime.now().timestamp() * 1000),
                            "name": name,
                            "email": reg_email,
                            "password": reg_password
                        })
                        save_users()
                        st.success("Cadastro salvo com sucesso. Agora você já pode entrar.")
                        st.session_state.showRegister = False
                        st.rerun()

# ============================================================================
# DASHBOARD PRINCIPAL
# ============================================================================

else:
    # Header
    col1, col2, col3 = st.columns([2, 3, 2])

    with col1:
        st.markdown("### 🐄 Alta Gallery")

    with col3:
        display_user = st.session_state.userName or st.session_state.email
        st.markdown(f"**{display_user}**")
        if st.button("Sair"):
            st.session_state.loggedIn = False
            st.session_state.email = ""
            st.session_state.userName = ""
            st.rerun()

    st.markdown("---")

    # Configuração do GitHub (Sidebar)
    with st.sidebar:
        st.markdown("### ⚙️ Configuração GitHub")
        st.info("Configure seu repositório GitHub para armazenar as imagens na nuvem.")

        github_token = st.text_input(
            "Token do GitHub",
            value=st.session_state.github_token,
            type="password",
            placeholder="ghp_xxxxxxxxxxxxx",
            help="Gere em: https://github.com/settings/tokens"
        )

        github_repo_owner = st.text_input(
            "Proprietário do repositório",
            value=st.session_state.github_repo_owner,
            placeholder="seu-usuario"
        )

        github_repo_name = st.text_input(
            "Nome do repositório",
            value=st.session_state.github_repo_name,
            placeholder="alta-gallery-assets"
        )

        if st.button("Testar conexão"):
            if github_token and github_repo_owner and github_repo_name:
                if test_github_connection(github_token, github_repo_owner, github_repo_name):
                    st.success("✅ Conexão com GitHub funcionando!")
                    st.session_state.github_token = github_token
                    st.session_state.github_repo_owner = github_repo_owner
                    st.session_state.github_repo_name = github_repo_name
                else:
                    st.error("❌ Falha na conexão. Verifique as credenciais.")
            else:
                st.error("Preencha todos os campos")

        st.markdown("---")
        st.markdown("**Como configurar:**")
        st.markdown("""
        1. Crie um repositório público no GitHub
        2. Gere um token em Settings → Developer settings
        3. Cole o token acima
        4. Clique em "Testar conexão"
        """)

    # Hero Section
    st.markdown("## Touros Cadastrados")
    st.markdown("Gerencie e visualize a progênie dos touros Alta Genetics.")

    # Stats
    col1, col2, col3 = st.columns(3)
    total_photos = sum(len(bull.get("daughters", [])) for bull in st.session_state.bulls)
    breeds_count = len(get_breeds()) - 1

    with col1:
        st.metric("Touros", len(st.session_state.bulls))
    with col2:
        st.metric("Raças", max(breeds_count, 0))
    with col3:
        st.metric("Fotos", total_photos)

    st.markdown("---")

    # Filtros
    col1, col2 = st.columns([3, 1])

    with col1:
        st.session_state.query = st.text_input(
            "Buscar por nome ou código do touro",
            value=st.session_state.query,
            placeholder="Digite para filtrar..."
        )

    with col2:
        st.session_state.breedFilter = st.selectbox(
            "Raça",
            get_breeds(),
            index=0
        )

    st.markdown("---")

    # Ações
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("➕ Adicionar Touro", use_container_width=True):
            st.session_state.showAddBull = True

    with col2:
        if st.button("📥 Importar", use_container_width=True):
            st.session_state.showImport = True

    with col3:
        if st.button("📤 Exportar", use_container_width=True):
            st.session_state.showExport = True

    with col4:
        if st.button("🔄 Resetar dados", use_container_width=True):
            if st.checkbox("Confirmar reset de dados"):
                st.session_state.bulls = [b.copy() for b in INITIAL_BULLS]
                save_data()
                st.success("Dados resetados com sucesso!")
                st.rerun()

    st.markdown("---")

    # Modal: Adicionar Touro
    if st.session_state.get("showAddBull", False):
        st.markdown("### Adicionar novo touro")
        with st.form("add_bull_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nome do touro")
                code = st.text_input("Código")
            with col2:
                breed = st.selectbox("Raça", ["Holandês", "Jersey", "Girolando", "Gir Leiteiro"])
                category = st.text_input("Categoria", placeholder="Ex.: Leite, Sólidos, Tropical")

            description = st.text_area("Descrição genética", placeholder="Resumo opcional")

            col1, col2 = st.columns(2)
            with col1:
                bull_image_url = st.text_input("URL da foto do touro")
            with col2:
                bull_file = st.file_uploader("Upload da foto do touro", type=["jpg", "jpeg", "png"], key="add_bull_photo")

            if st.form_submit_button("Salvar touro"):
                if not name or not code:
                    st.error("Preencha nome e código")
                else:
                    bull_image = ""

                    # Se houver arquivo e GitHub configurado, fazer upload
                    if bull_file and st.session_state.github_token:
                        with st.spinner("Enviando imagem para GitHub..."):
                            filename = f"bulls/{int(datetime.now().timestamp())}-{bull_file.name}"
                            bull_image = upload_image_to_github(
                                bull_file.read(),
                                filename,
                                st.session_state.github_token,
                                st.session_state.github_repo_owner,
                                st.session_state.github_repo_name
                            )
                    elif bull_file:
                        st.warning("GitHub não configurado. Usando URL local (base64).")
                        bull_image = base64.b64encode(bull_file.read()).decode()
                        bull_image = f"data:image/png;base64,{bull_image}"
                    elif bull_image_url:
                        bull_image = bull_image_url

                    if not bull_file and not bull_image_url:
                        st.warning("Nenhuma foto adicionada. Você pode adicionar depois.")

                    new_bull = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "name": name,
                        "code": code,
                        "breed": breed,
                        "category": category,
                        "description": description,
                        "bullImage": bull_image,
                        "daughters": []
                    }
                    st.session_state.bulls.insert(0, new_bull)
                    save_data()
                    st.session_state.showAddBull = False
                    st.success("Touro adicionado com sucesso!")
                    st.rerun()

        if st.button("Fechar"):
            st.session_state.showAddBull = False
            st.rerun()

        for bull in filtered_bulls:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    if bull.get("bullImage"):
                        st.image(bull["bullImage"], use_column_width=True)
                    else:
                        st.info("Sem foto")

                with col2:
                    st.markdown(f"### {bull['name']}")
                    st.markdown(f"**Código:** {bull['code']}")
                    st.markdown(f"**Raça:** {bull['breed']} | **Categoria:** {bull.get('category', 'N/A')}")
                    st.markdown(f"**Descrição:** {bull.get('description', 'Sem descrição genética cadastrada.')}")
                    st.markdown(f"**Fotos de filhas:** {len(bull.get('daughters', []))}")

                with col3:
                    if st.button("Abrir galeria", key=f"open_{bull['id']}"):
                        st.session_state.selectedBullId = bull["id"]
                        st.rerun()

                    if st.button("Excluir", key=f"delete_{bull['id']}"):
                        if st.checkbox(f"Confirmar exclusão de {bull['name']}", key=f"confirm_delete_{bull['id']}"):
                            st.session_state.bulls = [b for b in st.session_state.bulls if b["id"] != bull["id"]]
                            save_data()
                            st.success("Touro excluído com sucesso!")
                            st.rerun()

                st.divider()

    # Modal: Galeria do Touro (Admin)
    selected_bull = get_selected_bull()
    if selected_bull:
        st.markdown(f"## Galeria - {selected_bull['name']} ({selected_bull['code']})")

        col1, col2 = st.columns([1, 3])
        with col1:
            if selected_bull.get("bullImage"):
                st.image(selected_bull["bullImage"], use_column_width=True)
            else:
                st.info("Sem foto do touro")

        with col2:
            st.markdown(f"**Raça:** {selected_bull['breed']}")
            st.markdown(f"**Categoria:** {selected_bull.get('category', 'N/A')}")
            st.markdown(f"**Descrição:** {selected_bull.get('description', 'Sem descrição')}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Editar foto do touro"):
                st.session_state.showEditBullPhoto = True
        with col2:
            if st.button("➕ Adicionar foto de filha"):
                st.session_state.showAddPhoto = True
        with col3:
            if st.button("Fechar galeria"):
                st.session_state.selectedBullId = None
                st.rerun()

        st.divider()

        # Modal: Editar foto do touro
        if st.session_state.get("showEditBullPhoto", False):
            st.markdown("### Editar foto do touro")
            with st.form("edit_bull_photo_form"):
                new_url = st.text_input("Nova URL da foto")
                new_file = st.file_uploader("Upload da nova foto", type=["jpg", "jpeg", "png"], key="edit_bull_photo")

                if st.form_submit_button("Salvar foto do touro"):
                    if new_file and st.session_state.github_token:
                        with st.spinner("Enviando imagem para GitHub..."):
                            filename = f"bulls/{int(datetime.now().timestamp())}-{new_file.name}"
                            new_image = upload_image_to_github(
                                new_file.read(),
                                filename,
                                st.session_state.github_token,
                                st.session_state.github_repo_owner,
                                st.session_state.github_repo_name
                            )
                            if new_image:
                                selected_bull["bullImage"] = new_image
                                save_data()
                                st.session_state.showEditBullPhoto = False
                                st.success("Foto do touro atualizada!")
                                st.rerun()
                    elif new_file:
                        st.warning("GitHub não configurado. Usando base64 local.")
                        selected_bull["bullImage"] = base64.b64encode(new_file.read()).decode()
                        selected_bull["bullImage"] = f"data:image/png;base64,{selected_bull['bullImage']}"
                        save_data()
                        st.session_state.showEditBullPhoto = False
                        st.success("Foto do touro atualizada!")
                        st.rerun()
                    elif new_url:
                        selected_bull["bullImage"] = new_url
                        save_data()
                        st.session_state.showEditBullPhoto = False
                        st.success("Foto do touro atualizada!")
                        st.rerun()
                    else:
                        st.error("Informe uma URL ou faça upload de uma imagem")

            if st.button("Apagar foto do touro"):
                selected_bull["bullImage"] = ""
                save_data()
                st.session_state.showEditBullPhoto = False
                st.success("Foto removida!")
                st.rerun()

        # Modal: Adicionar foto de filha
        if st.session_state.get("showAddPhoto", False):
            st.markdown("### Adicionar foto de filha")
            with st.form("add_photo_form"):
                cow_name = st.text_input("Nome ou número da vaca")
                col1, col2 = st.columns(2)
                with col1:
                    farm = st.text_input("Fazenda")
                with col2:
                    location = st.text_input("Cidade / Estado")

                col1, col2 = st.columns(2)
                with col1:
                    milk = st.text_input("Produção de leite (opcional)")
                with col2:
                    lactation = st.text_input("Lactação (opcional)")

                image_url = st.text_input("URL da imagem")
                image_file = st.file_uploader("Upload da imagem", type=["jpg", "jpeg", "png"], key="add_photo_file")

                if st.form_submit_button("Salvar foto"):
                    if not cow_name:
                        st.error("Preencha o nome da vaca")
                    elif not image_url and not image_file:
                        st.error("Informe uma imagem")
                    else:
                        photo_image = ""
                        if image_file and st.session_state.github_token:
                            with st.spinner("Enviando imagem para GitHub..."):
                                filename = f"daughters/{int(datetime.now().timestamp())}-{image_file.name}"
                                photo_image = upload_image_to_github(
                                    image_file.read(),
                                    filename,
                                    st.session_state.github_token,
                                    st.session_state.github_repo_owner,
                                    st.session_state.github_repo_name
                                )
                        elif image_file:
                            st.warning("GitHub não configurado. Usando base64 local.")
                            photo_image = base64.b64encode(image_file.read()).decode()
                            photo_image = f"data:image/png;base64,{photo_image}"
                        else:
                            photo_image = image_url

                        new_photo = {
                            "id": int(datetime.now().timestamp() * 1000),
                            "cowName": cow_name,
                            "farm": farm,
                            "location": location,
                            "milk": milk,
                            "lactation": lactation,
                            "image": photo_image
                        }
                        selected_bull["daughters"].insert(0, new_photo)
                        save_data()
                        st.session_state.showAddPhoto = False
                        st.success("Foto adicionada com sucesso!")
                        st.rerun()

        # Galeria de fotos
        if selected_bull.get("daughters"):
            st.markdown(f"### Fotos de filhas ({len(selected_bull['daughters'])})")

            cols = st.columns(3)
            for idx, photo in enumerate(selected_bull["daughters"]):
                with cols[idx % 3]:
                    st.image(photo["image"], use_column_width=True)
                    st.markdown(f"**{photo['cowName']}**")
                    st.markdown(f"{photo.get('farm', '-')} | {photo.get('location', '-')}")
                    if photo.get("milk"):
                        st.markdown(f"Produção: {photo['milk']}")
                    if photo.get("lactation"):
                        st.markdown(f"Lactação: {photo['lactation']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Ampliar", key=f"preview_{photo['id']}"):
                            st.session_state.previewPhoto = photo
                            st.rerun()
                    with col2:
                        if st.button("Apagar", key=f"delete_photo_{photo['id']}"):
                            selected_bull["daughters"] = [p for p in selected_bull["daughters"] if p["id"] != photo["id"]]
                            save_data()
                            st.success("Foto removida!")
                            st.rerun()
        else:
            st.info("Nenhuma foto cadastrada para este touro ainda.")

    # Modal: Visualização de foto
    if st.session_state.get("previewPhoto"):
        photo = st.session_state.previewPhoto
        st.markdown(f"## Visualização - {photo['cowName']}")
        st.image(photo["image"], use_column_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Vaca:** {photo['cowName']}")
        with col2:
            st.markdown(f"**Fazenda:** {photo.get('farm', '-')}")
        with col3:
            st.markdown(f"**Local:** {photo.get('location', '-')}")

        if photo.get("milk"):
            st.markdown(f"**Produção:** {photo['milk']}")
        if photo.get("lactation"):
            st.markdown(f"**Lactação:** {photo['lactation']}")

        if st.button("Fechar visualização"):
            st.session_state.previewPhoto = None
            st.rerun()

