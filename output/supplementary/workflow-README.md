# 工作流结构导出

日期：2026-10-31（Asia/Shanghai）。

- langgraph-workflow.json：只读连接实际部署的Agent容器，调用build_graph(None).get_graph().to_json()取得的LangGraph结构。
- context → triage → model/validate → confirmation → end。紧急分支可绕过模型；确认节点支持中断与恢复。
- sciencepal-workflow.json：按项目实现整理的科研联动流程说明，含冻结输入、平台执行、取回产物和独立校验。
- 这些文件不含节点函数实现、应用源码、数据库凭据、API密钥或会话。
- LangGraph结构JSON用于查看节点与连接关系，不足以单独启动应用；SciencePal说明不是平台原生一键导入格式。
- 本包仅导出结构；节点实现与完整应用源码另见项目GitHub仓库。
