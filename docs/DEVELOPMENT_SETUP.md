# RocketTrainer - Development Setup Guide

## Prerequisites

### Required Software
- **Docker & Docker Compose** (latest version)
- **Node.js** (v18+ recommended)
- **Python** (3.9+ recommended)
- **Git** (latest version)

### Required API Keys
1. **Ballchasing.com API Key**
   - Visit: https://ballchasing.com/upload
   - Create account and request API access
   - Expected wait time: 1-2 weeks

2. **Steam Web API Key**
   - Visit: https://steamcommunity.com/dev/apikey
   - Register your domain (use localhost for development)

3. **Epic Games API Access** (Optional for MVP)
   - Visit: https://dev.epicgames.com/portal
   - Create developer account

## Quick Start (30 minutes)

### 1. Clone and Setup Project
```bash
# Clone repository
git clone <repository-url>
cd RocketTrainer

# Create environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Configure Environment Variables
```bash
# backend/.env
DATABASE_URL=postgresql://postgres:password@localhost:5432/rockettrainer
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
BALLCHASING_API_KEY=your-ballchasing-api-key
STEAM_API_KEY=your-steam-api-key

# frontend/.env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_STEAM_LOGIN_URL=http://localhost:8000/auth/steam-login
```

### 3. Start Development Environment
```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# rockettrainer_api_1      running   0.0.0.0:8000->8000/tcp
# rockettrainer_db_1       running   0.0.0.0:5432->5432/tcp
# rockettrainer_redis_1    running   0.0.0.0:6379->6379/tcp
# rockettrainer_frontend_1 running   0.0.0.0:3000->3000/tcp
```

### 4. Initialize Database
```bash
# Run database migrations
docker-compose exec api python -m alembic upgrade head

# Seed initial data (training packs, etc.)
docker-compose exec api python scripts/seed_data.py
```

### 5. Verify Setup
```bash
# Test API health check
curl http://localhost:8000/health

# Expected response: {"status": "healthy"}

# Open frontend
open http://localhost:3000
```

## Docker Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/rockettrainer
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
      - ./ml:/app/ml
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_DB=rockettrainer
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/sql:/docker-entrypoint-initdb.d

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    command: npm start

volumes:
  postgres_data:
  redis_data:
```

### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "start"]
```

## Development Workflow

### Daily Development Process
```bash
# 1. Start development environment
docker-compose up -d

# 2. Make code changes in your editor

# 3. View logs for debugging
docker-compose logs -f api     # Backend logs
docker-compose logs -f frontend # Frontend logs

# 4. Run tests
docker-compose exec api pytest
docker-compose exec frontend npm test

# 5. Stop environment when done
docker-compose down
```

### Database Management
```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Reset database (development only)
docker-compose down -v
docker-compose up -d
```

### Testing
```bash
# Backend tests
docker-compose exec api pytest tests/ -v

# Frontend tests
docker-compose exec frontend npm test

# Integration tests
docker-compose exec api pytest tests/integration/ -v

# Load testing
docker-compose exec api locust -f tests/load/locustfile.py
```

## IDE Setup

### VS Code Configuration
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Recommended Extensions
- Python
- TypeScript and JavaScript Language Features
- Docker
- GitLens
- Prettier - Code formatter
- ESLint

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different ports in docker-compose.yml
```

#### Database Connection Issues
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Reset database
docker-compose down -v db
docker-compose up -d db
```

#### Frontend Build Issues
```bash
# Clear node modules
docker-compose exec frontend rm -rf node_modules
docker-compose exec frontend npm install

# Or rebuild container
docker-compose build frontend
```

### Performance Optimization

#### Development Performance
```bash
# Use bind mounts for faster file sync
# Add to docker-compose.yml volumes:
- ./backend:/app:cached
- ./frontend:/app:cached

# Exclude node_modules from sync
- /app/node_modules
```

#### Database Performance
```sql
-- Add indexes for common queries
CREATE INDEX idx_matches_user_id ON matches(user_id);
CREATE INDEX idx_player_stats_user_time ON player_stats(user_id, time);
```

## Next Steps After Setup

### Week 1 Tasks
1. **Verify all services are running** ✓
2. **Implement health check endpoints**
3. **Set up basic user model and authentication**
4. **Create first API endpoint** (`GET /users/me`)
5. **Build basic React login page**

### Week 2 Tasks
1. **Implement Steam OAuth flow**
2. **Create user registration process**
3. **Set up database migrations**
4. **Build user dashboard skeleton**

### Validation Checklist
- [ ] Docker containers start without errors
- [ ] Database migrations run successfully
- [ ] API health check returns 200
- [ ] Frontend loads without console errors
- [ ] Can create and authenticate users
- [ ] Basic CRUD operations work

## Getting Help

### Resources
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://reactjs.org/docs/
- **Docker Documentation**: https://docs.docker.com/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

### Community
- **Discord**: Create project Discord server
- **GitHub Issues**: Use for bug tracking
- **Stack Overflow**: Tag questions with `rockettrainer`

---

**Status**: Ready for implementation  
**Estimated Setup Time**: 30-60 minutes  
**Next Action**: Run setup commands and verify all services
