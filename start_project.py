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


def crate_xlsx_file(responses, now, year_month):
    file_path = Path(f"xls_files/{year_month}/{now}.xlsx")
    excel_writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    for response in responses:
        for key, value in response.items():
            expanded_data = []
            for item in value:
                for detail in item['detal']:
                    expanded_item = {'类别': item['category'], '搜索词': item['key_word'], **detail}
                    expanded_data.append(expanded_item)
            df = pd.DataFrame(expanded_data)
            df = df[df.日期.str.contains(fr"小时|{now}| ")]
            df.drop_duplicates(subset='标题', inplace=True)
            df.to_excel(excel_writer, sheet_name=key, index=False)

    # 保存Excel文件
    excel_writer.close()

def start(start_date):
    now, year_month = get_date(yesterday=False)    # 定时任务，这里需要每天计算
    if not start_date:
        start_date = now

    # 读取关键词
    key_words_lst = read_key_words()

    # 初始化爬虫对象
    spider = BaiduSpider()

    # 开始爬虫
    logger.info(f'开始爬取时间 {start_date}')
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
            current_dct[sheet_name].append({
                'category': category,
                'key_word': key_word,
                'detal': spider.search_news(query=key_word, sort_by='time').plain
            })
            logger.info(f'当前爬取对象：{sheet_name}-{category}-{key_word}')
            time.sleep(1)
    responses.append(current_dct)
    # 采集完成，写入excel
    crate_xlsx_file(responses, now, year_month)

    logger.info(f'*****爬取完成*****\n\n\n')


if __name__ == "__main__":
    args = get_args()
    if args.timed_task:
        print("定时任务启动")
        schedule_daily_task(start, task_args=(args.start_date, ), hour=22, minute=0)
    else:
        start(args.start_date)
