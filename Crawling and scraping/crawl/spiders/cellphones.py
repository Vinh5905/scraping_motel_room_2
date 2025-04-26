import scrapy
from urllib.parse import urlencode
import os
from check_page_source.format import format_html_page_source
from msgraph_onedrive.operations import upload_file
from shared.globals import CHECKPOINTS_PATH, DATA_PATH_FUNC, DRIVER_PATH, ORIGINAL_PATH_FUNC
from shared.colorful import print_banner_colored
from shared.support_func import get_data_safe
import dotenv
import time
from datetime import datetime
import json
import clickhouse_connect
import functools
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
import math
import pyautogui
import sys
import re
from bs4 import BeautifulSoup
from scrapy_splash import SplashRequest 
from scrapy_selenium import SeleniumRequest
from selenium.common.exceptions import ElementClickInterceptedException
from scrapy.exceptions import CloseSpider
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By



from fake_useragent import UserAgent
ua = UserAgent()

def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={ua.random}")
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--headless')

    driver_num = 1
    chrome_service = Service(DRIVER_PATH(driver_num))

    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.implicitly_wait(5)

    return driver

def get_link_page(base_link, page_num):
    return f'{base_link}&pi={page_num}'
# .block-product-list-filter .button__show-more-product  -->  Không tồn tại là oke

def get_all_links(base_link):
    driver = get_driver()
    driver.get(base_link)

    remain = -1
    while True:
        try:
            try:
                button = driver.find_element(By.CSS_SELECTOR, '.block-product-list-filter .button__show-more-product')
                print_banner_colored('Found button!', 'success')
                # remain = int(re.sub(r'[\s\w]*(\d+)[\s\w]*', r"\1", button.text))
                remain = int(re.search(r'\d+', button.text).group())
                print_banner_colored(f'Xem thêm {remain}', 'small')
                try:
                    button.click()
                    print_banner_colored('Clicked button', 'success')
                    time.sleep(3)
                except ElementClickInterceptedException:
                    print_banner_colored('Bị popup!', 'danger')
                    time.sleep(4)
                    cancel_button = driver.find_element(By.CSS_SELECTOR, 'button.cancel-button-top')
                    cancel_button.click()
                    time.sleep(4)
                except Exception as e:
                    print_banner_colored(e, 'danger')
                    time.sleep(2)
                    continue
            except:
                time.sleep(1)
                if remain == -1:
                    continue
                if remain <= 20:
                    break
                
                print_banner_colored(f'VẪN CHƯA CHẠY HẾT TOÀN BỘ, CÒN LẠI {remain}', 'danger')
                raise Exception(f'VẪN CHƯA CHẠY HẾT TOÀN BỘ, CÒN LẠI {remain}')
        except KeyboardInterrupt:
            exit(1)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = get_data_safe(soup, '.product-info-container.product-item > .product-info > a', multi_value=True, attr='href')
    # with open(ORIGINAL_PATH_FUNC('cellphones', 'links.json'), 'w') as file:
    #     json.dump(links, file)
    print_banner_colored(f'HOÀN TẤT LẤY ĐƯỢC {len(links)} LINKS', 'success')

    driver.quit()
    return links
    
class CellphonesSpider(scrapy.Spider):
    name = "cellphones"

    base_link = 'https://cellphones.com.vn/laptop.html'
    time_start_run_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    time_start_run_datetime = datetime.now()

    custom_settings = {
        'USER_AGENT': ua.random
    }
    
    def start_requests(self):
        print_banner_colored('ĐÃ VÀO CELLPHONES', 'success')
        
        answer = input('Need to run get links again? Y/N :            ')
        if answer.lower() == 'y':
            get_all_links(self.base_link)
        exit(1)
        with open(ORIGINAL_PATH_FUNC('cellphones', 'links.json'), 'r') as file:
            links = json.load(file)
        # print_banner_colored('USE SELENIUM GET NEW LINKS', 'big')
        # links = get_all_links(self.base_link)

        self.client = clickhouse_connect.get_client(host='localhost', username='default')
        # Create database
        self.client.command('''
            CREATE DATABASE IF NOT EXISTS CELLPHONES
        ''')

        self.client.command('USE CELLPHONES')
        # Create table crawled
        self.client.command('''
            CREATE TABLE IF NOT EXISTS CELLPHONES.CRAWLED_STATUS (
                name String,
                link String,
                link_num UInt32,
                status Bool,
                time_crawled DateTime('Asia/Ho_Chi_Minh')
            )
            ENGINE = ReplacingMergeTree(time_crawled)
            PRIMARY KEY link
        ''')

        # Merge replace old -> new
        self.client.command('''
            OPTIMIZE TABLE CELLPHONES.CRAWLED_STATUS FINAL
        ''')

        # Get page minimun in pending status, then run from that page to inf
        page_not_crawled = self.client.query('''
            SELECT pcs.link
            FROM CELLPHONES.CRAWLED_STATUS AS pcs
            WHERE pcs.status = 0
        ''')
        
        self.page_crawl_not_done = page_not_crawled.result_columns[0] if page_not_crawled.result_columns else []

        # Get page crawled done
        page_crawled = self.client.query('''
            SELECT pcs.link
            FROM CELLPHONES.CRAWLED_STATUS AS pcs
            WHERE pcs.status = 1
        ''')

        self.page_crawl_done = page_crawled.result_columns[0] if page_crawled.result_columns else []

        # Column
        columns = self.client.query('''DESCRIBE TABLE CELLPHONES.CRAWLED_STATUS''')
        columns = columns.result_columns[0]

        # Link đã lấy từ url gốc mà chưa có trong DB
        links_new = []
        for i in range(len(links)):
            if links[i] not in self.page_crawl_done and links[i] not in self.page_crawl_not_done:
                links_new.append(links[i])

        # 
        self.client.insert(
            table='CELLPHONES.CRAWLED_STATUS',
            data=[['NN', link, idx, 0, self.time_start_run_datetime] for idx, link in enumerate(links_new)], 
            column_names=columns
        )
        
        self.page_crawl_not_done.extend(links_new)

        # Start to run query
        for idx, link in enumerate(self.page_crawl_not_done):
            yield SeleniumRequest(
                url=link,
                callback=functools.partial(self.handle_link, link_num=idx, url_origin=link)
            )

    def handle_link(self, response, link_num, url_origin):
        driver = response.request.meta["driver"]
        
        element = driver.find_element(By.CSS_SELECTOR, ".end-marker")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)

        for i in range(1, 10):
            ActionChains(driver).scroll_by_amount(0, 10000).perform()
            time.sleep(1)
        # print_banner_colored(f'Bắt đầu xử lí page_{page_num} link_{link_num} url_{url_origin}', 'wait')
        if ('https://wafcompute-sg-proxy.byteintlapi.com' in response.text):
            print_banner_colored(f'STATUS {response.status} - DÍNH CATPCHA!!', 'danger')
            raise CloseSpider()
        
        time_crawled = datetime.now()
        link = url_origin

        data = {
            'link': link,
            'time_crawled': time_crawled.isoformat(),
            'page_source': response.text
        }
        
        file_name = f'l{link_num}_{self.time_start_run_str}.json' 

        # Lấy html ném vào OneDrive
        # save_page_source(file_name, data, CHECKPOINTS_PATH['BATDONGSAN'])

        # Lưu page source local
        with open(DATA_PATH_FUNC('cellphones', file_name), 'w') as file:
            json.dump(data, file)

        # Lưu lại status lên Clickhouse
        status_data_crawled = [
            [file_name, link, link_num, 1, time_crawled]
        ]
        self.client.insert(
            table='CELLPHONES.CRAWLED_STATUS', 
            data=status_data_crawled, 
            column_names=['name', 'link', 'link_num', 'status', 'time_crawled']
        )

        # Lưu lại status ở local
        print_banner_colored(f'Đã lấy thành công page source của {file_name}', 'success')