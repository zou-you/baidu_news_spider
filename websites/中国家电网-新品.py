# -*- coding:utf-8 -*-
import requests
from pathlib import Path
import time
import sys
import os
import io
import re
import argparse
import random
from datetime import datetime
import sys 
sys.path.extend(['.', '..'])

from bs4 import BeautifulSoup
import pandas as pd

from utils import sleep_time, now, MyHeaders, logger, timeout, get_date, append_sheet_to_excel

requests.packages.urllib3.disable_warnings()

WEBSITE = "中国家电网-新品"
SHEET_NAME = "新产品资讯"
PRODUCTS = ["空调", "冰箱", "洗衣机", "电视影音", "智能家居"]
URL_MAPPING = {
    "空调": "http://ac.cheaa.com/xinpin.shtml",
    "冰箱": "http://icebox.cheaa.com/xinpin.shtml",
    "洗衣机": "http://washer.cheaa.com/xinpin.shtml",
    "电视影音": "http://digitalhome.cheaa.com/xinpin.shtml",
    "智能家居": "http://smarthome.cheaa.com/xinpin.shtml"
}


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--start_date",
        type=str,
        default=now,
        help="The start time of the spider",
    )

    parser.add_argument(
        "--file_path",
        type=str,
        default=None,
        help="The start time of the spider",
    )

    return parser.parse_args()


def get_bs(url):
    headers = {'User-Agent': random.choice(MyHeaders)}
    response = requests.get(url, headers=headers, verify=False)
    response.encoding = 'utf-8'
    bs = BeautifulSoup(response.text, 'html5lib')

    return bs


@timeout(3600)
def get_content(start_date=now, file_path=None):
    output = []
    for product in PRODUCTS: 
        logger.info(f"当前产品：{product}")

        # 访问链接
        bs = get_bs(URL_MAPPING[product])
        text_list = bs.select('.newsList li p.pctit a')
        time_list = bs.select('.newsList li p:nth-of-type(2)')

        # 找出符合要求的时间以及标题
        for text, tim in zip(text_list, time_list):
            source, date = tim.get_text(strip=True).split(' ')
            date = datetime.strptime(date, '%Y/%m/%d').strftime('%Y-%m-%d')
            if date < start_date:
                continue
            title = text.get_text().strip().replace('·', '').replace('\n', '').replace('\t', '')  # 获取纯文本内容（不带html标签）
            url = text['href']

            output.append({
                "标题": title,
                "来源": source,
                "日期": date,
                "简介": product,
                "链接": url,
                "网站": WEBSITE
            })

    if not file_path:
        now, year_month = get_date(yesterday=False)
        file_path = Path(f"xls_files/{year_month}/{now}.xlsx")

    # 保存结果
    df = pd.DataFrame(output, columns=["标题", "标签", "日期", "简介", "链接", "网站"])
    append_sheet_to_excel(df, file_path, SHEET_NAME)


if __name__ == "__main__":
    args = get_args()
    
    # 获取当前文件路径
    current_file_path = __file__
    # 使用 os.path.basename() 函数获取文件名，然后使用 os.path.splitext() 函数分割文件名和后缀
    current_file_name = os.path.splitext(os.path.basename(current_file_path))[0]

    # 记录最大尝试次数
    attempts, max_attempts = 0, 3

    # 开始抓取
    logger.info(f"{'-'*20}{current_file_name} 开始抓取{'-'*20}")
    while attempts < max_attempts:
        try:
            get_content(args.start_date, args.file_path)
            break  # 如果代码成功执行，跳出循环
        except Exception as e:
            attempts += 1  # 增加尝试次数
            logger.error(f"{e}")
            time.sleep(2)
            if attempts == max_attempts:
                logger.error("已达到最大尝试次数，程序终止。")
            else:
                logger.info(f"当前重试次数{attempts}...")
    logger.info(f"{'-'*20}{current_file_name} 抓取完成{'-'*20}\n\n")
