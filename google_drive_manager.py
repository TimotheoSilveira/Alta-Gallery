import os
import json
import io
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from dotenv import load_dotenv

load_dotenv()

class GoogleDriveManager:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.service = self._authenticate()

    def _authenticate(self):
        """Autentica com Google Drive usando credenciais de serviço"""
        try:
            # Tenta usar arquivo de credenciais
            creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
            if os.path.exists(creds_path):
                creds = Credentials.from_service_account_file(
                    creds_path,
                    scopes=self.SCOPES
                )
            else:
                # Alternativa: usar variável de ambiente com JSON
                creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
                if creds_json:
                    creds_dict = json.loads(creds_json)
                    creds = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=self.SCOPES
                    )
                else:
                    raise ValueError("Credenciais do Google não encontradas")

            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return None

    def load_bulls_data(self):
        """Carrega o arquivo JSON de touros do Google Drive"""
        try:
            file_id = self._find_file_by_name('alta-gallery-dados.json')
            if not file_id:
                return []

            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            return json.loads(file_content)
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return []

    def save_bulls_data(self, bulls_data):
        """Salva o arquivo JSON de touros no Google Drive"""
        try:
            file_id = self._find_file_by_name('alta-gallery-dados.json')
            json_content = json.dumps(bulls_data, ensure_ascii=False, indent=2)
            media = MediaIoBaseUpload(
                io.BytesIO(json_content.encode('utf-8')),
                mimetype='application/json',
                resumable=True
            )

            if file_id:
                # Atualiza arquivo existente
                self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
            else:
                # Cria novo arquivo
                file_metadata = {
                    'name': 'alta-gallery-dados.json',
                    'parents': [self.FOLDER_ID] if self.FOLDER_ID else []
                }
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

    def upload_image(self, file_bytes, filename):
        """Faz upload de imagem para Google Drive e retorna URL pública"""
        try:
            file_metadata = {
                'name': filename,
                'parents': [self.FOLDER_ID] if self.FOLDER_ID else []
            }
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes),
                mimetype='image/jpeg',
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            # Torna arquivo público
            self.service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()

            # Retorna URL pública
            return f"https://drive.google.com/uc?id={file['id']}"
        except Exception as e:
            print(f"Erro ao fazer upload: {e}")
            return None

    def _find_file_by_name(self, filename):
        """Encontra um arquivo por nome no Google Drive"""
        try:
            query = f"name='{filename}' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id)',
                pageSize=1
            ).execute()

            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception as e:
            print(f"Erro ao procurar arquivo: {e}")
            return None
