import pathlib
import time
import pandas as pd
from locale import atof, setlocale, LC_NUMERIC
from configs import init_config_mercadona

from postgres import save_df

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium import webdriver


def init_driver():
    script_directory = pathlib.Path().absolute()
    chrome_options = Options()
    chrome_options.add_argument(f'user-data-dir={script_directory}\\selenium')
    web_driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options)
    return web_driver


FIRST_LEVEL = 1

mercadona_params = init_config_mercadona()
driver = init_driver()
data_products = pd.DataFrame(
    columns=['name', 'brand', 'details', 'price', 'size'])

main_frame = None
menu_frame = None
sections_frame = None


def login():
    username = driver.find_element(by=By.ID, value='username')
    password = driver.find_element(by=By.ID, value='password')
    username.send_keys(mercadona_params['username'])
    password.send_keys(mercadona_params['password'])
    time.sleep(5)
    password.send_keys(Keys.ENTER)


def switch_table_frame():
    driver.switch_to.default_content()
    driver.switch_to.frame(main_frame)


def switch_sections_frame():
    driver.switch_to.default_content()
    driver.switch_to.frame(menu_frame)
    driver.switch_to.frame(sections_frame)


def get_is_by_weight(row):
    return driver.find_element(
        by=By.XPATH,
        value=f'//*[@id="TaulaLlista"]/tbody/tr[{row}]/td[1]/span/img'
    ).get_attribute('title') == 'PRODUCTOS A PESO'


def get_name(row):
    name, brand, size = None, None, None

    full_name = driver.find_element(
        by=By.XPATH,
        value=f'//*[@id="TaulaLlista"]/tbody/tr[{row}]/td[1]/span').text

    try:
        name, brand, size = full_name.rsplit(sep=',', maxsplit=2)
    except ValueError:
        name = full_name
    finally:
        return name, brand, size


def get_details(row):
    details = None
    try:
        details = driver.find_element(
            by=By.XPATH,
            value=f'//*[@id="TaulaLlista"]/tbody/tr[{row}]/td[2]/span/a'
        ).get_attribute('href')
    finally:
        return details


def get_price(row):
    price = driver.find_element(
        by=By.XPATH,
        value=f'//*[@id="TaulaLlista"]/tbody/tr[{row}]/td[3]/span[1]').text

    return atof(price.split(' ')[0])


def process_section(same_section=False):
    global data_products
    if not same_section:
        switch_table_frame()

    products = driver.find_elements(by=By.XPATH,
                                    value='//*[@id="TaulaLlista"]/tbody/tr')
    for i, product in enumerate(products, 1):
        data = dict()

        data['is_by_weight'] = get_is_by_weight(i)

        name, brand, size = get_name(i)
        data['name'] = name
        data['brand'] = brand
        data['size'] = size

        data['details'] = get_details(i)

        data['price'] = get_price(i)

        data_products = pd.concat([data_products, pd.DataFrame([data])])

    if next_button := driver.find_elements(by=By.ID, value='NEXT'):
        next_button[0].click()
        time.sleep(2)
        return process_section(same_section=True)

    switch_sections_frame()


def navigate(level):
    if root_section := driver.find_elements(
            by=By.CLASS_NAME, value=f'ulnivel{level}'):
        for section in root_section[0].find_elements(
                by=By.TAG_NAME, value='li'):
            time.sleep(2)
            section.find_element(by=By.TAG_NAME, value='a').click()
            if section.find_elements(
                    by=By.CLASS_NAME, value=f'ulnivel{level + 1}'):
                navigate(level + 1)
            else:
                process_section()


def main():
    global main_frame
    global sections_frame
    global menu_frame
    setlocale(LC_NUMERIC, '')

    try:
        driver.get("https://www.telecompra.mercadona.es/ns/entrada.php")
        login()

        main_frame = WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located((By.ID, "mainFrame")))

        menu_frame = driver.find_element(by=By.ID, value='toc')
        driver.switch_to.frame(menu_frame)
        sections_frame = driver.find_element(by=By.ID, value='menu')
        driver.switch_to.frame(sections_frame)

        navigate(FIRST_LEVEL)
        save_df(data_products)

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
