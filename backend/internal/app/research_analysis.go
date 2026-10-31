package app

import (
	"bytes"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"sort"
)

//go:embed fixtures/synthetic.json
var syntheticFixture []byte

var commonFields = []string{"chief", "onset", "severity", "impact", "medicine"}

type researchDefinition struct {
	Source       string `json:"source"`
	Topic        string `json:"topic"`
	Category     string `json:"category"`
	Window       int    `json:"window_days"`
	StartFrom    string `json:"start_from,omitempty"`
	StartTo      string `json:"start_to,omitempty"`
	ProductID    string `json:"product_id,omitempty"`
	Availability string `json:"availability,omitempty"`
}
type researchInput struct {
	SchemaVersion    string            `json:"schema_version"`
	DataOrigin       string            `json:"data_origin"`
	DataVersion      string            `json:"data_version"`
	Config           map[string]any    `json:"config"`
	FieldDefinitions []map[string]any  `json:"field_definitions"`
	RuleVersion      string            `json:"rule_version"`
	KnowledgeVersion string            `json:"knowledge_version"`
	Subjects         []researchSubject `json:"subjects"`
	Selection        *cohortSelection  `json:"selection,omitempty"`
}
type researchSubject struct {
	ParticipantID   string                `json:"participant_id,omitempty"`
	DayKeys         []string              `json:"patient_day_keys,omitempty"`
	ID              string                `json:"id"`
	Index           int                   `json:"index"`
	Topic           string                `json:"topic"`
	Category        string                `json:"category"`
	ResearchConsent bool                  `json:"research_consent"`
	ConsentVersion  string                `json:"consent_version"`
	ClosedDay       *int                  `json:"closed_day"`
	FirstFields     map[string]bool       `json:"first_fields"`
	Observations    []researchObservation `json:"observations"`
	ExpectedDays    int                   `json:"expected_days"`
}
type researchObservation struct {
	Day                  int                 `json:"day"`
	Date                 string              `json:"date"`
	Score                *float64            `json:"score"`
	Use                  string              `json:"use"`
	Known                map[string]bool     `json:"known"`
	FieldValues          map[string]any      `json:"field_values"`
	FieldSources         map[string]string   `json:"field_sources"`
	SourceText           string              `json:"source_text"`
	MedicationEvidence   map[string]any      `json:"medication_evidence"`
	Products             []researchProduct   `json:"products"`
	SymptomText          string              `json:"symptom_text"`
	SourceID             string              `json:"source_id"`
	SourceType           string              `json:"source_type"`
	ImageAvailable       bool                `json:"image_available"`
	ImageResearchConsent bool                `json:"image_research_consent"`
	Symptoms             []map[string]string `json:"symptoms,omitempty"`
}
type researchProduct struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	Ingredients []string `json:"ingredients"`
	Kind        string   `json:"kind"`
	Basis       any      `json:"basis"`
	Strength    any      `json:"strength"`
	Site        any      `json:"site"`
}
type researchCandidate struct {
	ParticipantID string   `json:"participant_id"`
	Rule          string   `json:"rule"`
	Topic         string   `json:"topic"`
	Date          string   `json:"date"`
	SourceID      string   `json:"source_id"`
	Facts         []string `json:"facts"`
}

func canonical(v any) []byte {
	var b bytes.Buffer
	e := json.NewEncoder(&b)
	e.SetEscapeHTML(false)
	_ = e.Encode(v)
	var normalized any
	_ = json.Unmarshal(b.Bytes(), &normalized)
	b.Reset()
	e = json.NewEncoder(&b)
	e.SetEscapeHTML(false)
	_ = e.Encode(normalized)
	return bytes.TrimSpace(b.Bytes())
}
func digest(v any) string { s := sha256.Sum256(canonical(v)); return hex.EncodeToString(s[:]) }
func percentage(n, d int) any {
	if d == 0 {
		return nil
	}
	return math.Floor(float64(n)*1000/float64(d)+0.5) / 10
}

func validateReportNumbers(report map[string]any, in researchInput) error {
	expected := analyze(in)
	if report["input_sha256"] != expected["input_sha256"] || report["schema_version"] != "1.0" || report["code_version"] != expected["code_version"] || !bytes.Equal(canonical(report["config"]), canonical(expected["config"])) || report["knowledge_version"] != in.KnowledgeVersion || report["rule_version"] != in.RuleVersion || report["data_version"] != in.DataVersion {
		return &domainError{400, "report_mismatch", "结果的输入、窗口、方法或知识版本不一致。"}
	}
	metrics, ok := report["metrics"].(map[string]any)
	if !ok {
		return &domainError{400, "invalid_report", "结果缺少指标。"}
	}
	for key, value := range expected["metrics"].(map[string]any) {
		if key == "events" {
			continue
		}
		got, exists := metrics[key]
		if !exists || !sameMetric(got, value) {
			return &domainError{400, "metric_mismatch", "结果指标或分母与当前快照不一致：" + key}
		}
	}
	return nil
}
func syntheticData(def researchDefinition) (researchInput, error) {
	var in researchInput
	if err := json.Unmarshal(syntheticFixture, &in); err != nil {
		return in, err
	}
	in.Config = cohortConfig(def)
	selection := &cohortSelection{Eligible: len(in.Subjects), Excluded: map[string]int{}}
	subjects := []researchSubject{}
	for _, s := range in.Subjects {
		if !s.ResearchConsent {
			selection.Excluded["not_authorized"]++
			continue
		}
		if s.ExpectedDays > def.Window {
			s.ExpectedDays = def.Window
		}
		obs := []researchObservation{}
		for _, o := range s.Observations {
			if o.Day < s.ExpectedDays {
				obs = append(obs, o)
			}
		}
		s.Observations = obs
		if reason := cohortExclusion(s, def, syntheticAnchor(s)); reason != "" {
			selection.Excluded[reason]++
			continue
		}
		subjects = append(subjects, s)
	}
	in.Subjects = subjects
	selection.Included = len(subjects)
	if advancedFilters(def) {
		in.Selection = selection
	}
	return in, nil
}
func analyze(in researchInput) map[string]any {
	expected, observed, first, full := 0, 0, 0, 0
	use := map[string]int{"used": 0, "not_used": 0, "unknown": 0}
	candidates := []researchCandidate{}
	byDay := map[int]map[string]int{}
	fields := []map[string]any{}
	paired := []map[string]any{}
	byRule := map[string]int{"duplicate": 0, "antibiotic": 0, "steroid": 0, "ingredient": 0}
	fieldFirst := map[string]int{}
	fieldFull := map[string]int{}
	candidateSubjects := map[string]bool{}
	participants := map[string]bool{}
	expectedKeys := map[string]bool{}
	observedUse := map[string]string{}
	for _, s := range in.Subjects {
		person := s.ParticipantID
		if person == "" {
			person = s.ID
		}
		participants[person] = true
		dayKey := func(day int) string {
			if day >= 0 && day < len(s.DayKeys) {
				return person + ":" + s.DayKeys[day]
			}
			return s.ID + fmt.Sprintf(":%d", day)
		}
		expected += s.ExpectedDays
		observed += len(s.Observations)
		found := map[string]researchCandidate{}
		for day := 0; day < s.ExpectedDays; day++ {
			expectedKeys[dayKey(day)] = true
			if byDay[day] == nil {
				byDay[day] = map[string]int{}
			}
			byDay[day]["expected"]++
		}
		for _, f := range commonFields {
			if s.FirstFields[f] {
				first++
				fieldFirst[f]++
			}
			if in.DataOrigin == "consented" && s.FirstFields[f] {
				full++
				fieldFull[f]++
				continue
			}
			for _, o := range s.Observations {
				if o.Known[f] {
					full++
					fieldFull[f]++
					break
				}
			}
		}
		for _, o := range s.Observations {
			key := dayKey(o.Day)
			previous := observedUse[key]
			if previous == "" || o.Use == "used" || (previous != "used" && o.Use == "unknown") {
				observedUse[key] = o.Use
			}
			use[o.Use]++
			byDay[o.Day]["observed"]++
			if o.Use != "used" {
				continue
			}
			components := map[string]map[string]bool{}
			add := func(rule string, facts []string) {
				if _, ok := found[rule]; !ok {
					source := o.SourceID
					if v, ok := o.MedicationEvidence["source_id"].(string); ok {
						source = v
					}
					found[rule] = researchCandidate{s.ID, rule, s.Topic, o.Date, source, facts}
				}
			}
			for _, p := range o.Products {
				for _, ing := range p.Ingredients {
					if components[ing] == nil {
						components[ing] = map[string]bool{}
					}
					components[ing][p.ID] = true
				}
				if len(p.Ingredients) == 0 {
					add("ingredient", []string{p.Name, "未记录可归一的成分"})
				}
				if p.Kind == "antibiotic" && (p.Basis == nil || p.Basis == "") {
					add("antibiotic", []string{p.Name, "使用依据未记录"})
				}
				if p.Kind == "topical_steroid" && (p.Strength == nil || p.Strength == "" || p.Site == nil || p.Site == "") {
					add("steroid", []string{p.Name, "强度或使用部位待补充"})
				}
			}
			ingredientKeys := []string{}
			for ing := range components {
				ingredientKeys = append(ingredientKeys, ing)
			}
			sort.Strings(ingredientKeys)
			for _, ing := range ingredientKeys {
				products := components[ing]
				if len(products) > 1 {
					add("duplicate", []string{ing, "同日存在不同产品记录"})
				}
			}
		}
		keys := []string{}
		for k := range found {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			candidates = append(candidates, found[k])
			byRule[k]++
			candidateSubjects[person] = true
		}
		var start, end *researchObservation
		for i := range s.Observations {
			o := &s.Observations[i]
			if o.Score == nil {
				continue
			}
			if start == nil || o.Day < start.Day {
				start = o
			}
			if end == nil || o.Day > end.Day {
				end = o
			}
		}
		if start != nil && end != nil && start.Day != end.Day {
			paired = append(paired, map[string]any{"id": s.ID, "topic": s.Topic, "first_score": start.Score, "last_score": end.Score, "first_day": start.Day + 1, "last_day": end.Day + 1})
		}
	}
	for _, f := range commonFields {
		fields = append(fields, map[string]any{"field": f, "first": fieldFirst[f], "full": fieldFull[f], "denominator": len(in.Subjects)})
	}
	expected = len(expectedKeys)
	observed = len(observedUse)
	use = map[string]int{"used": 0, "not_used": 0, "unknown": 0}
	for _, value := range observedUse {
		if value != "used" && value != "not_used" {
			value = "unknown"
		}
		use[value]++
	}
	days := []map[string]any{}
	for day := 0; day < 7; day++ {
		if v := byDay[day]; v != nil {
			days = append(days, map[string]any{"day": day + 1, "expected": v["expected"], "observed": v["observed"], "completeness_pct": percentage(v["observed"], v["expected"])})
		}
	}
	metrics := map[string]any{"participants": len(participants), "events": len(in.Subjects), "expected_patient_days": expected, "observed_patient_days": observed, "completeness_pct": percentage(observed, expected), "first_field_coverage_pct": percentage(first, len(in.Subjects)*5), "longitudinal_field_coverage_pct": percentage(full, len(in.Subjects)*5), "coverage_difference_pp": percentage(full-first, len(in.Subjects)*5), "medication_candidate_participants": len(candidateSubjects), "medication_candidate_count": len(candidates), "documented_use_days": use["used"], "documented_nonuse_days": use["not_used"], "unknown_use_days": use["unknown"], "missing_patient_days": expected - observed, "lower_use_pct": percentage(use["used"], expected), "upper_use_pct": percentage(use["used"]+use["unknown"]+expected-observed, expected)}
	return map[string]any{"schema_version": "1.0", "platform": "local-go", "data_origin": in.DataOrigin, "data_version": in.DataVersion, "code_version": "research-2026.10.18.2", "rule_version": in.RuleVersion, "knowledge_version": in.KnowledgeVersion, "config": in.Config, "input_sha256": digest(in), "selection": in.Selection, "history_matches": researchHistory(in), "metrics": metrics, "candidates": candidates, "fields": fields, "daily": days, "paired": paired, "rules": byRule, "limitations": []string{"候选不等于已经证实误用", "评分变化不等于痊愈", "来源标记不单独认证外部平台身份"}}
}
