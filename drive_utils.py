# drive_utils.py
import streamlit as st
import gspread
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from typing import Optional

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# ─── Credenciais ──────────────────────────────────────────────────────────────

@st.cache_resource
def get_credentials():
    """Carrega credenciais da service account via secrets.toml."""
    return service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

@st.cache_resource
def get_drive_service():
    return build("drive", "v3", credentials=get_credentials())

@st.cache_resource
def get_sheets_client():
    return gspread.authorize(get_credentials())

# ─── Google Sheets: Leitura ───────────────────────────────────────────────────

@st.cache_data(ttl=300)  # Cache de 5 minutos - suporta 1000 touros
def load_touros() -> pd.DataFrame:
    """Carrega todos os touros do Google Sheets."""
    gc = get_sheets_client()
    sheet_id = st.secrets["sheets"]["sheet_id"]
    ws = gc.open_by_key(sheet_id).worksheet(
        st.secrets["sheets"]["aba_touros"]
    )
    data = ws.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_progenies(id_touro: str) -> pd.DataFrame:
    """Carrega progênies de um touro específico."""
    gc = get_sheets_client()
    sheet_id = st.secrets["sheets"]["sheet_id"]
    ws = gc.open_by_key(sheet_id).worksheet(
        st.secrets["sheets"]["aba_progenies"]
    )
    data = ws.get_all_records()
    df = pd.DataFrame(data) if data else pd.DataFrame()

    if df.empty:
        return df
    return df[df["id_touro_pai"] == id_touro].reset_index(drop=True)


# ─── Google Sheets: Escrita (Admin) ──────────────────────────────────────────

def insert_touro(dados: dict) -> bool:
    """Insere novo touro no Google Sheets."""
    try:
        gc = get_sheets_client()
        sheet_id = st.secrets["sheets"]["sheet_id"]
        ws = gc.open_by_key(sheet_id).worksheet(
            st.secrets["sheets"]["aba_touros"]
        )
        # Garante a ordem das colunas
        headers = ws.row_values(1)
        row = [dados.get(h, "") for h in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")

        # Invalida cache após inserção
        load_touros.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir touro: {e}")
        return False


def insert_progenie(dados: dict) -> bool:
    """Insere nova progênie no Google Sheets."""
    try:
        gc = get_sheets_client()
        sheet_id = st.secrets["sheets"]["sheet_id"]
        ws = gc.open_by_key(sheet_id).worksheet(
            st.secrets["sheets"]["aba_progenies"]
        )
        headers = ws.row_values(1)
        row = [dados.get(h, "") for h in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")
        load_progenies.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir progênie: {e}")
        return False


# ─── Google Drive: Imagens e PDFs ────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_image_from_drive(file_id: str) -> Optional[Image.Image]:
    """
    Baixa imagem do Google Drive.
    Usa link de exportação direto - arquivo deve ter acesso "Qualquer pessoa com o link".
    """
    if not file_id:
        return None
    try:
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception:
        pass
    return None


def get_pdf_bytes_from_drive(file_id: str) -> Optional[bytes]:
    """Baixa PDF do Google Drive e retorna bytes para download."""
    if not file_id:
        return None
    try:
        service = get_drive_service()
        request = service.files().get_media(fileId=file_id)
        file_bytes = BytesIO()
        from googleapiclient.http import MediaIoBaseDownload
        downloader = MediaIoBaseDownload(file_bytes, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return file_bytes.getvalue()
    except Exception as e:
        st.error(f"Erro ao baixar PDF: {e}")
        return None


def upload_file_to_drive(
    file_bytes: bytes,
    filename: str,
    folder_id: str,
    mimetype: str = "image/jpeg"
) -> Optional[str]:
    """
    Faz upload de arquivo (imagem ou PDF) para pasta do Drive.
    Retorna o file_id do arquivo criado.
    """
    try:
        service = get_drive_service()
        file_metadata = {"name": filename, "parents": [folder_id]}
        media = MediaIoBaseUpload(
            BytesIO(file_bytes),
            mimetype=mimetype,
            resumable=True
        )
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        # Tornar arquivo publicamente legível
        service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"}
        ).execute()

        return file.get("id")
    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return None
