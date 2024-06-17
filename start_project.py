# -*- coding:utf-8 -*-
import os
import time
from datetime import datetime
import argparse
from pathlib import Path
from collections import defaultdict

import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler

from utils import get_date, logger, read_key_words
from baiduspider import BaiduSpider

# 定时任务
def schedule_daily_task(daily_task, task_args=None, hour=17, minute=20):
    # 创建一个调度器对象
    scheduler = BlockingScheduler()

    # 添加每日定时任务，在每天指定小时和分钟执行
    scheduler.add_job(daily_task, 'cron', args=task_args, hour=hour, minute=minute, max_instances=3)

    # 启动调度器
    scheduler.start()


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--start_date",
        type=str,
        default=None,
        help="The start time of the spider",
    )

    parser.add_argument(
        "--timed_task",
        action='store_true',
        help="Timed task",
    )

    return parser.parse_args()


def crate_xlsx_file(responses, file_path):
    excel_writer = pd.ExcelWriter(file_path, engine='openpyxl')

    for response in responses:
        for key, value in response.items():
            expanded_data = []
            for item in value:
                for detail in item['detal']:
                    expanded_item = {'类别': item['category'], '搜索词': item['key_word'], **detail}
                    expanded_data.append(expanded_item)
            df = pd.DataFrame(expanded_data)
            # df = df[df.日期.str.contains(fr"小时|{now}| ")]
            df.drop_duplicates(subset='标题', inplace=True)
            df.to_excel(excel_writer, sheet_name=key, index=False)

    # 保存Excel文件
    excel_writer.close()


def baidu_search(now, file_path):

    # 读取关键词
    key_words_lst = read_key_words()

    # 初始化爬虫对象
    spider = BaiduSpider()
    responses = []
    sheet_name, category = '', '', 
    current_dct = defaultdict(list)
    for key_word in key_words_lst:
        if key_word.startswith('# '):
            if sheet_name:
                responses.append(current_dct)
                current_dct = defaultdict(list)
            sheet_name = key_word[2:]
        elif key_word.startswith('## '):
            category = key_word[3:]
        else:
            # 抓取详情
            detal = spider.search_news(query=key_word, sort_by='time').plain
            # 按时间去除
            detal_select = []
            for item in detal:
                if '小时' in item['日期'] or now in item['日期'] or item['日期'] == ' ':
                    detal_select.append(item)
                else:
                    break

            current_dct[sheet_name].append({
                'category': category,
                'key_word': key_word,
                'detal': detal_select
            })
            logger.info(f'当前爬取对象：{sheet_name}-{category}-{key_word}')
            time.sleep(1)
    responses.append(current_dct)
    # 采集完成，写入excel
    crate_xlsx_file(responses, file_path)


def start(start_date):
    
    # 获取日期
    now, year_month = get_date(yesterday=False)    # 定时任务，这里需要每天计算
    # 指定文件
    file_path = Path(f"xls_files/{year_month}/{now}.xlsx")
    
    # 百度资讯爬虫
    logger.info(f'百度资讯爬取')
    baidu_search(now, file_path)

    # 其他网站
    code_path = "./websites/"
    file_list = os.listdir(code_path)
    logger.info(f'运行文件列表： {file_list}')
    for file in file_list:
        os.system(f'python3 {code_path}/{file} --start_date {now} --file_path {file_path}')

    logger.info(f'*****爬取完成*****\n\n\n')


if __name__ == "__main__":
    args = get_args()
    if args.timed_task:
        print("定时任务启动")
        schedule_daily_task(start, task_args=(args.start_date, ), hour=23, minute=0)
    else:
        start(args.start_date)
