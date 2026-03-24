import streamlit as st
import json
import base64
from pathlib import Path
from datetime import datetime
import io
import os

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

st.set_page_config(
    page_title="Alta Gallery",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CONFIGURAÇÃO DO GOOGLE DRIVE (usando Streamlit Secrets)
GOOGLE_DRIVE_FOLDER_ID = st.secrets.get("google_drive_folder_id", "")
SCOPES = ['https://www.googleapis.com/auth/drive']

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
# INICIALIZAR SESSION STATE
# ============================================================================

if "bulls" not in st.session_state:
    st.session_state.bulls = []
    st.session_state.query = ""
    st.session_state.breedFilter = "Todas as raças"
    st.session_state.selectedBullId = None
    st.session_state.previewPhoto = None

# ============================================================================
# FUNÇÕES DO GOOGLE DRIVE
# ============================================================================

@st.cache_resource
def get_drive_service():
    """Retorna serviço autenticado do Google Drive usando Streamlit Secrets"""
    if not GOOGLE_DRIVE_AVAILABLE:
        return None

    try:
        # Obter credenciais do Streamlit Secrets
        service_account_info = st.secrets.get("google_service_account")

        if not service_account_info:
            return None

        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Erro ao conectar com Google Drive: {str(e)}")
        return None

def upload_photo_to_google_drive(file_content, filename, folder_id=GOOGLE_DRIVE_FOLDER_ID):
    """Faz upload de foto para Google Drive e retorna a URL pública"""
    service = get_drive_service()

    if not service:
        st.error("Google Drive não configurado. Verifique Streamlit Secrets")
        return None

    try:
        # Metadados do arquivo
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'mimeType': 'image/jpeg'
        }

        # Fazer upload
        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype='image/jpeg',
            resumable=True
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = file.get('id')

        # Tornar arquivo público
        try:
            service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
        except:
            pass

        # Retornar URL pública
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    except Exception as e:
        st.error(f"Erro ao fazer upload: {str(e)}")
        return None

def test_google_drive_connection():
    """Testa conexão com Google Drive"""
    service = get_drive_service()
    if not service:
        return False

    try:
        service.files().list(spaces='drive', pageSize=1).execute()
        return True
    except:
        return False

# ============================================================================
# FUNÇÕES DE ARMAZENAMENTO LOCAL
# ============================================================================

def load_bulls():
    if Path("bulls_data.json").exists():
        with open("bulls_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return INITIAL_BULLS.copy()

def save_bulls():
    with open("bulls_data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.bulls, f, indent=2, ensure_ascii=False)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_breeds():
    breeds = set(bull["breed"] for bull in st.session_state.bulls)
    return ["Todas as raças"] + sorted(list(breeds))

def get_filtered_bulls():
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
    for bull in st.session_state.bulls:
        if bull["id"] == st.session_state.selectedBullId:
            return bull
    return None

# ============================================================================
# CARREGAR DADOS
# ============================================================================

if not st.session_state.bulls:
    st.session_state.bulls = load_bulls()

# ============================================================================
# GALERIA PÚBLICA
# ============================================================================

col1, col2, col3 = st.columns([2, 3, 2])

with col1:
    st.markdown("### 🐄 Alta Gallery")

st.divider()

st.markdown("## Touros Cadastrados")
st.markdown("Conheça os touros Alta Genetics e a progênie deles.")

col1, col2, col3 = st.columns(3)
total_photos = sum(len(bull.get("daughters", [])) for bull in st.session_state.bulls)
breeds_count = len(get_breeds()) - 1

with col1:
    st.metric("Touros", len(st.session_state.bulls))
with col2:
    st.metric("Raças", max(breeds_count, 0))
with col3:
    st.metric("Fotos", total_photos)

st.divider()

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

st.divider()

filtered_bulls = get_filtered_bulls()

if not filtered_bulls:
    st.info("Nenhum touro encontrado com esse filtro.")
else:
    st.markdown(f"### {len(filtered_bulls)} resultado(s)")

    for bull in filtered_bulls:
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
            if st.button("Ver galeria", key=f"open_{bull['id']}"):
                st.session_state.selectedBullId = bull["id"]
                st.rerun()

        st.divider()

# ============================================================================
# GALERIA DO TOURO
# ============================================================================

selected_bull = get_selected_bull()
if selected_bull:
    st.markdown(f"## Galeria - {selected_bull['name']} ({selected_bull['code']})")

    col1, col2 = st.columns([1, 3])
    with col1:
        if selected_bull.get("bullImage"):
            st.image(selected_bull["bullImage"], use_column_width=True)
        else:
            st.info("Sem foto")

    with col2:
        st.markdown(f"**Raça:** {selected_bull['breed']}")
        st.markdown(f"**Categoria:** {selected_bull.get('category', 'N/A')}")
        st.markdown(f"**Descrição:** {selected_bull.get('description', 'Sem descrição')}")

    if st.button("Fechar galeria"):
        st.session_state.selectedBullId = None
        st.rerun()

    st.divider()

    # Fotos das filhas
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

                if st.button("Ampliar", key=f"preview_{photo['id']}"):
                    st.session_state.previewPhoto = photo
                    st.rerun()
    else:
        st.info("Nenhuma foto cadastrada para este touro ainda.")

# ============================================================================
# VISUALIZAÇÃO DE FOTO
# ============================================================================

if st.session_state.previewPhoto:
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

# ============================================================================
# SIDEBAR - INFORMAÇÕES
# ============================================================================

with st.sidebar:
    st.markdown("### 📋 Informações")
    st.markdown(f"**Total de touros:** {len(st.session_state.bulls)}")
    st.markdown(f"**Total de fotos:** {total_photos}")
    st.markdown(f"**Raças cadastradas:** {breeds_count}")

    st.divider()

    st.markdown("### 🔧 Google Drive")
    if GOOGLE_DRIVE_AVAILABLE:
        if test_google_drive_connection():
            st.success("✅ Google Drive conectado")
        else:
            st.warning("⚠️ Google Drive não configurado")
    else:
        st.warning("⚠️ Bibliotecas do Google não instaladas")

    st.markdown(f"**ID da Pasta:** `{GOOGLE_DRIVE_FOLDER_ID}`")
    if GOOGLE_DRIVE_FOLDER_ID:
        st.markdown(f"[Abrir Google Drive](https://drive.google.com/drive/folders/{GOOGLE_DRIVE_FOLDER_ID}?usp=sharing)")
