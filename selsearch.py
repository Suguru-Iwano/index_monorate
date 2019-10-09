#!/usr/bin/env python3
from selenium.webdriver import Firefox, FirefoxOptions # pip3 install selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup # pip3 install bs4

import os
import time


class DriverQuitException(Exception):
    """Driver の quit() に失敗したException"""
    pass


class SeleniumSearch(object):

    def recreate_driver(self, driver_name='Firefox', headless=True):
        """
        ＊面倒だから、今はFirefoxしか対応してないよ！
        create_driver return new driver.
        default is driver->Firefox headless->True.

        Args:
            driver_name (str):
                driver_name is the name of the driver you want.
            headless (bool):

        Returns:
            driver (Firefox and more...):
                driver type is the same as driver_name.
        Raises:
            Exception: DriverQuitException

        """
        if self.driver is not None:
            try:
                self.driver.quit()
            except:
                raise DriverQuitException
            self.driver = None

        # Firefox用
        if driver_name.upper() == 'FIREFOX':
            options = FirefoxOptions()
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--proxy-server='direct://'")
            options.add_argument("--proxy-bypass-list=*")
            options.add_argument("--start-maximized")
            if headless:
                options.add_argument("--headless")
            self.driver = Firefox(options=options, log_path=os.path.devnull)
        return self.driver


    def get_driver(self):
        if self.driver is None:
            recreate_driver(self.driver_name, self.headless)
        return self.driver


    def __init__ (self, driver_name='Firefox', headless=True):
        self.driver = None
        self.driver_name = driver_name
        self.headless = headless
        self.recreate_driver(driver_name=driver_name, headless=headless)
