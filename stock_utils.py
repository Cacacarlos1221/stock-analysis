#!/usr/bin/env python3
"""
股票工具模块
提供通用的股票数据获取函数
"""

import requests
import re

# 股票列表（统一4只）
STOCKS = [
    {"name": "完美世界", "code": "002624", "market": "sz"},
    {"name": "北方稀土", "code": "600111", "market": "sh"},
    {"name": "升达林业", "code": "002259", "market": "sz"},
    {"name": "上证指数", "code": "000001", "market": "sh"},
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
