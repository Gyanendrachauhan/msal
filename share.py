from dotenv import load_dotenv
import os,requests
import logging
from flask import jsonify
from llm import upload
import urllib.parse

file_link_dict = {}


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
# Replace these variables with your actual values
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
tenant_id = os.getenv('tenant_id')
resource = os.getenv('resource')
site_id = os.getenv('site_id')

base_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items'

def get_access_token():
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    body = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': resource + '/.default'
    }

    try:
        response = requests.post(url, headers=headers, data=body)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.HTTPError as err:
        logger.error(f"Error obtaining access token: {err}")
        return None





def fetch_pdf_content(file_id, access_token, base_url):
    """Fetches the content of a file from SharePoint."""
    file_url = f'{base_url}/{file_id}/content'
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        file_response = requests.get(file_url, headers=headers)
        file_response.raise_for_status()
        return file_response.content
    except requests.HTTPError as err:
        logger.error(f"Failed to download file with ID {file_id}. Error: {err}")
        return None




def list_items_in_folder(folder_id, access_token, base_url):
    """Fetch items in a given folder."""
    url = f'{base_url}/{folder_id}/children'
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('value', [])
    except requests.HTTPError as err:
        logger.error(f"Failed to list items in folder with ID {folder_id}. Error: {err}")
        return []

def process_items(items, folder_name, access_token, base_url):
    """Process items recursively, listing PDF files and their download URLs."""
    file_identifiers = []
    file_link_dict = {}

    for item in items:
        if 'folder' in item:
            _, child_identifiers, child_links = process_items(
                list_items_in_folder(item['id'], access_token, base_url),
                os.path.join(folder_name, item['name']),
                access_token,
                base_url
            )
            file_identifiers.extend(child_identifiers)
            file_link_dict.update(child_links)
        elif 'file' in item and item['name'].endswith('.pdf'):
            file_identifiers.append(item['name'])
            file_link_dict[item['name']] = item['@microsoft.graph.downloadUrl']

    return None, file_identifiers, file_link_dict


def download_pdf_files(folder_id, folder_name, access_token, base_url):
    items = list_items_in_folder(folder_id, access_token, base_url)
    return process_items(items, folder_name, access_token, base_url)

# def clean_local_directory(all_files):
#     root_directory_path = r'C:\Users\Gyani\PycharmProjects\sharepointfinal\local_directory'
#     for foldername, _, filenames in os.walk(root_directory_path):
#         for filename in filenames:
#             rel_path = os.path.relpath(os.path.join(foldername, filename), root_directory_path)
#             if rel_path not in all_files:
#                 os.remove(os.path.join(foldername, filename))



def upload_pdfs_to_server(selected_web_urls, access_token, base_url):
    pdf_contents = []

    for web_url in selected_web_urls:
        print(access_token)
        # Fetch the file content from the webUrl
        file_response = requests.get(web_url, headers={'Authorization': f'Bearer {access_token}'})
        print(file_response)

        if file_response.status_code == 200:
            pdf_contents.append(file_response.content)
        else:
            logger.error(f"Failed to fetch content from {web_url}. Error: {file_response.text}")

    upload_response = upload(pdf_contents)

    if isinstance(upload_response, dict) and "error" in upload_response:
        logger.error(f"Upload failed with error: {upload_response['error']}")
        response = jsonify({"error": "Failed to upload PDFs", "response": upload_response['error']})
        response.status_code = upload_response.get('status_code', 400)
        return response

    logger.info("Upload successful!")
    return jsonify({"message": "Upload successful!"}), 200

