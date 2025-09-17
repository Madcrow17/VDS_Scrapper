import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# Путь к chromedriver
CHROMEDRIVER_PATH = './chrome_driver/chromedriver'

# Путь к браузеру chrome
BROWSER_BINARY_PATH = './browser/chrome-headless-shell'

# URL поиска с нужными фильтрами
BASE_URL = 'https://gunsbroker.ru/search/none/&cat=hunting&subcat=2&cal=202&reloading_type=0&stvol_type=0'

# Путь к файлу для хранения данных
DATA_FILE = './guns_data_223.csv'

def init_driver():
    service = Service(CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.binary_location = BROWSER_BINARY_PATH
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('div.main__item')
    data = []
    for item in items:
        title_tag = item.select_one('section.main__item--desc hgroup a h3')
        price_tag = item.select_one('section.main__item--desc span.main__item--info strong')
        date_tag = item.select_one('section.main__item--desc hgroup time span')
        if title_tag and price_tag and date_tag:
            data.append({
                'title': title_tag.text.strip(),
                'price': price_tag.text.strip(),
                'date': date_tag.text.strip()
            })
    return data

def save_data(new_data):
    if not new_data:
        print("Данные для сохранения отсутствуют")
        return
    if os.path.exists(DATA_FILE):
        df_existing = pd.read_csv(DATA_FILE)
        df_new = pd.DataFrame(new_data)
        df_merged = pd.concat([df_existing, df_new], ignore_index=True)
        df_merged.drop_duplicates(subset=['title', 'price', 'date'], inplace=True)
        df_merged.to_csv(DATA_FILE, index=False)
    else:
        df_new = pd.DataFrame(new_data)
        df_new.to_csv(DATA_FILE, index=False)


def main():
    logging.info("Запуск скраппинга по формированию таблицы оружия в калибре .223")
    driver = init_driver()
    logging.info("Инициализация драйвера")
    driver.get(BASE_URL)
    logging.info(f"Загружена страница {BASE_URL}")

    WAIT_TIME = 10
    SCROLL_PAUSE_TIME = 1

    # Цикл загрузки всех товаров
    while True:
        try:
            show_more_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.search__more'))
            )
            logging.info("Кнопка 'Показать еще' найдена, кликаем")

            driver.execute_script("arguments[0].click();", show_more_btn)

            old_count = len(driver.find_elements(By.CSS_SELECTOR, 'div.main__item'))

            # ждем, пока добавятся новые товары
            WebDriverWait(driver, WAIT_TIME).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, 'div.main__item')) > old_count
            )
            logging.info(f"Подгружено новых элементов, всего на странице {len(driver.find_elements(By.CSS_SELECTOR, 'div.main__item'))}")
            time.sleep(SCROLL_PAUSE_TIME)

        except Exception as e:
            logging.info(f"Кнопка 'Показать еще' недоступна или новых данных нет, подгрузка завершена: {e}")
            break

    # После полной подгрузки парсим всю страницу
    html = driver.page_source
    all_data = parse_page(html)
    logging.info(f"Парсинг завершен. Всего записей: {len(all_data)}")

    # Удаляем дубликаты и сохраняем
    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset=['title', 'price', 'date'], inplace=True)
    df.to_csv(DATA_FILE, index=False)
    logging.info(f"Данные сохранены. Всего уникальных записей: {len(df)}")

    driver.quit()
    logging.info("Драйвер закрыт, скраппинг завершен")


if __name__ == '__main__':
    main()
