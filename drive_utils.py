# drive_utils.py — SEM Service Account, apenas URLs públicas
import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from typing import Optional

# ══════════════════════════════════════════════════════════════
# GOOGLE SHEETS — leitura via URL pública CSV
# ══════════════════════════════════════════════════════════════

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
    Não precisa de autenticação.
    """
    try:
        sheet_id = st.secrets["sheets"]["sheet_id"]
        url = _sheet_csv_url(sheet_id, "touros")
        df = pd.read_csv(url)
        # Remove colunas e linhas completamente vazias
        df = df.dropna(how="all").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar touros: {e}")
        st.info(
            "💡 Verifique se a planilha está compartilhada como "
            "'Qualquer pessoa com o link pode ver'."
        )
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_progenies(id_touro: str) -> pd.DataFrame:
    """
    Carrega aba 'progenies' e filtra pelo id_touro.
    """
    try:
        sheet_id = st.secrets["sheets"]["sheet_id"]
        url = _sheet_csv_url(sheet_id, "progenies")
        df = pd.read_csv(url)
        df = df.dropna(how="all").reset_index(drop=True)

        if df.empty or "id_touro_pai" not in df.columns:
            return pd.DataFrame()

        return df[
            df["id_touro_pai"].astype(str) == str(id_touro)
        ].reset_index(drop=True)

    except Exception as e:
        st.error(f"❌ Erro ao carregar progênies: {e}")
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════
# GOOGLE DRIVE — imagens e PDFs via URL pública
# ══════════════════════════════════════════════════════════════

def _drive_image_url(file_id: str) -> str:
    """
    Monta URL direta de imagem do Google Drive.
    O arquivo DEVE estar compartilhado publicamente.
    """
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def _drive_thumbnail_url(file_id: str, size: int = 400) -> str:
    """
    URL de thumbnail do Drive — mais rápido para galeria.
    Não exige autenticação.
    """
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"


@st.cache_data(ttl=600)
def get_image_from_drive(file_id: str) -> Optional[Image.Image]:
    """
    Baixa imagem do Google Drive pelo file_id.
    Tenta thumbnail primeiro (mais rápido), depois download direto.
    """
    if not file_id or str(file_id).strip() in ("", "nan", "None"):
        return None

    file_id = str(file_id).strip()

    # Tenta thumbnail primeiro (carrega mais rápido na galeria)
    for url in [
        _drive_thumbnail_url(file_id, 600),
        _drive_image_url(file_id),
    ]:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                return Image.open(BytesIO(resp.content))
        except Exception:
            continue

    return None


@st.cache_data(ttl=600)
def get_pdf_bytes_from_drive(file_id: str) -> Optional[bytes]:
    """
    Baixa PDF do Google Drive pelo file_id.
    Retorna bytes prontos para st.download_button.
    """
    if not file_id or str(file_id).strip() in ("", "nan", "None"):
        return None

    file_id = str(file_id).strip()
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        st.warning(f"⚠️ Erro ao baixar PDF: {e}")

    return None


# ══════════════════════════════════════════════════════════════
# GOOGLE SHEETS — escrita via gspread (só para admin)
# ══════════════════════════════════════════════════════════════

def append_touro(dados: dict) -> bool:
    """
    Adiciona linha na aba 'touros' do Google Sheets.
    Usa gspread com credenciais anônimas via link público de edição.

    NOTA: Para escrita sem Service Account, o admin preenche
    diretamente no Google Sheets. Esta função é reservada
    para futuras implementações.
    """
    # Por enquanto, o admin preenche o Sheets diretamente.
    # O upload de imagens é feito via pasta pública do Drive.
    st.info(
        "📝 Para adicionar touros, acesse diretamente o Google Sheets "
        "e a pasta do Drive usando os links abaixo."
    )
    return False
