# 启动、配置与开发

本指南针对从公开仓库取得的源码。需要 Docker Engine 或 Docker Desktop、Docker Compose 2.24.4+ 和 Python 3.10+。容器内提供 Go、Node.js、Python Agent、PostgreSQL 和 Redis。

## 本地启动

```sh
git clone https://github.com/bamboo-ye/healthy-care.git
cd healthy-care
python3 scripts/bootstrap.py
```

脚本从 `.env.example` 创建本机 `.env`，生成数据库、内部通信、签名和科研账户密码；文件权限0600。已有配置不会被覆盖。`.env` 不进入 Git。

先在本机编辑 `.env` 配置模型及需要的 SciencePal 连接，再启动：

```sh
docker compose up -d --build
docker compose ps
curl --fail http://localhost:8780/readyz
```

用户端为 <http://localhost:8780/>，科研端为 <http://localhost:8780/research/>。普通用户从用户端注册；科研账户使用本机 `.env` 中的 `RESEARCH_EMAIL` 和 `RESEARCH_PASSWORD`。注册接口不能创建科研角色。

默认来源为 `http://localhost:8780`，端口只绑定宿主回环地址。`127.0.0.1` 与 `localhost` 是不同 Origin；若改变入口，要同步配置 `APP_ORIGIN`。

## 图文模型

```dotenv
AGENT_PROVIDER=openai_compatible
MODEL_BASE_URL=https://your-provider.example/v1
MODEL_NAME=your-vision-model
MODEL_API_KEY=replace-with-your-model-key
MODEL_TEMPERATURE=
MODEL_STREAM_USAGE=true
MODEL_TIMEOUT_SECONDS=90
```

适配器使用 OpenAI 兼容的 `chat/completions`、SSE 和 JSON 响应格式。所选服务需支持图片输入及 JSON 输出，配置存在不代表链路已验收。

- 模型不支持 `temperature` 时留空；支持时可填写0到2。
- 上游不支持 `stream_options` 时设 `MODEL_STREAM_USAGE=false`，未返回的用量保留未知。
- 格式校验最多重试一次；原始模型 JSON 不直接成为用户建议，也不会直接写入业务事实。
- 未配置时明确显示服务未就绪；主环境不会自动降级为测试 Provider。

已验证部署使用 OpenRouter 的 `openai/gpt-6-luna`，属于一次已有配置与合成输入验收记录，不保证其他服务的兼容性或医学能力。

## SciencePal

在自己的 SciencePal 账户创建具备 Python 执行及沙箱文件读写能力的科研 Agent。系统提示词见 [Agent配置](sciencepal-agent-system-prompt.md)。

```dotenv
SCIENCEPAL_BASE_URL=https://sciencepal.ai/api
SCIENCEPAL_AGENT_ID=replace-with-your-agent-id
SCIENCEPAL_API_KEY=replace-with-your-sciencepal-key
```

重新加载配置：

```sh
docker compose up -d --force-recreate api worker agent-runtime
```

科研端选择“合成数据演示”，调整3天或7天窗口，在“分析任务”启动任务。当前只开放合成输入的外部执行；服务端上传冻结输入、manifest及脚本，取回平台产物后核对输入、版本和统计指标。SciencePal Key 与用户端模型 Key 用途不同。详见 [接口与复现](sciencepal-integration.md)。

## 软件验收

```sh
python3 scripts/acceptance.py
```

该命令创建 `healthy-care-test` 独立环境和 `.local/acceptance.env`，显式启用测试 Provider，只重置合成验收数据库，执行构建测试、API、重试、恢复、备份、产品说明和队列检查。它不会重置主环境，也不调用真实模型或 SciencePal。

真实服务验收会调用外部服务并使用其额度：

```sh
python3 scripts/live_acceptance.py --synthetic-only --only model --output .local/model-acceptance.json
python3 scripts/live_acceptance.py --synthetic-only --only sciencepal --output .local/sciencepal-acceptance.json
python3 tests/live_workflow_acceptance.py --synthetic-only
```

未配置所需凭据时停止。验收脚本产生的账户、会话、日志与图片仅保存在 `.local/`，不能公开提交。

## 宿主开发

运行依赖以 `backend/go.mod`、`apps/web/package-lock.json`、`agent/requirements.lock` 为准。常用检查：

```sh
go -C backend test -race ./...
go -C backend vet ./...
npm --prefix apps/web ci
npm --prefix apps/web test
npm --prefix apps/web run build
python3 -m unittest discover -s analysis/recording_benchmark -p 'test_*.py'
```

Agent 使用 Python 3.12，在单独虚拟环境安装 `agent/requirements.lock` 后，从 `agent/` 执行 `python -m pytest -q tests`。不要把宿主虚拟环境提交到仓库。

## 备份与部署

日常运维、固定域名HTTPS覆盖、备份与全新环境恢复见 [运维指南](operations.md)。默认备份包含个人记录与附件，未声称备份自动加密。

`compose.server.yaml` 是已有演示服务器的版本化镜像与资源覆盖，镜像并未发布到公共镜像仓库；新用户应先使用默认源码构建。生成PDF、视频和发布材料的脚本保留制作过程，部分依赖本机字体或私有原始录屏；这些材料不影响应用容器构建和公开合成实验的离线重算。
