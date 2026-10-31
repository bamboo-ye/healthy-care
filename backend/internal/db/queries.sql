-- name: UserByEmail :one
SELECT id,email,role,password_hash FROM users WHERE email=$1;

-- name: CountOwnerEpisodes :one
SELECT count(*) FROM episodes WHERE user_id=$1;
