import os

import bs4
import requests
import datetime
from time import sleep
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

import colorama
from colorama import Fore, Style
colorama.init()


class Parser:

    def __init__(self, article: int):
        """ Объект страницы на товар (определяющийся по артикулу) """
        self.article = article
        self.url = f'https://www.wildberries.ru/catalog/{article}/detail.aspx?targetUrl=GP'
        self.user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, ' \
                          'like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36'

        # main
        self.name = None
        self.brand = None
        self.price_now = 0
        self.price_old = 0
        self.sold_out = False
        self.seller = None
        self.date = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.errors = 'No'
        self.image = None

    def _get_name(self, soup: bs4.BeautifulSoup) -> None:
        try:
            name_header = soup.find('h1', class_='same-part-kt__header')
            self.name = [s.text for s in name_header.find_all('span')][1]
            print(Fore.GREEN + '[+] The "name" was successfully received!' + Style.RESET_ALL)
        except AttributeError:
            print(Fore.RED + '[-] Failed to parse the "name"!' + Style.RESET_ALL)

    def _get_brand(self, soup: bs4.BeautifulSoup) -> None:
        try:
            name_header = soup.find('h1', class_='same-part-kt__header')
            self.brand = [s.text for s in name_header.find_all('span')][0]
            print(Fore.GREEN + '[+] The "brand" was successfully received!' + Style.RESET_ALL)
        except AttributeError:
            print(Fore.RED + '[-] Failed to parse the "brand"!' + Style.RESET_ALL)

    def _get_seller(self) -> None:
        options_chrome = Options()
        options_chrome.add_argument(f'user-agent={self.user_agent}')
        options_chrome.add_argument('--headless')
        options_chrome.add_argument('--ignore-certificate-errors')
        options_chrome.add_argument('--ignore-ssl-errors')

        s = Service(r'C:\Users\palac\PycharmProjects\ParserWildberries_bs4\chromedriver101\chromedriver.exe')
        driver = webdriver.Chrome(service=s, options=options_chrome)
        try:
            driver.get(url=self.url)
            sleep(2)
            try:
                self.seller = driver.find_element(By.XPATH,
                                                  '//*[@id="infoBlockProductCard"]/div[8]/div[2]/div/div/div[2]/span[1]').text
            except NoSuchElementException:
                sleep(1)
                self.seller = driver.find_element(By.XPATH,
                                                  '//*[@id="infoBlockProductCard"]/div[8]/div[2]/div/div[1]/div[2]/div[1]/a').text

        except NoSuchElementException:
            pass

        finally:
            if self.seller:
                print(Fore.GREEN + '[+] The "seller" was successfully received!' + Style.RESET_ALL)
            else:
                print(Fore.RED + '[-] Failed to parse the "seller"!' + Style.RESET_ALL)
            driver.close()
            driver.quit()

    def _get_image(self, soup: bs4.BeautifulSoup) -> None:
        try:
            image_url = 'https:' + soup.find('div', id='photo').img.get('src')
            img_data = requests.get(image_url).content
            img_path = os.path.realpath(f'media\\photos\\{self.article}.png')
            with open(img_path, 'wb') as f:
                f.write(img_data)

            self.image = img_path
            print(Fore.GREEN + '[+] The "image" was successfully received!' + Style.RESET_ALL)
        except AttributeError:
            print(Fore.RED + '[-] Failed to parse the "image"!' + Style.RESET_ALL)

    def _get_price(self, soup: bs4.BeautifulSoup) -> None:
        try:
            self.price_now = str(soup.find(class_='price-block__final-price').text.strip().replace(u'\xa0', u''))
            self.price_now = int(self.price_now.replace('₽', ''))

            self.price_old = str(soup.find(class_='price-block__content').find('del').text.strip().replace(
                u'\xa0', u''))
            self.price_old = int(self.price_old.replace('₽', ''))
            print(Fore.GREEN + '[+] The "price" was successfully received!' + Style.RESET_ALL)
        except AttributeError:
            self.sold_out = True if self.price_now == 0 else False  # Товара нет в наличии
            if self.sold_out:
                print(Fore.YELLOW + '[!] The product is out of stock!' + Style.RESET_ALL)
            else:
                print(Fore.RED + '[-] Failed to parse the "price"!' + Style.RESET_ALL)

    def parse(self, **options: bool) -> list:
        """
            ** options:
                name(bool): Спарсить ли наименование товара. По умолчанию True.
                brand(bool): Спарсить ли наименование бренда товара. По умолчанию True.
                seller(bool): Спарсить ли наименование поставщика товара. По умолчанию True (Может негативно повляить на
                        производительность процесса парсинга, рекомендуется использовать False).
                price(bool): Спарсить ли стоимость товара (со скидкой/без  скидки). По умолчанию True.
                image(bool): Спарсить ли фото товара. По умолчанию True.

            Возвращает словарь со всеми данными
         """
        print('----- Started parsing the page! -----')
        r = requests.get(self.url)
        soup = BeautifulSoup(r.text, 'html.parser')
        if soup.find(class_='content404__title'):
            self.errors = 'Ошибка 404'
            print('----- Page not found! -----')
            return self._render()

        if options.get('name', True):
            self._get_name(soup)
        if options.get('brand', True):
            self._get_brand(soup)
        if options.get('seller', True):
            self._get_seller()
        if options.get('price', True):
            self._get_price(soup)
        if options.get('image', True):
            self._get_image(soup)

        print('----- Parsing completed successfully! -----')
        return self._render()

    def _render(self) -> list:
        """ Формиррует словарь для возврата """
        self.price_old = self.price_old if self.price_old else self.price_now

        data = [{'main':
                     {'article_id': self.article,
                      'url': self.url,
                      'name': self.name,
                      'brand': self.brand,
                      'price_now': self.price_now,
                      'price_old': self.price_old,
                      'sold_out': self.sold_out,
                      'seller': str(self.seller),
                      'date_upload': self.date,
                      'errors': self.errors,
                      'image': self.image
                      }}]
        return data

    def upload_price(self) -> list:
        """ Собирает со страницы только цены на товар (Вызывает только get_price) """
        return self.parse(name=False, brand=False, seller=False, image=False, description=False)

    def __str__(self):
        return f'Артикул: {self.article} / Ссылка: {self.url}'

    def __call__(self):
        return self._render()


if __name__ == '__main__':
    from pprint import pprint
    article_id = 14722186
    p = Parser(article=article_id)
    print(p)
    p.parse()
    pprint(p())
