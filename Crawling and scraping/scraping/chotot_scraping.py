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

        print(page_source_raw['link'])
        data_general = {
            'link': page_source_raw['link']
        }

        displayed_data_container = {}
        # Title of post
        displayed_data_container['title'] = get_data_safe(soup, '.cd9gm5n > h1', return_text=True)
        # Sub info
        displayed_data_container['sub_info'] = get_data_safe(soup='.i1qen30x span', return_text=True)
        # Address
        displayed_data_container['address'] = get_data_safe(soup, '.bwq0cbs.flex-1', return_text=True)
        # Price
        displayed_data_container['price'] = get_data_safe(soup, '.slhwvq6 > .pyhk1dv', return_text=True)
        # Dienj tich
        displayed_data_container['dien_tich'] = get_data_safe(soup, '.slhwvq6 > .brnpcl3 > strong', return_text=True)
        # Describe
        describe_content = get_data_safe(soup, '.styles_adBody__vGW74', return_text=True)
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
        # imgs = get_data_safe(soup, "a[data-fslightbox='featured-gallery']", multi_value=True)
        # imgs = [get_data_safe(img, attr='href') for img in imgs]
        # imgs = [img for img in imgs if img is not None]
        # displayed_data_container['imgs'] = imgs
        # displayed_data_container['imgs'] = ';'.join(imgs)
        # Cần xử lí driver
        # imgs_base64 = get_base64_imgs(imgs)
        # binary_imgs = base64_to_binary(imgs_base64)
        # save_img(binary_imgs, file_name)


        characteris = get_data_safe(soup, '.a13uoc2z .abzctes', multi_value=True)
        for couple in characteris:
            key = get_data_safe(couple, '.a4ep88f', return_text=True)
            if not key: continue # if not exists then passs

            value = get_data_safe(couple, '.a3jfi3v', return_text=True)

            displayed_data_container[key.strip()] = value.strip()

        full_data = {}
        full_data.update(data_general)
        full_data.update(displayed_data_container)

        full_data_no_none = {k: v.replace("'", '"') for k, v in full_data.items() if v is not None}

        print_banner_colored(f'Scraping successful {file_name}!', 'success')
        return full_data_no_none
    except KeyboardInterrupt:
        sys.exit("NGẮT CHƯƠNG TRÌNH TỪ BÀN PHÍM !!")
    except Exception as e:
        print_banner_colored(f'Scraping failed {file_name}!', 'danger')
        print(e)
        return None


def main():
    client = clickhouse_connect.get_client(host='localhost', username='default')

    # Create database
    client.command('''
        CREATE DATABASE IF NOT EXISTS CHOTOT
    ''')

    client.command('USE CHOTOT')

    # Create table crawled
    client.command('''
        CREATE TABLE IF NOT EXISTS CHOTOT.RAW_DATA (
            `filename` String,                  -- Tên file lưu (để lấy ra so sánh cho nhanh)
            `time_scraping` String
        )
        ENGINE = MergeTree()
        PRIMARY KEY (`filename`);
    ''')

    columns = client.query('''DESCRIBE TABLE CHOTOT.RAW_DATA ''')
    columns = columns.result_columns[0]

    link_scraped = client.query('''
        SELECT r.filename
        FROM CHOTOT.RAW_DATA as r
    ''')

    link_scraped = link_scraped.result_columns[0] if link_scraped.result_columns else []

    for file_path in DATA_PATH_FUNC('CHOTOT').iterdir():
        if file_path.stem in link_scraped:
            continue
        
        with open(file_path, 'r') as file:
            data_page_source_raw = json.load(file)
            data_scraped = extract_one_page_source(data_page_source_raw, file_path.stem) 
            print(data_scraped)
            if data_scraped is None:
                continue
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
                        ALTER TABLE CHOTOT.RAW_DATA 
                        ADD COLUMN `{key}` Nullable(String)
                    ''')

                    data_values[index] = str(data_values[index])

            client.command(f'''INSERT INTO CHOTOT.RAW_DATA ({', '.join([f'`{key}`' for key in data_keys])}) VALUES ({', '.join([f"'{value}'" for value in data_values])})''')

            # Này thiết cột thì chạy lại không được ??
            # client.insert(
            #     table='CHOTOT.RAW_DATA',
            #     data=data_values,
            #     column_names=data_keys
            # )

    

def test():
    with open('./data/data_chotot/page_source/p1-l1_20250404-155753.json', 'r') as file:
        data = json.load(file)
        format_html_page_source(data['page_source'])
        # Chú ý cho time_scraped vào !!
        pprint.pprint(extract_one_page_source(data, 'helooooo'))


if __name__ == '__main__':
    main()
    # test()