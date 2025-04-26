import scrapy
from urllib.parse import urlencode
import os
from check_page_source.format import format_html_page_source
from msgraph_onedrive.operations import upload_file
from shared.globals import CHECKPOINTS_PATH, DATA_PATH_FUNC
from shared.colorful import print_banner_colored
import dotenv
import time
from datetime import datetime
import json
import clickhouse_connect
import functools
from scrapy_splash import SplashRequest 

def get_scrapeops_url(url):
    API_KEY = '4a213a0c-2197-4636-a6a2-283390c3b658'
    payload = {'api_key': API_KEY, 'url': url}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url

def get_link_page(page_num):
    base_link = 'http://batdongsan.com.vn/cho-thue-nha-tro-phong-tro-tp-hcm'
    if page_num == 1: 
        # Keep origin because page 1 is as same as base link
        return f'{base_link}?vrs=1'
    else: 
        return f'{base_link}/p{page_num}?vrs=1'

def save_page_source(file_name, data, PATH):
    dotenv.load_dotenv()
    folder_storage = os.getenv(PATH['FOLDER_STORAGE_ID_ENV_NAME'])

    # Nếu để name là link thì sẽ fail vì có nhiều kí tự đặc biệt
    upload_file(folder_storage, file_name, data_upload=data, type='replace')
    print_banner_colored(file_name, 'success')


class BatdongsanSpider(scrapy.Spider):
    name = "batdongsan"

    limit_page_run = 1
    actived_page_count = 0
    pending_request_count = {}
    time_start_run_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    latest_page = 1
    links_crawled = []
    page_crawled = []
    
    def start_requests(self):
        self.client = clickhouse_connect.get_client(host='localhost', username='default')
        # Create database
        self.client.command('''
            CREATE DATABASE IF NOT EXISTS STATUS_BATDONGSAN
        ''')

        self.client.command('USE STATUS_BATDONGSAN')
        # Create table crawled
        self.client.command('''
            CREATE TABLE IF NOT EXISTS STATUS_BATDONGSAN.CRAWLED (
                name String,
                link String,
                page_num UInt32,
                link_num UInt32,
                time_crawled DateTime('Asia/Ho_Chi_Minh')
            )
            ENGINE = ReplacingMergeTree(time_crawled)
            PRIMARY KEY link
        ''')
        # Create table page crawl status
        self.client.command('''
            CREATE TABLE IF NOT EXISTS STATUS_BATDONGSAN.PAGE_CRAWL_STATUS (
                page_num UInt32,
                status Enum8('pending' = 0, 'done' = 1),
                time_crawled DateTime('Asia/Ho_Chi_Minh')
            )
            ENGINE = ReplacingMergeTree(time_crawled)
            PRIMARY KEY page_num
        ''')
        print_banner_colored('tạo xong db rồi!', 'success')

        # Merge replace old -> new
        self.client.command('''
            OPTIMIZE TABLE STATUS_BATDONGSAN.CRAWLED FINAL
        ''')

        # Get page minimun in pending status, then run from that page to inf
        start_page = self.client.query('''
            SELECT MIN(pcs.page_num)
            FROM STATUS_BATDONGSAN.PAGE_CRAWL_STATUS AS pcs
            WHERE pcs.status = 'pending'
        ''')
        
        if start_page.result_columns[0][0] != 0: self.latest_page = start_page.result_columns[0][0]

        # Get page crawled done
        page_crawled = self.client.query('''
            SELECT pcs.page_num
            FROM STATUS_BATDONGSAN.PAGE_CRAWL_STATUS AS pcs
            WHERE pcs.status = 'done'
        ''')

        self.page_crawl_done = page_crawled.result_columns[0] if page_crawled.result_columns else []

        # Get all links crawled before
        links_crawled = self.client.query('''
            SELECT c.link
            FROM STATUS_BATDONGSAN.CRAWLED as c
        ''')

        self.links_crawled = links_crawled.result_columns[0] if links_crawled.result_columns else []

        # Start to run query
        print_banner_colored('Bắt đầu run page request', 'wait')
        for _ in range(self.limit_page_run):
            yield self.page_request()

        
    def page_request(self):
        if self.actived_page_count < self.limit_page_run:
            print_banner_colored(f'Bắt đầu xử lí page request {self.latest_page}', 'wait')

            while self.latest_page in self.page_crawled:
                self.latest_page += 1

            page_num = self.latest_page
            self.latest_page += 1 # Lần tiếp theo
            
            # + 1 page đang hoạt động -> giới hạn page
            self.actived_page_count += 1

            # Update pending status
            status_data_page_pending = [
                [page_num, 'pending', datetime.now()] # k xài .isoformat() vì clickhouse yêu cầu DateTime, not string
            ]
            self.client.insert(
                table='STATUS_BATDONGSAN.PAGE_CRAWL_STATUS', 
                data=status_data_page_pending, 
                column_names=['page_num', 'status', 'time_crawled']
            )

            page_url = get_link_page(page_num)
            scrapeops_page_url = get_scrapeops_url(page_url)
            return scrapy.Request(
                url=scrapeops_page_url,
                callback=functools.partial(self.handle_page, page_num=page_num)
            )
        else:
            pass
            # for _ in range(self.limit_page_run - self.actived_page_count):
            #     yield self.page_request()
    
    def handle_page(self, response, page_num):
        # print(response.text)
        # print_banner_colored('Xử lí page', 'wait')
        print_banner_colored(f'Hoàn tất lấy links page_{page_num}', 'success')
        links = response.css('.js__card.js__card-full-web > .js__product-link-for-product-id')
        urls_extracted_from_links = ['https://batdongsan.com.vn' + link.attrib['href'] for link in links]

        self.pending_request_count[page_num] = len(urls_extracted_from_links)

        for index, url in enumerate(urls_extracted_from_links):
            # Nếu nằm trong đống link cũ thì continue và giảm pending
            if url in self.links_crawled:
                self.pending_request_count[page_num] -= 1
                continue

            scrapeops_link_url = get_scrapeops_url(url)
            yield scrapy.Request(
                url=scrapeops_link_url,
                # callback=lambda response: self.handle_link(response, page_num, index, url) # lỗi closure lambda vì lambda tham chiếu đến các giá trị đó -> Đến lúc gọi thì nó chạy cái cuối cùng
                callback=functools.partial(self.handle_link, page_num=page_num, link_num=index, url_origin=url) # lưu giá trị thực
            )
        
    def handle_link(self, response, page_num, link_num, url_origin):
        print_banner_colored(f'Bắt đầu xử lí page_{page_num} link_{link_num} url_{url_origin}', 'wait')
        # format_html_page_source(response.text)   # Nếu cần check html
        time_crawled = datetime.now()
        link = url_origin

        data = {
            'link': link,
            'time_crawled': time_crawled.isoformat(),
            'page_source': response.text
        }
        
        file_name = f'p{page_num}-l{link_num}_{self.time_start_run_str}.json' 

        # Lấy html ném vào OneDrive
        # save_page_source(file_name, data, CHECKPOINTS_PATH['BATDONGSAN'])

        # Lưu page source local
        with open(DATA_PATH_FUNC('batdongsan', file_name), 'w') as file:
            json.dump(data, file)

        # Lưu lại status lên Clickhouse
        status_data_crawled = [
            [file_name, link, page_num, link_num, time_crawled]
        ]
        self.client.insert(
            table='STATUS_BATDONGSAN.CRAWLED', 
            data=status_data_crawled, 
            column_names=['name', 'link', 'page_num', 'link_num', 'time_crawled']
        )

        # Lưu lại status ở local
        self.links_crawled.append(link)
        print_banner_colored(f'Đã xử lí page_{page_num} link_{link_num}', 'success')

        # Giảm pending link
        self.pending_request_count[page_num] -= 1

        # Nếu toàn bộ link trong trang đó xong -> chuyển trang
        if self.pending_request_count[page_num] == 0:
            # Update status done cho page_num cho local
            self.page_crawled.append(page_num)

            # Update status done cho page_num trên Clickhouse
            status_data_page_crawled = [
                [page_num, 'done', time_crawled]
            ]
            self.client.insert(
                table='STATUS_BATDONGSAN.PAGE_CRAWL_STATUS', 
                data=status_data_page_crawled, 
                column_names=['page_num', 'status', 'time_crawled']
            )

            self.actived_page_count -= 1
            del self.pending_request_count[page_num]
            
            # Bắt đầu 1 trang khác (chắc chắn được vì active page giảm)
            yield self.page_request()