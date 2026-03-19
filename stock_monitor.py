#!/usr/bin/env python3
"""
股票监控工具 - 腾讯数据源版
使用腾讯股票 API 获取 A 股实时行情（更稳定）
"""

import os
import requests
import re
from datetime import datetime

# 导入工具模块
from stock_utils import STOCKS, get_stock_realtime


def format_number(num):
    """格式化数字"""
    if num >= 100000000:
        return f"{num/100000000:.2f}亿"
    elif num >= 10000:
        return f"{num/10000:.2f}万"
    else:
        return f"{num:.0f}"


def get_market_status():
    """获取市场状态"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()
    
    if weekday >= 5:
        return "🚫 周末休市"
    
    if hour < 9 or (hour == 9 and minute < 30):
        return "⏰ 盘前（9:30开市）"
    elif (hour == 9 and minute >= 30) or (hour == 10) or (hour == 11 and minute <= 30):
        return "📈 上午交易中"
    elif hour == 11 and minute > 30:
        return "🍱 午间休市"
    elif hour == 12:
        return "🍱 午间休市"
    elif 13 <= hour < 15:
        return "📈 下午交易中"
    else:
        return "🌙 已收盘"


def print_stock_info(stock: dict):
    """打印股票信息"""
    if not stock or stock['最新价'] == 0:
        print("  ⏸️ 非交易时间或数据获取失败")
        return
    
    change_symbol = "📈" if stock['涨跌幅'] > 0 else "📉" if stock['涨跌幅'] < 0 else "➡️"
    color_start = "\033[91m" if stock['涨跌幅'] > 0 else "\033[92m" if stock['涨跌幅'] < 0 else ""
    color_end = "\033[0m"
    
    print(f"\n  {change_symbol} {stock['名称']} ({stock['代码']})")
    print(f"  最新价: ¥{stock['最新价']:.2f}")
    print(f"  涨跌幅: {color_start}{stock['涨跌幅']:+.2f}%{color_end}")
    print(f"  涨跌额: {color_start}{stock['涨跌额']:+.2f}{color_end}")
    print(f"  今开: ¥{stock['今开']:.2f} | 昨收: ¥{stock['昨收']:.2f}")
    print(f"  最高: ¥{stock['最高']:.2f} | 最低: ¥{stock['最低']:.2f}")
    print(f"  成交量: {format_number(stock['成交量'])}股")
    print(f"  成交额: {format_number(stock['成交额'])}元")


def monitor_stocks():
    """监控股票"""
    status = get_market_status()
    print("=" * 50)
    print(f"📊 股票监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   市场状态: {status}")
    print("=" * 50)
    
    for stock_info in STOCKS:
        print(f"\n🔍 查询: {stock_info['name']} ({stock_info['code']})")
        symbol = f"{stock_info['market']}{stock_info['code']}"
        data = get_stock_realtime(symbol)
        print_stock_info(data)
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        print(get_market_status())
    else:
        monitor_stocks()
