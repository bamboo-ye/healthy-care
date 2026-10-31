package config

import (
	"errors"
	"os"
	"strconv"
)

type Config struct {
	DatabaseURL, RedisURL, InternalToken, AgentURL, Origin, StorageDir, Addr string
	ResearchEmail, ResearchPassword                                          string
	RunSigningKey                                                            string
	CookieSecure                                                             bool
	AllowSyntheticKnowledge                                                  bool
}

func Env(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func Load() (Config, error) {
	secure, _ := strconv.ParseBool(Env("COOKIE_SECURE", "true"))
	c := Config{
		DatabaseURL: os.Getenv("DATABASE_URL"), RedisURL: Env("REDIS_URL", "redis://redis:6379/0"),
		InternalToken: os.Getenv("INTERNAL_TOKEN"), AgentURL: Env("AGENT_URL", "http://agent-runtime:8000"),
		Origin: Env("APP_ORIGIN", "http://localhost:8780"), StorageDir: Env("STORAGE_DIR", "/data/files"),
		Addr: Env("LISTEN_ADDR", ":8080"), CookieSecure: secure,
		ResearchEmail: os.Getenv("RESEARCH_EMAIL"), ResearchPassword: os.Getenv("RESEARCH_PASSWORD"),
		RunSigningKey:           os.Getenv("RUN_SIGNING_KEY"),
		AllowSyntheticKnowledge: os.Getenv("ALLOW_SYNTHETIC_KNOWLEDGE") == "true",
	}
	if c.DatabaseURL == "" || len(c.InternalToken) < 32 || len(c.RunSigningKey) < 32 {
		return c, errors.New("DATABASE_URL, INTERNAL_TOKEN and RUN_SIGNING_KEY of at least 32 characters are required")
	}
	return c, nil
}
