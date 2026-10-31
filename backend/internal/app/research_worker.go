package app

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

func (a *App) agentJSON(ctx context.Context, method, path string, body any) (map[string]any, int, error) {
	var input io.Reader
	if body != nil {
		input = bytes.NewReader(encode(body))
	}
	req, err := http.NewRequestWithContext(ctx, method, a.Config.AgentURL+path, input)
	if err != nil {
		return nil, 0, err
	}
	req.Header.Set("Authorization", "Bearer "+a.Config.InternalToken)
	req.Header.Set("Content-Type", "application/json")
	res, err := a.HTTP.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer res.Body.Close()
	var result map[string]any
	err = json.NewDecoder(io.LimitReader(res.Body, 2<<20)).Decode(&result)
	return result, res.StatusCode, err
}
func (a *App) processResearch(parent context.Context) {
	ctx, cancel := context.WithTimeout(parent, 60*time.Second)
	defer cancel()
	_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status=CASE WHEN platform='local-reference' THEN 'queued' ELSE 'external_unknown' END,error_code=CASE WHEN platform='local-reference' THEN NULL ELSE 'initiation_uncertain' END,updated_at=now() WHERE status='running' AND updated_at<now()-interval '2 minutes'")
	_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='external_unknown',error_code='platform_operation_uncertain',updated_at=now() WHERE status IN ('external_replying','external_stopping') AND updated_at<now()-interval '2 minutes'")
	var id, snapshot, platform string
	err := a.DB.QueryRow(ctx, `UPDATE research_runs SET status='running',updated_at=now() WHERE id=(SELECT id FROM research_runs WHERE status='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING id,snapshot_id,platform`).Scan(&id, &snapshot, &platform)
	if err == nil {
		in, e := a.loadSnapshot(ctx, snapshot)
		if e != nil {
			_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='invalidated',error_code='snapshot_unavailable' WHERE id=$1", id)
			return
		}
		manifest, manifestErr := a.snapshotManifest(ctx, snapshot, in)
		if manifestErr != nil {
			_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='failed',error_code='manifest_unavailable' WHERE id=$1", id)
			return
		}
		if platform == "local-reference" {
			result := analyze(in)
			result["manifest"] = manifest
			_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='completed',result=$1,updated_at=now() WHERE id=$2 AND status='running'", encode(result), id)
			return
		}
		outputDir := "/workspace/healthy-care/" + id
		prompt := "你是本项目科研分析Agent。附件包含冻结的合成输入health-research-input.json和版本化脚本run_analysis.py。请找到附件并实际运行脚本，不要复制参考结果或用推测代替执行。创建目录" + outputDir + "，执行 python3 run_analysis.py health-research-input.json --out " + outputDir + "，保存真实stdout.log与stderr.log到该目录。核对输入SHA256=" + digest(in) + "，解释字段分母、未知与无记录的区别、候选和评分变化的边界。不要把脚本的local-python标记当作未运行，运行平台通过本任务链路另外记录。保留真实任务过程、运行链接和产物；候选不等于滥用，合成数据不证明临床效能。"
		result, status, e := a.agentJSON(ctx, "POST", "/internal/sciencepal/initiate", map[string]any{"prompt": prompt, "input": in, "manifest": manifest})
		if e != nil {
			_, _ = a.DB.Exec(parent, "UPDATE research_runs SET status='external_unknown',error_code='initiation_uncertain',updated_at=now() WHERE id=$1 AND status='running'", id)
			return
		}
		if status != 200 {
			code := "sciencepal_upstream_error"
			if result["detail"] == "sciencepal_not_configured" {
				code = "sciencepal_not_configured"
			}
			_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='failed',error_code=$1,updated_at=now() WHERE id=$2 AND status='running'", code, id)
			return
		}
		thread, ok1 := result["thread_id"].(string)
		run, ok2 := result["agent_run_id"].(string)
		if !ok1 || !ok2 || thread == "" || run == "" {
			_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='external_unknown',error_code='invalid_platform_response',updated_at=now() WHERE id=$1", id)
			return
		}
		_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='external_running',external_thread_id=$1,external_run_id=$2,updated_at=now() WHERE id=$3 AND status='running'", thread, run, id)
		return
	}
	active, e := rows(ctx, a.DB, "SELECT id,snapshot_id,external_thread_id,external_run_id FROM research_runs WHERE status='external_running' AND updated_at<now()-interval '5 seconds' LIMIT 3")
	if e != nil {
		return
	}
	for _, item := range active {
		runID := fmt.Sprint(item["id"])
		in, loadErr := a.loadSnapshot(ctx, fmt.Sprint(item["snapshot_id"]))
		if loadErr != nil {
			_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='invalidated',updated_at=now() WHERE id=$1", runID)
			continue
		}
		result, status, e := a.agentJSON(ctx, "GET", "/internal/sciencepal/runs/"+url.PathEscape(fmt.Sprint(item["external_run_id"])), nil)
		if e != nil || status != 200 {
			continue
		}
		local := "external_running"
		switch fmt.Sprint(result["status"]) {
		case "completed", "succeeded", "finished":
			local = "awaiting_import"
			artifact, code, fetchErr := a.agentJSON(ctx, "GET", "/internal/sciencepal/threads/"+url.PathEscape(fmt.Sprint(item["external_thread_id"]))+"/artifacts/"+runID, nil)
			if fetchErr == nil && code == 200 {
				report, ok := artifact["report"].(map[string]any)
				if ok && validateReportNumbers(report, in) == nil {
					manifest, manifestErr := a.snapshotManifest(ctx, fmt.Sprint(item["snapshot_id"]), in)
					if manifestErr != nil {
						continue
					}
					report["manifest"] = manifest
					report["origin_verification"] = "api-fetched-artifact"
					report["execution_platform"] = "SciencePal"
					report["external_run_id"] = item["external_run_id"]
					report["execution_log"] = artifact["execution_log"]
					if _, loadErr = a.loadSnapshot(ctx, fmt.Sprint(item["snapshot_id"])); loadErr == nil {
						_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status='completed',result=$1,updated_at=now() WHERE id=$2 AND status='external_running'", encode(report), runID)
						continue
					}
				}
			}
		case "asked":
			local = "external_asked"
		case "failed", "stopped":
			local = "failed"
		}
		_, _ = a.DB.Exec(ctx, "UPDATE research_runs SET status=$1,updated_at=now() WHERE id=$2 AND status='external_running'", local, runID)
	}
}
