import io
import json
import os
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]

# IDs das pastas raiz no seu Google Drive
# Crie essas pastas manualmente no Drive e cole os IDs aqui
FOLDER_BULLS_DATA = "ID_DA_PASTA_DADOS"        # pasta onde fica bulls_data.json
FOLDER_BULLS_IMAGES = "ID_DA_PASTA_IMAGENS"    # pasta onde ficam as fotos dos touros
FOLDER_DAUGHTERS = "ID_DA_PASTA_FILHAS"        # pasta onde ficam as fotos das filhas


class GoogleDriveManager:

    def __init__(self):
        self.service = self._authenticate()

    # ------------------------------------------------------------------
    # Autenticação via Service Account (secrets do Streamlit Cloud)
    # ------------------------------------------------------------------
   def _authenticate(self):
    """
    Tenta autenticar via st.secrets primeiro.
    Se falhar, tenta variável de ambiente.
    Lança erro claro em ambos os casos de falha.
    """
    creds_dict = None

    # Tentativa 1: Streamlit secrets
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        else:
            raise KeyError("Chave 'gcp_service_account' não encontrada nos secrets.")
    except Exception as e_secrets:
        # Tentativa 2: arquivo local via variável de ambiente
        json_path = os.environ.get("SERVICE_ACCOUNT_JSON", "service_account.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                creds_dict = json.load(f)
        else:
            raise FileNotFoundError(
                f"Credenciais não encontradas.\n"
                f"- st.secrets falhou com: {e_secrets}\n"
                f"- Arquivo local '{json_path}' não existe.\n"
                f"Configure os secrets no Streamlit Cloud conforme o README."
            )

    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)

    # ------------------------------------------------------------------
    # Utilitários internos
    # ------------------------------------------------------------------
    def _find_file(self, filename: str, parent_folder_id: str) -> str | None:
        """Retorna o file_id se o arquivo existir na pasta, senão None."""
        query = (
            f"name='{filename}' "
            f"and '{parent_folder_id}' in parents "
            f"and trashed=false"
        )
        result = (
            self.service.files()
            .list(q=query, fields="files(id, name)")
            .execute()
        )
        files = result.get("files", [])
        return files[0]["id"] if files else None

    def _list_files_in_folder(self, folder_id: str) -> list[dict]:
        """Lista todos os arquivos de uma pasta."""
        query = f"'{folder_id}' in parents and trashed=false"
        result = (
            self.service.files()
            .list(
                q=query,
                fields="files(id, name, mimeType, webContentLink, webViewLink)",
            )
            .execute()
        )
        return result.get("files", [])

    def _get_public_url(self, file_id: str) -> str:
        """
        Torna o arquivo público (leitor) e retorna a URL de visualização
        direta — ideal para st.image().
        """
        self.service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()
        # URL que força o download/visualização direta
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    # ------------------------------------------------------------------
    # JSON de dados dos touros
    # ------------------------------------------------------------------
    def load_bulls_data(self) -> list[dict]:
        """Carrega bulls_data.json do Drive. Retorna lista vazia se não existir."""
        file_id = self._find_file("bulls_data.json", FOLDER_BULLS_DATA)
        if not file_id:
            return []

        request = self.service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        try:
            return json.loads(buffer.read().decode("utf-8"))
        except json.JSONDecodeError:
            return []

    def save_bulls_data(self, bulls: list[dict]) -> None:
        """Salva (cria ou sobrescreve) bulls_data.json no Drive."""
        content = json.dumps(bulls, ensure_ascii=False, indent=2).encode("utf-8")
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/json")

        file_id = self._find_file("bulls_data.json", FOLDER_BULLS_DATA)

        if file_id:
            # Atualiza arquivo existente
            self.service.files().update(
                fileId=file_id, media_body=media
            ).execute()
        else:
            # Cria novo arquivo
            metadata = {
                "name": "bulls_data.json",
                "parents": [FOLDER_BULLS_DATA],
            }
            self.service.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()

    # ------------------------------------------------------------------
    # Upload de imagens
    # ------------------------------------------------------------------
    def upload_image(
        self,
        image_bytes: bytes,
        filename: str,
        folder_id: str = None,
    ) -> str:
        """
        Faz upload de uma imagem para o Drive e retorna a URL pública.
        Por padrão usa FOLDER_BULLS_IMAGES.
        """
        folder_id = folder_id or FOLDER_BULLS_IMAGES
        media = MediaIoBaseUpload(
            io.BytesIO(image_bytes), mimetype="image/jpeg"
        )
        metadata = {"name": filename, "parents": [folder_id]}
        file = (
            self.service.files()
            .create(body=metadata, media_body=media, fields="id")
            .execute()
        )
        return self._get_public_url(file["id"])

    def upload_daughter_image(
        self, image_bytes: bytes, filename: str, bull_code: str
    ) -> str:
        """
        Faz upload da foto de uma filha numa subpasta específica do touro.
        Cria a subpasta se não existir.
        """
        subfolder_id = self._get_or_create_subfolder(bull_code)
        return self.upload_image(image_bytes, filename, folder_id=subfolder_id)

    # ------------------------------------------------------------------
    # Subpastas por touro (organização das filhas)
    # ------------------------------------------------------------------
    def _get_or_create_subfolder(self, bull_code: str) -> str:
        """
        Garante que exista uma subpasta com o nome do código do touro
        dentro de FOLDER_DAUGHTERS. Retorna o folder_id.
        """
        query = (
            f"name='{bull_code}' "
            f"and '{FOLDER_DAUGHTERS}' in parents "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )
        result = (
            self.service.files()
            .list(q=query, fields="files(id)")
            .execute()
        )
        files = result.get("files", [])
        if files:
            return files[0]["id"]

        # Cria subpasta
        metadata = {
            "name": bull_code,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [FOLDER_DAUGHTERS],
        }
        folder = (
            self.service.files()
            .create(body=metadata, fields="id")
            .execute()
        )
        return folder["id"]

    def list_daughter_images(self, bull_code: str) -> list[dict]:
        """
        Lista as imagens de filhas de um touro específico.
        Retorna lista de dicts com 'name' e 'url'.
        """
        subfolder_id = self._get_or_create_subfolder(bull_code)
        files = self._list_files_in_folder(subfolder_id)

        result = []
        for f in files:
            if "image" in f.get("mimeType", ""):
                result.append(
                    {
                        "name": f["name"],
                        "url": self._get_public_url(f["id"]),
                        "file_id": f["id"],
                    }
                )
        return result

    def delete_file(self, file_id: str) -> None:
        """Move um arquivo para a lixeira do Drive."""
        self.service.files().update(
            fileId=file_id, body={"trashed": True}
        ).execute()
