# Codex 任务：优化 stock-analysis 项目

## 项目位置
/Users/boxuncao/Desktop/歪比巴卜(Openclaw)/代码/stock-analysis

## 需要完成的任务

### 1. 路径修复
- data_collector.py 和 fetch_history.py 里的 DATA_FILE 路径需要修正
- 当前路径指向 ~/Desktop/Experiment/stock-analysis/daily_data.csv
- 正确路径：~/Desktop/歪比巴卜(Openclaw)/代码/stock-analysis/daily_data.csv

### 2. 统一股票列表
- stock_monitor.py: 3只股票 → 添加上证指数变成4只
- 4只股票：完美世界(002624)、北方稀土(600111)、升达林业(002259)、上证指数(000001)

### 3. 代码合并
- stock_monitor.py 和 data_collector.py 有重复的 get_stock_realtime 函数
- 建议：提取到一个共享模块或合并重复代码

### 4. 技术指标计算
- data_collector.py 收集34字段但 MA5/MA10/MA20/MACD/KDJ/RSI 等都是 None
- fetch_history.py 已经有 calculate_ma, calculate_macd, calculate_kdj, calculate_rsi 函数
- 需要在 data_collector.py 中调用这些函数计算技术指标

## 输出要求
1. 直接修改代码文件
2. 修改完成后运行: git add . && git commit -m "优化: 修复路径、统一股票列表、合并代码、添加技术指标计算"
3. git push 推送到远程仓库
