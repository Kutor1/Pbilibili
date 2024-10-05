import time
import json
from lib2to3.pgen2 import driver

import scrapy
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from scrapy.http import HtmlResponse

from pb.items import PbItem


class PiliSpider(scrapy.Spider):
    name = "pili"
    allowed_domains = ["search.bilibili.com", "www.bilibili.com"]
    start_urls = ["https://search.bilibili.com/all?vt=34593826&keyword=%E9%97%AA%E8%80%80%E8%89%B2%E5%BD%A9&from_source=webtop_search&spm_id_from=333.1007&search_source=5", "https://www.bilibili.com/video/BV1FApEePELN/"]

    page = 1
    page_number = 0
    links = ''
    data_path = 'items_data.json'

    def __init__(self, *args, **kwargs):
        super(PiliSpider, self).__init__(*args, **kwargs)
        # 初始化 Selenium WebDriver（这里使用 Chrome）
        chrome_driver_path = 'C:/Program Files/Google/Chrome/Application/chromedriver.exe'  # 设置浏览器Driver路径
        user_data_dir = 'D:/google-user-data'  # 设置用户数据目录路径

        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={user_data_dir}")  # 设置用户数据目录
        chrome_options.add_argument("profile-directory=Default")  # 指定配置文件目录

        self.driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)

    def start_requests(self):
        for url in self.start_urls:
            # print(url)
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):

        # print(1)
        self.links = self.load_all_links(self.data_path)
        self.page = self.page + 1
        self.page_number = self.page_number + 36

        items = PbItem()
        self.driver.get(response.url)
        # 获取页面 HTML 源代码
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        # 检测到页尾时，进行下一步操作。
        if soup.find('div', class_='search-nodata-container p_relative'):
            # self.close_spider()
            for link in self.links:
                time.sleep(3)
                # self.driver.get("https://" + link)
                self.net_operate(link)
                time.sleep(3)
            self.close_spider()

        links = response.xpath('//div[@class="bili-video-card__wrap __scale-wrap"]/a/@href').extract()
        for link in links:
            link = re.sub(r'//', '', link)
            items['link'] = link
            yield items

        next_url = self.get_current_index(response.url)
        yield scrapy.Request(url=next_url, callback=self.parse)

    def net_operate(self, url):
        # 打开网页进行操作
        link = "https://" + url
        print(link)
        self.driver.get(link)
        time.sleep(1)

        # 调用操作方法
        self.pop_love()
        self.comment()

    # 点赞方法
    def pop_love(self):

        # 检测到未点赞时，点赞，并跳出当前步骤
        try:
            love_element = self.driver.find_element(By.XPATH, "//div[@class='video-like video-toolbar-left-item']")
            time.sleep(0.5)
            love_element.click()
            time.sleep(2)
            pass
        except: print("love on")

        time.sleep(1)

        # 检测到已点赞时，直接跳出
        try:
            love_on_element = self.driver.find_element(By.XPATH, "//div[@class='video-like video-toolbar-left-item on']")
            pass
        except: pass

    # 评论方法
    def comment(self):
        comment_script = """
        return document.querySelector('bili-comments').shadowRoot
          .querySelector('bili-comments-header-renderer').shadowRoot
          .querySelector('bili-comment-box').shadowRoot.querySelector('bili-comment-rich-textarea')
        """
        # 执行脚本并获取目标元素
        comment_element = self.driver.execute_script(comment_script)
        comment_element.click()
        comment_element.send_keys("好用心的视频！")

        pub_script = """
        return document.querySelector('bili-comments').shadowRoot
          .querySelector('bili-comments-header-renderer').shadowRoot
          .querySelector('bili-comment-box').shadowRoot.querySelector('[data-v-risk="fingerprint"]')
        """

        # 执行脚本并获取目标元素
        pub_element = self.driver.execute_script(pub_script)
        self.driver.execute_script("arguments[0].click();", pub_element)
        time.sleep(3)

    # 构造下一页的页码
    def get_current_index(self, url):
        # 解析 URL 中的 index 参数
        new_url = re.sub(r'search_source=5.*', f'search_source=5&page={self.page}&o={self.page_number}', url)
        return new_url

    # 获取所有链接
    def load_all_links(self, json_file_path):
        links = set()  # 使用集合以避免重复的链接
        with open(json_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item_dict = json.loads(line)
                        if 'link' in item_dict:
                            links.add(item_dict['link'])
                    except json.JSONDecodeError:
                        # 处理无效的 JSON 行
                        print(f"Skipping invalid JSON line: {line}")

        return links

    def close_spider(self, spider):
        self.driver.quit()
