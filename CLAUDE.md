# RocketTrainer - Claude Code Assistant Guide

## Project Overview

**RocketTrainer** is an AI-powered Rocket League coaching platform that analyzes gameplay replays, identifies player weaknesses using machine learning, and generates personalized training recommendations with progress tracking.

### Core Mission
Democratize professional-level Rocket League coaching through intelligent gameplay analysis and data-driven training recommendations.

## Tech Stack & Architecture

### Backend
- **FastAPI** - Main API framework
- **PostgreSQL** - Core data storage
- **TimescaleDB** - Time series data for player statistics
- **Redis** - Caching and session management
- **Celery** - Background task processing
- **Scikit-learn** - Machine learning models (TensorFlow planned for Phase 2)
- **Docker** - Containerization

### Frontend
- **React 18** with **TypeScript**
- **Tailwind CSS** - Styling framework
- **Three.js** - 3D replay visualization (advanced feature)
- **D3.js** - Analytics charts and data visualization
- **Axios** - API communication

### External Integrations
- **Ballchasing.com API** - Primary replay data source
- **Steam Web API** - User authentication and stats
- **Epic Games API** - Alternative authentication (future)

## Project Structure

```
RocketTrainer/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database connection
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes (auth, users, replays, training)
│   │   ├── services/          # Business logic services
│   │   ├── ml/                # Machine learning models (planned)
│   │   └── utils/             # Utility functions
│   ├── sql/                   # Database initialization scripts
│   │   ├── 01_init_extensions.sql    # TimescaleDB extensions
│   │   └── 02_create_hypertables.sql # Time-series table setup
│   ├── alembic/               # Database migrations
│   ├── scripts/               # Utility scripts
│   ├── tests/                 # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # React context providers
│   │   ├── services/         # API service functions
│   │   └── types/            # TypeScript type definitions
│   ├── package.json
│   └── Dockerfile
├── ml/                       # ML training scripts and notebooks (planned)
├── docs/                     # Project documentation
├── .github/                  # GitHub workflows
└── docker-compose.yml       # Development environment setup
```

## Core Features & Functionality

### MVP Features (Phase 1-2)
1. **Replay Analysis Engine** - Upload and process .replay files, extract 50+ gameplay metrics
2. **Weakness Detection System** - ML models identify top 3 weaknesses with 80% accuracy
3. **Training Recommendation Engine** - Personalized training pack recommendations
4. **Progress Tracking Dashboard** - Visualize improvement over time with interactive charts

### Advanced Features (Post-MVP)
1. **3D Replay Viewer** - Three.js-based replay visualization
2. **Training Partner Matching** - Algorithm-based player matching
3. **Discord Bot Integration** - Community features and reminders

## Key Development Standards

### Code Organization
- **Keep functions small and focused** - Split into functions if comments needed
- **Prefer explicit over implicit** - Clear function names, obvious data flow
- **Delete old code completely** - No versioned functions or deprecation
- **Follow existing patterns** - Check neighboring files for conventions

### API Design
- RESTful endpoints with proper HTTP status codes
- Comprehensive input validation using Pydantic schemas
- JWT token-based authentication
- Rate limiting and proper error handling

### Database Schema (Core Tables)
- **users** - User profiles and authentication data
- **matches** - Replay data and match results
- **player_stats** - Time-series performance metrics (TimescaleDB)
- **training_packs** - Available training content
- **training_sessions** - User training progress

### ML Pipeline (Phase 2)
- **Feature extraction** from replay data (positioning, mechanical skills, game sense)
- **Weakness detection models** using Random Forest/Gradient Boosting (scikit-learn)
- **Rank prediction models** using XGBoost (planned)
- **Confidence scoring** and improvement potential calculation
- **TensorFlow integration** for advanced deep learning models (future)

## Development Workflow

### Environment Setup
```bash
# Start development environment
docker-compose up -d

# Initialize database
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed_data.py

# Run tests
docker-compose exec api pytest
docker-compose exec frontend npm test
```

### Required API Keys
1. **Ballchasing.com API Key** - Apply early (1-2 week wait time)
2. **Steam Web API Key** - For user authentication
3. **Epic Games API** (optional for MVP)

## Performance & Scalability Requirements

### Response Time Targets
- API endpoints: < 200ms (95th percentile)
- Replay processing: < 30 seconds
- Dashboard loading: < 2 seconds

### Scalability Targets
- Support 10,000 concurrent users
- Process 1,000 replays per hour
- Handle 100,000 API requests per hour

### Caching Strategy
- User stats: 1 hour TTL
- Replay analysis: 24 hours TTL
- Training recommendations: 6 hours TTL

## Security & Privacy

### Authentication
- JWT tokens for API access
- OAuth integration with Steam/Epic Games
- Role-based access control

### Data Protection
- Encrypt sensitive data at rest
- HTTPS for all communications
- Input validation and SQL injection prevention
- GDPR compliance for EU users

## Target Users & Market

### Primary Target
- Competitive Rocket League players (Diamond-Grand Champion ranks)
- Age 16-28, willing to invest in improvement
- Active in community forums and Discord

### Market Context
- 50M+ registered Rocket League players
- ~5M active competitive players
- First-mover advantage in AI-powered RL coaching
- TAM: $25M annually

## Development Phases

### Phase 1: Foundation (Weeks 1-4) ✅ COMPLETED
- Project setup and infrastructure ✅
- Database schema and user authentication ✅
- TimescaleDB hypertables for time-series data ✅
- Docker containerization and development environment ✅
- FastAPI application structure with modular routing ✅

### Phase 2: Core Analysis (Weeks 5-8) 🚧 IN PROGRESS
- Ballchasing.com API integration
- Basic replay parsing and analysis
- ML model development for weakness detection (scikit-learn)
- Training pack database and recommendation algorithm
- Advanced dashboard features and progress tracking

### Phase 3: Advanced ML & Features (Weeks 9-12)
- TensorFlow integration for deep learning models
- 3D replay viewer with Three.js
- Advanced analytics and performance optimization

### Phase 4: Community Features (Weeks 13-16)
- Player matching and Discord bot integration
- Mobile responsiveness and user onboarding
- Community features and social aspects

## Key Success Metrics
- **User Acquisition**: 1,000 registered users in first 3 months
- **Engagement**: 60% weekly active users
- **Retention**: 40% monthly retention rate
- **Effectiveness**: 25% of users show rank improvement within 30 days

## Risk Mitigation
- **Data Dependency**: Develop fallback data sources for Ballchasing API
- **ML Accuracy**: Start with simpler models and iterate
- **Scalability**: Implement caching and optimization early

## Important Notes for Development

### Critical Dependencies
- Ballchasing.com API access is essential - apply early
- Need 1000+ replays for ML training data
- Steam/Epic OAuth registration required

### Development Priorities
1. Complete Ballchasing.com API integration (Phase 2 focus)
2. Implement basic replay parsing and data extraction
3. Start with simple heuristic-based analysis before ML models
4. Focus on core user flow: upload → analysis → recommendations
5. Add scikit-learn models for weakness detection
6. Plan TensorFlow integration for Phase 3

### Anti-patterns to Avoid
- Don't over-engineer early - start simple
- Avoid premature optimization
- Don't build features without user validation
- No version-suffixed functions (processV2, etc.)

---

**Document Version**: 1.0
**Last Updated**: 2024-09-23
**Primary Focus**: AI-powered Rocket League coaching through replay analysis and personalized training recommendations