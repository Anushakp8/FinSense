# FinSense â€” Lessons Learned

## Purpose
This file tracks patterns, mistakes, and rules to prevent repeating errors.
Updated after every correction from the user.

---

## Lessons

### 1. No `version` key in docker-compose.yml
**Pattern**: Modern Docker Compose ignores the `version` attribute and warns about it.
**Rule**: Never include `version: "3.x"` in docker-compose.yml files.

### 2. Verify Docker image tags exist before using them
**Pattern**: `apache/airflow:2.8.1-python3.12` doesn't exist on Docker Hub. The available Python variant is `python3.11`.
**Rule**: Always check Docker Hub for exact available tags before specifying images. Don't assume version combinations exist.
