from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from shared.globals import DRIVER_PATH, DATA_PATH_FUNC, MAX_WORKERS
from check_page_source.format import format_html_page_source
from pathlib import Path
from bs4 import BeautifulSoup
from shared.colorful import print_banner_colored
import clickhouse_connect
import json
from datetime import datetime
import sys
import time
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor

ua = UserAgent()

def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={ua.random}")
    # chrome_options.add_argument('--disable-web-security')
    # chrome_options.add_argument('--allow-running-insecure-content')
    # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # chrome_options.add_experimental_option("useAutomationExtension", False)
    # chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--headless')

    driver_num = 1
    chrome_service = Service(DRIVER_PATH(driver_num))

    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.implicitly_wait(5)

    return driver

def get_all_links(client):
    # Create folder
    father_folder = Path('./data/data_chotot')
    father_folder.mkdir(exist_ok=True)

    links_file = father_folder / 'status.json'

    # Get page minimun in pending status, then run from that page to inf
    existed_links_table = client.query('''
        SELECT cts.link
        FROM CHOTOT.CRAWLED_STATUS AS cts
    ''')
    
    existed_links = existed_links_table.result_columns[0] if existed_links_table.result_columns else []
    existed_links = set(existed_links)

    # Column
    columns = client.query('''DESCRIBE TABLE CHOTOT.CRAWLED_STATUS''')
    columns = columns.result_columns[0]

    # Code to run
    base_link = 'https://www.nhatot.com/thue-phong-tro-tp-ho-chi-minh?f=protection_entitlement'
    time_start_run_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    time_start_run_datetime = datetime.now()

    try:
        with open(links_file, 'r') as file:
            page_run = json.load(file)
            page_run = list(map(int, page_run))
    except:
        page_run = [0, 200]

    current_page = page_run[0] + 1
    last_page = page_run[1]
    print_banner_colored(f'Page sẽ chạy {page_run[0] + 1} - {page_run[1]}', 'big')

    while current_page <= last_page:
        try:
            driver = get_driver()

            # print_banner_colored(f'Start get links from page {current_page}', 'wait')

            link_page = f'{base_link}&page={current_page}'

            driver.get(link_page)
            page_source = driver.page_source
            format_html_page_source(page_source)
            soup = BeautifulSoup(page_source, 'html.parser')
            # links = soup.select('a.crd7gu7')
            links = soup.select('div[role="button"] li[itemprop="itemListElement"] > a')
            urls_extracted_from_links = ['https://www.nhatot.com' + link['href'] for link in links]

            if len(urls_extracted_from_links) == 0:
                print_banner_colored('KHÔNG TÌM THẤY LINK NÀO TRONG PAGE!!', 'danger')
                raise Exception()

            file_name_func = lambda a, b: f'p{a}-l{b}_{time_start_run_str}.json' 

            client.insert(
                table='CHOTOT.CRAWLED_STATUS',
                data=[[file_name_func(current_page, idx), link, 0, time_start_run_datetime] for idx, link in enumerate(urls_extracted_from_links) if link not in existed_links], 
                column_names=columns
            )

            with open(links_file, 'w') as file:
                json.dump([current_page, page_run[1]], file)

            query = client.query('''
                SELECT COUNT(*) FROM CHOTOT.CRAWLED_STATUS
            ''')

            count_all_links = query.result_columns[0][0]
            print_banner_colored(f'TOÀN BỘ LINK PAGE {current_page} -> TỔNG {count_all_links}: ', 'success')

            driver.quit()

            current_page += 1
        except KeyboardInterrupt:
            sys.exit("NGẮT CHƯƠNG TRÌNH TỪ BÀN PHÍM !!")
        except Exception as e:
            driver.quit()
            print(e)
            print_banner_colored(f'RERUN PAGE {current_page}')

def save_page_source(client, link, file_name):
    thread_id = threading.get_ident()
    print(f'[Thread-{thread_id}] Try: {file_name}')

    time_crawled = datetime.now()

    driver = get_driver()
    driver.get(link)

    data = {
        'link': link,
        'time_crawled': time_crawled.isoformat(),
        'page_source': driver.page_source
    }
    
    # Lưu page source local
    with open(DATA_PATH_FUNC('chotot', file_name), 'w') as file:
        json.dump(data, file)

    print(f"✅ [Thread-{thread_id}] Xong: {file_name}")

    # Lưu lại status lên Clickhouse
    status_data_crawled = [
        [file_name, link, 1, time_crawled]
    ]

    client.insert(
        table='CHOTOT.CRAWLED_STATUS', 
        data=status_data_crawled, 
        column_names=['name', 'link', 'status', 'time_crawled']
    )

def run():
    client = clickhouse_connect.get_client(host='localhost', username='default')

    client.command('''
        CREATE DATABASE IF NOT EXISTS CHOTOT
    ''')

    # Create table crawled
    client.command('''
        CREATE TABLE IF NOT EXISTS CHOTOT.CRAWLED_STATUS (
            name String,
            link String,
            status Bool,
            time_crawled DateTime('Asia/Ho_Chi_Minh')
        )
        ENGINE = ReplacingMergeTree(time_crawled)
        PRIMARY KEY link
    ''')

    # GET LINKS
    answer = input('Need to run get links again? Y/N :            ')
    if answer.lower() == 'y':
        get_all_links(client)

    # Merge replace old -> new
    client.command('''
        OPTIMIZE TABLE CHOTOT.CRAWLED_STATUS FINAL
    ''')

    # Get page minimun in pending status, then run from that page to inf
    link_crawled_table = client.query('''
        SELECT pcs.name, pcs.link
        FROM CHOTOT.CRAWLED_STATUS AS pcs
        WHERE pcs.status = 0
    ''')
    
    names_crawled = link_crawled_table.result_columns[0] if link_crawled_table.result_columns else []
    links_crawled = link_crawled_table.result_columns[1] if link_crawled_table.result_columns else []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:    
        futures = []
        for idx, link in enumerate(links_crawled):
            name = names_crawled[idx]
            # print(f"📦 Gửi task: {link} -> {name}")
            futures.append(executor.submit(save_page_source, client, link, name))
            # futures = ([executor.submit(save_page_source, link, names_crawled[idx]) for idx, link in enumerate(links_crawled)])
        for future in as_completed(futures):
            future.result()

if __name__ == '__main__':
    run()