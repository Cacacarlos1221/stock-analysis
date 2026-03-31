#!/usr/bin/env python3
"""
历史数据抓取工具
使用 akshare 获取股票历史数据
"""

import os
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 导入工具模块获取统一股票列表
from stock_utils import STOCKS

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据文件路径（使用脚本相对路径）
DATA_FILE = os.path.join(SCRIPT_DIR, "data", "raw", "prices", "daily_data.csv")


def fetch_stock_history(code: str, start_date: str, end_date: str):
    """
    获取股票历史数据
    """
    try:
        # 使用 akshare 获取日K线数据
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        return df
    except Exception as e:
        print(f"获取 {code} 历史数据失败: {e}")
        return None


def calculate_ma(df, periods=[5, 10, 20]):
    """
    计算移动平均线
    """
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
    return df


def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算 MACD
    """
    ema_fast = df['收盘'].ewm(span=fast).mean()
    ema_slow = df['收盘'].ewm(span=slow).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD信号'] = df['MACD'].ewm(span=signal).mean()
    return df


def calculate_kdj(df, n=9, m1=3, m2=3):
    """
    计算 KDJ
    """
    low_list = df['最低'].rolling(window=n, min_periods=n).min()
    high_list = df['最高'].rolling(window=n, min_periods=n).max()
    rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
    
    df['KDJ-K'] = rsv.ewm(alpha=1/m1).mean()
    df['KDJ-D'] = df['KDJ-K'].ewm(alpha=1/m2).mean()
    df['KDJ-J'] = 3 * df['KDJ-K'] - 2 * df['KDJ-D']
    return df


def calculate_rsi(df, periods=[6, 12]):
    """
    计算 RSI
    """
    for period in periods:
        delta = df['收盘'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f'RSI{period}'] = 100 - (100 / (1 + rs))
    return df


def process_stock_data(df, stock_info):
    """
    处理股票数据，计算指标
    """
    if df is None or df.empty:
        return None
    
    # 重命名列
    df = df.rename(columns={
        '日期': '日期',
        '开盘': '今日开盘',
        '收盘': '今日收盘',
        '最高': '最高价',
        '最低': '最低价',
        '成交量': '成交量',
        '成交额': '成交额',
        '振幅': '振幅',
        '涨跌幅': '涨跌幅',
        '涨跌额': '涨跌额',
        '换手率': '换手率'
    })
    
    # 添加股票信息
    df['股票代码'] = stock_info['code']
    df['股票名称'] = stock_info['name']
    
    # 计算昨日收盘（前一天的收盘）
    df['昨日收盘'] = df['今日收盘'].shift(1)
    
    # 计算技术指标
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_kdj(df)
    df = calculate_rsi(df)
    
    # 计算其他指标
    df['市盈率'] = None  # 需要另外获取
    df['总市值'] = None  # 需要另外获取
    df['流通市值'] = None  # 需要另外获取
    df['委买'] = None  # 实时数据，无法获取历史
    df['委卖'] = None  # 实时数据，无法获取历史
    df['量比'] = None  # 需要计算
    df['主力净流入'] = None  # 实时数据，无法获取历史
    df['所属板块'] = None  # 需要另外获取
    df['板块涨幅'] = None  # 实时数据，无法获取历史
    df['涨跌家数比'] = None  # 大盘数据，需要另外获取
    df['大盘成交额'] = None  # 大盘数据，需要另外获取
    
    return df


def fetch_all_history(start_date: str, end_date: str):
    """
    获取所有股票的历史数据
    """
    all_data = []
    
    for stock in STOCKS:
        print(f"正在获取 {stock['name']} ({stock['code']}) 的历史数据...")
        df = fetch_stock_history(stock['code'], start_date, end_date)
        df = process_stock_data(df, stock)
        if df is not None:
            all_data.append(df)
            print(f"  ✓ 获取到 {len(df)} 条数据")
        else:
            print(f"  ✗ 获取失败")
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined
    return None


def save_to_csv(df, filename=DATA_FILE):
    """
    保存数据到 CSV
    """
    if df is None or df.empty:
        print("没有数据可保存")
        return
    
    # 确保目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 选择需要的列
    columns = [
        '日期', '股票代码', '股票名称', '昨日收盘', '今日开盘', '今日收盘',
        '涨跌幅', '最高价', '最低价', '成交量', '成交额', '委买', '委卖',
        '换手率', '振幅', '量比', '市盈率', '总市值', '流通市值',
        'MA5', 'MA10', 'MA20', 'MACD', 'MACD信号', 'KDJ-K', 'KDJ-D', 'KDJ-J',
        'RSI6', 'RSI12', '主力净流入', '所属板块', '板块涨幅', '涨跌家数比', '大盘成交额'
    ]
    
    # 只保留存在的列
    available_columns = [c for c in columns if c in df.columns]
    df = df[available_columns]
    
    # 检查文件是否存在
    file_exists = os.path.exists(filename)
    
    # 保存到 CSV
    df.to_csv(filename, mode='a', header=not file_exists, index=False, encoding='utf-8')
    
    print(f"\n✓ 数据已保存到 {filename}")
    print(f"  共 {len(df)} 条记录")


def main():
    """
    主函数
    """
    # 设置时间范围（从2月19日到昨天）
    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    start_date = '20250219'
    
    print(f"抓取历史数据: {start_date} 到 {end_date}")
    print("=" * 50)
    
    # 获取数据
    df = fetch_all_history(start_date, end_date)
    
    if df is not None:
        # 保存数据
        save_to_csv(df)
        print("\n" + "=" * 50)
        print("历史数据抓取完成！")
    else:
        print("\n抓取失败，请检查网络连接")


if __name__ == "__main__":
    main()
