import scrapy
from urllib.parse import urlencode
import os
from check_page_source.format import format_html_page_source
from msgraph_onedrive.operations import upload_file
from shared.globals import CHECKPOINTS_PATH, DATA_PATH_FUNC, DRIVER_PATH
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
from bs4 import BeautifulSoup
import random

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

def typing(text, include_typo=True):
    for char in text:
        delay = random.uniform(0.1, 0.4)
        pyautogui.typewrite(char, interval=delay)

def find_all_links(base_link):
    driver = get_driver()
    driver.get(f'{base_link}&pi={0}')

    # Lấy được number page cần
    try:
        button = driver.find_element(By.CSS_SELECTOR, '.see-more-btn .remain')
        remain_laptop = int(button.text)
    except Exception as e:
        print('ERROR: ', e)
        raise ValueError('KHÔNG TÌM THẤY BUTTON CLICK??')

    last_page = math.ceil(float(remain_laptop) / 20.0)
    new_url = f'{base_link}&pi={last_page}'

    # Thao tác thanh url -> load được page đó
    pyautogui.moveTo(520, 90)
    time.sleep(1)
    pyautogui.click()
    time.sleep(1)

    print(new_url)
    pyautogui.write(new_url, interval=0.5)
    pyautogui.press("enter")
    time.sleep(2)

    driver.refresh()
    time.sleep(2)

    # Nhận diện được khi nào nó hết load
    while True:
        try:
            element = driver.find_element(By.CSS_SELECTOR, '#preloader')
            style = element.get_attribute('style')
            if 'block' in style:
                time.sleep(4)
            elif 'none' in style:
                break
            else:
                raise ValueError('Block và None đều không phải, có khả năng đã thay đổi class!!')
        except KeyboardInterrupt:
            print_banner_colored('ĐÃ OUT VÌ KEYBOARD!')
        except ValueError as ve:
            print_banner_colored(ve, 'danger')
        except:
            time.sleep(4)
            print_banner_colored('Vẫn chưa load xong!', 'danger')
                

    # format_html_page_source(driver.page_source)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links_get_from_ps = get_data_safe(soup, '.__cate_44 > a', multi_value=True, attr='href')
    urls_extracted_from_links = ['https://www.thegioididong.com' + link for link in links_get_from_ps]
    print_banner_colored(f'LINK HIỆN ĐANG CÓ TRONG PAGE: {len(urls_extracted_from_links)}')
    for i in range(5):
        print(urls_extracted_from_links[i])

    driver.quit()

    return urls_extracted_from_links




class ThegioididongSpider(scrapy.Spider):
    name = "thegioididong"

    base_link = 'https://www.thegioididong.com/laptop#c=44&o=13'
    time_start_run_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    time_start_run_datetime = datetime.now()
    links_crawled = []
    page_crawled = []

    custom_settings = {
        'USER_AGENT': ua.random
    }

    def get_link_page(self, page_num):
        return f'{self.base_link}?pi={page_num}'
    
    def start_requests(self):
        print_banner_colored('ĐÃ VÀO THEGIOIDIDONG', 'success')

        # links = [
        #     'https://www.thegioididong.com/laptop/asus-vivobook-go-15-e1504fa-r5-nj776w',
        #     'https://www.thegioididong.com/laptop/hp-15-fc0085au-r5-a6vv8pa'
        # ]
        # links = []
        links = find_all_links(self.base_link)

        self.client = clickhouse_connect.get_client(host='localhost', username='default')
        # Create database
        self.client.command('''
            CREATE DATABASE IF NOT EXISTS THEGIOIDIDONG
        ''')

        self.client.command('USE THEGIOIDIDONG')
        # Create table crawled
        self.client.command('''
            CREATE TABLE IF NOT EXISTS THEGIOIDIDONG.CRAWLED_STATUS (
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
            OPTIMIZE TABLE THEGIOIDIDONG.CRAWLED_STATUS FINAL
        ''')

        # Get page minimun in pending status, then run from that page to inf
        page_not_crawled = self.client.query('''
            SELECT pcs.link
            FROM THEGIOIDIDONG.CRAWLED_STATUS AS pcs
            WHERE pcs.status = 0
        ''')
        
        self.page_crawl_not_done = page_not_crawled.result_columns[0] if page_not_crawled.result_columns else []

        # Get page crawled done
        page_crawled = self.client.query('''
            SELECT pcs.link
            FROM THEGIOIDIDONG.CRAWLED_STATUS AS pcs
            WHERE pcs.status = 1
        ''')

        self.page_crawl_done = page_crawled.result_columns[0] if page_crawled.result_columns else []

        # Column
        columns = self.client.query('''DESCRIBE TABLE THEGIOIDIDONG.CRAWLED_STATUS''')
        columns = columns.result_columns[0]

        # print('Not done: ', self.page_crawl_not_done)
        # print('Done: ', self.page_crawl_done)
        # print('Columns: ', columns)
        # Insert new
        links_new = []
        for i in range(len(links)):
            if links[i] not in self.page_crawl_done:
                links_new.append(links[i])
        # print('Link news: ', links_new)
        # for idx, link in enumerate(links_new):
        #     print(['NN', link, idx, 0, self.time_start_run_datetime])
        self.client.insert(
            table='THEGIOIDIDONG.CRAWLED_STATUS',
            data=[['NN', link, idx, 0, self.time_start_run_datetime] for idx, link in enumerate(links_new)], 
            column_names=columns
        )

        print_banner_colored("ĐẾN ĐÂY RỒI!", 'success')
        self.page_crawl_not_done.extend(links_new)
        # Start to run query
        for idx, link in enumerate(self.page_crawl_not_done):
            yield scrapy.Request(
                url=link,
                callback=functools.partial(self.handle_link, link_num=idx, url_origin=link)
            )

    def handle_link(self, response, link_num, url_origin):
        # print_banner_colored(f'Bắt đầu xử lí page_{page_num} link_{link_num} url_{url_origin}', 'wait')
        # format_html_page_source(response.text)   # Nếu cần check html
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
        with open(DATA_PATH_FUNC('thegioididong', file_name), 'w') as file:
            json.dump(data, file)

        # Lưu lại status lên Clickhouse
        status_data_crawled = [
            [file_name, link, link_num, 1, time_crawled]
        ]
        self.client.insert(
            table='THEGIOIDIDONG.CRAWLED_STATUS', 
            data=status_data_crawled, 
            column_names=['name', 'link', 'link_num', 'status', 'time_crawled']
        )

        # Lưu lại status ở local
        self.links_crawled.append(link)
        print_banner_colored(f'Đã xử lí link_{link_num}', 'success')

