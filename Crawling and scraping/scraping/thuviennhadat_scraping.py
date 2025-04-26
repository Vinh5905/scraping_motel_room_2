from bs4 import BeautifulSoup
from shared.colorful import print_banner_colored
from shared.support_func import string_to_dict, get_data_safe
from shared.globals import IMG_PATH_FUNC, DATA_PATH_FUNC
import re
import sys
import json
import clickhouse_connect
import pprint
from check_page_source.format import format_html_page_source
from datetime import datetime


def extract_one_page_source(page_source_raw, file_name):
    page_source_data = page_source_raw['page_source']
    format_html_page_source(page_source_data)

    try:
        if page_source_data == '':
            print('Page source no value???')
            raise ValueError()
    
        soup = BeautifulSoup(page_source_data, 'html.parser')
    # DATA GENERAL
        print(file_name)
        print(page_source_raw['link'])
        data_general = {
            'link': page_source_raw['link']
        }

    # DATA SHOW IN UI (everything you see when open website - ABOUT PRODUCT)
        displayed_data_container = {}
        # Title of post
        displayed_data_container['title'] = get_data_safe(soup, '#title', return_text=True)
        # Address
        displayed_data_container['address'] = get_data_safe(soup, '#title-section p', return_text=True)
        # Describe
        describe_content = get_data_safe(soup, 'aside.ui.segment > section.KinhDoanhNhaDat-detail-header-title + p', return_text=True)
        # print(displayed_data_container['describe'])
        describe_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+", flags=re.UNICODE)
        displayed_data_container['describe'] = describe_pattern.sub(r'', describe_content) # no emoji
        displayed_data_container['describe'] = re.sub("'", '"', displayed_data_container['describe'])

        # Image
        imgs = get_data_safe(soup, "a[data-fslightbox='featured-gallery']", multi_value=True)
        imgs = [get_data_safe(img, attr='href') for img in imgs]
        imgs = [img for img in imgs if img is not None]
        # displayed_data_container['imgs'] = imgs
        displayed_data_container['imgs'] = ';'.join(imgs)
        # Cần xử lí driver
        # imgs_base64 = get_base64_imgs(imgs)
        # binary_imgs = base64_to_binary(imgs_base64)
        # save_img(binary_imgs, file_name)

        # Example in ./image/example/a.png
        a = get_data_safe(soup, 'div.ui.horizontal.borderless.segments > div', multi_value=True)
        for couple in a:
            key = get_data_safe(couple, '.unit-name-style', return_text=True)
            if not key: continue # if not exists then passs

            value = get_data_safe(couple, '.unit-value-style', return_text=True)

            displayed_data_container[key.strip()] = value.strip()

        # Example in ./image/example/b.png
        b = get_data_safe(soup, '.KinhDoanhNhaDat-detail-grid-amenitites .column.info-estate', multi_value=True)
        for couple in b:
            key = get_data_safe(couple, '.unit-name-style', return_text=True)
            if not key: continue # if not exists then passs

            value = get_data_safe(couple, '.floated.end', return_text=True)

            displayed_data_container[key.strip()] = value.strip()

        # Example in ./image/example/c.png
        c = get_data_safe(soup, '.mobile-display-none div.four.wide.column', multi_value=True)
        for couple in c:
            key = get_data_safe(couple, '.text-muted', return_text=True)
            if not key: continue # if not exists then passs

            value = get_data_safe(couple, '.text-muted + div', return_text=True)

            displayed_data_container[key.strip()] = value.strip()

        # pprint.pprint(displayed_data_container)

        full_data = {}
        full_data.update(data_general)
        full_data.update(displayed_data_container)

        full_data_no_none = {k: v for k, v in full_data.items() if v is not None}

        print_banner_colored(f'Scraping successful {file_name}!', 'success')
        return full_data_no_none
    except KeyboardInterrupt:
        sys.exit("NGẮT CHƯƠNG TRÌNH TỪ BÀN PHÍM !!")
    except Exception as e:
        print_banner_colored(f'Scraping failed {file_name}!', 'danger')
        raise e


def main():
    client = clickhouse_connect.get_client(host='localhost', username='default')

    # Create database
    client.command('''
        CREATE DATABASE IF NOT EXISTS THUVIENNHADAT
    ''')

    client.command('USE THUVIENNHADAT')

    # Create table crawled
    client.command('''
        CREATE TABLE IF NOT EXISTS THUVIENNHADAT.RAW_DATA (
            `filename` String,                  -- Tên file lưu (để lấy ra so sánh cho nhanh)
            `time_scraping` String
        )
        ENGINE = MergeTree()
        PRIMARY KEY (`filename`);
    ''')

    columns = client.query('''DESCRIBE TABLE THUVIENNHADAT.RAW_DATA ''')
    columns = columns.result_columns[0]

    link_scraped = client.query('''
        SELECT r.filename
        FROM THUVIENNHADAT.RAW_DATA as r
    ''')

    link_scraped = link_scraped.result_columns[0] if link_scraped.result_columns else []

    for file_path in DATA_PATH_FUNC('thuviennhadat').iterdir():
        if file_path.stem in link_scraped:
            continue
        
        with open(file_path, 'r') as file:
            data_page_source_raw = json.load(file)
            data_scraped = extract_one_page_source(data_page_source_raw, file_path.stem) 
            data_scraped.update({
                'filename': file_path.stem,
                'time_scraping': datetime.now()
            })

            data_keys = list(data_scraped.keys())
            data_values = list(data_scraped.values())

            for index, key in enumerate(data_keys):
                if key not in columns:
                    columns.append(key)

                    client.command(f'''
                        ALTER TABLE THUVIENNHADAT.RAW_DATA 
                        ADD COLUMN `{key}` Nullable(String)
                    ''')

                    data_values[index] = str(data_values[index])

            client.command(f'''INSERT INTO THUVIENNHADAT.RAW_DATA ({', '.join([f'`{key}`' for key in data_keys])}) VALUES ({', '.join([f"'{value}'" for value in data_values])})''')

            # Này thiết cột thì chạy lại không được ??
            # client.insert(
            #     table='THUVIENNHADAT.RAW_DATA',
            #     data=data_values,
            #     column_names=data_keys
            # )

    

def test():
    with open('./data/data_thuviennhadat/page_source/p80-l6_20250321-114439.json', 'r') as file:
        data = json.load(file)
        format_html_page_source(data['page_source'])
        # Chú ý cho time_scraped vào !!
        pprint.pprint(extract_one_page_source(data, 'helooooo'))


if __name__ == '__main__':
    main()
    # test()