# 连续健康记录：可复现组件基准

这是科研评估工具，独立于用户端，不改变临床边界或发布未经审阅的用量。协议与数据先冻结再调用真实模型。读取protocol.md了解适用范围：一轮结构化字段追问，固定合成响应器，非真实自然聊天或临床研究。

```bash
python3 -m unittest discover -s analysis/recording_benchmark -p 'test_*.py'
# 显式使用供应商额度；不得覆盖已有实验目录。
python3 analysis/recording_benchmark/run_live.py --synthetic-only --split test --out .local/benchmark-new
python3 analysis/recording_benchmark/build_pack.py .local/benchmark-new/observations.json --out output/benchmark-pack-new
# 如需真实SciencePal执行：只上传脱密合成观测、协议与脚本，不上传.env或私有目录。
python3 analysis/recording_benchmark/platform_run.py --synthetic-only --pack output/benchmark-pack-new --out .local/benchmark-platform-new
```

文件清单：dataset.json（60事件，开发12/保留48）、protocol.md、run_live.py（真实模型；不发送隐藏事实给追问模型）、run_analysis.py（标准库评分与模板簇bootstrap）、build_pack.py（脱密导出）、platform_run.py（平台实际执行、认证取回与独立一致性检查）、test_benchmark.py（方法边界）。

重要：initial臂没有追问，generic和directed各最多3个字段、仅一轮；不是三臂等总成本。generic与directed共享同样字段字典、输出上限和模型；Token/耗时应报告实际值，不宣称完全相等。模型API使用固定max_tokens=450，未对不支持temperature的模型强加采样参数。生产系统更长的提示词、知识检索、确认与安全路由均未包含，不能用此分数代表其整体性能。

平台脚本只评分已经采集的真实模型输出，不假称SciencePal运行了外部模型本身。平台提交超时或状态不明时不自动重启；先检查私有receipt及平台实际状态。所有失败和负结果保留，无法执行的步骤如实记录。
