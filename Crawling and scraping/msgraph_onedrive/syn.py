from msgraph_onedrive.operations import download_file, list_folder_children, upload_file, search_file_id, create_folder
from shared.globals import CHECKPOINTS_PATH, CHECKPOINTS_PATH_TEST
import dotenv
import os
import time
import json
from shared.colorful import print_banner_colored

dotenv.load_dotenv()
def update_crawl_info(PATH):
    upload_file(os.getenv(PATH['FOLDER_STORAGE_ID_ENV_NAME']), PATH['CRAWL'].name, file_path=PATH['CRAWL'], type='replace')
    print_banner_colored('Upload crawl info thành công', 'success')

def update_extract_info(PATH):
    upload_file(os.getenv(PATH['FOLDER_SCRAPING_ENV_NAME']), PATH['EXTRACT'].name, file_path=PATH['EXTRACT'], type='replace')
    print_banner_colored('Upload extract info thành công', 'success')

def update_link_list(PATH):
    upload_file(os.getenv(PATH['FOLDER_STORAGE_ID_ENV_NAME']), PATH['LINK_LIST'].name, file_path=PATH['LINK_LIST'], type='replace')
    print_banner_colored('Upload link list thành công', 'success')

def pull_from_onedrive(PATH):
    try:
        previous_crawl_info = search_file_id(PATH['CRAWL'].name, folder_id=os.getenv(PATH['FOLDER_STORAGE_ID_ENV_NAME']))
        previous_crawl_info_data = download_file(previous_crawl_info)
        with open(PATH['CRAWL'], 'w') as file:
            json.dump(previous_crawl_info_data, file)
    except:
        print_banner_colored('Khi pull: File crawl info chưa tồn tại', 'danger')

    try:
        previous_extract_info = search_file_id(PATH['EXTRACT'].name, folder_id=os.getenv(PATH['FOLDER_SCRAPING_ENV_NAME']))
        previous_extract_info_data = download_file(previous_extract_info)
        with open(PATH['EXTRACT'], 'w') as file:
            json.dump(previous_extract_info_data, file)
    except:
        print_banner_colored('Khi pull: File extract info chưa tồn tại', 'danger')

    try:
        previous_link_list = search_file_id(PATH['LINK_LIST'].name, folder_id=os.getenv(PATH['FOLDER_STORAGE_ID_ENV_NAME']))
        previous_link_list_data = download_file(previous_link_list)
        with open(PATH['LINK_LIST'], 'w') as file:
            json.dump(previous_link_list_data, file)
    except:
        print_banner_colored('Khi pull: File link list info chưa tồn tại', 'danger')


    print_banner_colored('Pull checkpoint từ OneDrive thành công', 'success')


def push_all_to_onedrive(PATH=None, web=None, test=False):
    # Kiem tra lại là xài test hay xài thường
    if not PATH:
        PATH = CHECKPOINTS_PATH_TEST[web.upper()] if test else CHECKPOINTS_PATH[web.upper()]

    update_crawl_info(PATH)
    update_extract_info(PATH)
    update_link_list(PATH)

def reset_all(PATH=None, web=None, test=False):
    if PATH:
        PATH = CHECKPOINTS_PATH_TEST[web.upper()] if test else CHECKPOINTS_PATH[web.upper()]
    
    with open(PATH['CRAWL'], 'w') as file:
        json.dump('', file)
    with open(PATH['EXTRACT'], 'w') as file:
        json.dump('', file)
    with open(PATH['LINK_LIST'], 'w') as file:
        json.dump('', file)

    # Không chắc là có nên xóa toàn bộ data trong folder không (hoặc thủ công cho nó an toàn)

    push_all_to_onedrive(PATH)

if __name__ == '__main__':
    pass
    # push_all_to_onedrive(web='BATDONGSAN')