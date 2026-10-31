# SciencePal创作、运行与复现

平台承担核心科研分析工作流。Go保留队列与授权边界，LangGraph运行时通过SciencePal Agent API上传冻结合成输入、manifest清单及参考脚本、启动平台Agent、轮询真实状态、取得沙箱产物并回传校验结果。2026年10月23日已完成真实账号接入与一次合成数据平台实际运行，见[验收证据](sciencepal-live-acceptance-2026-10-23.md)。

## 配置步骤

1. 在SciencePal创建科研Agent，授予所需的代码执行和文件读写能力。不要给它真实用户资料或业务库凭据。
2. 工作流以冻结JSON为输入，运行版本化Python脚本，返回实际生成的 `report.json`、候选结果与执行日志。核心统计必须实际运行，不能由语言模型猜数。
3. 在本机 `.env` 配置 `SCIENCEPAL_API_KEY` 和 `SCIENCEPAL_AGENT_ID`，重建Agent运行容器的配置。
4. 科研端选择“合成数据演示”，冻结队列并启动SciencePal任务。保存平台可访问的作品、线程/任务链接，供参赛演示与复现。
5. 核对平台任务状态、输入SHA256、代码/规则/知识版本、分子分母、实际日志和产物，再进行真实平台验收。

建议Agent指令：

> 分析随任务上传的合成院外健康记录。必须实际运行附件run_analysis.py，不上传或访问真实身份、聊天或照片。保留未知与无记录，不将信息缺口或重复成分候选命名为滥用率，不从合成数据推断临床获益。按本次任务给定的输出目录保存report.json和真实运行日志；缺少文件或执行失败时报告失败，不编造成功结果。

API运行的每次提示会带唯一的 `/workspace/healthy-care/<本地run UUID>` 输出目录，避免读取其他任务留下的旧产物。上传的脚本不含平台Key、数据库凭据或预计算报告。

## 接口与状态

实现参照SciencePal官方SDK 0.2.1的HTTP调用约定。仅从官方站点下载并核对SHA256用于阅读，未执行下载代码。

| 操作 | 平台接口 |
| --- | --- |
| 创建运行与上传附件 | `POST /api/agent/initiate`，multipart中重复的`files`字段 |
| 状态 | `GET /api/agent-run/{id}` |
| 事件 | `GET /api/agent-run/{id}/stream`，适配器支持 |
| 补充信息 | `POST /api/thread/{id}/messages`后`POST /api/thread/{id}/agent/start` |
| 停止 | `POST /api/agent-run/{id}/stop` |
| 定位沙箱 | `GET /api/thread/{id}/sandbox` |
| 获取固定目录产物 | `GET /api/sandboxes/{id}/files/content?path=...` |

本地状态包含排队、运行、平台运行中、等待补充、等待导入、未知、失败、停止及完成。首次受理、补充或停止发生网络不确定性时不重复启动远端任务；应先到平台核实。凭据未配置时不发外部请求。

平台完成后自动下载固定目录报告与日志，重新计算指标并检查哈希和方法版本；当前授权失效的结果不会重新发布。取得产物标为`api-fetched-artifact`，表示取得渠道与数值校验，不表示完成临床有效性验证。

## 文件回退与独立复现

每个合成快照可下载ZIP任务包，包括输入、Python脚本、manifest.json、输入与脚本SHA256、冻结截点、队列、方法/知识/规则/数据版本、随机种子与运行说明。合成筛选可少于5人；真实授权记录仍执行至少5名参与者的展示门槛。

```sh
python3 run_analysis.py health-research-input.json --out actual-output
```

科研端可导入JSON报告，严格验证输入、窗口、代码、规则、知识版本和数值指标。导入标为`imported-not-platform-authenticated`；手填SciencePal平台名和链接或数值一致都不能单独证明平台执行。导入文件不作为服务器代码执行。

## 来源

- [SciencePal SDK说明](https://sciencepal.ai/help/sdk)
- [SciencePal帮助](https://sciencepal.ai/help)
- [官方SDK文件校验清单](https://sciencepal.ai/downloads/sdk/SHA256SUMS)

正式提交应使用真实账号中的Agent作品、实际任务与日志。本地参考计算或HTTP契约测试不能替代平台执行证据；本次真实执行证据已单独留存，最终演示视频与公开访问安排仍需准备。


## 2026年10月23日网页配置进展

已在用户登录的SciencePal账户创建“伴AI·健康伙伴｜院外健康科研Agent”，版本0.1.0；提示词经平台生成后补充了规范化输入哈希、固定观察窗口和执行失败要求，并在编辑界面确认保存。实际提示词见sciencepal-agent-system-prompt.md。用户明确授权后生成90天的科研服务专用密钥，保存到本机0600权限的.env。通过官方API获取实际Agent ID，重载服务后完成一次合成数据真实联调：平台运行脚本，认证API取回报告和日志，Go独立数值校验通过，最终标记api-fetched-artifact。用户端图文模型由独立OpenRouter配置提供，已完成真实服务验收，见[live-service-acceptance-2026-10-23.md](live-service-acceptance-2026-10-23.md)。SciencePal密钥不充当用户端模型密钥。
