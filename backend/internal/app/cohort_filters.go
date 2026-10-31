package app

import (
	"fmt"
	"time"
)

type cohortSelection struct {
	Eligible int            `json:"eligible_events"`
	Excluded map[string]int `json:"excluded"`
	Included int            `json:"included_events"`
}

func advancedFilters(d researchDefinition) bool {
	return d.StartFrom != "" || d.StartTo != "" || d.ProductID != "" || (d.Availability != "" && d.Availability != "all")
}
func cohortConfig(d researchDefinition) map[string]any {
	c := map[string]any{"topic": d.Topic, "category": d.Category, "window_days": d.Window}
	if d.StartFrom != "" {
		c["start_from"] = d.StartFrom
	}
	if d.StartTo != "" {
		c["start_to"] = d.StartTo
	}
	if d.ProductID != "" {
		c["product_id"] = d.ProductID
	}
	if d.Availability != "" && d.Availability != "all" {
		c["availability"] = d.Availability
	}
	return c
}
func cohortExclusion(s researchSubject, d researchDefinition, anchor time.Time) string {
	if d.Topic != "all" && s.Topic != d.Topic {
		return "topic"
	}
	if d.Category != "all" && s.Category != d.Category {
		return "category"
	}
	if d.StartFrom != "" || d.StartTo != "" {
		if anchor.IsZero() {
			return "anchor_unknown"
		}
		date := anchor.Format("2006-01-02")
		if (d.StartFrom != "" && date < d.StartFrom) || (d.StartTo != "" && date > d.StartTo) {
			return "date_range"
		}
	}
	if d.ProductID != "" {
		found := false
		for _, o := range s.Observations {
			for _, p := range o.Products {
				if p.ID == d.ProductID {
					found = true
				}
			}
		}
		if !found {
			return "product"
		}
	}
	scores := 0
	for _, o := range s.Observations {
		if o.Score != nil {
			scores++
		}
	}
	switch d.Availability {
	case "observed":
		if len(s.Observations) == 0 {
			return "no_observation"
		}
	case "missing":
		if len(s.Observations) >= s.ExpectedDays {
			return "complete_window"
		}
	case "paired_scores":
		if scores < 2 {
			return "unpaired_scores"
		}
	}
	return ""
}
func syntheticAnchor(s researchSubject) time.Time {
	for _, o := range s.Observations {
		if date, err := time.Parse("2006-01-02", o.Date); err == nil {
			return date.AddDate(0, 0, -o.Day)
		}
	}
	return time.Time{}
}

// Descriptive matches within the selected observation window, not a probability
// or a current personal alert. Negation and unknown assertions clear a concept.
func researchHistory(in researchInput) []map[string]any {
	out := []map[string]any{}
	for _, s := range in.Subjects {
		latest := map[string]map[string]any{}
		for _, o := range s.Observations {
			for _, symptom := range o.Symptoms {
				code := symptom["code"]
				if symptomLabels[code] == "" {
					continue
				}
				if old := latest[code]; old == nil || o.Day >= old["day"].(int) {
					latest[code] = map[string]any{"code": code, "label": symptomLabels[code], "assertion": symptom["assertion"], "day": o.Day, "source_id": o.SourceID}
				}
			}
		}
		evidence := []map[string]any{}
		for _, code := range []string{"thirst", "urination", "weight_loss"} {
			if latest[code] == nil || latest[code]["assertion"] != "present" {
				break
			}
			evidence = append(evidence, latest[code])
		}
		if len(evidence) == 3 {
			out = append(out, map[string]any{"id": s.ID, "topic": s.Topic, "evidence": evidence, "rule_version": "history-window-1", "source_url": "https://www.nhs.uk/conditions/type-2-diabetes/symptoms/", "knowledge_version": in.KnowledgeVersion, "label": fmt.Sprintf("%d天观察窗口内的组合，待核实", s.ExpectedDays)})
		}
	}
	return out
}
