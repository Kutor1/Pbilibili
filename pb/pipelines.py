# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import json

class PbPipeline:
    def __init__(self):
        # 初始化已存在的 BV 列表
        self.existing_bvs = set()
        self.load_existing_bvs()

    def load_existing_bvs(self):
        # 如果文件存在，读取其中所有的 BV 值
        try:
            with open('items_data.json', 'r', encoding='utf-8') as f:
                for line in f:
                    item_dict = json.loads(line)
                    if 'BV' in item_dict:
                        self.existing_bvs.add(item_dict['BV'])
        except FileNotFoundError:
            # 如果文件不存在，初始化为空集合
            self.existing_bvs = set()

    def process_item(self, item, spider):
        item_dict = dict(item)

        # 匹配并提取 BV
        match = re.search(r'/video/(BV\w+)', item['link'])
        if match:
            item_dict['BV'] = match.group(1)
        else:
            # 如果没有匹配到 BV，跳过这个 item
            return None

        # 检查 BV 是否已存在
        if item_dict['BV'] in self.existing_bvs:
            # 如果 BV 已存在，忽略这个 item
            return None

        # 添加额外的属性

        # 将 item 数据转换为 JSON 格式的字符串
        item_data = json.dumps(item_dict, ensure_ascii=False)

        # 将新的 BV 添加到已存在的集合中
        self.existing_bvs.add(item_dict['BV'])

        # 以追加模式 ('a') 打开 json 文件，并写入数据
        with open('items_data.json', 'a', encoding='utf-8') as f:
            f.write(item_data + '\n')  # 每次写入一个 item 并换行

        return item
