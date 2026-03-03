# FinSense â€” Lessons Learned

## Lessons

### 1. No `version` key in docker-compose.yml
**Rule**: Never include `version: "3.x"` in docker-compose.yml files.

### 2. Verify Docker image tags exist before using them
**Rule**: Always check Docker Hub for exact available tags.

### 3. Use `docker compose` (no hyphen) on modern Docker
**Rule**: The standalone `docker-compose` binary is deprecated.
