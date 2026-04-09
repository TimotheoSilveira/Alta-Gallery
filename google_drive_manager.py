import io
import json
import os

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

FOLDER_BULLS_DATA = "ID_DA_PASTA_DADOS"
FOLDER_BULLS_IMAGES = "ID_DA_PASTA_IMAGENS"
FOLDER_DAUGHTERS = "ID_DA_PASTA_FILHAS"


class GoogleDriveManager:

    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        creds_dict = None

        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
            else:
                raise KeyError("Chave gcp_service_account nao encontrada.")
        except Exception as e_secrets:
            json_path = os.environ.get("SERVICE_ACCOUNT_JSON", "service_account.json")
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    creds_dict = json.load(f)
            else:
                raise FileNotFoundError(
                    f"Credenciais nao encontradas.\n"
                    f"st.secrets falhou: {e_secrets}\n"
                    f"Arquivo '{json_path}' nao existe."
                )

        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        return build("drive", "v3", credentials=credentials)

    def _find_file(self, filename, parent_folder_id):
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

    def _list_files_in_folder(self, folder_id):
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

    def _get_public_url(self, file_id):
        self.service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    def _get_or_create_subfolder(self, bull_code):
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

    def load_bulls_data(self):
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

    def save_bulls_data(self, bulls):
        content = json.dumps(bulls, ensure_ascii=False, indent=2).encode("utf-8")
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/json")
        file_id = self._find_file("bulls_data.json", FOLDER_BULLS_DATA)

        if file_id:
            self.service.files().update(
                fileId=file_id, media_body=media
            ).execute()
        else:
            metadata = {
                "name": "bulls_data.json",
                "parents": [FOLDER_BULLS_DATA],
            }
            self.service.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()

    def upload_image(self, image_bytes, filename, folder_id=None):
        folder_id = folder_id or FOLDER_BULLS_IMAGES
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype="image/jpeg")
        metadata = {"name": filename, "parents": [folder_id]}
        file = (
            self.service.files()
            .create(body=metadata, media_body=media, fields="id")
            .execute()
        )
        return self._get_public_url(file["id"])

    def upload_daughter_image(self, image_bytes, filename, bull_code):
        subfolder_id = self._get_or_create_subfolder(bull_code)
        return self.upload_image(image_bytes, filename, folder_id=subfolder_id)

    def list_daughter_images(self, bull_code):
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

    def delete_file(self, file_id):
        self.service.files().update(
            fileId=file_id, body={"trashed": True}
        ).execute()
