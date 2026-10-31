# SciencePal核心执行任务：院外轻症数据质量与自主用药情境

这是固定48人、7天窗口的合成方法验证包。它不是临床数据，也不证明产品疗效。
SciencePal官方说明支持文献检索与代码执行：https://sciencepal.ai/help

## 在SciencePal中实际完成

1. 阅读research-program.json中的研究问题与原始来源；核实来源支持的结论及场景局限，特别区分临床病历、院外自述和客观检测标签。
2. 实际执行Python脚本，不仅解释代码。三条命令如下：

python3 run_analysis.py health-research-input.json --out actual-output
python3 run_experiments.py health-research-input.json --out actual-experiments
python3 run_methods.py health-research-input.json --out actual-methods

3. 对照reference/中的本地参考结果，核对输入规范哈希、各项分子分母和三种条件；保留真实stdout、stderr、命令与产物。不要把reference复制为平台执行证据。
4. 解释3天与7天窗口、总体与主题子集的差异；它们是观察窗口敏感性，不是AI消融试验，也不证明因果。
   对轨迹检查首末可用评分、缺失及起始日，不把归档或评分降低改写为痊愈。
   对基率情境核对数学公式；0.1%/1%/5%基率及80%敏感度、95%特异度全部是假设，不是论文或产品性能。
5. 分开报告观察事实、候选线索、方法限制与拟开展的验证。不要编造受试者研究、模型得分、临床准确率或伦理审批。
6. 如需记录平台来源，再使用真实可访问的运行链接执行：

python3 run_analysis.py health-research-input.json --platform SciencePal --run-url 'https://sciencepal.ai/实际运行链接' --out actual-output

来源参数是声明，评审仍需核实SciencePal会话、执行过程与原始文件。若暂时拿不到真实链接，保留local-python标识并如实说明，不能伪造。

## 应交回科研端与比赛材料

- actual-output/report.json：可在默认队列的科研端导入，哈希与全部统计应一致。
- actual-output/*.csv与actual-experiments/experiments.json、experiments.csv。
- actual-methods/methods.json：描述性轨迹与纯假设基率结果，不能导入为临床或主分析报告。
- SciencePal真实项目/会话链接、执行日志与截图、来源核验记录。
- 不超过5页的项目说明、3—5分钟演示、原创性与模型/代码/API/资源声明。

导入一致性校验不能认证平台身份。医生确认不属于本项目必须实现的功能。
