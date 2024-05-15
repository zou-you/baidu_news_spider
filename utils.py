import re
import time
import random
from datetime import datetime, timedelta
import os
from pathlib import Path

from logger import setup_logger

import signal
import time
from functools import wraps


def timeout(seconds):
    def decorator(func):
        def handler(signum, frame):
            raise TimeoutError("Function timed out")

        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wrapper
    return decorator


def read_key_words(file_path="key_words.txt"):
    key_list = []
    f = open(file_path, encoding='utf-8')  # 返回一个文件对象
    lines = f.readlines()  # 读取全部内容
    for line in lines:
        # 如果读到空行，就跳过
        if line.isspace():
            continue
        else:
            # 去除文本中的换行等等，可以追加其他操作
            line = line.replace("\n", "")
            line = line.replace("\t", "")
            # 处理完成后的行，追加到列表中
            key_list.append(line)
    f.close()
    return key_list


def get_date(yesterday=False): 
    # 获取当前日期
    date = datetime.now()

    # 计算昨天的日期
    if yesterday:
        date = date - timedelta(days=1)
    
    # 将日期格式化为字符串
    return date.strftime("%Y-%m-%d"), date.strftime("%Y年%m月")


# 创建当前日期文件夹
now, year_month = get_date(yesterday=False)
os.makedirs(f'xls_files/{year_month}', exist_ok=True)

# 生成随机睡眠时间
sleep_time = random.uniform(1, 2)

# 设置日志对象
os.makedirs(f'logs', exist_ok=True)
logger = setup_logger(
    log_name='Spider System',
    log_filename=Path('logs/spider.log'),
    log_level='info',
    use_console=False
)