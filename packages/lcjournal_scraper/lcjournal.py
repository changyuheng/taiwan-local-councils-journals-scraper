import logging
import os
import pathlib
import shutil
import stat
import time
from typing import Any, Callable, Optional, Union

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from .config import Config
from .log import get_logger


class SimpleLCJournal:
    HOME_PAGE: str = "https://journal.th.gov.tw/"

    def __init__(self, config: Config) -> None:
        self.cache_path: pathlib.Path = pathlib.Path("cache").absolute()
        self.config: Config = config

        self.clear_cache()

        LOGGER.setLevel(logging.WARNING)
        if config.browser.lower() == 'firefox':
            self.browser_driver: webdriver.Firefox = webdriver.Firefox(
                service=Service(GeckoDriverManager().install()))
        else:
            edge_options: webdriver.EdgeOptions = webdriver.EdgeOptions()
            edge_options.add_argument(f"user-data-dir={self.cache_path}")
            self.browser_driver: webdriver.Edge = webdriver.Edge(
                EdgeChromiumDriverManager().install(), options=edge_options)

    def clear_cache(self) -> None:
        def on_rm_error(func: Callable[[Any], None], path: str, exc_info: Any):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        if self.cache_path.is_dir():
            shutil.rmtree(self.cache_path, onerror=on_rm_error)
        if not self.cache_path.is_dir():
            self.cache_path.mkdir()

    def _get_metas_from_search_result_link_element(self, link: WebElement) -> dict[str, str]:
        meta: dict[str, str] = dict()
        e: Optional[Union[ElementClickInterceptedException, TimeoutException]] = None
        search_window: str = self.browser_driver.current_window_handle

        i: int
        for i in range(100):
            try:
                link.click()
                d: webdriver.Edge | webdriver.Firefox
                WebDriverWait(self.browser_driver, 10).until(lambda d: len(d.window_handles) > 1)
                self.browser_driver.switch_to.window(
                    self.browser_driver.window_handles[len(self.browser_driver.window_handles) - 1])
                WebDriverWait(self.browser_driver, 10).until(
                    lambda d: d.find_element(By.CLASS_NAME, 'project_object_area'))
            except (ElementClickInterceptedException, TimeoutException) as e:
                get_logger().info(f"retry: {i+1}")
                while len(self.browser_driver.window_handles) > 1:
                    self.browser_driver.switch_to.window(
                        self.browser_driver.window_handles[len(self.browser_driver.window_handles) - 1])
                    self.browser_driver.close()
                self.browser_driver.switch_to.window(search_window)
                time.sleep(1)
                continue
            else:
                break
        else:
            if e:
                raise e

        data_table: WebElement = self.browser_driver.find_element(By.CLASS_NAME, 'meta_table')
        field: WebElement
        value: WebElement
        meta: dict[str, str] = {"連結": self.browser_driver.current_url}
        for field, value in zip(
                data_table.find_elements(By.CLASS_NAME, 'meta_field'),
                data_table.find_elements(By.CLASS_NAME, 'meta_value')):
            if not field.text.strip():
                continue
            meta[field.text.strip().removesuffix("：")] = value.text.strip()

        self.browser_driver.close()
        self.browser_driver.switch_to.window(search_window)
        return meta

    def search(self, keyword: str, councils: Optional[list[str]] = None) -> list[dict[str, str]]:
        results: list[dict[str, str]] = list()
        e: Optional[TimeoutException] = None

        i: int
        for i in range(100):
            try:
                self.browser_driver.get(self.HOME_PAGE)
                d: webdriver.Edge | webdriver.Firefox
                WebDriverWait(self.browser_driver, 10).until(lambda d: d.find_element(By.ID, 'MenuBar1'))
                self.browser_driver.find_element(By.XPATH, "//*[@id='menu']/ul/li[2]/a").click()

                WebDriverWait(self.browser_driver, 10).until(lambda d: d.find_element(By.ID, 'search_input'))
                WebDriverWait(self.browser_driver, 10).until(lambda d: d.find_element(By.ID, 'search_submit'))
                WebDriverWait(self.browser_driver, 10).until(lambda d: d.find_element(By.ID, 'council_selecter'))

                if councils:
                    element: WebElement = self.browser_driver.find_element(By.ID, 'all_organ_filter')
                    if element.is_selected():
                        element.click()
                    for element in self.browser_driver.find_elements(By.XPATH, "//ul[@class='council_list']/li"):
                        council: str
                        for council in councils:
                            if element.find_elements(By.XPATH, f".//span[text()='{council}']"):
                                element.find_element(By.XPATH, ".//input").click()
                self.browser_driver.find_element(By.ID, 'search_input').clear()
                self.browser_driver.find_element(By.ID, 'search_input').send_keys(keyword)
                self.browser_driver.find_element(By.ID, 'search_submit').click()
                WebDriverWait(self.browser_driver, 10).until(lambda d: d.find_element(
                    By.XPATH, f'//span[text()="{keyword}"]'))
            except TimeoutException as e:
                get_logger().info(f"retry: {i+1}")
                time.sleep(1)
                continue
            else:
                break
        else:
            if e:
                raise e

        if self.browser_driver.find_elements(By.CLASS_NAME, 'page_ctrl_area.tr_like'):
            while True:
                current_page_num: int = int(self.browser_driver.find_element(By.CLASS_NAME, "page_now").text.strip())
                get_logger().info(f"current page: {current_page_num}")

                element: WebElement
                for element in self.browser_driver.find_elements(By.CLASS_NAME, 'result_content'):
                    result: dict[str, str] = {
                        "來源": element.find_element(By.CLASS_NAME, "result_source").text.strip().removeprefix("來源:"),
                        "標題": element.find_element(By.XPATH, ".//span[@class='acc_link']/a").text.strip(),
                        # "典藏序號及頁碼": element.find_element(By.CLASS_NAME, "acc_type").text.strip(),
                    }
                    if result["標題"].startswith("雲林縣議會"):
                        result["來源"] = "雲林縣議會"
                        result["標題"] = result["標題"].removeprefix("雲林縣議會")
                    # field: WebElement
                    # value: WebElement
                    # for field, value in zip(
                    #         element.find_elements(By.CLASS_NAME, "field_name"),
                    #         element.find_elements(By.CLASS_NAME, "field_value")):
                    #     result[field.text.removeprefix(" » ").strip()] = value.text.removeprefix(" : ").strip()
                    result |= self._get_metas_from_search_result_link_element(
                        self.browser_driver.find_element(By.XPATH, ".//span[@class='acc_link']/a"))
                    result["相關內容摘要"] = element.find_element(By.CLASS_NAME, "result_text").text.strip() \
                        .replace("<search>", "") \
                        .replace("</search>", "")
                    results.append(result)

                if f"&Query_String={current_page_num}&" in self.browser_driver.find_element(
                        By.CLASS_NAME, "page_botton.pb_pagedw").get_attribute("href"):
                    break

                for i in range(100):
                    try:
                        self.browser_driver.find_element(By.CLASS_NAME, "page_botton.pb_pagedw").click()
                        WebDriverWait(self.browser_driver, 10).until(lambda d: d.find_element(
                            By.CLASS_NAME, "page_now").text.strip() != str(current_page_num))
                    except TimeoutException as e:
                        get_logger().info(f"retry: {i+1}")
                        time.sleep(1)
                        continue
                    else:
                        break
                else:
                    if e:
                        raise e
        return results

    def quit(self) -> None:
        if self.config.browser.lower() == 'firefox':
            self.browser_driver.close()
