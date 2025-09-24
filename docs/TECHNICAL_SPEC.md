# RocketTrainer - Technical Specification

## System Architecture Overview

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   React App     │   3D Viewer     │      Mobile App             │
│   (Dashboard)   │   (Three.js)    │     (Future)                │
└─────────────────┴─────────────────┴─────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │   API Gateway   │
                    │   (FastAPI)     │
                    └─────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Services                           │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  User Service   │  Analysis       │   Training Service          │
│  (Auth/Profile) │  Service (ML)   │   (Recommendations)         │
└─────────────────┴─────────────────┴─────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   PostgreSQL    │   TimescaleDB   │      Redis Cache            │
│   (Core Data)   │  (Time Series)  │    (Sessions/Cache)         │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

## Database Schema Design

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    steam_id VARCHAR(20) UNIQUE NOT NULL,
    epic_id VARCHAR(50),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE,
    current_rank VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Matches Table
```sql
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ballchasing_id VARCHAR(50) UNIQUE,
    user_id UUID REFERENCES users(id),
    playlist VARCHAR(20), -- ranked-duels, ranked-doubles, etc.
    duration INTEGER, -- seconds
    score_team_0 INTEGER,
    score_team_1 INTEGER,
    result VARCHAR(10), -- win/loss/draw
    replay_data JSONB, -- full replay analysis
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Player Stats (TimescaleDB)
```sql
CREATE TABLE player_stats (
    time TIMESTAMPTZ NOT NULL,
    user_id UUID NOT NULL,
    match_id UUID REFERENCES matches(id),
    stat_type VARCHAR(50), -- 'aerial_accuracy', 'save_percentage', etc.
    value FLOAT NOT NULL,
    rank_percentile FLOAT -- compared to same rank
);

SELECT create_hypertable('player_stats', 'time');
```

#### Training Packs Table
```sql
CREATE TABLE training_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    category VARCHAR(50), -- aerials, saves, shooting, etc.
    difficulty INTEGER, -- 1-10 scale
    description TEXT,
    creator VARCHAR(100),
    tags TEXT[], -- array of tags
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### User Training Sessions
```sql
CREATE TABLE training_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    training_pack_id UUID REFERENCES training_packs(id),
    duration INTEGER, -- seconds
    attempts INTEGER,
    successes INTEGER,
    improvement_score FLOAT,
    completed_at TIMESTAMP DEFAULT NOW()
);
```

## API Specification

### Authentication Endpoints
```
POST /auth/steam-login     # Steam OAuth integration
POST /auth/epic-login      # Epic Games OAuth
GET  /auth/me             # Get current user info
POST /auth/logout         # Logout user
```

### User Management
```
GET    /users/profile      # Get user profile
PUT    /users/profile      # Update profile
GET    /users/stats        # Get user statistics
DELETE /users/account      # Delete account
```

### Replay Analysis
```
POST /replays/upload       # Upload replay file
GET  /replays/{id}         # Get replay analysis
POST /replays/ballchasing  # Import from Ballchasing.com
GET  /replays/recent       # Get recent replays
```

### Training System
```
GET  /training/recommendations  # Get personalized recommendations
POST /training/sessions        # Log training session
GET  /training/packs          # Search training packs
GET  /training/progress       # Get training progress
```

### Analytics
```
GET /analytics/weaknesses     # Get weakness analysis
GET /analytics/progress       # Get improvement metrics
GET /analytics/rank-prediction # Get rank prediction
GET /analytics/comparison     # Compare with similar players
```

## Machine Learning Pipeline

### Data Processing Flow
```
Replay File → Parser → Feature Extraction → ML Models → Insights
```

### Feature Engineering

#### Positional Features
- Average position on field (x, y, z coordinates)
- Position variance (how much player moves)
- Time spent in defensive/offensive thirds
- Rotation efficiency score

#### Mechanical Features
- Aerial attempt frequency and success rate
- Save attempt frequency and success rate
- Shot accuracy and power
- Boost management efficiency

#### Game Sense Features
- Positioning relative to ball and teammates
- Rotation timing
- Challenge timing
- Boost collection patterns

### ML Models

#### Weakness Detection Model
```python
# Simplified model architecture
class WeaknessDetector:
    def __init__(self):
        self.models = {
            'aerials': RandomForestClassifier(),
            'saves': GradientBoostingClassifier(),
            'positioning': SupportVectorClassifier(),
            'rotation': LogisticRegression(),
            'shooting': RandomForestClassifier()
        }
    
    def predict_weaknesses(self, features):
        weaknesses = {}
        for skill, model in self.models.items():
            score = model.predict_proba(features)[0][1]
            weaknesses[skill] = {
                'score': score,
                'percentile': self.get_rank_percentile(skill, score),
                'improvement_potential': self.calculate_potential(score)
            }
        return weaknesses
```

#### Rank Prediction Model
```python
class RankPredictor:
    def __init__(self):
        self.model = XGBRegressor()
        self.features = [
            'aerial_accuracy', 'save_percentage', 'shot_accuracy',
            'positioning_score', 'rotation_efficiency', 'boost_efficiency'
        ]
    
    def predict_rank_change(self, user_stats, training_progress):
        # Predict rank change based on current stats and training
        pass
```

## External API Integrations

### Ballchasing.com API
```python
class BallchasingClient:
    BASE_URL = "https://ballchasing.com/api"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })
    
    def get_replay(self, replay_id):
        """Get replay data by ID"""
        response = self.session.get(f"{self.BASE_URL}/replays/{replay_id}")
        return response.json()
    
    def upload_replay(self, replay_file):
        """Upload replay file for analysis"""
        files = {'file': replay_file}
        response = self.session.post(f"{self.BASE_URL}/v2/upload", files=files)
        return response.json()
```

### Steam API Integration
```python
class SteamClient:
    BASE_URL = "https://api.steampowered.com"
    
    def get_player_stats(self, steam_id):
        """Get Rocket League stats from Steam"""
        # Implementation for Steam Web API
        pass
```

## Performance Requirements

### Response Time Targets
- API endpoints: < 200ms (95th percentile)
- Replay processing: < 30 seconds
- Dashboard loading: < 2 seconds
- 3D replay viewer: < 5 seconds initial load

### Scalability Targets
- Support 10,000 concurrent users
- Process 1,000 replays per hour
- Store 1TB of replay data
- Handle 100,000 API requests per hour

### Caching Strategy
```python
# Redis caching layers
CACHE_KEYS = {
    'user_stats': 'user:{user_id}:stats',  # TTL: 1 hour
    'replay_analysis': 'replay:{replay_id}:analysis',  # TTL: 24 hours
    'training_recommendations': 'user:{user_id}:recommendations',  # TTL: 6 hours
    'leaderboards': 'leaderboard:{category}',  # TTL: 30 minutes
}
```

## Security Considerations

### Authentication & Authorization
- JWT tokens for API authentication
- OAuth integration with Steam/Epic Games
- Role-based access control (user, premium, admin)
- Rate limiting per user/IP

### Data Protection
- Encrypt sensitive user data at rest
- HTTPS for all API communications
- Input validation and sanitization
- SQL injection prevention

### Privacy
- GDPR compliance for EU users
- Data retention policies
- User consent for data processing
- Right to data deletion

## Deployment Architecture

### Development Environment
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/rockettrainer
      - REDIS_URL=redis://redis:6379
  
  db:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_DB=rockettrainer
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:alpine
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

### Production Deployment
- **Backend**: Railway/Heroku with auto-scaling
- **Database**: Managed PostgreSQL + TimescaleDB
- **Frontend**: Vercel with CDN
- **Caching**: Redis Cloud
- **Monitoring**: Sentry + DataDog
- **CI/CD**: GitHub Actions

## Monitoring & Observability

### Key Metrics to Track
- API response times and error rates
- Replay processing success rate
- ML model accuracy metrics
- User engagement metrics
- Database performance metrics

### Alerting Rules
- API error rate > 5%
- Database connection pool exhaustion
- Replay processing queue backup > 100 items
- Memory usage > 80%

---

**Document Version**: 1.0  
**Last Updated**: 2024-09-24  
**Dependencies**: PRD.md
