import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = 'https://gunsbroker.ru/search/none/&cat=hunting&subcat=2&cal=203&reloading_type=0&stvol_type=0'

def parse_page(html, start_pos):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('div.main__item')
    data = []
    pos = start_pos
    for item in items:
        title_tag = item.select_one('section.main__item--desc hgroup a h3')
        price_tag = item.select_one('section.main__item--desc span.main__item--info strong')
        date_tag = item.select_one('section.main__item--desc hgroup time span')
        link_tag = item.select_one('section.main__item--desc hgroup a')
        location_tag = item.select_one('section.main__item--desc span.main__item--info address')
        if title_tag and price_tag and date_tag and link_tag and location_tag:
            # Формируем полную ссылку
            full_link = 'https://gunsbroker.ru' + link_tag['href']

            data.append({
                'position': pos,
                'title': title_tag.text.strip(),
                'price': price_tag.text.strip(),
                'date': date_tag.text.strip(),
                'link': full_link,
                'location': location_tag.text.strip()
            })
            pos += 1
    return data

def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    all_data = []
    page = 1
    position_counter = 1
    while True:
        url = f"{BASE_URL}&page={page}"
        print(f"Запрос страницы {page}: {url}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка запроса страницы {page}, код {response.status_code}")
            break
        page_data = parse_page(response.text, position_counter)
        if not page_data:
            print(f"Данные на странице {page} отсутствуют, прекращаем парсинг.")
            break
        print(f"Найдено записей на странице {page}: {len(page_data)}, всего записей: {len(all_data)+len(page_data)}")
        all_data.extend(page_data)
        position_counter += len(page_data)
        page += 1

    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset=['title', 'price', 'date'], inplace=True)
    df.to_csv('./guns_data_308.csv', index=False)
    print(f"Всего сохранено уникальных записей: {len(df)}")

if __name__ == '__main__':
    main()

