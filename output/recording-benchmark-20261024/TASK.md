# 合成记录组件对照实验

这是独立于既有患者日统计的新方法recording-benchmark-v1。输入为实际模型对冻结合成事件的响应，不含真实患者。

先核对manifest内各文件字节SHA256，再实际执行：

python3 run_analysis.py health-research-input.json --out actual-output > stdout.log 2> stderr.log

保留退出码、stdout、stderr和actual-output/report.json；对照reference报告，不能复制参考结果冒充运行。报告主要成对差值、模板簇bootstrap区间、失败率和局限。不要把字段实验解释为生产整体收益或医学准确率，也不要更改原始观测。
