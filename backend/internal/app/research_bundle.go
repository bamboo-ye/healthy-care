package app

import (
	"archive/zip"
	"bytes"
	"context"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
)

//go:embed fixtures/run_analysis.py
var referenceScript []byte

func (a *App) snapshotManifest(ctx context.Context, id string, in researchInput) (map[string]any, error) {
	var created time.Time
	var definition []byte
	if err := a.DB.QueryRow(ctx, "SELECT created_at,definition FROM research_snapshots WHERE id=$1", id).Scan(&created, &definition); err != nil {
		return nil, err
	}
	var cohort any
	if err := json.Unmarshal(definition, &cohort); err != nil {
		return nil, err
	}
	cutoff := created.UTC().Format(time.RFC3339Nano)
	if value, ok := in.Config["cutoff_at"].(string); ok {
		cutoff = value
	}
	sum := sha256.Sum256(referenceScript)
	return map[string]any{"schema_version": "1.0", "snapshot_id": id, "input_sha256": digest(in), "cohort_definition": cohort, "cutoff_at": cutoff, "analysis_window": in.Config["window_days"], "code_version": "research-2026.10.18.2", "code_sha256": hex.EncodeToString(sum[:]), "knowledge_version": in.KnowledgeVersion, "rule_version": in.RuleVersion, "data_version": in.DataVersion, "random_seed": 0, "data_origin": in.DataOrigin, "config": in.Config}, nil
}
func buildBundle(in researchInput, manifest map[string]any) ([]byte, error) {
	files := map[string][]byte{
		"health-research-input.json": canonical(in), "run_analysis.py": referenceScript,
		"manifest.json": canonical(manifest),
		"README.md":     []byte("# 冻结研究任务\n\n此包用于合成数据方法验证。运行：\n\npython3 run_analysis.py health-research-input.json --out actual-output\n\n保留实际命令、日志、结果和SciencePal运行链接。标注平台名称不单独证明平台执行；不能将候选或自评分变化解释为临床效能。\n"),
	}
	var out bytes.Buffer
	w := zip.NewWriter(&out)
	for _, name := range []string{"README.md", "manifest.json", "health-research-input.json", "run_analysis.py"} {
		f, err := w.Create(name)
		if err != nil {
			return nil, err
		}
		if _, err = f.Write(files[name]); err != nil {
			return nil, err
		}
	}
	if err := w.Close(); err != nil {
		return nil, err
	}
	return out.Bytes(), nil
}
func (a *App) snapshotBundle(c *gin.Context) {
	if !validID(c, "id") {
		return
	}
	in, err := a.loadSnapshot(c, c.Param("id"))
	if err != nil {
		snapshotError(c, err)
		return
	}
	if in.DataOrigin != "synthetic" {
		fail(c, 403, "unsupported_bundle", "当前外部执行任务包只包含合成数据。")
		return
	}
	manifest, err := a.snapshotManifest(c, c.Param("id"), in)
	if err != nil {
		internalError(c, err)
		return
	}
	body, err := buildBundle(in, manifest)
	if err != nil {
		internalError(c, err)
		return
	}
	a.audit(c, actor(c).ID, "task_bundle_download", c.Param("id"), "research")
	c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=research-task-%s.zip", c.Param("id")))
	c.Data(200, "application/zip", body)
}
