# drive_utils.py
# ✅ Zero autenticação — usa apenas links públicos do Google Drive/Sheets
import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES — IDs do Google (sem secrets complexos!)
# ══════════════════════════════════════════════════════════════════════════════

def _get_sheet_id() -> str:
    """Lê o ID da planilha dos secrets (apenas uma string simples)."""
    try:
        return st.secrets["sheets"]["sheet_id"]
    except Exception:
        st.error("❌ Configure o sheet_id nos secrets do Streamlit.")
        st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE SHEETS — leitura via CSV público (SEM API!)
# ══════════════════════════════════════════════════════════════════════════════

def _sheet_csv_url(sheet_id: str, aba: str) -> str:
    """
    Gera URL de exportação CSV de uma aba do Google Sheets.
    A planilha deve estar compartilhada como 'Qualquer pessoa com o link'.
    """
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={aba}"
    )


@st.cache_data(ttl=300)  # Cache de 5 minutos
def load_touros() -> pd.DataFrame:
    """
    Carrega dados dos touros diretamente do Google Sheets via CSV público.
    Zero autenticação necessária.
    """
    sheet_id = _get_sheet_id()
    url = _sheet_csv_url(sheet_id, "touros")

    try:
        df = pd.read_csv(url)
        # Garante que colunas essenciais existem
        for col in ["id_touro", "nome_curto", "raca", "foto_id"]:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar planilha de touros: {e}")
        st.info(
            "💡 Verifique se a planilha está compartilhada como "
            "'Qualquer pessoa com o link pode visualizar'."
        )
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_progenies(id_touro: str) -> pd.DataFrame:
    """
    Carrega filhas de um touro específico via Google Sheets público.
    """
    sheet_id = _get_sheet_id()
    url = _sheet_csv_url(sheet_id, "progenies")

    try:
        df = pd.read_csv(url)
        if df.empty or "id_touro_pai" not in df.columns:
            return pd.DataFrame()
        return df[df["id_touro_pai"].astype(str) == str(id_touro)].reset_index(drop=True)
    except Exception as e:
        st.error(f"❌ Erro ao carregar filhas: {e}")
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE — imagens e PDFs via link público direto
# ══════════════════════════════════════════════════════════════════════════════

def _drive_img_url(file_id: str) -> str:
    """URL de visualização direta para imagens do Drive."""
    return f"https://drive.google.com/uc?export=view&id={file_id}"


def _drive_download_url(file_id: str) -> str:
    """URL de download direto para arquivos do Drive."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


@st.cache_data(ttl=600)  # Cache de 10 minutos para imagens
def get_image_from_drive(file_id: str) -> Optional[Image.Image]:
    """
    Carrega imagem do Google Drive via link público.
    O arquivo deve estar compartilhado como 'Qualquer pessoa com o link'.
    """
    if not file_id or str(file_id).strip() == "":
        return None

    file_id = str(file_id).strip()

    try:
        url = _drive_img_url(file_id)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Verifica se retornou imagem (não página HTML de erro)
            content_type = response.headers.get("Content-Type", "")
            if "image" in content_type:
                return Image.open(BytesIO(response.content))

        # Tenta URL alternativa se a primeira falhar
        url2 = f"https://lh3.googleusercontent.com/d/{file_id}"
        response2 = requests.get(url2, headers=headers, timeout=10)
        if response2.status_code == 200:
            return Image.open(BytesIO(response2.content))

    except Exception:
        pass

    return None


@st.cache_data(ttl=600)
def get_pdf_bytes_from_drive(file_id: str) -> Optional[bytes]:
    """
    Baixa PDF do Google Drive via link público.
    """
    if not file_id or str(file_id).strip() == "":
        return None

    try:
        url = _drive_download_url(str(file_id).strip())
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            return response.content
    except Exception:
        pass

    return None


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD — Admin escreve direto na planilha via link de edição
# ══════════════════════════════════════════════════════════════════════════════

def get_drive_upload_folder_url() -> str:
    """
    Retorna o link da pasta do Drive para upload manual pelo admin.
    Admin faz upload pelo próprio Google Drive e cola o file_id na planilha.
    """
    try:
        return st.secrets["drive"]["pasta_touros_url"]
    except Exception:
        return ""
