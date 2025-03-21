from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime as dt
import re
import random
import subprocess

from pprint import pprint


# Загружаем переменные из .env
load_dotenv()


INSTAGRAM_URL = 'https://www.instagram.com/'


def get_insta_number(source_str):
    # num_str = source_str.replace("\xa0", "")
    num_str = source_str
    # print(num_str)
    factor = 1
    if "тыс." in num_str:
        factor = 1000
        num_str = num_str.replace("тыс.", "")
        num_str = num_str.replace(",", ".")
    elif "K" in num_str:
        factor = 1000
        num_str = num_str.replace("K", "")
        num_str = num_str.replace(",", ".")
    elif "К" in num_str:
        factor = 1000
        num_str = num_str.replace("К", "")
        num_str = num_str.replace(",", ".")
    else:
        num_str = num_str.replace(",", "")
        num_str = num_str.replace(".", "")

    num_str = re.sub(r"[^\d.]", "", num_str)  # Удаляем все, кроме цифр и запятой
    # num_str = num_str.replace(",", ".")
    result = int(float(num_str) * factor)
    # print(result)

    return result



class InstagramBot:

    def __init__(self, show_browser=False):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_experimental_option("detach", True)  # This line of code keeps Chrome browser window opened
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        if not show_browser:
            chrome_options.add_argument("--headless")  # Без графического интерфейса
        chrome_options.add_argument("--no-sandbox")  # Полезно для Ubuntu
        chrome_options.add_argument("--disable-dev-shm-usage")  # Исправляет возможные ошибки памяти
        
        # ✅ Уникальный профиль, чтобы избежать конфликта
        # chrome_options.add_argument("--user-data-dir=/tmp/selenium_profile") # For Ubuntu
        
        # Запуск браузера
        # service = Service("/usr/local/bin/chromedriver") # For Ubuntu
        # self.driver = webdriver.Chrome(service=service, options=chrome_options) # For Ubuntu
        self.driver = webdriver.Chrome(options=chrome_options) # For Windows
        
        # Устанавливаем таймаут на загрузку страницы (например, 5 минут)
        self.driver.set_page_load_timeout(300)
        self.driver.implicitly_wait(10)
        
        self.min_delay = 6
        self.delay = 10
        self.follow_delay = 2
        
    def test(self):
        self.driver.get("https://www.google.com")
        
    def auth(self, insta_username, insta_password):
        """Авторизация."""
        print("self.driver.get")
        self.driver.get(f"{INSTAGRAM_URL}")
        print("time.sleep(self.delay)")
        time.sleep(self.delay)
        # input("Нажмите Enter, чтобы продолжить...")
        print("try")
        # Находим кнопку принятия cookies и кликаем по ней, если она есть
        try:
            cookies_button = self.driver.find_element(By.CSS_SELECTOR, 'button._a9--._ap36._a9_1')
        except:
            try:
                cookies_button = self.driver.find_element(By.XPATH, "//button[text()='Отклонить необязательные файлы cookie']")
            except:
                cookies_button = None  # Кнопка не найдена

        if cookies_button:
            print("cookies_button.click()")
            cookies_button.click()
            time.sleep(self.delay)
            
        print("time.sleep(self.delay)")
        time.sleep(self.delay)
        try:
            print("auth")
            username_tag = self.driver.find_element(By.NAME, 'username')
            username_tag.send_keys(insta_username)
            # input("Нажмите Enter, чтобы продолжить...")
            print("username")
            password_tag = self.driver.find_element(By.NAME, 'password')
            password_tag.send_keys(insta_password)
            # input("Нажмите Enter, чтобы продолжить...")
            print("password")
        

            submit_btn_tag = self.driver.find_element(By.CSS_SELECTOR, 'button[type=submit]')
            submit_btn_tag.click()
            time.sleep(self.delay)
        
            # input("Нажмите Enter, чтобы продолжить...")
    
            # Close Save Auth modal window
            splash_screen_key = True
            attempt_n = 0
            while splash_screen_key and (attempt_n < 5):
                attempt_n += 1
    
                btn_tags = self.driver.find_elements(By.XPATH, '//div[@role="button" and @tabindex="0"][contains(., "Не сейчас")]')
                if (not btn_tags) or (len(btn_tags) == 0):
                    btn_tags = self.driver.find_elements(By.XPATH, '//div[@role="button" and @tabindex="0"][contains(., "Not now")]')
                print(len(btn_tags))
                if btn_tags and len(btn_tags) == 1:
                    splash_screen_key = False
                    not_now_btn_tag = btn_tags[0]
                    not_now_btn_tag.click()
                    time.sleep(self.delay)
                
                # Попытка закрыть окно сохранения пароля по 1-му алгоритму
                btn_tags = self.driver.find_elements(By.CSS_SELECTOR, 'div.x1yrsyyn:nth-child(2) > div:nth-child(2) > div:nth-child(1)')
                print(len(btn_tags))
                if btn_tags and len(btn_tags) == 1:
                    splash_screen_key = False
                    not_now_btn_tag = btn_tags[0]
                    not_now_btn_tag.click()
                    time.sleep(self.delay)
        except:
            pass
        
        # input("Нажмите Enter, чтобы продолжить...")

    def get_reels_list(self, username, links_dict, max_items=20):
        print(f"{INSTAGRAM_URL}/{username}/reels/")
        self.driver.get(f"{INSTAGRAM_URL}/{username}/reels/")
        time.sleep(self.delay)

        # Находим body
        body = self.driver.find_element(By.TAG_NAME, "body")

        main_selector = 'main[role="main"]'
        main = self.driver.find_element(By.CSS_SELECTOR, main_selector)

        if not main:
            print(f"Не найден селектор: {main_selector}")
            return None

        reels_selector = 'a[role="link"]'

        # Do scrolling
        reels_count = 0
        do_scroll = True
        reels_tags = []
        reels_info = []
        processed_links = []
        step = 0
        attempts = 7

        actions = ActionChains(self.driver)
        # Пролистываем, пока количество reels или похожих ссылок на листе не станет больше max_items
        # while do_scroll and (reels_count < max_items) and (len(reels_info) < len(links_dict)):
        while do_scroll and (len(reels_info) < max_items):
            main = self.driver.find_element(By.CSS_SELECTOR, main_selector)
            reels_tags = main.find_elements(By.CSS_SELECTOR, reels_selector)
            
            for reel in reels_tags:
                reel_info = {}
                href = reel.get_attribute('href')
                if not '/reel/' in href:
                    continue

                if not (href in processed_links):
                    processed_links.append(href)
                    data_tags = reel.find_elements(By.CSS_SELECTOR, 'span[dir="auto"] > span')

                    if len(data_tags) == 3:
                        reel_info['href'] = href
                        reel_info['likes'] = get_insta_number(data_tags[0].get_attribute("textContent"))
                        reel_info['comments'] = get_insta_number(data_tags[1].get_attribute("textContent"))
                        reel_info['views'] = get_insta_number(data_tags[2].get_attribute("textContent"))
                        reel_info['nick'] = ""
                        reel_info['promo_code'] = ""
                        reels_info.append(reel_info)
                # is_new = True
                # links_dict = links_dict.copy()
                # if bool(links_dict.get(href)):
                #     links_dict[href] = False
                #     data_tags = reel.find_elements(By.CSS_SELECTOR, 'span[dir="auto"] > span')

                #     if len(data_tags) == 3:
                #         reel_info['href'] = href
                #         reel_info['likes'] = get_insta_number(data_tags[0].get_attribute("textContent"))
                #         reel_info['comments'] = get_insta_number(data_tags[1].get_attribute("textContent"))
                #         reel_info['views'] = get_insta_number(data_tags[2].get_attribute("textContent"))
                #         reels_info.append(reel_info)

            print("len(reels_tags): ", len(reels_tags))
            print("len(reels_info): ", len(reels_info))
            if reels_count < len(reels_tags):
                reels_count = len(reels_tags)
                bar = reels_tags[-1]
                if step % 2 == 0:
                    body.send_keys(Keys.PAGE_DOWN)  
                else:
                    bar.send_keys(Keys.END)
                step += 1
    
                # Прокрутка к последнему элементу
                # self.driver.execute_script("arguments[0].scrollIntoView();", bar)
                # self.driver.execute_script("window.scrollBy(0, 300);")

                print(f"step: {step}")
                actions.move_by_offset(5, 5).perform()  # Имитация движения мыши
                # Рандомная задержка для эмуляции пользователя
                self.random_sleep()
                # time.sleep(delay)
            elif attempts > 0:
                attempts -= 1
                # Находим body и отправляем команду PageDown
                body.send_keys(Keys.PAGE_UP)
                self.random_sleep()
                body.send_keys(Keys.PAGE_DOWN)
                self.random_sleep()
                body.send_keys(Keys.END)
                self.random_sleep()
                print("attempts: ", attempts)
            else:
                do_scroll = False
            # pprint(reel_info)

        self.get_reels_nicks_and_promo(reels_info=reels_info, links_dict=links_dict)

        return reels_info

    def get_reels_nicks_and_promo(self, reels_info, links_dict):
        print("Start")
        attempts = 10
        i = 0
        while i < len(reels_info) and attempts > 0:
            href = reels_info[i]['href'] 
            if not bool(links_dict.get(href)):
                attempts -= 1
                try:
                    self.driver.get(href)
                    self.random_sleep()
                    main_selector = 'main[role="main"]'
                    main = self.driver.find_element(By.CSS_SELECTOR, main_selector)

                    # Находим никнейм блогера
                    header = main.find_element(By.CSS_SELECTOR, "header")
                    a_tags = header.find_elements(By.CSS_SELECTOR, 'a')
                    # for i, a in enumerate(a_tags):
                    #     print(f"Ссылка {i+1}: {a.get_attribute('textContent').strip()}")

                    nick = ''
                    if len(a_tags) > 1:
                        text1 = a_tags[0].get_attribute("textContent").strip() # Текст ссылки 1
                        href2 = a_tags[1].get_attribute("href") # URL ссылки 2
                        text2 = a_tags[1].get_attribute("textContent").strip() # Текст ссылки 2
                        if text1 == 'topodrom':
                            nick = 'topodrom'
                        if not ("/reels/audio/" in href2):
                            nick = text2

                    reels_info[i]['nick'] = nick

                    # print("Найден ник:", nick)

                    # Находим промокод
                    h1 = main.find_element(By.CSS_SELECTOR, 'h1[dir="auto"]')
                    text = h1.text  # Получаем текст из элемента

                    # Используем регулярное выражение для поиска слова после "по промокоду "
                    match = re.search(r"промокоду (\S+)", text, re.IGNORECASE)

                    if match:
                        reels_info[i]['promo_code'] = match.group(1)  # Берём первое слово после фразы
                    #     print("Найден промокод:", promo_code)
                    # else:
                    #     print("Фраза 'по промокоду' не найдена.")
                except Exception as e:
                    print(f"Произошла ошибка: {e}")
            # Увеличиваем счётчик
            i += 1
                

    def random_sleep(self):
        # Рандомная задержка для эмуляции пользователя
        delay = random.uniform(self.min_delay, self.delay)
        time.sleep(delay)
        
    def close(self):
        """Корректное завершение работы браузера"""
        if self.driver:
            self.driver.quit()  # Закрывает Chrome + ChromeDriver


def get_sheet(spreadsheet_id, sheet_name):

    # Авторизация в Google API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("insta-parsing-service-account.json", scope)
    client = gspread.authorize(creds)

    # Открываем Google Таблицу (по названию или ID)
    spreadsheet = client.open_by_key(spreadsheet_id)

    # Выбираем лист
    sheet = spreadsheet.worksheet(sheet_name)
    return sheet


def add_reels_to_sheet(reels, sheet):
    # current_date = dt.now().date()  # Только дата
    # current_datetime = dt.now()  # Дата + Время
    current_date = dt.now().strftime("%Y-%m-%d")  # Только дата
    current_datetime = dt.now().strftime("%Y-%m-%d %H:%M:%S")  # Дата + Время
    print(current_date)
    # print(current_date.strftime("%Y-%m-%d"))
    rows = []
    for reel in reels:
        rows.append([
            reel['href'], 
            reel['views'], 
            reel['likes'], 
            reel['comments'],
            current_date,
            current_datetime,
            reel['nick'],
            reel['promo_code'],
            ])
        # Добавляем строку в таблицу
    # sheet.append_row(row, value_input_option="USER_ENTERED")
    # Записываем данные сразу пачкой
    # sheet.append_rows(rows, value_input_option='USER_ENTERED')
    # Вставляем данные начиная со 2-й строки (сдвигая остальные вниз)
    sheet.insert_rows(rows, row=2, value_input_option='USER_ENTERED')


# Получаем список уже имеющихся Reels и проставляем признак парсинга Ника и Промокода 
def get_links_dict(spreadsheet_id):
    sheet = get_sheet(spreadsheet_id, "Статистика")
    # Чтение данных из Google Таблицы
    all_data = sheet.get_all_values()
    links_dict = {}
    for item in all_data:
        if '/reel/' in item[4]:
            links_dict[item[4]] = bool(item[0] or item[1])
            
    return links_dict


# Функция запуска процесса парсинга
def process_parsing():
    insta_username = os.getenv('INSTA_USERNAME')
    insta_password = os.getenv('INSTA_PASSWORD')
    show_browser = os.getenv('SHOW_BROWSER') == '1'
    spreadsheet_id = os.getenv('SPREADSHEET_ID')

    links_dict = get_links_dict(spreadsheet_id)
    # links_dict = []
    pprint(links_dict)
    print(len(links_dict))

    insta_bot = InstagramBot(show_browser)
    
    try:
        insta_bot.auth(insta_username=insta_username, insta_password=insta_password)
        # insta_bot.get_reels_nicks_and_promo(reels_info=reels_info, links_dict=links_dict)

    
        reels = insta_bot.get_reels_list(username='topodrom', links_dict=links_dict, max_items=100)
    
        sheet = get_sheet(spreadsheet_id, "Reels")
        add_reels_to_sheet(reels, sheet)
    finally:
        insta_bot.close()



reel_info = {}
reels_info = []
reel_info['href'] = "https://www.instagram.com/topodrom/reel/DHYVHtaoUTr/"
reel_info['likes'] = "10"
reel_info['comments'] = "1"
reel_info['views'] = "100"
reel_info['nick'] = ""
reel_info['promocode'] = ""
reels_info.append(reel_info)

process_parsing()
# d = get_links_dict()
# pprint(d)

# input("Нажмите Enter, чтобы закрыть браузер...")


