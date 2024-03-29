#import os libs
import os.path
import io
import time

#google drive libs
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

#import aws libs
import boto3
import json
from botocore.exceptions import ClientError
#import localstack_client.session as boto3

from typing import List, Set, Dict, Tuple

from dotenv import load_dotenv

load_dotenv()


#thinking about passing SA account as a command-line arg
import sys


## Gdrive Globals
# If modifying these scopes, delete the file token.json:
SCOPES = ["https://www.googleapis.com/auth/drive.metadata", "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.metadata.readonly"]

## AWS Globals
#ENDPOINT_URL = "http://localhost.localstack.cloud:4566"

BUCKET_NAME="project-chocolate"


s3_client = boto3.client('s3',
                      aws_access_key_id=os.getenv('Accesskey'),
                      aws_secret_access_key=os.getenv('Secretaccesskey'),
                      region_name="us-east-1"
                      )


# need to validate the return type here
def authenticate_google_drive(service_account_file: str) -> str:

  credentials = service_account.Credentials.from_service_account_file(service_account_file)

  return credentials

def get_drive_id(service):

    response = service.files().list(pageSize=10, fields="nextPageToken, files(id, name, description)",
                                  q="mimeType='application/vnd.google-apps.folder'",
                                  ).execute()

    for folder in response.get('files',[]):
        if folder['name'] == 'Dataset':
           dataset_drive_id = folder['id'] 
    else: 
        'Not found'
    return dataset_drive_id

def get_image_classes(service, drive_id: str) -> List:

    query_for_files = service.files().list(q = "'" + drive_id + "' in parents",
                                           pageSize=10, fields="nextPageToken, files(id, name)").execute()
    return query_for_files.get('files', [])                                        

def process_image_class(service, list_of_class_folders: List) -> None:

    for folder in list_of_class_folders:
        response = service.files().list(q = "'" + folder['id'] + "' in parents",
                                       pageSize=10,fields="nextPageToken, files(id, name)").execute()
        chocolate_images  = response.get('files',[])

        for img in chocolate_images:
            score_folders = service.files().get_media(fileId=img['id'])
            score_name = f'{img["name"]}'
            with open(score_name,'wb') as chocolate_image: 
                downloader = MediaIoBaseDownload(chocolate_image, score_folders)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        print("Download %d%%." % int(status.progress() * 100))
                    file_path = os.path.join(folder['name'], score_name)
                    # lets add a check here before we upload
                    try:
                         s3_client.head_object(Bucket=BUCKET_NAME, Key=file_path)
                    except ClientError as e:
                        if e.response['Error']['Code'] == '404' or e.response['Error']['Code'] == 'NoSuchKey':
                            s3_client.upload_file(score_name, BUCKET_NAME, file_path)

    print("Upload Complete!")

if __name__ == "__main__":
    #lets first check the proper command line args exist first -- if not, let's not even start the script"
    start = time.time()
    creds = authenticate_google_drive(os.getenv('SERVICE_ACCOUNT_FILE'))
    service = build("drive", "v3", credentials=creds)
    drive_id = get_drive_id(service)
    list_of_class_folders = get_image_classes(service, drive_id)
    process_image_class = process_image_class(service, list_of_class_folders)
    print('This Job took', time.time()-start, 'seconds.')
