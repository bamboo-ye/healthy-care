# 原创性、AI辅助与资源使用声明

本文件记录当前工程事实；用户已确认个人参赛。个人实名及资格信息以已完成的报名登记为准，正式入口署名须与登记一致；由个人统筹需求、产品设计、开发验收与参赛材料，使用下述AI辅助，不虚构其他队员或专业审阅人。实际SciencePal任务与模型调用证据见docs/live-service-acceptance-2026-10-23.md。

## 赛期成果与既有资源

本项目可核实的原型、工程实现、实验及材料更新发生于2026年10月18日至26日，属于赛事期间；不将早期原型自动归类为赛前成果。伴AI参考项目、第三方模型、平台与依赖属于外部既有资源，按下文披露，不主张其为本项目原创。其他个人赛前成果如需声明，应按真实报名信息补充。

- 既有设计：prototype/中的可点击原型、绿色角色与背景，以及analysis/中的合成研究参考资料。它们保留用于设计和方法追溯，不称为本次新开发的在线服务。
- 本轮工程：apps/web/双端应用，backend/的Go业务与worker，agent/的LangGraph运行时与Provider/SciencePal适配，数据库迁移、Docker部署、授权与清理、备份恢复及自动验收。
- 伴AI参考：按用户指定参考项目的布局和插画风格，保留“伴AI·健康伙伴”品牌，健康应用独立实现；没有加入伴AI仓库或引入其他业务模块。参考地址：https://github.com/bamboo-ye/ai-companion。
- AI辅助：使用Codex协助需求、原型、代码、文档和测试；插画由内置图像生成工具基于参考风格生成，提示词见docs/image-assets.md。不能将AI辅助输出描述为未经辅助的人工原创。

## 模型、数据、代码、API与工具

| 类别 | 当前使用和证据 |
| --- | --- |
| 对话模型 | OpenRouter的openai/gpt-6-luna；真实文本/图片6项、完整业务19项通过；另运行冻结48例三臂合成组件对照，结果与局限见benchmark-results-2026-10-24.md；不等于临床准确率 |
| 测试Provider | 显式隔离的确定性合成输出，只作软件验收；主部署禁用 |
| 数据 | analysis/demo-input.json为48段合成事件；自动验收账户、描述、图片及产品均为虚构；没有真实患者数据或临床效果试验 |
| 医学来源 | 版本化公开护理/历史参考及4篇研究，见知识库、研究文档和原始来源；不冒充已专业审阅的具体药品说明 |
| 科研平台 | SciencePal Agent API与官方SDK 0.2.1契约；只阅读SDK，服务由本项目适配实现；已在真实账号创作Agent v0.1.0，患者日统计平台Python执行及Go独立校验完成；新增记录组件实验实际平台评分，认证API产物与独立Python重算完全一致；见两项专项报告 |
| 业务依赖 | Go、Gin、pgx/sqlc、go-redis、pgvector-go；完整依赖与校验见backend/go.mod、go.sum和sqlc配置 |
| Agent依赖 | Python、FastAPI、LangGraph、PostgreSQL检查点、psycopg与httpx；完整版本见agent/requirements.lock |
| 前端依赖 | React、TypeScript、Vite、lucide-react；完整版本见apps/web/package-lock.json |
| 部署 | Docker Compose、Caddy、PostgreSQL/pgvector、Redis；服务器覆盖见compose.server.yaml；独立Cloudflare临时隧道提供HTTPS，不冒称固定域名 |
| 演示视频 | 实际操作截图分步讲解，合成场景；macOS Tingting语音合成中文旁白，FFmpeg编码，明确标注AI配音及非连续录屏 |

第三方依赖及参考来源按其发行包中的许可证和引用信息使用；本声明不改变这些许可证。正式提交需由团队核对参赛署名、合作和资源使用声明。

## 可复现材料与待补证据

可提交源码、锁文件、固定合成输入、任务包、manifest、命令、自动验收报告及真实生成的本地指标。不能提交.env、.local/、数据库卷、备份、真实个人聊天、图片或密钥。各任务输入包以科研端下载内容为准，固定原型资料包不代表当前筛选。

已取得实际模型配置、SciencePal任务链接、日志、产物和更新后的五页说明。已生成3分58秒演示视频，独立Docker公网部署和SciencePal公开只读链接均已验证；个人资源声明由本人在正式提交时确认；具体药品用量按用户决定暂不发布，未来发布前需专业审阅。真实外部成本和额度尚未测得，不预填性能、价格、临床准确率或合作方。
