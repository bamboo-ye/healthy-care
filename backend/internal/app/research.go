package app

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
)

func (a *App) researchRoutes(q *gin.RouterGroup) {
	q.GET("/overview", a.researchOverview)
	q.GET("/records", a.researchRecords)
	q.GET("/records/:id", a.researchRecord)
	q.GET("/knowledge", a.researchKnowledge)
	q.GET("/cohorts", a.listCohorts)
	q.POST("/cohorts", a.saveCohort)
	q.POST("/snapshots", a.createSnapshot)
	q.GET("/snapshots/:id/package", a.snapshotPackage)
	q.GET("/snapshots/:id/bundle", a.snapshotBundle)
	q.GET("/runs", a.researchRuns)
	q.POST("/runs", a.createResearchRun)
	q.POST("/runs/:id/import", a.importReport)
	q.POST("/runs/:id/control", a.controlResearchRun)
	q.GET("/runs/:id", a.researchRun)
	q.GET("/export", a.researchExport)
}
func definition(c *gin.Context) (researchDefinition, error) {
	w := 7
	if c.Query("window_days") != "" {
		w, _ = strconv.Atoi(c.Query("window_days"))
	}
	d := researchDefinition{Source: c.DefaultQuery("source", "synthetic"), Topic: c.DefaultQuery("topic", "all"), Category: c.DefaultQuery("category", "all"), Window: w}
	d.StartFrom = c.Query("start_from")
	d.StartTo = c.Query("start_to")
	d.ProductID = c.Query("product_id")
	d.Availability = c.Query("availability")
	return d, validateDefinition(d)
}
func validateDefinition(d researchDefinition) error {
	for _, date := range []string{d.StartFrom, d.StartTo} {
		if date != "" {
			if _, err := time.Parse("2006-01-02", date); err != nil {
				return invalid("队列起点日期格式不正确。")
			}
		}
	}
	if (d.StartFrom != "" && d.StartTo != "" && d.StartFrom > d.StartTo) || len(d.ProductID) > 150 {
		return invalid("日期范围或产品条件不正确。")
	}
	if d.Availability != "" && d.Availability != "all" && d.Availability != "observed" && d.Availability != "missing" && d.Availability != "paired_scores" {
		return invalid("数据可用性条件不正确。")
	}
	if (d.Source != "synthetic" && d.Source != "consented") || (d.Window != 3 && d.Window != 7) || len(d.Topic) > 100 || len(d.Category) > 100 || d.Topic == "" || d.Category == "" {
		return invalid("队列定义不正确，观察窗口可选3或7天。")
	}
	return nil
}

func researchIngredient(value string) string {
	return map[string]string{"paracetamol": "paracetamol", "acetaminophen": "paracetamol", "对乙酰氨基酚": "paracetamol", "ibuprofen": "ibuprofen", "布洛芬": "ibuprofen"}[strings.ToLower(strings.TrimSpace(value))]
}
func (a *App) pseudonym(value string) string {
	mac := hmac.New(sha256.New, []byte(a.Config.InternalToken))
	mac.Write([]byte(value))
	return hex.EncodeToString(mac.Sum(nil))[:16]
}
func (a *App) researchData(c *gin.Context, d researchDefinition) (researchInput, map[string]int, error) {
	if d.Source == "synthetic" {
		in, e := syntheticData(d)
		return in, nil, e
	}
	in := researchInput{SchemaVersion: "1.0", DataOrigin: "consented", DataVersion: "health-records-v1", Config: cohortConfig(d), FieldDefinitions: []map[string]any{}, RuleVersion: "medication-context-1", KnowledgeVersion: "reference-2026-10-19", Subjects: []researchSubject{}}
	var dictionary researchInput
	if err := json.Unmarshal(syntheticFixture, &dictionary); err != nil {
		return in, nil, err
	}
	in.FieldDefinitions = dictionary.FieldDefinitions
	members := map[string]int{}
	tx, err := a.DB.BeginTx(c, pgx.TxOptions{IsoLevel: pgx.RepeatableRead, AccessMode: pgx.ReadOnly})
	if err != nil {
		return in, nil, err
	}
	defer tx.Rollback(c)
	var cutoff time.Time
	if err = tx.QueryRow(c, "SELECT clock_timestamp()").Scan(&cutoff); err != nil {
		return in, nil, err
	}
	in.Config["cutoff_at"] = cutoff.UTC().Format(time.RFC3339Nano)

	eps, err := rows(c, tx, `SELECT e.id,e.user_id,e.topic,e.started_at,e.onset_known,e.status,e.updated_at,c.version AS consent_version FROM episodes e JOIN consents c ON c.user_id=e.user_id AND c.purpose='research' AND c.granted=true ORDER BY e.started_at`)
	if err != nil {
		return in, nil, err
	}
	selection := &cohortSelection{Eligible: len(eps), Excluded: map[string]int{}}
	for _, e := range eps {
		topic := fmt.Sprint(e["topic"])
		if d.Topic != "all" && topic != d.Topic {
			selection.Excluded["topic"]++
			continue
		}
		if d.Category != "all" {
			selection.Excluded["category"]++
			continue
		}
		user := fmt.Sprint(e["user_id"])
		id := fmt.Sprint(e["id"])
		started := e["started_at"].(time.Time)
		loc, err := userLocation(c, tx, user)
		if err != nil {
			return in, nil, err
		}
		startDay, _ := time.Parse("2006-01-02", started.In(loc).Format("2006-01-02"))
		today, _ := time.Parse("2006-01-02", cutoff.In(loc).Format("2006-01-02"))
		expected := int(today.Sub(startDay).Hours()/24) + 1
		if expected < 1 {
			continue
		}
		if expected > d.Window {
			expected = d.Window
		}
		obs, err := rows(c, tx, "SELECT observed_date,data FROM observations WHERE episode_id=$1 ORDER BY observed_date", id)
		if err != nil {
			return in, nil, err
		}
		onsetKnown, _ := e["onset_known"].(bool)
		s := researchSubject{ParticipantID: "P" + a.pseudonym(user), ID: "E" + a.pseudonym(id), Topic: topic, Category: "自报记录", ResearchConsent: true, ConsentVersion: fmt.Sprint(e["consent_version"]), ExpectedDays: expected, FirstFields: map[string]bool{"chief": true, "onset": onsetKnown}, Observations: []researchObservation{}}
		meds, err := rows(c, tx, "SELECT id,data FROM medication_uses WHERE episode_id=$1 ORDER BY recorded_at", id)
		if err != nil {
			return in, nil, err
		}
		for _, v := range obs {
			date := v["observed_date"].(time.Time)
			day := int(date.Sub(startDay).Hours() / 24)
			if day < 0 || day >= expected {
				continue
			}
			data, _ := v["data"].(map[string]any)
			use := text(data, "medication_state")
			if use == "" {
				use = "unknown"
			}
			var score *float64
			if n, ok := number(data, "score"); ok {
				score = &n
			}
			known := map[string]bool{"chief": true, "onset": onsetKnown, "severity": score != nil, "impact": text(data, "activity") != "", "medicine": text(data, "medication_state") != ""}
			symptoms := []map[string]string{}
			if values, ok := data["symptoms"].([]any); ok {
				for _, v := range values {
					if m, ok := v.(map[string]any); ok && symptomLabels[text(m, "code")] != "" {
						symptoms = append(symptoms, map[string]string{"code": text(m, "code"), "assertion": text(m, "assertion")})
					}
				}
			}
			o := researchObservation{Symptoms: symptoms, Day: day, Date: fmt.Sprintf("day_%d", day+1), Score: score, Use: use, Known: known, FieldValues: map[string]any{}, FieldSources: map[string]string{}, MedicationEvidence: map[string]any{}, Products: []researchProduct{}, SourceID: s.ID + fmt.Sprintf("-D%d", day), SourceType: "consented-structured-self-report"}
			for _, med := range meds {
				md, _ := med["data"].(map[string]any)
				usedAt, parseErr := time.Parse(time.RFC3339, text(md, "used_at"))
				if parseErr != nil || usedAt.In(loc).Format("2006-01-02") != date.Format("2006-01-02") || text(md, "state") != "used" {
					continue
				}
				ingredients := []string{}
				if values, ok := md["ingredients"].([]any); ok {
					for _, v := range values {
						if s, ok := v.(string); ok {
							if normalized := researchIngredient(s); normalized != "" {
								ingredients = append(ingredients, normalized)
							}
						}
					}
				}
				// Free text product names and notes stay in the personal service.
				pid := "M" + a.pseudonym(fmt.Sprint(med["id"]))
				if product := text(md, "product_id"); product != "" {
					pid = product
				}
				o.Products = append(o.Products, researchProduct{ID: pid, Name: pid, Ingredients: ingredients})
				o.Use = "used"
				o.Known["medicine"] = true
			}
			s.Observations = append(s.Observations, o)
		}
		if e["status"] == "archived" {
			lastDay := int(e["updated_at"].(time.Time).Sub(started).Hours() / 24)
			if lastDay < expected-1 && lastDay >= 0 {
				s.ExpectedDays = lastDay + 1
				s.ClosedDay = &lastDay
				filtered := []researchObservation{}
				for _, o := range s.Observations {
					if o.Day < s.ExpectedDays {
						filtered = append(filtered, o)
					}
				}
				s.Observations = filtered
			}
		}
		s.DayKeys = []string{}
		for day := 0; day < s.ExpectedDays; day++ {
			s.DayKeys = append(s.DayKeys, a.pseudonym(user+":"+startDay.AddDate(0, 0, day).Format("2006-01-02")))
		}
		if reason := cohortExclusion(s, d, startDay); reason != "" {
			selection.Excluded[reason]++
			continue
		}
		in.Subjects = append(in.Subjects, s)
		members[user] = int(e["consent_version"].(int32))
	}
	selection.Included = len(in.Subjects)
	if advancedFilters(d) {
		in.Selection = selection
	}
	return in, members, nil
}
func (a *App) researchOverview(c *gin.Context) {
	d, err := definition(c)
	if err != nil {
		fail(c, 400, "invalid_filter", err.Error())
		return
	}
	in, members, err := a.researchData(c, d)
	if err != nil {
		internalError(c, err)
		return
	}
	if d.Source == "consented" && len(members) < 5 {
		c.JSON(200, gin.H{"suppressed": true, "reason": "授权参与者少于5人，暂不展示明细和聚合。", "source": d.Source})
		return
	}
	r := analyze(in)
	if d.Source == "consented" {
		r["metrics"].(map[string]any)["participants"] = len(members)
	}
	c.JSON(200, r)
}
func (a *App) researchRecords(c *gin.Context) {
	d, e := definition(c)
	if e != nil {
		fail(c, 400, "invalid_filter", e.Error())
		return
	}
	in, members, err := a.researchData(c, d)
	if err != nil {
		internalError(c, err)
		return
	}
	if d.Source == "consented" && len(members) < 5 {
		c.JSON(200, gin.H{"items": []any{}, "suppressed": true})
		return
	}
	items := []map[string]any{}
	for _, s := range in.Subjects {
		if search := strings.TrimSpace(c.Query("search")); search != "" && !strings.Contains(s.ID+" "+s.Topic, search) {
			continue
		}
		items = append(items, map[string]any{"id": s.ID, "topic": s.Topic, "category": s.Category, "expected_days": s.ExpectedDays, "recorded_days": len(s.Observations), "source": in.DataOrigin})
	}
	c.JSON(200, gin.H{"items": items, "source": in.DataOrigin})
}
func (a *App) researchRecord(c *gin.Context) {
	d, e := definition(c)
	if e != nil {
		fail(c, 400, "invalid_filter", e.Error())
		return
	}
	in, members, err := a.researchData(c, d)
	if err != nil {
		internalError(c, err)
		return
	}
	if d.Source == "consented" && len(members) < 5 {
		fail(c, 403, "small_sample_suppressed", "样本较少，暂不开放单例。")
		return
	}
	for _, s := range in.Subjects {
		if s.ID == c.Param("id") {
			a.audit(c, actor(c).ID, "research_record_view", s.ID, "research")
			c.JSON(200, s)
			return
		}
	}
	fail(c, 404, "not_found", "没有找到记录。")
}
func (a *App) researchKnowledge(c *gin.Context) {
	v, err := rows(c, a.DB, "SELECT id,topic,title,content,source_url,version,review_status FROM knowledge_items ORDER BY id")
	if err != nil {
		internalError(c, err)
		return
	}
	papers, err := rows(c, a.DB, "SELECT id,title,topic,abstract AS content,source_url,year::text AS version,venue AS source_label FROM research_papers ORDER BY year DESC,id")
	if err != nil {
		internalError(c, err)
		return
	}
	c.JSON(200, gin.H{"items": v, "papers": papers})
}
func (a *App) listCohorts(c *gin.Context) {
	v, err := rows(c, a.DB, "SELECT id,name,definition,created_at FROM research_cohorts WHERE created_by=$1 ORDER BY created_at DESC", actor(c).ID)
	if err != nil {
		internalError(c, err)
		return
	}
	c.JSON(200, gin.H{"items": v})
}
func (a *App) saveCohort(c *gin.Context) {
	var in struct {
		Name       string             `json:"name"`
		Definition researchDefinition `json:"definition"`
	}
	if !bind(c, &in) {
		return
	}
	if len(in.Name) < 1 || len(in.Name) > 150 || validateDefinition(in.Definition) != nil {
		fail(c, 400, "invalid_cohort", "请核对队列名称与定义。")
		return
	}
	var id string
	err := a.DB.QueryRow(c, "INSERT INTO research_cohorts(created_by,name,definition) VALUES($1,$2,$3) RETURNING id", actor(c).ID, in.Name, encode(in.Definition)).Scan(&id)
	if err != nil {
		internalError(c, err)
		return
	}
	c.JSON(201, gin.H{"id": id})
}
func (a *App) createSnapshot(c *gin.Context) {
	var d researchDefinition
	if !bind(c, &d) {
		return
	}
	if err := validateDefinition(d); err != nil {
		fail(c, 400, "invalid_filter", err.Error())
		return
	}
	in, members, err := a.researchData(c, d)
	if err != nil {
		internalError(c, err)
		return
	}
	if d.Source == "consented" && len(members) < 5 {
		fail(c, 403, "small_sample_suppressed", "授权参与者不足，暂不生成研究快照。")
		return
	}
	tx, err := a.DB.Begin(c)
	if err != nil {
		internalError(c, err)
		return
	}
	defer tx.Rollback(c)
	var id string
	sum := digest(in)
	err = tx.QueryRow(c, "INSERT INTO research_snapshots(created_by,definition,source,input,input_sha256) VALUES($1,$2,$3,$4,$5) RETURNING id", actor(c).ID, encode(d), d.Source, encode(in), sum).Scan(&id)
	if err != nil {
		internalError(c, err)
		return
	}
	for user, version := range members {
		_, err = tx.Exec(c, "INSERT INTO snapshot_members(snapshot_id,user_id,consent_version) VALUES($1,$2,$3)", id, user, version)
		if err != nil {
			internalError(c, err)
			return
		}
	}
	if err = tx.Commit(c); err != nil {
		internalError(c, err)
		return
	}
	a.audit(c, actor(c).ID, "snapshot_create", id, "research")
	c.JSON(201, gin.H{"id": id, "input_sha256": sum, "source": d.Source})
}
func (a *App) loadSnapshot(c context.Context, id string) (researchInput, error) {
	var in researchInput
	var b []byte
	var invalid bool
	err := a.DB.QueryRow(c, `SELECT input,(invalidated_at IS NOT NULL OR EXISTS(SELECT 1 FROM snapshot_members m LEFT JOIN consents c ON c.user_id=m.user_id AND c.purpose='research' WHERE m.snapshot_id=s.id AND (c.granted IS DISTINCT FROM true OR c.version<>m.consent_version))) FROM research_snapshots s WHERE id=$1`, id).Scan(&b, &invalid)
	if err != nil {
		return in, err
	}
	if invalid {
		return in, &domainError{403, "snapshot_invalidated", "授权或数据范围已变化，请重新生成快照。"}
	}
	err = json.Unmarshal(b, &in)
	return in, err
}
func snapshotError(c *gin.Context, err error) {
	var d *domainError
	if errors.As(err, &d) {
		fail(c, d.Status, d.Code, d.Message)
	} else if errors.Is(err, pgx.ErrNoRows) {
		fail(c, 404, "not_found", "没有找到快照。")
	} else {
		internalError(c, err)
	}
}
func (a *App) snapshotPackage(c *gin.Context) {
	if !validID(c, "id") {
		return
	}
	in, err := a.loadSnapshot(c, c.Param("id"))
	if err != nil {
		snapshotError(c, err)
		return
	}
	a.audit(c, actor(c).ID, "snapshot_download", c.Param("id"), "research")
	c.Header("Content-Disposition", "attachment; filename=research-input.json")
	c.JSON(200, in)
}
func (a *App) createResearchRun(c *gin.Context) {
	var in struct {
		SnapshotID string `json:"snapshot_id"`
		Platform   string `json:"platform"`
	}
	if !bind(c, &in) {
		return
	}
	if _, err := uuid.Parse(in.SnapshotID); err != nil || (in.Platform != "SciencePal" && in.Platform != "local-reference") {
		fail(c, 400, "invalid_run", "请指定快照和运行平台。")
		return
	}
	snapshot, err := a.loadSnapshot(c, in.SnapshotID)
	if err != nil {
		snapshotError(c, err)
		return
	}
	if in.Platform == "SciencePal" && snapshot.DataOrigin != "synthetic" {
		fail(c, 403, "external_scope_restricted", "当前外部平台演示仅接收合成数据。")
		return
	}
	var id string
	err = a.DB.QueryRow(c, "INSERT INTO research_runs(snapshot_id,created_by,platform) VALUES($1,$2,$3) RETURNING id", in.SnapshotID, actor(c).ID, in.Platform).Scan(&id)
	if err != nil {
		internalError(c, err)
		return
	}
	c.JSON(202, gin.H{"id": id, "status": "queued"})
}
func (a *App) researchRuns(c *gin.Context) {
	v, err := rows(c, a.DB, "SELECT r.id,r.snapshot_id,r.platform,r.status,r.error_code,r.external_run_id,r.created_at,r.updated_at FROM research_runs r JOIN research_snapshots s ON s.id=r.snapshot_id WHERE s.invalidated_at IS NULL AND r.created_by=$1 ORDER BY r.created_at DESC LIMIT 50", actor(c).ID)
	if err != nil {
		internalError(c, err)
		return
	}
	c.JSON(200, gin.H{"items": v})
}
func (a *App) researchRun(c *gin.Context) {
	if !validID(c, "id") {
		return
	}
	v, err := rows(c, a.DB, "SELECT * FROM research_runs WHERE id=$1 AND created_by=$2", c.Param("id"), actor(c).ID)
	if err != nil {
		internalError(c, err)
		return
	}
	if len(v) == 0 {
		fail(c, 404, "not_found", "没有找到分析任务。")
		return
	}
	if _, err = a.loadSnapshot(c, fmt.Sprint(v[0]["snapshot_id"])); err != nil {
		snapshotError(c, err)
		return
	}
	c.JSON(200, v[0])
}
func (a *App) importReport(c *gin.Context) {
	if !validID(c, "id") {
		return
	}
	var report map[string]any
	if !bind(c, &report) {
		return
	}
	var sid string
	err := a.DB.QueryRow(c, "SELECT snapshot_id FROM research_runs WHERE id=$1 AND created_by=$2", c.Param("id"), actor(c).ID).Scan(&sid)
	if errors.Is(err, pgx.ErrNoRows) {
		fail(c, 404, "not_found", "没有找到分析任务。")
		return
	}
	if err != nil {
		internalError(c, err)
		return
	}
	in, err := a.loadSnapshot(c, sid)
	if err != nil {
		snapshotError(c, err)
		return
	}
	if err = validateReportNumbers(report, in); err != nil {
		snapshotError(c, err)
		return
	}
	if report["platform"] == "SciencePal" {
		u, err := url.Parse(fmt.Sprint(report["run_url"]))
		if err != nil || u.Scheme != "https" || u.Hostname() != "sciencepal.ai" {
			fail(c, 400, "invalid_provenance", "请提供SciencePal实际运行链接。")
			return
		}
	}
	manifest, err := a.snapshotManifest(c, sid, in)
	if err != nil {
		internalError(c, err)
		return
	}
	report["manifest"] = manifest
	report["origin_verification"] = "imported-not-platform-authenticated"
	_, err = a.DB.Exec(c, "UPDATE research_runs SET result=$1,status='completed',updated_at=now() WHERE id=$2", encode(report), c.Param("id"))
	if err != nil {
		internalError(c, err)
		return
	}
	a.audit(c, actor(c).ID, "report_import", c.Param("id"), "research")
	c.JSON(200, gin.H{"ok": true, "origin_verification": report["origin_verification"]})
}
func sameMetric(a, b any) bool {
	if a == nil || b == nil {
		return a == nil && b == nil
	}
	aa, ok := a.(float64)
	if !ok {
		return false
	}
	var bb float64
	switch n := b.(type) {
	case int:
		bb = float64(n)
	case float64:
		bb = n
	default:
		return false
	}
	return math.Abs(aa-bb) < 0.000001
}
func (a *App) researchExport(c *gin.Context) {
	d, err := definition(c)
	if err != nil {
		fail(c, 400, "invalid_filter", err.Error())
		return
	}
	in, members, err := a.researchData(c, d)
	if err != nil {
		internalError(c, err)
		return
	}
	if d.Source == "consented" && len(members) < 5 {
		fail(c, 403, "small_sample_suppressed", "授权参与者不足，暂不导出。")
		return
	}
	a.audit(c, actor(c).ID, "research_export", digest(in), "research")
	if c.Query("format") == "csv" {
		c.Header("Content-Type", "text/csv; charset=utf-8")
		c.Header("Content-Disposition", "attachment; filename=research-records.csv")
		writer := csv.NewWriter(c.Writer)
		_ = writer.Write([]string{"event_id", "topic", "patient_day", "score", "medication_state", "source_id"})
		for _, s := range in.Subjects {
			for _, o := range s.Observations {
				score := ""
				if o.Score != nil {
					score = strconv.FormatFloat(*o.Score, 'f', -1, 64)
				}
				_ = writer.Write([]string{csvSafe(s.ID), csvSafe(s.Topic), strconv.Itoa(o.Day + 1), score, o.Use, csvSafe(o.SourceID)})
			}
		}
		writer.Flush()
		return
	}
	c.Header("Content-Disposition", "attachment; filename=research-data.json")
	c.JSON(200, in)
}
func csvSafe(s string) string {
	if len(s) > 0 && strings.ContainsAny(s[:1], "=+-@\t\r") {
		return "'" + s
	}
	return s
}

var _ io.Reader
var _ = http.MethodGet
