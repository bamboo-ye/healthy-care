package app

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"net/url"
)

func (a *App) controlResearchRun(c *gin.Context) {
	if !validID(c, "id") {
		return
	}
	var in struct {
		Operation string `json:"operation"`
		Content   string `json:"content"`
	}
	if !bind(c, &in) {
		return
	}
	if in.Operation != "reply" && in.Operation != "stop" {
		fail(c, 400, "invalid_operation", "请指定补充信息或停止任务。")
		return
	}
	var snapshot, thread, remote, status string
	err := a.DB.QueryRow(c, "SELECT snapshot_id,COALESCE(external_thread_id,''),COALESCE(external_run_id,''),status FROM research_runs WHERE id=$1 AND created_by=$2", c.Param("id"), actor(c).ID).Scan(&snapshot, &thread, &remote, &status)
	if err != nil {
		fail(c, 404, "not_found", "没有找到任务。")
		return
	}
	if _, err = a.loadSnapshot(c, snapshot); err != nil {
		snapshotError(c, err)
		return
	}
	if (in.Operation == "reply" && (status != "external_asked" || len(in.Content) == 0 || len(in.Content) > 12000)) || (in.Operation == "stop" && status != "external_running" && status != "external_asked") {
		fail(c, 409, "invalid_run_state", "任务状态已变化，请刷新后再操作。")
		return
	}
	next := "external_replying"
	if in.Operation == "stop" {
		next = "external_stopping"
	}
	tag, err := a.DB.Exec(c, "UPDATE research_runs SET status=$1,updated_at=now() WHERE id=$2 AND status=$3", next, c.Param("id"), status)
	if err != nil {
		internalError(c, err)
		return
	}
	if tag.RowsAffected() != 1 {
		fail(c, 409, "invalid_run_state", "任务状态已变化。")
		return
	}
	path := "/internal/sciencepal/threads/" + url.PathEscape(thread) + "/reply"
	var body any = map[string]any{"content": in.Content, "message_id": uuid.NewString()}
	if in.Operation == "stop" {
		path = "/internal/sciencepal/runs/" + url.PathEscape(remote) + "/stop"
		body = map[string]any{}
	}
	result, code, err := a.agentJSON(c, "POST", path, body)
	final := "external_unknown"
	errorCode := "platform_operation_uncertain"
	if err == nil && code == 200 {
		final = "cancelled"
		errorCode = ""
		if in.Operation == "reply" {
			if id, ok := result["agent_run_id"].(string); ok && id != "" {
				remote = id
				final = "external_running"
			} else {
				final = "external_unknown"
				errorCode = "invalid_platform_response"
			}
		}
	}
	_, err = a.DB.Exec(c, "UPDATE research_runs SET status=$1,external_run_id=$2,error_code=$3,updated_at=now() WHERE id=$4 AND status=$5", final, remote, errorCode, c.Param("id"), next)
	if err != nil {
		internalError(c, err)
		return
	}
	a.audit(c, actor(c).ID, "research_"+in.Operation, c.Param("id"), "research")
	c.JSON(200, gin.H{"status": final, "error_code": errorCode})
}
