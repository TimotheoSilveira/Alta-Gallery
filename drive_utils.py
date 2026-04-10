# drive_utils.py
# Leitura de dados via Google Sheets e Google Drive públicos.
# Zero autenticação — usa apenas URLs públicas.

import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE SHEETS — leitura via CSV público
# ══════════════════════════════════════════════════════════════════════════════

def _sheet_csv_url(sheet_id: str, aba: str) -> str:
    """
    Monta a URL de exportação CSV de uma aba do Google Sheets.
    A planilha DEVE estar compartilhada como 'Qualquer pessoa com o link'.
    """
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={aba}"
    )


@st.cache_data(ttl=300)  # Cache de 5 minutos
def load_touros() -> pd.DataFrame:
    """
    Carrega aba 'touros' do Google Sheets via CSV público.

    Colunas esperadas:
        Código NAAB, InterRegNumber, Nome, Nome completo, Raça,
        foto_id, prova_id, TPI, NM$, CM$, FM$, GM$,
        Leite, Proteína, Prot%, Gordura, % Gordura,
        CGP, VP, REI, IF, PTAT, MUI, CUB,
        Kapa-Caseína, Beta-Caseína, EFI, Birth Date, Prova
    """
    try:
        sheet_id = st.secrets["sheets"]["sheet_id"]
        aba      = st.secrets["sheets"].get("aba_touros", "touros")
        url      = _sheet_csv_url(sheet_id, aba)

        df = pd.read_csv(url)

        # Remove linhas e colunas completamente vazias
        df = df.dropna(how="all").reset_index(drop=True)

        # Remove espaços extras dos nomes das colunas
        df.columns = df.columns.str.strip()

        return df

    except KeyError:
        st.error("❌ Secret ausente: [sheets] não encontrado no secrets.toml")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        st.info(
            "💡 Verifique se a planilha está compartilhada como "
            "'Qualquer pessoa com o link pode ver'."
        )
        return pd.DataFrame()


@st.cache_data(ttl=300)  # Cache de 5 minutos
def load_progenies(codigo_naab: str) -> pd.DataFrame:
    """
    Carrega aba 'progenies' e filtra pelo Código NAAB do touro pai.

    Colunas esperadas na aba progenies:
        id_touro_pai, nome, data_nascimento,
        proprietario, leite_lts, fotos_drive_ids
    """
    try:
        sheet_id = st.secrets["sheets"]["sheet_id"]
        aba      = st.secrets["sheets"].get("aba_progenies", "progenies")
        url      = _sheet_csv_url(sheet_id, aba)

        df = pd.read_csv(url)
        df = df.dropna(how="all").reset_index(drop=True)
        df.columns = df.columns.str.strip()

        if df.empty:
            return pd.DataFrame()

        if "id_touro_pai" not in df.columns:
            st.warning(
                "⚠️ Coluna 'id_touro_pai' não encontrada na aba 'progenies'."
            )
            return pd.DataFrame()

        return df[
            df["id_touro_pai"].astype(str).str.strip() == str(codigo_naab).strip()
        ].reset_index(drop=True)

    except KeyError:
        st.error("❌ Secret ausente: [sheets] não encontrado no secrets.toml")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar filhas: {e}")
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE — imagens via URL pública
# ══════════════════════════════════════════════════════════════════════════════

def _drive_thumbnail_url(file_id: str, size: int = 600) -> str:
    """
    URL de thumbnail do Google Drive.
    Mais rápido para carregar na galeria.
    O arquivo DEVE estar compartilhado publicamente.
    """
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"


def _drive_download_url(file_id: str) -> str:
    """
    URL de download direto do Google Drive.
    Usada como fallback se o thumbnail falhar.
    """
    return f"https://drive.google.com/uc?export=download&id={file_id}"


@st.cache_data(ttl=600)  # Cache de 10 minutos
def get_image_from_drive(file_id: str) -> Optional[Image.Image]:
    """
    Baixa e retorna imagem do Google Drive pelo file_id.
    Tenta thumbnail primeiro (mais rápido), depois download direto.
    O arquivo DEVE estar compartilhado como 'Qualquer pessoa com o link'.

    Args:
        file_id: ID do arquivo no Drive
                 (parte da URL: drive.google.com/file/d/[FILE_ID]/view)

    Returns:
        PIL.Image ou None se não conseguir carregar.
    """
    # Validação do file_id
    if not file_id:
        return None
    file_id = str(file_id).strip()
    if file_id in ("", "nan", "None", "-"):
        return None

    headers = {"User-Agent": "Mozilla/5.0"}

    urls = [
        _drive_thumbnail_url(file_id, 600),
        _drive_download_url(file_id),
        f"https://lh3.googleusercontent.com/d/{file_id}",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                if "image" in content_type:
                    return Image.open(BytesIO(resp.content))
        except Exception:
            continue

    return None


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE — PDFs via URL pública
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)  # Cache de 10 minutos
def get_pdf_bytes_from_drive(file_id: str) -> Optional[bytes]:
    """
    Baixa PDF do Google Drive pelo file_id.
    Retorna bytes prontos para usar em st.download_button.
    O arquivo DEVE estar compartilhado como 'Qualquer pessoa com o link'.

    Args:
        file_id: ID do arquivo PDF no Drive.

    Returns:
        bytes do PDF ou None se falhar.
    """
    # Validação do file_id
    if not file_id:
        return None
    file_id = str(file_id).strip()
    if file_id in ("", "nan", "None", "-"):
        return None

    headers = {"User-Agent": "Mozilla/5.0"}
    url = _drive_download_url(file_id)

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        st.warning(f"⚠️ Não foi possível baixar o PDF: {e}")

    return None


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS ÚTEIS
# ══════════════════════════════════════════════════════════════════════════════

def get_drive_folder_url(pasta: str) -> str:
    """
    Retorna a URL da pasta do Drive configurada nos secrets.
    Usado para direcionar o admin ao local correto de upload.

    Args:
        pasta: chave do secrets.toml — ex: 'pasta_touros'
    """
    try:
        folder_id = st.secrets["drive"][pasta]
        return f"https://drive.google.com/drive/folders/{folder_id}"
    except Exception:
        return ""


def invalidate_cache():
    """
    Limpa o cache do Streamlit.
    Útil após o admin adicionar novos dados na planilha.
    """
    st.cache_data.clear()
    st.success("✅ Cache limpo! Os dados serão recarregados.")
