from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from rest_framework.test import APIRequestFactory, APIClient
from selenium import webdriver
import sys
import time
import os
from selenium.common.exceptions import StaleElementReferenceException

class FunctionalTest(StaticLiveServerTestCase):  #1
    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_url = 'http://' + arg.split('=')[1]
                return
        super().setUpClass()
        cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url == cls.live_server_url:
            super().tearDownClass()

    def setUp(self):
        try:
            if os.environ['BROWSER_TEST'] == "chrome":
                self.browser = webdriver.Chrome()
            else:
                raise KeyError
        except KeyError:
            self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()

    def click_link_and_wait(self, link):
        link.click()

        def link_has_gone_stale():
            try:
                # poll the link with an arbitrary call
                link.find_elements_by_id('doesnt-matter')
                return False
            except StaleElementReferenceException:
                return True

        self.wait_for(link_has_gone_stale)

    def wait_for(self, condition_function):
        start_time = time.time()
        while time.time() < start_time + 3:
            if condition_function():
                return True
            else:
                time.sleep(0.1)
        raise Exception(
            'Timeout waiting for {}'.format(condition_function.__name__)
        )
