import mimetypes
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive']


def folder_upload(folder_name, service):
    """Uploads folder and all it's content (if it doesnt exists)
        in root folder.

        Args:
            folder_name: Name of folder in OS
            service: Authorized Google Drive service

        Returns:
            Dictionary, where keys are folder's names
            and values are id's of these folders.
    """

    parents_id = {}
    for root, _, files in os.walk(folder_name):
        last_dir = root.split('/')[-1]
        pre_last_dir = root.split('/')[-2]
        if pre_last_dir not in parents_id.keys():
            pre_last_dir = []
        else:
            pre_last_dir = parents_id[pre_last_dir]

        folder_metadata = {'name': last_dir,
                           'parents': pre_last_dir,
                           'mimeType': 'application/vnd.google-apps.folder'}
        create_folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = create_folder.get('id', [])

        for file_name in files:
            file_metadata = {'name': file_name, 'parents': folder_id}
            media = MediaFileUpload(
                os.path.join(root, file_name),
                mimetype=mimetypes.MimeTypes.guess_type(file_name)[0]
            )
            service.files().create(body=file_metadata,
                                   media_body=media,
                                   fields='id').execute()

        parents_id[last_dir] = folder_id
    return parents_id


def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = get_creds()
    try:
        service = build("drive", "v3", credentials=creds)
        result = (
            service.about().get(fields='user').execute()
        )
        print(result.get("user", []))
        # Call the Drive v3 API
        results = (
            service.files()
            .list(pageSize=10, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")
    except HttpError as error:
        print(f"An error occurred: {error}")
        exit(-1)


if __name__ == "__main__":
    main()
