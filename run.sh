#!/bin/bash
# 股票监控定时任务脚本

PROJECT_DIR="$HOME/Desktop/Experiment/stock-analysis"
source "$PROJECT_DIR/venv/bin/activate" 2>/dev/null || source /usr/local/bin/activate 2>/dev/null

cd "$PROJECT_DIR"

# 运行监控
python stock_monitor.py