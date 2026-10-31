# 评审访问与权限说明

更新：2026年10月30日。用户已授权设置评审所需访问权限。作品在用户指定服务器的独立Docker Compose项目中运行；未修改伴AI代码、数据库或权限。

## 在线入口

- 用户端：https://admissions-broadband-bend-vanilla.trycloudflare.com/
- 科研端：https://admissions-broadband-bend-vanilla.trycloudflare.com/research/
- SciencePal公开只读运行：https://sciencepal.ai/share/65ecd584-6adf-4000-88d9-4004e3f82a65
- 最新五页说明：https://admissions-broadband-bend-vanilla.trycloudflare.com/materials/health-companion-project-description.pdf
- 最终视频（4分59秒）：https://admissions-broadband-bend-vanilla.trycloudflare.com/materials/healthy-care-demo-v7.mp4

## 评审账号

已分别创建普通用户与科研角色的专用评审账号。本机`.local/reviewer-access.md`保存两组凭据及操作说明，文件权限0600；通过比赛后台的非公开访问授权字段交付，不进入公开材料。

| 身份 | 可使用能力 | 已验证边界 |
|---|---|---|
| 未登录 | 打开登录页、PDF、视频及SciencePal公开回放 | 科研API返回401 |
| 用户评审 | 空白个人空间、健康对话、确认记录、跟进与用药记录 | 科研读写API返回403 |
| 科研评审 | 合成队列、观察窗口、来源追溯、导出、冻结输入、保存队列、启动与查看SciencePal任务 | 个人健康API返回403；没有服务器权限或账户级API密钥 |

登录会话有效7天，过期后可重新登录；账号未设置自动停用，评审结束后可撤回。使用同一浏览器切换两个账号时需先退出，也可分用普通与无痕窗口。普通账号可自行注册，不会自行获得科研权限。

## SciencePal操作

科研端选择“合成数据演示”，调整主题与3天/7天观察窗口；进入“分析任务”，查看专用账号下的任务，或启动新任务。平台连接已由服务端配置，评审无需提供API Key或切换平台。已为科研评审账号实际完成一条SciencePal合成分析，任务ID为`0ccc7791-daa9-4189-8e0b-588a7e09ffa3`，平台运行ID为`96af437e-0174-4772-958a-530217913d47`。认证接口产物已取回并通过输入与指标核验（api-fetched-artifact），Chrome任务详情确认48例、82.4%完整率与32项待核对候选，可下载冻结输入和执行任务包。

公开SciencePal链接无需登录，展示独立的追问组件评分实验，只读回放与应用内患者日分析是不同任务。外部执行仅开放合成输入。

## 本轮检查

- 用户端、科研端、就绪接口：公网GET 200。
- 最新PDF：公网200，SHA256与本机最终文件一致。
- 最终视频：公网206 Range，起始字节与本机最终文件一致；服务器整文件SHA256与本机一致。
- 两个专用账号登录及接口角色检查通过，Cookie带Secure、HttpOnly。
- Chrome实际登录确认：用户端初始个人空间为空；科研端可查看48例合成队列、267/324患者日与32项待核对候选。
- SciencePal公开链接在浏览器中显示共享只读回放，不要求登录。
- 原始验收记录位于`.local/reviewer-access-verification.json`和`.local/reviewer-public-link-checks.json`。

当前地址使用Cloudflare临时隧道，隧道重建后可能改变，不能视为固定域名。评审期间应保持该独立隧道和Docker服务运行；如需固定域名，仍需域名DNS或命名隧道的配置权限。
