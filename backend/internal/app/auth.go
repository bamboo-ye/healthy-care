package app

import (
	"context"
	"errors"
	"net/mail"
	"strings"
	"time"

	"healthycare/internal/store"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"golang.org/x/crypto/bcrypt"
)

type credentials struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

func (a *App) authLimit(c *gin.Context) bool {
	ctx, cancel := context.WithTimeout(c, time.Second)
	defer cancel()
	key := "auth-rate:" + hash(c.ClientIP())
	n, err := a.Cache.Incr(ctx, key).Result()
	if err != nil {
		// Redis is a cache; loss must not disable authentication throttling.
		a.rateMu.Lock()
		if a.rates == nil {
			a.rates = map[string]rateWindow{}
		}
		now := time.Now()
		for k, entry := range a.rates {
			if now.After(entry.Until) {
				delete(a.rates, k)
			}
		}
		entry := a.rates[key]
		if entry.Until.IsZero() {
			entry.Until = now.Add(15 * time.Minute)
		}
		entry.Count++
		a.rates[key] = entry
		n = int64(entry.Count)
		a.rateMu.Unlock()
	}
	if n == 1 {
		a.Cache.Expire(ctx, key, 15*time.Minute)
	}
	if n > 30 {
		fail(c, 429, "rate_limited", "尝试次数较多，请稍后再试。")
		return false
	}
	return true
}
func (a *App) register(c *gin.Context) {
	if !a.authLimit(c) {
		return
	}
	var in credentials
	if !bind(c, &in) {
		return
	}
	in.Email = strings.ToLower(strings.TrimSpace(in.Email))
	address, err := mail.ParseAddress(in.Email)
	if err != nil || address.Address != in.Email || len(in.Email) > 254 || len(in.Password) < 12 || len(in.Password) > 72 {
		fail(c, 400, "invalid_credentials", "请输入有效邮箱和12至72字节的密码。")
		return
	}
	hashed, err := bcrypt.GenerateFromPassword([]byte(in.Password), bcrypt.DefaultCost)
	if err != nil {
		internalError(c, err)
		return
	}
	tx, err := a.DB.Begin(c)
	if err != nil {
		internalError(c, err)
		return
	}
	defer tx.Rollback(c)
	var u Actor
	err = tx.QueryRow(c, "INSERT INTO users(email,password_hash) VALUES($1,$2) RETURNING id,email,role", in.Email, string(hashed)).Scan(&u.ID, &u.Email, &u.Role)
	if err != nil {
		var pe *pgconn.PgError
		if errors.As(err, &pe) && pe.Code == "23505" {
			fail(c, 409, "account_unavailable", "此邮箱无法注册，请尝试登录。")
		} else {
			internalError(c, err)
		}
		return
	}
	if _, err = tx.Exec(c, "INSERT INTO profiles(user_id) VALUES($1)", u.ID); err != nil {
		internalError(c, err)
		return
	}
	if _, err = tx.Exec(c, "INSERT INTO conversations(user_id) VALUES($1)", u.ID); err != nil {
		internalError(c, err)
		return
	}
	if err = tx.Commit(c); err != nil {
		internalError(c, err)
		return
	}
	a.createSession(c, u)
}
func (a *App) initUser(ctx context.Context, id string) error {
	_, err := a.DB.Exec(ctx, "INSERT INTO profiles(user_id) VALUES($1) ON CONFLICT DO NOTHING", id)
	if err != nil {
		return err
	}
	_, err = a.DB.Exec(ctx, "INSERT INTO conversations(user_id) VALUES($1) ON CONFLICT DO NOTHING", id)
	return err
}
func (a *App) login(c *gin.Context) {
	if !a.authLimit(c) {
		return
	}
	var in credentials
	if !bind(c, &in) {
		return
	}
	var u Actor
	var hashed string
	row, err := store.New(a.DB).UserByEmail(c, strings.ToLower(strings.TrimSpace(in.Email)))
	if err == nil {
		u.ID = uuid.UUID(row.ID.Bytes).String()
		u.Email = row.Email
		u.Role = row.Role
		hashed = row.PasswordHash
	}
	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		internalError(c, err)
		return
	}
	if len(hashed) == 0 {
		hashed = "$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
	}
	passErr := bcrypt.CompareHashAndPassword([]byte(hashed), []byte(in.Password))
	if err != nil || passErr != nil {
		fail(c, 401, "invalid_credentials", "邮箱或密码不正确。")
		return
	}
	a.createSession(c, u)
}
func (a *App) createSession(c *gin.Context, u Actor) {
	token := randomToken()
	u.CSRF = randomToken()
	_, err := a.DB.Exec(c, "INSERT INTO sessions(token_hash,user_id,csrf,expires_at) VALUES($1,$2,$3,$4)", hash(token), u.ID, u.CSRF, time.Now().Add(7*24*time.Hour))
	if err != nil {
		internalError(c, err)
		return
	}
	c.SetSameSite(3)
	c.SetCookie("hc_session", token, 7*24*3600, "/", "", a.Config.CookieSecure, true)
	c.JSON(200, u)
}
func (a *App) logout(c *gin.Context) {
	token, _ := c.Cookie("hc_session")
	_, err := a.DB.Exec(c, "DELETE FROM sessions WHERE token_hash=$1", hash(token))
	if err != nil {
		internalError(c, err)
		return
	}
	c.SetSameSite(3)
	c.SetCookie("hc_session", "", -1, "/", "", a.Config.CookieSecure, true)
	c.JSON(200, gin.H{"ok": true})
}
func (a *App) SeedResearcher(ctx context.Context) error {
	if a.Config.ResearchEmail == "" || len(a.Config.ResearchPassword) < 12 {
		return nil
	}
	b, err := bcrypt.GenerateFromPassword([]byte(a.Config.ResearchPassword), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	_, err = a.DB.Exec(ctx, "INSERT INTO users(email,password_hash,role) VALUES($1,$2,'researcher') ON CONFLICT(email) DO NOTHING", strings.ToLower(a.Config.ResearchEmail), string(b))
	return err
}
