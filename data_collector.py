#!/usr/bin/env python3
"""
股票数据收集工具
用于定时任务收集每日收盘数据
"""

import requests
import re
import csv
import os
from datetime import datetime

# 股票列表
STOCKS = [
    {"name": "完美世界", "code": "002624", "market": "sz"},
    {"name": "北方稀土", "code": "600111", "market": "sh"},
    {"name": "升达林业", "code": "002259", "market": "sz"},
    {"name": "上证指数", "code": "000001", "market": "sh"},
]

# 数据文件路径
DATA_FILE = os.path.expanduser("~/Desktop/Experiment/stock-analysis/daily_data.csv")

# CSV 表头
CSV_HEADERS = [
    '日期', '股票代码', '股票名称', '昨日收盘', '今日开盘', '今日收盘',
    '涨跌幅%', '最高价', '最低价', '成交量', '成交额', '委买', '委卖',
    '换手率%', '振幅%', '量比', '市盈率', '总市值', '流通市值',
    'MA5', 'MA10', 'MA20', 'MACD', 'MACD信号', 'KDJ-K', 'KDJ-D', 'KDJ-J',
    'RSI6', 'RSI12', '主力净流入', '所属板块', '板块涨幅%', '涨跌家数比', '大盘成交额'
]


def get_stock_realtime(symbol: str):
    """
    使用腾讯 API 获取实时行情
    """
    try:
        url = f"http://qt.gtimg.cn/q={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'
        
        text = response.text
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
            "委买": int(float(parts[7])) if parts[7] else 0,
            "委卖": int(float(parts[8])) if parts[8] else 0,
            "换手率": float(parts[38]) if len(parts) > 38 and parts[38] else 0,
            "振幅": float(parts[43]) if len(parts) > 43 and parts[43] else 0,
            "量比": float(parts[49]) if len(parts) > 49 and parts[49] else 0,
            "市盈率": float(parts[52]) if len(parts) > 52 and parts[52] else 0,
            "总市值": float(parts[44]) if len(parts) > 44 and parts[44] else 0,
            "流通市值": float(parts[45]) if len(parts) > 45 and parts[45] else 0,
        }
    except Exception as e:
        print(f"获取 {symbol} 数据失败: {e}")
        return None


def collect_daily_data():
    """
    收集每日收盘数据
    """
    today = datetime.now().strftime('%Y-%m-%d')
    data_rows = []
    
    print(f"正在收集 {today} 的收盘数据...")
    
    for stock in STOCKS:
        symbol = f"{stock['market']}{stock['code']}"
        print(f"  查询: {stock['name']} ({stock['code']})")
        
        data = get_stock_realtime(symbol)
        if data:
            row = {
                '日期': today,
                '股票代码': stock['code'],
                '股票名称': stock['name'],
                '昨日收盘': data['昨收'],
                '今日开盘': data['今开'],
                '今日收盘': data['最新价'],
                '涨跌幅%': data['涨跌幅'],
                '最高价': data['最高'],
                '最低价': data['最低'],
                '成交量': data['成交量'],
                '成交额': data['成交额'],
                '委买': data['委买'],
                '委卖': data['委卖'],
                '换手率%': data['换手率'],
                '振幅%': data['振幅'],
                '量比': data['量比'],
                '市盈率': data['市盈率'],
                '总市值': data['总市值'],
                '流通市值': data['流通市值'],
                # 以下字段需要计算或从其他接口获取
                'MA5': None,
                'MA10': None,
                'MA20': None,
                'MACD': None,
                'MACD信号': None,
                'KDJ-K': None,
                'KDJ-D': None,
                'KDJ-J': None,
                'RSI6': None,
                'RSI12': None,
                '主力净流入': None,
                '所属板块': None,
                '板块涨幅%': None,
                '涨跌家数比': None,
                '大盘成交额': None,
            }
            data_rows.append(row)
            print(f"    ✓ 获取成功")
        else:
            print(f"    ✗ 获取失败")
    
    return data_rows


def save_to_csv(data_rows):
    """
    保存数据到 CSV 文件
    """
    if not data_rows:
        print("没有数据可保存")
        return
    
    # 确保目录存在
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    # 检查文件是否存在
    file_exists = os.path.exists(DATA_FILE)
    
    # 写入 CSV
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(data_rows)
    
    print(f"\n✓ 数据已保存到 {DATA_FILE}")
    print(f"  共 {len(data_rows)} 条记录")


def generate_report(data_rows):
    """
    生成收盘总结报告
    """
    if not data_rows:
        return "数据获取失败，无法生成报告"
    
    report = f"📊 {data_rows[0]['日期']} 收盘总结\n\n"
    
    for row in data_rows:
        change_symbol = "📈" if row['涨跌幅%'] > 0 else "📉" if row['涨跌幅%'] < 0 else "➡️"
        report += f"{change_symbol} **{row['股票名称']} ({row['股票代码']})**\n"
        report += f"- 收盘: ¥{row['今日收盘']:.2f} ({row['涨跌幅%']:+.2f}%)\n"
        report += f"- 成交: {row['成交量']/10000:.2f}万手 / {row['成交额']/100000000:.2f}亿\n"
        report += f"- 最高: ¥{row['最高价']:.2f} | 最低: ¥{row['最低价']:.2f}\n\n"
    
    return report


def main():
    """
    主函数
    """
    print("=" * 50)
    print("股票数据收集工具")
    print("=" * 50)
    
    # 收集数据
    data_rows = collect_daily_data()
    
    if data_rows:
        # 保存到 CSV
        save_to_csv(data_rows)
        
        # 生成报告
        report = generate_report(data_rows)
        print("\n" + "=" * 50)
        print(report)
    else:
        print("\n数据收集失败")


if __name__ == "__main__":
    main()
