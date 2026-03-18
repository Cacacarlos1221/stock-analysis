#!/usr/bin/env python3
"""
股票监控工具 - 腾讯数据源版
使用腾讯股票 API 获取 A 股实时行情（更稳定）
"""

import requests
import re
from datetime import datetime

# 关注的股票列表
WATCH_LIST = [
    {"name": "完美世界", "code": "002624", "market": "sz"},
    {"name": "北方稀土", "code": "600111", "market": "sh"},
    {"name": "升达林业", "code": "002259", "market": "sz"},
]

def get_stock_realtime_tencent(code: str, market: str) -> dict:
    """
    使用腾讯 API 获取实时行情
    """
    try:
        symbol = f"{market}{code}"
        url = f"http://qt.gtimg.cn/q={symbol}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'
        
        text = response.text
        
        # 解析返回数据
        # 格式: v_sz002624="1~完美世界~002624~..."
        match = re.search(r'="([^"]+)"', text)
        if not match:
            return None
        
        parts = match.group(1).split('~')
        
        if len(parts) < 35:
            return None
        
        return {
            "名称": parts[1],
            "代码": parts[2],
            "最新价": float(parts[3]) if parts[3] else 0,
            "昨收": float(parts[4]) if parts[4] else 0,
            "今开": float(parts[5]) if parts[5] else 0,
            "成交量": int(float(parts[6])) if parts[6] else 0,
            "成交额": float(parts[37]) if len(parts) > 37 and parts[37] else 0,
            "涨跌额": float(parts[31]) if parts[31] else 0,
            "涨跌幅": float(parts[32]) if parts[32] else 0,
            "最高": float(parts[33]) if parts[33] else 0,
            "最低": float(parts[34]) if parts[34] else 0,
        }
    except Exception as e:
        print(f"  错误: {e}")
        return None


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
    
    for stock_info in WATCH_LIST:
        print(f"\n🔍 查询: {stock_info['name']} ({stock_info['code']})")
        data = get_stock_realtime_tencent(stock_info['code'], stock_info['market'])
        print_stock_info(data)
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        print(get_market_status())
    else:
        monitor_stocks()
