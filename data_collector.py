#!/usr/bin/env python3
"""
股票数据收集工具
用于定时任务收集每日收盘数据
"""

import os
import csv
from datetime import datetime, timedelta

# 导入工具模块
from stock_utils import STOCKS, get_stock_realtime
from fetch_history import (
    calculate_ma, calculate_macd, calculate_kdj, calculate_rsi,
    fetch_stock_history
)

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据文件路径（使用脚本相对路径）
DATA_FILE = os.path.join(SCRIPT_DIR, "daily_data.csv")

# CSV 表头
CSV_HEADERS = [
    '日期', '股票代码', '股票名称', '昨日收盘', '今日开盘', '今日收盘',
    '涨跌幅%', '最高价', '最低价', '成交量', '成交额', '委买', '委卖',
    '换手率%', '振幅%', '量比', '市盈率', '总市值', '流通市值',
    'MA5', 'MA10', 'MA20', 'MACD', 'MACD信号', 'KDJ-K', 'KDJ-D', 'KDJ-J',
    'RSI6', 'RSI12', '主力净流入', '所属板块', '板块涨幅%', '涨跌家数比', '大盘成交额'
]


def calculate_technical_indicators(stock_code: str):
    """
    计算技术指标
    从历史数据中获取并计算 MA, MACD, KDJ, RSI
    """
    try:
        # 获取最近60个交易日的数据用于计算技术指标
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
        
        df = fetch_stock_history(stock_code, start_date, end_date)
        if df is None or df.empty:
            return {}
        
        # 重命名列
        df = df.rename(columns={
            '日期': '日期',
            '开盘': '今日开盘',
            '收盘': '今日收盘',
            '最高': '最高价',
            '最低': '最低价',
            '成交量': '成交量',
            '成交额': '成交额',
        })
        
        # 计算技术指标
        df = calculate_ma(df)
        df = calculate_macd(df)
        df = calculate_kdj(df)
        df = calculate_rsi(df)
        
        # 获取最新的技术指标值
        if not df.empty:
            latest = df.iloc[-1]
            return {
                'MA5': latest.get('MA5'),
                'MA10': latest.get('MA10'),
                'MA20': latest.get('MA20'),
                'MACD': latest.get('MACD'),
                'MACD信号': latest.get('MACD信号'),
                'KDJ-K': latest.get('KDJ-K'),
                'KDJ-D': latest.get('KDJ-D'),
                'KDJ-J': latest.get('KDJ-J'),
                'RSI6': latest.get('RSI6'),
                'RSI12': latest.get('RSI12'),
            }
    except Exception as e:
        print(f"    计算技术指标失败: {e}")
    
    return {}


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
            # 获取技术指标
            tech_indicators = calculate_technical_indicators(stock['code'])
            
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
                # 技术指标
                'MA5': tech_indicators.get('MA5'),
                'MA10': tech_indicators.get('MA10'),
                'MA20': tech_indicators.get('MA20'),
                'MACD': tech_indicators.get('MACD'),
                'MACD信号': tech_indicators.get('MACD信号'),
                'KDJ-K': tech_indicators.get('KDJ-K'),
                'KDJ-D': tech_indicators.get('KDJ-D'),
                'KDJ-J': tech_indicators.get('KDJ-J'),
                'RSI6': tech_indicators.get('RSI6'),
                'RSI12': tech_indicators.get('RSI12'),
                # 以下字段需要计算或从其他接口获取
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
