# 科研参考分析

所有输入与输出均为固定合成数据，不运行医学语言模型，不执行真实临床研究。

- `demo-input.json`：科研端默认队列对应的冻结输入。
- `demo-output/`：Python实际计算产物。
- `test_research.js`：授权、分母、同日成分、否定与时间边界以及JS/Python一致性检查。
- 参考脚本位于 `prototype/research/run_analysis.py`，科研端可直接下载。

从项目根目录运行：

```bash
python3 prototype/research/run_analysis.py analysis/demo-input.json --out analysis/demo-output
node analysis/test_research.js
```

浏览器端“运行本地分析”执行同样定义的统计计算；不会把动画作为平台运行。SciencePal实际执行与平台证据仍需补齐，详见 `docs/research-design.md`。

## 新增窗口实验与SciencePal任务包

```bash
python3 prototype/research/run_experiments.py analysis/demo-input.json --out analysis/window-experiments
python3 analysis/build_sciencepal_pack.py
python3 analysis/test_experiments.py
```

`window-experiments/`保存实际运行的三条件JSON和CSV。构建脚本生成科研端固定结果素材与`materials/sciencepal-research-pack.zip`，使用默认48人输入，包含独立重跑所需的输入、Python脚本、研究方案、任务说明、本地参考结果和逐文件哈希。构建时需要Node和Python；包内重跑仅需Python标准库。窗口变化不是AI组件消融，也不用于因果或临床效能结论。

固定包不随浏览器筛选变化。`test_experiments.py`在独立临时目录解压重跑，核验文件哈希、输入哈希和结果一致性。SciencePal平台实际执行依然待补。

## 描述性轨迹与假设基率

```bash
python3 prototype/research/run_methods.py analysis/demo-input.json --out analysis/methods-output
node analysis/test_methods.js
```

methods-output/methods.json包含首末可用自评分配对和三个纯假设基率情境。JS与Python在三个队列的结果一致；测试覆盖稀疏评分、非数值、未来归档隔离、升降方向和零阳性。任务包现含三个Python脚本，独立重跑测试覆盖全部三项；该方法结果不用于临床或主报告导入。
