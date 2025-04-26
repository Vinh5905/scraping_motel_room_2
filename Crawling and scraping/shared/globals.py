import os
import threading
from pathlib import Path

# Get terminal size -> print more beautiful :>
TERMINAL_WIDTH = os.get_terminal_size().columns

# CHECK HTML PAGE SOURCE
CHECK_FORMATTED_PAGE_SOURCE_PATH = Path('./check_page_source/formatted.html')

# CHECKPOINT PATH
CHECKPOINTS_PATH = {
    'BATDONGSAN': {
        'NAME': 'BATDONGSAN',
        # 'CHECKPOINT': Path('./data/checkpoints_batdongsan'),
        # 'CRAWL': Path('./data/checkpoints_batdongsan/previous_crawl_info.json'),
        # 'EXTRACT': Path('./data/checkpoints_batdongsan/previous_extract_info.json'),
        # 'LINK_LIST': Path('./data/checkpoints_batdongsan/previous_link_list.json'),
        'FOLDER_FRAUD_DETECTION_ENV_NAME': 'FOLDER_FRAUD_DETECTION_ID',
        'FOLDER_WEB_ENV_NAME': 'FOLDER_BATDONGSAN',
        'FOLDER_STORAGE_ID_ENV_NAME': 'FOLDER_BATDONGSAN_STORAGE_ID',
        'FOLDER_IMG_STORAGE_ID_ENV_NAME': 'FOLDER_BATDONGSAN_IMG_STORAGE_ID',
        'FOLDER_SCRAPING_ENV_NAME': 'FOLDER_BATDONGSAN_SCRAPING'
    },
    # 'CHOTOT': {
    #     'NAME': 'CHOTOT',
    #     'CHECKPOINT': Path('./data/checkpoints_chotot'),
    #     'CRAWL': Path('./data/checkpoints_chotot/previous_crawl_info.json'),
    #     'EXTRACT': Path('./data/checkpoints_chotot/previous_extract_info.json'),
    #     'LINK_LIST': Path('./data/checkpoints_chotot/previous_link_list.json')
    # }
}

# DATA PATH
ORIGINAL_PATH_FUNC = lambda web_name, name = '': Path(f'./data/data_{web_name.lower()}/' + name)
DATA_PATH_FUNC = lambda web_name, name = '': Path(f'./data/data_{web_name.lower()}/page_source/' + name)
IMG_PATH_FUNC = lambda web_name, name = '': Path(f'./data/data_{web_name.lower()}/images/' + name)

# ACCESS TOKEN PATH
ACCESS_TOKEN_PATH = Path('./data/access_token/access_token.json')
TOKEN_CACHE_PATH = Path('./data/access_token/token_cache.bin')

# DRIVER
DRIVER_PATH = lambda num: Path(f'/Users/hoangvinh/OneDrive/Workspace/Support/Driver/chromedriver-mac-x64_{str(num)}/chromedriver')

# COOKIES PATH
COOKIES_PATH = Path('./data/cookies/cookies.json')

MAX_WORKERS = 2
'''
# PROXIES
PROXIES_RAW_PATH = Path('./proxies/proxies_raw.txt')
PROXIES_VALID_PATH = Path('./proxies/proxies_valid.txt')

# Get proxies list
with open(PROXIES_RAW_PATH, 'r') as file:
    # Use splitlines() to split by lines without \n
    PROXIES_LIST = file.read().splitlines()


# LOCK
LOCK_DATA = threading.Lock()
LOCK_PREVIOUS_CRAWL = threading.Lock()
LOCK_LINK_LIST = threading.Lock()


# PATH EXTRACTED DATA
EXTRACTED_PATH = {
    'BATDONGSAN': {
        'FOLDER_CONTAINTER': Path('./data/all_extracted_data/save_extracted_batdongsan'),
        'ALL_EXTRACTED_DATA': Path('./data/all_extracted_data/save_extracted_batdongsan/data_batdongsan.csv'),
        'ALL_FILE_NAME_GET_SUCCESS': Path('./data/all_extracted_data/save_extracted_batdongsan/files_get_success.json')
    }
}

EXTRACTED_PATH_TEST = {
    'BATDONGSAN': {
        'FOLDER_CONTAINTER': Path('./data/all_extracted_data/save_extracted_batdongsan_test'),
        'ALL_EXTRACTED_DATA': Path('./data/all_extracted_data/save_extracted_batdongsan_test/data_batdongsan_test.csv'),
        'ALL_FILE_NAME_GET_SUCCESS': Path('./data/all_extracted_data/save_extracted_batdongsan_test/files_get_success.json')
    }
}


CHECKPOINTS_PATH_TEST = {
    'BATDONGSAN': {
        'NAME': 'BATDONGSAN',
        'CHECKPOINT': Path('./data/checkpoints_batdongsan_test'),
        'CRAWL': Path('./data/checkpoints_batdongsan_test/previous_crawl_info.json'),
        'EXTRACT': Path('./data/checkpoints_batdongsan_test/previous_extract_info.json'),
        'LINK_LIST': Path('./data/checkpoints_batdongsan_test/previous_link_list.json'),
        'FOLDER_FRAUD_DETECTION_ENV_NAME': 'FOLDER_FRAUD_DETECTION_ID_FOR_TEST',
        'FOLDER_WEB_ENV_NAME': 'FOLDER_BATDONGSAN_FOR_TEST',
        'FOLDER_STORAGE_ID_ENV_NAME': 'FOLDER_BATDONGSAN_STORAGE_ID_FOR_TEST',
        'FOLDER_IMG_STORAGE_ID_ENV_NAME': 'FOLDER_BATDONGSAN_IMG_STORAGE_ID_FOR_TEST',
        'FOLDER_SCRAPING_ENV_NAME': 'FOLDER_BATDONGSAN_SCRAPING_FOR_TEST'
    },
}
'''