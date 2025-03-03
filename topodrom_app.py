from selenium import webdriver
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

from pprint import pprint


# Загружаем переменные из .env
load_dotenv()


INSTAGRAM_URL = 'https://www.instagram.com/'
SHEET_ID = "1WEePEePYiYWfWrJkBQbQti8owtOC00Sf8xfBLcIcKdo"


def get_insta_number(source_str):
    # num_str = source_str.replace("\xa0", "")
    num_str = source_str
    factor = 1
    if "тыс." in num_str:
        factor = 1000
        num_str = num_str.replace("тыс.", "")

    num_str = re.sub(r"[^\d,]", "", num_str)  # Удаляем все, кроме цифр и запятой
    num_str = num_str.replace(",", ".")
    result = int(float(num_str) * factor)

    return result



class InstagramBot:

    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", True)  # This line of code keeps Chrome browser window opened
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        # chrome_options.add_argument("--headless")  # Без графического интерфейса
        self.driver = webdriver.Chrome(options=chrome_options)
        self.min_delay = 3
        self.delay = 6
        self.follow_delay = 2

    def auth(self, insta_username, insta_password):
        """Авторизация."""
        self.driver.get(f"{INSTAGRAM_URL}")

        time.sleep(self.delay)

        print("auth")
        username_tag = self.driver.find_element(By.NAME, 'username')
        username_tag.send_keys(insta_username)
        print("username")
        password_tag = self.driver.find_element(By.NAME, 'password')
        password_tag.send_keys(insta_password)
        print("password")

        submit_btn_tag = self.driver.find_element(By.CSS_SELECTOR, 'button[type=submit]')
        submit_btn_tag.click()
        time.sleep(self.delay)

        # Close Save Auth modal window
        splash_screen_key = True
        attempt_n = 0
        while splash_screen_key and (attempt_n < 100):
            attempt_n += 1
            # Попытка закрыть окно сохранения пароля по 1-му алгоритму
            btn_tags = self.driver.find_elements(By.CSS_SELECTOR, 'div.x1yrsyyn:nth-child(2) > div:nth-child(2) > div:nth-child(1)')
            print(len(btn_tags))
            if btn_tags and len(btn_tags) == 1:
                splash_screen_key = False
                not_now_btn_tag = btn_tags[0]
                not_now_btn_tag.click()
                time.sleep(self.delay)
            # Попытка закрыть окно сохранения пароля по 2-му алгоритму
            if not splash_screen_key:
                btn_tags = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="button"][tabindex="0"]:has(:contains("Не сейчас"))')
                print(len(btn_tags))
                if btn_tags and len(btn_tags) == 1:
                    splash_screen_key = False
                    not_now_btn_tag = btn_tags[0]
                    not_now_btn_tag.click()
                    time.sleep(self.delay)



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
        # Храним уникальные ссылки (set автоматически удаляет дубли)
        unique_reels = set()
        step = 0
        attempts = 3

        actions = ActionChains(self.driver)
        # Пролистываем, пока количество reels или похожих ссылок на листе не станет больше max_items
        while do_scroll and (reels_count < max_items) and (len(reels_info) < len(links_dict)):
            main = self.driver.find_element(By.CSS_SELECTOR, main_selector)
            reels_tags = main.find_elements(By.CSS_SELECTOR, reels_selector)
            
            for reel in reels_tags:
                reel_info = {}
                href = reel.get_attribute('href')
                if not '/reel/' in href:
                    continue

                # is_new = True
                # links_dict = links_dict.copy()
                if bool(links_dict.get(href)):
                    links_dict[href] = False
                    data_tags = reel.find_elements(By.CSS_SELECTOR, 'span[dir="auto"] > span')

                    if len(data_tags) == 3:
                        reel_info['href'] = href
                        reel_info['likes'] = get_insta_number(data_tags[0].get_attribute("textContent"))
                        reel_info['comments'] = get_insta_number(data_tags[1].get_attribute("textContent"))
                        reel_info['views'] = get_insta_number(data_tags[2].get_attribute("textContent"))
                        reels_info.append(reel_info)


                # for key, value in links_dict.items():
                #     if item['href'] == reel_info['href']:
                #         is_new = False
                #         break
                # for item in reels_info:
                #     if item['href'] == reel_info['href']:
                #         is_new = False
                #         break

                # if is_new:
                #     # print(reel['href'])
                #     data_tags = reel.find_elements(By.CSS_SELECTOR, 'span[dir="auto"] > span')

                #     if len(data_tags) == 3:
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

        # reels = main.find_elements(By.CSS_SELECTOR, reels_selector)
        # i = 0
        # time.sleep(self.delay)
        # for reel in reels_tags:
        #     i += 1
        #     if i > max_items:
        #         break
        #     reel_info = {}
        #     href = reel.get_attribute('href')
        #     if not '/reel/' in href:
        #         continue
        #     reel_info['href'] = href

        #     # print(reel['href'])
        #     data_tags = reel.find_elements(By.CSS_SELECTOR, 'span[dir="auto"] > span')

        #     if len(data_tags) == 3:
        #         reel_info['likes'] = get_insta_number(data_tags[0].get_attribute("textContent"))
        #         reel_info['comments'] = get_insta_number(data_tags[1].get_attribute("textContent"))
        #         reel_info['views'] = get_insta_number(data_tags[2].get_attribute("textContent"))
        #         reels_info.append(reel_info)
            # pprint(reel_info)
        return reels_info
    
    def random_sleep(self):
        # Рандомная задержка для эмуляции пользователя
        delay = random.uniform(self.min_delay, self.delay)
        time.sleep(delay)


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
            current_datetime
            ])
        # Добавляем строку в таблицу
    # sheet.append_row(row, value_input_option="USER_ENTERED")
    # Записываем данные сразу пачкой
    sheet.append_rows(rows, value_input_option='USER_ENTERED')


def get_links_dict():
    sheet = get_sheet(SHEET_ID, "Статистика")
    # Чтение данных из Google Таблицы
    all_data = sheet.get_all_values()
    links_dict = {}
    for item in all_data:
        if '/reel/' in item[4]:
            links_dict[item[4]] = True
    return links_dict


def process_parsing():
    links_dict = get_links_dict()
    
    insta_username = os.getenv('INSTA_USERNAME')
    insta_password = os.getenv('INSTA_PASSWORD')

    insta_bot = InstagramBot()
    insta_bot.auth(insta_username=insta_username, insta_password=insta_password)

    reels = insta_bot.get_reels_list(username='topodrom', links_dict=links_dict, max_items=100)

    sheet = get_sheet(SHEET_ID, "Reels")
    add_reels_to_sheet(reels, sheet)
    # return reels


process_parsing()
# d = get_links_dict()
# pprint(d)

# input("Нажмите Enter, чтобы закрыть браузер...")


