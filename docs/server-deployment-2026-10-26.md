# Docker服务器部署与公网验收

2026年10月26日。按用户指示复用伴AI的现有服务器，通过其本机私有SSH配置连接。部署目录为/opt/healthy-care，独立Compose项目healthy-care；没有把健康伙伴代码加入伴AI仓库，没有复用其数据库或数据卷。

## 可访问入口

- 用户端：https://admissions-broadband-bend-vanilla.trycloudflare.com/
- 科研端：https://admissions-broadband-bend-vanilla.trycloudflare.com/research/
- 3分58秒演示视频：https://admissions-broadband-bend-vanilla.trycloudflare.com/materials/healthy-care-demo.mp4
- 五页项目说明：https://admissions-broadband-bend-vanilla.trycloudflare.com/materials/health-companion-brief.pdf
- SciencePal公开组件实验：https://sciencepal.ai/share/65ecd584-6adf-4000-88d9-4004e3f82a65

公网沿用伴AI的Cloudflare临时隧道方式，两个应用使用独立隧道。该地址不是固定域名，隧道重建后可能变化；截止前与评审期间需要复查。如需绑定固定域名，还需要域名DNS/命名隧道的配置权限。已查到的伴AI配置没有该权限凭据，不推断其存在。

## 部署状态与边界

服务器为x86_64、约2GB内存。通过本机构建和测试linux/amd64镜像，再校验SHA256、上传并加载；compose.server.yaml降低内存上限及数据库缓存，不争用现有端口。健康伙伴网关仅绑定服务器127.0.0.1:8781，HTTPS经专用隧道终止，Cookie Secure开启，APP_ORIGIN绑定实际公网来源。数据库和Redis没有公网端口。

运行中的服务为PostgreSQL/pgvector、Redis、Go API、worker、Python LangGraph、Caddy、备份与专用隧道；5个健康检查正常。发布路径/opt/healthy-care/releases/20261026-01，current链接指向该版本；环境位于独立shared/.env，权限0600，使用新生成的数据库、内部通信和科研登录凭据。仅复用用户授权的模型及SciencePal服务配置。

## 已验证

- 目标x86运行时32项测试通过；Go镜像构建测试通过，前端构建测试通过。新增实验方法7项测试通过。
- 主部署注册、HTTPS登录、空白用户首页、真实模型回复、草案确认保存通过。
- 普通账户访问科研工作区被拒绝；专用科研账户能读取48例合成队列，显示实际分母和缺失状态。
- 从公网执行五类文本及人工色块图片的真实模型检查通过；不等于医学影像或临床验证。
- 从本次服务器部署启动SciencePal真实合成任务，完成后认证API取得产物，Go校验通过，标记api-fetched-artifact。任务c1665e02-84fe-4b17-86a6-c774685ab21e，平台运行65194ad5-0cb1-4522-8e8d-4332a238c19a，输入规范哈希c4fae3592e5dd5703019372cfa775651a1529d49e565216e8facf34cf4fb30eb。
- 视频及PDF通过公网下载与本机最终文件逐字节核对；视频支持HTTP 206 Range，H.264/AAC、1920×1080、约237.6秒，非静音。
- SciencePal组件实验公开分享经用户明确授权创建；独立未登录浏览器可查看只读回放和结果。该公开链接不是用户账户凭据。
- 未发布具体药品说明；只提供护理参考与用药记录。部署后伴AI原就绪接口仍返回200。

原始技术验收与环境保存在本机.local/私有目录，不加入公开材料。科研登录凭据见本机.local/server-access.md，不能作为公开README内容。没有执行真人研究或冒充专业审阅。

## 运维

连接沿用伴AI的管理员私有SSH别名与现有主机指纹校验。进入/opt/healthy-care/current后，使用`docker compose -f compose.yaml -f compose.server.yaml ps`检查；不运行伴AI项目的down、迁移或清理。只读演示材料挂载到网关/srv/materials。

重建公网隧道前需记录新URL并同步shared/.env中的APP_ORIGIN，再只重建健康伙伴api/worker，复查登录、CSRF、视频和科研访问。源文件修改不等于已更新容器，镜像变更须另建版本并重新验证。固定域名绑定及正式提交署名仍需对应信息。
