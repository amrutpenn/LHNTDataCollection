from boxsdk import Client, OAuth2
import os


def authenticate():
    client_id = 'bq09tmdv7v99bcivrw6z5z6hdgny907i'
    client_secret = 'bq09tmdv7v99bcivrw6z5z6hdgny907i'
    # dev token HAS to be refreshed during every session for now, it only lasts an hour
    developer_token = '3CWZGA2Ow0I9yjJKHCSv30vEZjI5POc0'
    auth = OAuth2(
        client_id=client_id,
        client_secret=client_secret,
        access_token=developer_token
    )
    return Client(auth)

def download_file(client, file_id, download_dir):
    file = client.file(file_id).get()
    download_path = os.path.join(download_dir, file.name)
    with open(download_path, 'wb') as open_file:
        file.download_to(open_file)
    print(f'{file.name} has been downloaded to {download_path}')

def upload_file(client, folder_id, local_file_path):
    file_name = os.path.basename(local_file_path)
    uploaded_file = client.folder(folder_id).upload(local_file_path, file_name)
    print(f'File {file_name} uploaded to Box folder {folder_id} with ID {uploaded_file.id}')
    return uploaded_file.id

# Usage
    #client = authenticate()
    #file_id = '1679766376012'  # Specify the file ID you want to download and modify
    #folder_id = '289622073398'
    #script_dir = os.path.dirname(os.path.abspath(__file__))
    #download_dir = script_dir  # Ensure this points to a directory

    #download_file(client, file_id, download_dir)

    # Modify your file here
    #download_path = os.path.join(download_dir, "InitAuthentication.py")
    #with open(download_path, 'a') as open_file:
    #open_file.write('\nModification done.')

    #upload_file(client, folder_id, download_path)
