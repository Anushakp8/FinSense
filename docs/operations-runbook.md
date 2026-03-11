# FinSense Operations Runbook

## Required Services

- PostgreSQL/TimescaleDB
- Redis (recommended for production rate limiting)
- API service

## Startup Checklist

1. Start infrastructure:

```bash
docker compose up -d postgres redis
```

2. Confirm services:

```bash
docker compose ps
```

3. Apply migrations:

```bash
cd backend
alembic upgrade head
```

4. Start API:

```bash
uvicorn src.api.main:app --reload
```

## Production Security Defaults

Set these in `.env`:

```bash
API_REQUIRE_KEY=true
API_KEY=<strong-random-secret>

API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_USE_REDIS=true
API_RATE_LIMIT_MAX_REQUESTS=60
API_RATE_LIMIT_WINDOW_SECONDS=60
```

Protected routes:

- `POST /api/v1/predict`
- `GET /api/v1/portfolio-risk`

## Health and Metrics Checks

1. Health:

```bash
curl http://127.0.0.1:8000/health
```

2. Metrics:

```bash
curl http://127.0.0.1:8000/metrics
```

Look for:

- `finsense_requests_total`
- `finsense_rate_limited_total`
- `finsense_responses_2xx_total`
- `finsense_responses_4xx_total`
- `finsense_responses_5xx_total`
- `finsense_requests_by_path_total{path="..."}`
- `finsense_rate_limited_by_path_total{path="..."}`

## Prometheus Alert Examples

Use these as a starting point and tune thresholds for your traffic profile.

```yaml
groups:
	- name: finsense-api-alerts
		rules:
			- alert: FinSensePredictRateLimitSpike
				expr: rate(finsense_rate_limited_by_path_total{path="/api/v1/predict"}[5m]) > 0.5
				for: 10m
				labels:
					severity: warning
					service: finsense-api
				annotations:
					summary: High 429 rate on /api/v1/predict
					description: Predict endpoint is being rate-limited frequently.

			- alert: FinSensePortfolioRateLimitSpike
				expr: rate(finsense_rate_limited_by_path_total{path="/api/v1/portfolio-risk"}[5m]) > 0.2
				for: 10m
				labels:
					severity: warning
					service: finsense-api
				annotations:
					summary: High 429 rate on /api/v1/portfolio-risk
					description: Portfolio endpoint requests are being throttled.

			- alert: FinSenseApiHigh5xx
				expr: rate(finsense_responses_5xx_total[5m]) > 0.1
				for: 5m
				labels:
					severity: critical
					service: finsense-api
				annotations:
					summary: Elevated 5xx responses from FinSense API
					description: API is returning server errors above baseline.
```

Recommended follow-up when alerts fire:

- Check API logs using `request_id` correlation.
- Confirm Redis health if rate limiting is enabled with Redis.
- Inspect recent deploy/migration changes.
- Review caller behavior for sudden bursts or retries.

## Alertmanager Notification Template

Example `alertmanager.yml` skeleton for Slack and email routing:

```yaml
global:
	resolve_timeout: 5m

route:
	receiver: default
	group_by: [alertname, service]
	group_wait: 30s
	group_interval: 5m
	repeat_interval: 2h
	routes:
		- matchers:
				- severity="critical"
			receiver: critical-slack
		- matchers:
				- severity="warning"
			receiver: warning-slack

receivers:
	- name: default
		email_configs:
			- to: ops@example.com
				from: alerts@example.com
				smarthost: smtp.example.com:587
				auth_username: alerts@example.com
				auth_password: <smtp-password>
				require_tls: true
				headers:
					Subject: "[FinSense] {{ .Status | toUpper }}: {{ .CommonLabels.alertname }}"

	- name: critical-slack
		slack_configs:
			- api_url: <slack-webhook-url>
				channel: "#finsense-critical"
				title: "[CRITICAL] {{ .CommonLabels.alertname }}"
				text: >-
					Service: {{ .CommonLabels.service }}
					Summary: {{ .CommonAnnotations.summary }}
					Description: {{ .CommonAnnotations.description }}

	- name: warning-slack
		slack_configs:
			- api_url: <slack-webhook-url>
				channel: "#finsense-warnings"
				title: "[WARNING] {{ .CommonLabels.alertname }}"
				text: >-
					Service: {{ .CommonLabels.service }}
					Summary: {{ .CommonAnnotations.summary }}
					Description: {{ .CommonAnnotations.description }}
```

Suggested routing policy:

- `critical`: immediate Slack page + email.
- `warning`: Slack notification with grouped alerts.
- Add mute windows for known maintenance periods.

Standalone templates are also available at:

- `docs/prometheus.yml`
- `docs/alertmanager.yml`

## Prometheus Scrape Config

Example `prometheus.yml` snippet to scrape FinSense API metrics and Redis exporter:

```yaml
global:
	scrape_interval: 15s
	evaluation_interval: 15s

scrape_configs:
	- job_name: finsense-api
		metrics_path: /metrics
		static_configs:
			- targets:
					- host.docker.internal:8000
				labels:
					service: finsense-api

	- job_name: redis-exporter
		static_configs:
			- targets:
					- redis-exporter:9121
				labels:
					service: redis
```

If Prometheus runs directly on host instead of Docker, replace `host.docker.internal`
with `127.0.0.1` or your host IP as appropriate.

Optional Docker Compose service for Redis exporter:

```yaml
redis-exporter:
	image: oliver006/redis_exporter:latest
	container_name: finsense-redis-exporter
	environment:
		REDIS_ADDR: redis://redis:6379
	ports:
		- "9121:9121"
	depends_on:
		- redis
	networks:
		- finsense-net
```

## Common Issues

### PostgreSQL connection refused

- Verify Docker Desktop is running.
- Verify `postgres` is healthy in `docker compose ps`.
- Verify `DATABASE_URL_SYNC` points to reachable host/port.

### Too many 429 responses

- Check traffic source and `x-forwarded-for` behavior.
- Increase `API_RATE_LIMIT_MAX_REQUESTS` temporarily if needed.
- Ensure Redis is up if `API_RATE_LIMIT_USE_REDIS=true`.

### API key errors (401/503)

- 401: missing/invalid `x-api-key` header.
- 503: `API_REQUIRE_KEY=true` but `API_KEY` is not configured.
