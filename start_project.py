# -*- coding:utf-8 -*-
import os
import time
from datetime import datetime
import argparse
from pathlib import Path

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
        "--only_start_date",
        action='store_true',
        help="Only the start date is recorded",
    )

    parser.add_argument(
        "--timed_task",
        action='store_true',
        help="Timed task",
    )

    return parser.parse_args()


def crate_xlsx_file(responses, now, year_month):
    df = pd.DataFrame(responses)
    df = df[df.日期.str.contains(fr"小时|{now}| ")]
    file_path = Path(f"xls_files/{year_month}/{now}.xlsx")
    df.to_excel(file_path, index=False)

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
    for key_word in key_words_lst:
        responses.extend(spider.search_news(query=key_word, sort_by='time').plain)
        time.sleep(2)

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
