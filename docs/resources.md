# 运行资源与许可

此表仅列作品运行与科研分析所用资源。完整版本见 `backend/go.mod`、`apps/web/package-lock.json`、`agent/requirements.lock` 和部署镜像摘要。自研代码当前未设置统一开源许可证；第三方许可不因代码公开而改变。

| 资源 | 来源 | 用途 | 许可或使用依据 |
|---|---|---|---|
| 图文模型 `openai/gpt-6-luna`，经OpenRouter调用 | [OpenRouter](https://openrouter.ai/) | 对话、图文理解和动作草案；这是已有部署配置，使用者可选择兼容服务 | [服务条款](https://openrouter.ai/terms)及实际模型提供方条款；不分发模型权重 |
| SciencePal，项目科研Agent v0.1.0 | [SciencePal](https://sciencepal.ai/) | 科研脚本实际执行、报告和日志回传 | 本人账户与API授权及平台规则；SDK 0.2.1只作接口契约参考，未打包官方SDK |
| `synthetic-light-illness-v2`、`recording-benchmark-v1` | 本项目 `analysis/` 与 `output/recording-benchmark-20261024/` | 合成队列、组件对照和离线复现 | 自建合成数据，非真实患者资料；保留协议和生成/评分脚本 |
| 护理/历史知识，项目整理版本2026-10-19 | [NHS](https://www.nhs.uk/conditions/) | 6条知识参考 | [OGL v3及NHS附加条件](https://www.nhs.uk/our-policies/terms-and-conditions/)；自行摘要并保留出处，不代表NHS背书 |
| 正式知识库内4篇研究文献 | 数据迁移 `004_research_papers.sql` 中的原文链接 | 科学问题与方法参考 | 自行概括和链接引用；原文权利归各权利人，未使用其原始患者数据 |
| LangGraph 1.2.16、检查点组件3.2.0、FastAPI 0.146.0 | [LangGraph](https://github.com/langchain-ai/langgraph)、[FastAPI](https://github.com/fastapi/fastapi) | Agent运行时与接口 | MIT |
| HTTPX 0.28.1、psycopg 3.3.6 | [HTTPX](https://github.com/encode/httpx)、[psycopg](https://www.psycopg.org/) | 外部接口与PostgreSQL访问 | 分别为BSD-3-Clause、LGPL-3.0-or-later；遵循发行包许可 |
| Gin 1.11.0、pgx 5.7.6、go-redis 9.12.1 | [Gin](https://github.com/gin-gonic/gin)、[pgx](https://github.com/jackc/pgx)、[go-redis](https://github.com/redis/go-redis) | Go业务服务、数据库和缓存访问 | 分别为MIT、MIT、BSD-2-Clause |
| React 19.1.1、lucide-react 0.468.0 | [React](https://github.com/facebook/react)、[Lucide](https://github.com/lucide-icons/lucide) | 双端界面与图标 | 分别为MIT、ISC；保留发行包内第三方声明 |
| PostgreSQL 17、pgvector 0.8.2 | [PostgreSQL](https://www.postgresql.org/)、[pgvector](https://github.com/pgvector/pgvector) | 事实、授权、任务和检查点存储 | PostgreSQL License及扩展随附许可 |
| Redis 7.4 | [Redis许可](https://redis.io/legal/licenses/) | 公共知识缓存和限流 | RSALv2或SSPLv1双许可；应用内部缓存 |
| Docker Compose、Caddy 2.10、cloudflared，摘要见部署配置 | [Compose](https://github.com/docker/compose)、[Caddy](https://github.com/caddyserver/caddy)、[cloudflared](https://github.com/cloudflare/cloudflared) | 编排、网关、HTTPS入口 | 上述代码采用Apache-2.0；在线服务另按其服务条款使用 |
| 真实患者数据、电子病历、外部临床数据库 | 无 | 无 | 无 |
| 自行训练或微调的模型权重 | 无 | 无 | 无 |
| 在线医生、处方、购药、天气和可穿戴API | 无 | 无 | 无 |

绿色角色与背景为项目生成素材，制作说明及参考范围见 [插画记录](image-assets.md)。参考项目没有在本仓库提供通用开源授权，不将其代码或原图视为可自由再分发资源。
