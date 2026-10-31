# 伴AI·健康伙伴：提交材料索引

2026年10月30日更新。用户已确认报名、个人参赛。定位：面向院外轻症的来源可追溯记录与科研工作流；不是已验证的诊疗系统。

## 已准备

- 五页项目说明：output/pdf/health-companion-project-description.pdf，包含科学问题、技术方案、SciencePal核心作用、创新点、验证结果、局限及后续计划；已逐页检查。
- 项目源码：https://github.com/bamboo-ye/healthy-care；本地归档工具按白名单生成材料包并检查配置密钥。
- 实验包：output/recording-benchmark-20261024.zip。冻结60事件开发/测试分离，实际测试48例；含实际合成响应、协议、评分脚本、manifest与本地参考。
- 平台证据：output/recording-benchmark-platform-evidence-20261024/。真实任务completed，认证API产物与独立重算完全一致；含日志和SHA256。
- 详细实验结果：docs/submission/benchmark-results-2026-10-24.md。定向与通用差值区间包含零，尚不能宣称优于。
- 最终演示：output/video-v7/healthy-care-demo-v7.mp4，4分59秒。真实产品操作、虚构日常案例，包含连续科研操作、过渡动画、AI配音和配乐；安全性与拟接入在线医生处方确认已注明能力边界。公网内容一致性与Range播放检查已通过。
- 原创性与资源声明：docs/submission/resource-statement.md。模型、数据、代码、API、外部工具、AI辅助已列；已按个人参赛整理，实名署名沿用报名信息。
- 可用性执行单：docs/submission/usability-session-kit.md。准备完成但尚未实际招募，不将其计为真人证据。
- 部署访问计划：docs/submission/reviewer-access-plan.md。已复用用户指定的伴AI服务器SSH配置，独立Docker部署及公网验收已完成。

## 已验证的评审链接

- 用户端：https://admissions-broadband-bend-vanilla.trycloudflare.com/
- 科研端：https://admissions-broadband-bend-vanilla.trycloudflare.com/research/ （已配置专用科研评审账号，两端凭据见私有.local/reviewer-access.md，通过非公开渠道交付）
- 视频：https://admissions-broadband-bend-vanilla.trycloudflare.com/materials/healthy-care-demo-v7.mp4
- 五页说明：https://admissions-broadband-bend-vanilla.trycloudflare.com/materials/health-companion-project-description.pdf
- SciencePal公开运行：https://sciencepal.ai/share/65ecd584-6adf-4000-88d9-4004e3f82a65 （未登录浏览器可查看只读运行与结果）

服务器复用伴AI，独立Compose项目及数据库；公网方式与伴AI相同，使用各自独立的Cloudflare临时隧道。临时地址在隧道重建后可能改变，截止前及评审期间需复查，不冒称固定域名。

10月30日已实际登录两个专用评审账号并验证角色隔离，科研评审账号下新增SciencePal任务已完成且平台产物校验通过，公开文件与最终本机文件一致。旧视频/PDF链接也已更新内容。详见reviewer-access-plan.md；密码不进入公开PDF或提交材料包。

## 正式提交仍需

1. 正式入口署名沿用报名登记，本人确认个人资源声明。
2. 将以上材料与链接填入正式提交入口，复核后提交并保存确认凭证。

工程部署、真实服务验收、公开科研运行链接、视频与资料准备已完成；材料包不等于正式参赛提交。独立真人可用性反馈尚未开展，不计入已验证证据。

## 推荐讲述

先展示院外记录缺失这一问题，再用一个对话—确认—更正—归档例子说明记录可信度；随后展示SciencePal对冻结真实模型观测实际评分、产物取回及独立校验。报告正负结果：追问组字段覆盖高于初始输入，但定向相对通用的优势尚未建立。强调下一步用自然语言与独立反馈改进，而不是声称已经实现临床获益。

## 补充材料（2026年10月30日）

- 代码仓库：https://github.com/bamboo-ye/healthy-care 。公开项目源码、锁文件、部署配置与合成科研材料；本机凭据和原始个人记录不进入仓库。
- 材料总入口：https://admissions-broadband-bend-vanilla.trycloudflare.com/materials/supplementary/index.html 。含技术补充、脱密Agent配置、工作流结构、可用性执行计划、技术验收、实验结果与可复现包。
- 逐项链接与访问说明：supplementary-links.md。
- LangGraph结构JSON来自实际部署运行时；SciencePal配置及联动说明不是平台原生一键导入文件。
- 科研复现包只含独立评分/敏感性脚本、合成观测及平台产物；两个分析已离线重算并与参考结果一致。完整应用源码另见GitHub仓库。
- 独立真人用户测试尚未开展；计划与技术验收分别提供，不以软件检查替代用户反馈。
