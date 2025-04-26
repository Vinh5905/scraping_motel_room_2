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

# CRAWL PHẢI SỬ DỤNG scrapy-splash ĐỂ KHÔNG BỊ MẤT MỘT SỐ THÔNG TIN (K CHẮC LÀ PHẢI ĐỢI BAO LÂU)

def save_img(binary_imgs, name):
    folder_path = IMG_PATH_FUNC(name)
    print()
    folder_path.mkdir(exist_ok=True)

    for index, binary_img in enumerate(binary_imgs):
        with open(folder_path / str(index), 'wb') as file:
            file.write(binary_img)

def extract_one_page_source(page_source_raw, file_name):
    page_source_data = page_source_raw['page_source']
    format_html_page_source(page_source_data)

    try:
        if page_source_data == '':
            print('Page source no value???')
            raise ValueError()
    
        soup = BeautifulSoup(page_source_data, 'html.parser')
    # DATA GENERAL
        data_general = {
            'link': page_source_raw['link']
        }


        # CHECK REQUEST NEW OR OLD HTML
        new_html = False
        try:
            element_testing_data = soup.select_one('.re__pr-title.pr-title.js__pr-title')
            element_testing_data.get_text()
            new_html =True
        except:
            new_html = False


        if new_html:
        # DATA SHOW IN UI (everything you see when open website - ABOUT PRODUCT)
            displayed_data_container = {}
            # Title of post
            displayed_data_container['title'] = get_data_safe(soup, '.re__pr-title.pr-title.js__pr-title', return_text=True)
            # Address
            displayed_data_container['address'] = get_data_safe(soup, '.re__pr-short-description.js__pr-address', return_text=True)
            # Vertified from batdongsan
            displayed_data_container['verified'] = get_data_safe(soup, '.re__pr-stick-listing-verified') is not None
            # Describe
            displayed_data_container['describe'] = get_data_safe(soup, '.re__detail-content', return_text=True)
            # Image
            imgs = get_data_safe(soup, '.swiper-slide.js__media-item-container div.re__pr-image-cover', multi_value=True)
            imgs = [get_data_safe(img, attr='style') or get_data_safe(img, attr='data-bg') for img in imgs]
            imgs = [img for img in imgs if img is not None]
            for index in range(len(imgs)):
                imgs[index] = re.sub(r'"', r"'", imgs[index])
                imgs[index] = re.sub(r"[\s\S]+(url\('([\s\S]+)'\))[\s\S]*", r"\2", imgs[index])
            # displayed_data_container['imgs'] = imgs
            displayed_data_container['imgs'] = ';'.join(imgs)
            # Cần xử lí driver
            # imgs_base64 = get_base64_imgs(imgs)
            # binary_imgs = base64_to_binary(imgs_base64)
            # save_img(binary_imgs, file_name)

            # Example in ./image/example/a.png
            a = get_data_safe(soup, '.re__pr-short-info-item.js__pr-short-info-item', multi_value=True)
            for couple in a:
                key = get_data_safe(couple, '.title', return_text=True)
                if not key: continue # if not exists then passs

                value = get_data_safe(couple, '.value', return_text=True)
                # Some post have ext info below
                ext = get_data_safe(couple, '.ext', return_text=True)
                
                displayed_data_container[key] = value
                displayed_data_container[key + ' ' + 'ext'] = ext

            # Example in ./image/example/b.png
            b = get_data_safe(soup, '.re__pr-specs-content-item', multi_value=True)
            for couple in b:
                key = get_data_safe(couple, '.re__pr-specs-content-item-title', return_text=True)
                if not key: continue # if not exists then passs

                value = get_data_safe(couple, '.re__pr-specs-content-item-value', return_text=True)

                displayed_data_container[key] = value

            # Example in ./image/example/c.png
            c = get_data_safe(soup, '.re__pr-short-info-item.js__pr-config-item', multi_value=True)
            for couple in c:
                key = get_data_safe(couple, '.title', return_text=True)
                if not key: continue # if not exists then passs

                value = get_data_safe(couple, '.value', return_text=True)

                displayed_data_container[key] = value  

            # pprint.pprint(displayed_data_container)

        # DATA IN SCRIPT ELEMENT (NOT SHOW IN UI - ABOUT PRODUCT) - see in ./image/example/undisplayed_data.png
            # Get data inside all script elements
            script_elements = get_data_safe(soup, 'script[type="text/javascript"]', multi_value=True, return_text=True) # script
            undisplayed_data_container = '' # contain text inside script
            for script in script_elements:
                # print(script)
                # If conditions is correct then that is element we need (only one exists)
                if script.find('getListingRecommendationParams') != -1:
                    undisplayed_data_container = script
                    break
            # Position of the dict we need in type string (start - end)
            undisplayed_text_start = 0
            undisplayed_text_end = 0
            # You can see picture to know why
            for i in range(len(undisplayed_data_container)):
                # get nearest {
                if undisplayed_data_container[i] == '{': 
                    undisplayed_text_start = i
                # get first }
                if undisplayed_data_container[i] == '}':
                    undisplayed_text_end = i
                    break
            # Get dict but in type string
            undisplayed_in_curly_braces = undisplayed_data_container[undisplayed_text_start:(undisplayed_text_end + 1)]
            # Change to dict
            undisplayed_info = string_to_dict(undisplayed_in_curly_braces)

            # pprint.pprint(undisplayed_info)

        # DATA IN SCRIPT ELEMEMENT (CAN SHOW SOME IN UI - ABOUT LANDLORD) - see in ./image/example/landlord.png
            landlord_data_container = ''
            for script in script_elements:
                if script.find('FrontEnd_Product_Details_ContactBox') != -1:
                    landlord_data_container = script
                    break
            
            # Set start from {  (see image to understand why)
            landlord_text_start = landlord_data_container.index('window.FrontEnd_Product_Details_ContactBox')
            landlord_text_start = landlord_data_container.find('{', landlord_text_start)
            landlord_text_end = 0

            landlord_container_from_first_curly_braces = landlord_data_container[landlord_text_start:]

            # Try to find } close dict, use stack to find
            array = [] # contain { } , as same as stack
            for i in range(len(landlord_container_from_first_curly_braces)):
                if landlord_container_from_first_curly_braces[i] == '{': 
                    array.append(landlord_container_from_first_curly_braces[i])
                if landlord_container_from_first_curly_braces[i] == '}':
                    array.pop()
                    if len(array) == 0:
                        landlord_text_end = i + 1
                        break

            landlord_in_curly_braces = landlord_container_from_first_curly_braces[0:landlord_text_end] 

            # Error parseInt when change to dict, so erase it - see image to know where is it
            landlord_in_curly_braces = re.sub(r'(parseInt\(("(\d+)")\))', r'\3', landlord_in_curly_braces)  

            # Change to dict
            landlord_info = string_to_dict(landlord_in_curly_braces)

            # Get many key, but only some can be used
            key_needed = ['nameSeller', 'emailSeller', 'userId']
            landlord_needed_info = {key: value for key, value in landlord_info.items() if key in key_needed}

            # pprint.pprint(landlord_info)
            # print(now)

            full_data = {}
            full_data.update(data_general)
            full_data.update(undisplayed_info)
            full_data.update(landlord_needed_info)
            full_data.update(displayed_data_container)

            full_data_no_none = {k: v for k, v in full_data.items() if v is not None}

# Trường hợp old
        else:
        # DATA SHOW IN UI (everything you see when open website - ABOUT PRODUCT)
            displayed_data_container = {}
            # Title of post
            displayed_data_container['title'] = get_data_safe(soup, '.js__product-title', return_text=True)
            # Address
            displayed_data_container['address'] = get_data_safe(soup, '.js__product-address', return_text=True)
            # Vertified from batdongsan
            displayed_data_container['verified'] = get_data_safe(soup, '.re__pr-stick-listing-verified') is not None
            # Describe
            displayed_data_container['describe'] = get_data_safe(soup, '.re__detail-content', return_text=True)
            # Image
            imgs = get_data_safe(soup, '.swiper-slide.js__media-item-container div.re__pr-image-cover', multi_value=True)
            imgs = [get_data_safe(img, attr='style') or get_data_safe(img, attr='data-bg') for img in imgs]
            imgs = [img for img in imgs if img is not None]
            for index in range(len(imgs)):
                imgs[index] = re.sub(r'"', r"'", imgs[index])
                imgs[index] = re.sub(r"[\s\S]+(url\('([\s\S]+)'\))[\s\S]*", r"\2", imgs[index])
            # displayed_data_container['imgs'] = imgs
            displayed_data_container['imgs'] = ';'.join(imgs)
            # Cần xử lí driver
            # imgs_base64 = get_base64_imgs(imgs)
            # binary_imgs = base64_to_binary(imgs_base64)
            # save_img(binary_imgs, file_name)

            # Example in ./image/example/a.png
            a = get_data_safe(soup, '.re__list-info > ul > li', multi_value=True)
            for couple in a:
                key = get_data_safe(couple, '.re__text', return_text=True)
                if not key: continue # if not exists then passs

                value = get_data_safe(couple, '.re__txt-content > .re__f-big', return_text=True)
                # Some post have ext info below
                ext = get_data_safe(couple, '.re__txt-content > re__f-none', return_text=True)

                displayed_data_container[key] = value
                displayed_data_container[key + ' ' + 'ext'] = ext

            # Example in ./image/example/b.png
            b = get_data_safe(soup, '.re__pr-specs-content-item', multi_value=True)
            for couple in b:
                key = get_data_safe(couple, '.re__pr-specs-content-item-title', return_text=True)
                if not key: continue # if not exists then passs

                value = get_data_safe(couple, '.re__pr-specs-content-item-value', return_text=True)

                displayed_data_container[key] = value
                
            # Example in ./image/example/c.png
            c = get_data_safe(soup, 'ul.re__product-info > li', multi_value=True)
            for couple in c:
                key = get_data_safe(couple, '.re__sp1', return_text=True)
                if not key: continue # if not exists then passs

                value = get_data_safe(couple, '.re__sp3', return_text=True)

                displayed_data_container[key] = value

            # pprint.pprint(displayed_data_container)

        # DATA IN SCRIPT ELEMENT (NOT SHOW IN UI - ABOUT PRODUCT) - see in ./image/example/undisplayed_data.png
            # Get data inside all script elements
            script_elements = get_data_safe(soup, 'script[type="text/javascript"]', multi_value=True, return_text=True) # script
            undisplayed_data_container = '' # contain text inside script
            for script in script_elements:
                # print_banner_colored('BÀI SCRIPT', 'success')
                # print(script)
                # If conditions is correct then that is element we need (only one exists)
                if script.find('initListingHistoryLazy') != -1:
                    undisplayed_data_container = script[script.find('getListingRecommendationParams'):]
                    # pprint.pprint('TÌM: ', undisplayed_data_container)
                    break
                    
            # Position of the dict we need in type string (start - end)
            undisplayed_text_start = 0
            undisplayed_text_end = 0
            # print(undisplayed_data_container)
            # You can see picture to know why
            for i in range(len(undisplayed_data_container)):
                # get nearest {
                if undisplayed_data_container[i] == '{': 
                    undisplayed_text_start = i
                # get first }
                if undisplayed_data_container[i] == '}':
                    undisplayed_text_end = i
                    break
            # Get dict but in type string
            undisplayed_in_curly_braces = undisplayed_data_container[undisplayed_text_start:(undisplayed_text_end + 1)]
            # Change to dict
            undisplayed_info = string_to_dict(undisplayed_in_curly_braces)

            # pprint.pprint(undisplayed_info)

        # DATA IN SCRIPT ELEMEMENT (CAN SHOW SOME IN UI - ABOUT LANDLORD) - see in ./image/example/landlord.png
            landlord_data_container = ''
            for script in script_elements:
                if script.find('initProductDetails') != -1:
                    landlord_data_container = script
                    break
            
            # Set start from {  (see image to understand why)
            landlord_text_start = landlord_data_container.index('window.FrontEnd_Product_Details_Details')
            landlord_text_start = landlord_data_container.find('{', landlord_text_start)
            landlord_text_end = 0

            landlord_container_from_first_curly_braces = landlord_data_container[landlord_text_start:]

            # Try to find } close dict, use stack to find
            array = [] # contain { } , as same as stack
            for i in range(len(landlord_container_from_first_curly_braces)):
                if landlord_container_from_first_curly_braces[i] == '{': 
                    array.append(landlord_container_from_first_curly_braces[i])
                if landlord_container_from_first_curly_braces[i] == '}':
                    array.pop()
                    if len(array) == 0:
                        landlord_text_end = i + 1
                        break

            landlord_in_curly_braces = landlord_container_from_first_curly_braces[0:landlord_text_end] 

            # Error parseInt when change to dict, so erase it - see image to know where is it
            landlord_in_curly_braces = re.sub(r'(parseInt\(("(\d+)")\))', r'\3', landlord_in_curly_braces)  

            # Change to dict
            landlord_info = string_to_dict(landlord_in_curly_braces)

            # Get many key, but only some can be used
            key_needed = ['nameSeller', 'emailSeller', 'userId']
            landlord_needed_info = {key: value for key, value in landlord_info.items() if key in key_needed}

            # pprint.pprint(landlord_info)
            # print(now)

            full_data = {}
            full_data.update(data_general)
            full_data.update(undisplayed_info)
            full_data.update(landlord_needed_info)
            full_data.update(displayed_data_container)

            full_data_no_none = {k: v for k, v in full_data.items() if v is not None}

        print_banner_colored(f'Scraping successful {file_name} ({'NEW' if new_html else 'OLD'})!', 'success')
        return full_data_no_none
    except KeyboardInterrupt:
        sys.exit("NGẮT CHƯƠNG TRÌNH TỪ BÀN PHÍM !!")
    except Exception as e:
        print_banner_colored(f'Scraping failed {file_name} ({'NEW' if new_html else 'OLD'})!', 'danger')
        raise e


def main():
    client = clickhouse_connect.get_client(host='localhost', username='default')

    # Create database
    client.command('''
        CREATE DATABASE IF NOT EXISTS BATDONGSAN
    ''')

    client.command('USE BATDONGSAN')

    # Create table crawled
    client.command('''
        CREATE TABLE IF NOT EXISTS BATDONGSAN.RAW_DATA (
            `filename` String,                  -- Tên file lưu (để lấy ra so sánh cho nhanh)
            `time_scraping` String
        )
        ENGINE = MergeTree()
        PRIMARY KEY (`filename`);
    ''')

    columns = client.query('''DESCRIBE TABLE BATDONGSAN.RAW_DATA ''')
    columns = columns.result_columns[0]

    link_scraped = client.query('''
        SELECT r.filename
        FROM BATDONGSAN.RAW_DATA as r
    ''')

    link_scraped = link_scraped.result_columns[0] if link_scraped.result_columns else []

    for file_path in DATA_PATH_FUNC('batdongsan').iterdir():
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
                        ALTER TABLE BATDONGSAN.RAW_DATA 
                        ADD COLUMN `{key}` Nullable(String)
                    ''')

                    data_values[index] = str(data_values[index])

            client.command(f'''INSERT INTO BATDONGSAN.RAW_DATA ({', '.join([f'`{key}`' for key in data_keys])}) VALUES ({', '.join([f"'{value}'" for value in data_values])})''')

            # Này thiết cột thì chạy lại không được ??
            # client.insert(
            #     table='BATDONGSAN.RAW_DATA',
            #     data=data_values,
            #     column_names=data_keys
            # )

    

def test():
    with open('./data/data_raw/page_source/p80-l6_20250321-114439.json', 'r') as file:
        data = json.load(file)
        format_html_page_source(data['page_source'])
        # Chú ý cho time_scraped vào !!
        pprint.pprint(extract_one_page_source(data, 'helooooo'))


if __name__ == '__main__':
    # main()
    test()