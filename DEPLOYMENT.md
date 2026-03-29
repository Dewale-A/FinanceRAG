# FinanceRAG Deployment Guide

## Infrastructure
- **Server:** AWS EC2 t3.small (Ubuntu 24.04)
- **Region:** us-east-1
- **IP:** 35.171.2.221
- **Stack:** FastAPI + Docker + Nginx + ChromaDB + PostgreSQL
- **CI/CD:** GitHub Actions (auto-deploy on push to main)

## Architecture
```
Client → Nginx (port 80) → Docker (port 8000) → FastAPI
                                                    ├── ChromaDB (vector store)
                                                    ├── PostgreSQL (query logs)
                                                    └── OpenAI API (embeddings + LLM)
```

## Deploy from Scratch

### 1. Launch EC2
- AMI: Ubuntu 24.04 LTS
- Instance type: t3.small (2 vCPU, 2GB RAM)
- Security group: ports 22, 80, 443, 8000
- Key pair: financerag-key.pem

### 2. Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 nginx postgresql postgresql-contrib
sudo systemctl enable docker
sudo systemctl enable postgresql
sudo systemctl enable nginx
```

### 3. Clone and Configure
```bash
cd ~
git clone https://github.com/Dewale-A/FinanceRAG.git
cd FinanceRAG
cp .env.example .env
nano .env  # Fill in all values
```

### 4. Set Up PostgreSQL
```bash
sudo -u postgres psql
CREATE USER financerag WITH PASSWORD 'your_password';
CREATE DATABASE financerag OWNER financerag;
GRANT ALL PRIVILEGES ON DATABASE financerag TO financerag;
\q
```

Configure pg_hba.conf for Docker access:
```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
# Add: host all all 172.16.0.0/12 md5

sudo nano /etc/postgresql/16/main/postgresql.conf
# Set: listen_addresses = '*'

sudo systemctl restart postgresql
```

### 5. Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/financerag
```
```nginx
server {
    listen 80;
    server_name 35.171.2.221;
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/financerag /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Deploy
```bash
docker compose up --build -d
```

### 7. Ingest Documents
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"source_path": "/app/sample_docs/aml_policy.md"}'
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| OPENAI_API_KEY | OpenAI API key for embeddings + LLM | Yes |
| DATABASE_URL | PostgreSQL connection string | Yes |
| API_KEY | API authentication key | Yes |
| SENTRY_DSN | Sentry error tracking URL | No |
| ENVIRONMENT | Deployment environment | No |
| LLM_MODEL | LLM model name (default: gpt-4o-mini) | No |
| EMBEDDING_MODEL | Embedding model (default: text-embedding-ada-002) | No |
| CHROMA_PERSIST_DIR | ChromaDB storage path | No |

## Monitoring
- **Uptime:** UptimeRobot (5-min health checks)
- **Errors:** Sentry (real-time error tracking)
- **Health:** http://35.171.2.221/health
- **Logs:** `docker logs financerag`

## CI/CD Pipeline
Push to `main` triggers:
1. **CI:** 22 tests + Docker build verification
2. **CD:** Auto-deploy to EC2 via SSH

Status: https://github.com/Dewale-A/FinanceRAG/actions

## Common Commands

```bash
# View logs
docker logs financerag --tail 50

# Restart app
docker compose down && docker compose up -d

# Rebuild after code changes
docker compose down && docker compose up --build -d

# Check PostgreSQL
psql -U financerag -d financerag -h localhost -W

# View query logs
psql -U financerag -d financerag -h localhost -W -c "SELECT * FROM query_logs ORDER BY timestamp DESC LIMIT 10;"

# Backup database
pg_dump -U financerag financerag > backup_$(date +%Y%m%d).sql

# Check disk space
df -h

# Clean Docker cache
docker system prune -af
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| / | GET | No | API info |
| /health | GET | No | Health check |
| /stats | GET | No | Collection stats |
| /query | POST | Yes | RAG query |
| /chat | POST | Yes | Chat with history |
| /ingest | POST | Yes | Ingest from path |
| /ingest/upload | POST | Yes | Upload and ingest |
| /collection | DELETE | Yes | Clear collection |
| /docs | GET | No | Swagger UI |

Authentication: Include `X-API-Key: YOUR_KEY` header for protected endpoints.

## Troubleshooting

**App not starting:** `docker logs financerag`
**502 Bad Gateway:** App is down. `docker compose ps` to check.
**Database connection error:** `sudo systemctl status postgresql`
**Disk full:** `docker system prune -af` to clean Docker cache.
**Port conflict:** `sudo lsof -i :8000` to find conflicting process.
