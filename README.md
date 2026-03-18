# 📊 股票监控工具

A股实时行情监控工具，使用腾讯股票 API 获取数据。

## 关注股票

- 完美世界 (002624)
- 北方稀土 (600111)
- 升达林业 (002259)

## 功能

- ✅ 实时获取 A 股行情
- ✅ 自动判断交易时间
- ✅ 彩色显示涨跌
- ✅ 成交量/成交额统计

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 查看所有股票行情
python3 stock_monitor.py

# 查看市场状态
python3 stock_monitor.py --status
```

## 交易时间

- 上午：9:30 - 11:30
- 下午：13:00 - 15:00
- 周末休市

## 数据来源

腾讯股票 API (qt.gtimg.cn)

## License

MIT
