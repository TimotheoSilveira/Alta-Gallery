# drive_utils.py
# Versão SEM Google Cloud, SEM Service Account
# Usa apenas links públicos do Google Drive

import streamlit as st
import pandas as pd
import requests
import gspread
from PIL import Image
from io import BytesIO
from typing import Optional
from google.oauth2.service_account import Credentials

# ══════════════════════════════════════════════════════════════════════════════
# IMAGENS E PDFs — via link público do Drive
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def get_image_from_drive(file_id: str) -> Optional[Image.Image]:
    """
    Baixa imagem do Google Drive via link público.
    O arquivo deve estar compartilhado como 'Qualquer pessoa com o link'.

    Args:
        file_id: ID do arquivo no Drive
                 (parte da URL: drive.google.com/file/d/[FILE_ID]/view)
    """
    if not file_id or not file_id.strip():
        return None

    # Tenta primeiro com o link de exportação direto
    urls = [
        f"https://drive.google.com/uc?export=download&id={file_id}",
        f"https://drive.google.com/uc?id={file_id}",
        f"https://lh3.googleusercontent.com/d/{file_id}",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)

            # Verifica se retornou uma imagem (não uma página HTML)
            content_type = response.headers.get("Content-Type", "")
            if response.status_code == 200 and "image" in content_type:
                return Image.open(BytesIO(response.content))

        except Exception:
            continue

    return None


@st.cache_data(ttl=600)
def get_pdf_bytes_from_drive(file_id: str) -> Optional[bytes]:
    """
    Baixa PDF do Google Drive via link público.
    Retorna bytes prontos para st.download_button.
    """
    if not file_id or not file_id.strip():
        return None

    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        st.warning(f"⚠️ Não foi possível baixar o PDF: {e}")

    return None


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE SHEETS — via link público (somente leitura)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_touros() -> pd.DataFrame:
    """
    Lê os dados dos touros direto do Google Sheets público.
    A planilha deve estar compartilhada como 'Qualquer pessoa com o link'.
    """
    try:
        sheet_id  = st.secrets["sheets"]["sheet_id"]
        aba       = st.secrets["sheets"]["aba_touros"]

        # URL de exportação CSV do Google Sheets (sem autenticação)
        url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            f"/gviz/tq?tqx=out:csv&sheet={aba}"
        )

        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()  # Remove espaços dos headers
        return df

    except Exception as e:
        st.error(f"❌ Erro ao carregar touros: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_progenies(id_touro: str) -> pd.DataFrame:
    """
    Lê os dados das progênies direto do Google Sheets público.
    Filtra pelo id do touro pai.
    """
    try:
        sheet_id = st.secrets["sheets"]["sheet_id"]
        aba      = st.secrets["sheets"]["aba_progenies"]

        url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            f"/gviz/tq?tqx=out:csv&sheet={aba}"
        )

        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

        if df.empty or "id_touro_pai" not in df.columns:
            return pd.DataFrame()

        return df[
            df["id_touro_pai"].astype(str) == str(id_touro)
        ].reset_index(drop=True)

    except Exception as e:
        st.error(f"❌ Erro ao carregar progênies: {e}")
        return pd.DataFrame()
