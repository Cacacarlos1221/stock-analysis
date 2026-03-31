#!/usr/bin/env python3
"""
股票历史数据收集工具 - 使用新浪API
用于收集每日收盘数据和技术指标
"""

import os
import json
import csv
import re
import requests
from datetime import datetime, timedelta
from io import StringIO

# 股票配置
STOCKS = [
    {"symbol": "sz002624", "code": "002624", "name": "完美世界", "market": "sz"},
    {"symbol": "sh600111", "code": "600111", "name": "北方稀土", "market": "sh"},
    {"symbol": "sz002259", "code": "002259", "name": "升达林业", "market": "sz"},
    {"symbol": "sh000001", "code": "000001", "name": "上证指数", "market": "sh"},
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "data", "raw", "prices", "stock_history.csv")

# CSV 表头
CSV_HEADERS = [
    '日期', '股票代码', '股票名称', '昨日收盘', '今日开盘', '今日收盘',
    '涨跌幅%', '最高价', '最低价', '成交量', '成交额', 'MA5', 'MA10', 'MA20',
    'MA5量', 'MA10量', 'MA20量'
]


def fetch_sina_kline(symbol: str, days: int = 30) -> list:
    """
    从新浪API获取K线数据
    """
    url = f"https://quotes.sina.cn/cn/api/jsonp.php/var%20_{symbol}=/CN_MarketDataService.getKLineData"
    params = {
        "symbol": symbol,
        "scale": "240",  # 日线
        "ma": "20",       # 包含20日均线
        "datalen": str(days)
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        text = response.text
        
        # 解析 JSONP 格式 - 找到 [ 和 ] 之间的内容
        start = text.find('[')
        end = text.rfind(']')
        
        if start >= 0 and end > start:
            json_str = text[start:end+1]
            data = json.loads(json_str)
            return data if data else []
        return []
    except Exception as e:
        print(f"获取 {symbol} 数据失败: {e}")
        return []


def calculate_change_pct(row: dict, prev_close: float = None) -> float:
    """计算涨跌幅"""
    try:
        close = float(row.get('close', 0))
        if prev_close:
            return round((close - prev_close) / prev_close * 100, 2)
        # 用开盘价和收盘价估算
        open_price = float(row.get('open', 0))
        if open_price and close:
            return round((close - open_price) / open_price * 100, 2)
    except:
        pass
    return 0.0


def save_to_csv(data_rows: list):
    """保存数据到CSV"""
    if not data_rows:
        print("没有数据可保存")
        return
    
    # 按日期排序（新的在前）
    data_rows.sort(key=lambda x: x.get('日期', ''), reverse=True)
    
    # 写入CSV
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(data_rows)
    
    print(f"\n✓ 数据已保存到 {DATA_FILE}")
    print(f"  共 {len(data_rows)} 条记录")


def main():
    print("=" * 60)
    print("股票历史数据收集工具 (新浪API)")
    print("=" * 60)
    
    all_data = []
    
    for stock in STOCKS:
        symbol = stock['symbol']
        code = stock['code']
        name = stock['name']
        
        print(f"\n查询: {name} ({code})")
        
        # 获取30天数据
        klines = fetch_sina_kline(symbol, days=30)
        
        if not klines:
            print(f"  ✗ 获取失败")
            continue
        
        print(f"  ✓ 获取 {len(klines)} 条数据")
        
        for i, row in enumerate(klines):
            # 计算昨日收盘价
            prev_close = None
            if i < len(klines) - 1:
                try:
                    prev_close = float(klines[i + 1].get('close', 0))
                except:
                    pass
            
            try:
                close = float(row.get('close', 0))
                open_price = float(row.get('open', 0))
                high = float(row.get('high', 0))
                low = float(row.get('low', 0))
                volume = int(row.get('volume', 0))
                
                # 计算涨跌额和涨跌幅
                if prev_close:
                    change_pct = round((close - prev_close) / prev_close * 100, 2)
                    change = round(close - prev_close, 2)
                else:
                    change_pct = round((close - open_price) / open_price * 100, 2)
                    change = round(close - open_price, 2)
                
                data_row = {
                    '日期': row.get('day', ''),
                    '股票代码': code,
                    '股票名称': name,
                    '昨日收盘': prev_close if prev_close else '',
                    '今日开盘': open_price,
                    '今日收盘': close,
                    '涨跌幅%': change_pct,
                    '最高价': high,
                    '最低价': low,
                    '成交量': volume,
                    '成交额': '',
                    'MA5': row.get('ma_price5', ''),
                    'MA10': row.get('ma_price10', ''),
                    'MA20': row.get('ma_price20', ''),
                    'MA5量': row.get('ma_volume5', ''),
                    'MA10量': row.get('ma_volume10', ''),
                    'MA20量': row.get('ma_volume20', ''),
                }
                all_data.append(data_row)
            except Exception as e:
                print(f"  处理数据出错: {e}")
                continue
    
    if all_data:
        save_to_csv(all_data)
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("📊 今日数据摘要")
        print("=" * 60)
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_data = [r for r in all_data if r['日期'] == today]
        
        for row in today_data:
            change_symbol = "📈" if float(row['涨跌幅%'] or 0) > 0 else "📉" if float(row['涨跌幅%'] or 0) < 0 else "➡️"
            print(f"{change_symbol} {row['股票名称']}: ¥{row['今日收盘']} ({row['涨跌幅%']}%)")
    else:
        print("\n没有获取到数据")


if __name__ == "__main__":
    main()
