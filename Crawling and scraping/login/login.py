import pickle
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from shared.globals import COOKIES_PATH

class Login_Chotot():
    def __init__(self):
        self.__chrome_options = webdriver.ChromeOptions()
        user_agent_string = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        self.__chrome_options.add_argument(f"user-agent={user_agent_string}")
        self.__chrome_options.add_argument('--disable-web-security')
        self.__chrome_options.add_argument('--allow-running-insecure-content')
        self.__chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.__chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.__chrome_options.add_experimental_option("useAutomationExtension", False)
        self.__chrome_options.add_argument("--start-maximized")

        self.__driver = webdriver.Chrome(options=self.__chrome_options)
        self.__driver.implicitly_wait(5)
        self.__driver.get('https://www.nhatot.com/thue-phong-tro-tp-ho-chi-minh?f=protection_entitlement')
        
    
    def prepare_cookies(self):
        login_button = self.__driver.find_element(By.CSS_SELECTOR, '.ct_lr__b1e0gj3u')
        login_button.click()

        time.sleep(5)   # wait to redirect to login

        wait = WebDriverWait(self.__driver, 20)

        gg_login = wait.until(lambda driver: driver.find_element(By.CSS_SELECTOR, '#google-login-btn'))
        gg_login.click()

        while True:
            print('CAN I START NOW ??')
            print('[Y] Yes     [N] No')
            wait_to_login_success = input('Answer: ')
            if wait_to_login_success.lower() == 'y' or wait_to_login_success.lower() == 'yes':
                break
        
        cookies = self.__driver.get_cookies()
        print(cookies)
        COOKIES_PATH.parent.mkdir(exist_ok=True)
        with open(COOKIES_PATH, 'wb') as file:
            pickle.dump(cookies, file)

        self.quit()
    
    def quit(self):
        self.__driver.quit()