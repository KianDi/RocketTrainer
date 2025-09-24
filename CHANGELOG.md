# Changelog

All notable changes to RocketTrainer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Frontend compilation errors due to missing `@tailwindcss/forms` dependency
- Missing TypeScript type definitions in `frontend/src/types/index.ts`
- Database seeding import errors with missing `Base` import
- Docker build context optimization with proper `.dockerignore` files

### Planned
- Ballchasing.com API integration
- Real replay parsing and analysis
- ML models for weakness detection
- Enhanced training recommendations

## [0.1.0] - 2024-09-24

### Added - Phase 1: Foundation & Infrastructure

#### Project Setup
- Docker-based development environment with 4 services
- Comprehensive Makefile with 12 development commands
- Automated setup script (`setup.sh`) for easy onboarding
- GitHub Actions CI/CD pipeline with 5 jobs
- Environment configuration with `.env.example`
- Professional README with setup instructions

#### Backend (FastAPI)
- FastAPI application with modular structure
- PostgreSQL + TimescaleDB database integration
- Redis caching and session management
- SQLAlchemy ORM with 5 core models:
  - `User`: Steam/Epic OAuth, profile management
  - `Match`: Replay data and match results
  - `PlayerStats`: Time-series performance data
  - `TrainingPack`: Curated training content
  - `TrainingSession`: Progress tracking
- Alembic database migrations
- JWT-based authentication system
- Steam OAuth integration (simplified)
- Comprehensive API endpoints:
  - Health checks (basic + detailed)
  - User management (profile, stats, deletion)
  - Replay upload/analysis (mock processing)
  - Training pack management
  - Training session tracking
- Pydantic schemas for request/response validation
- Structured logging with contextual information
- Background task processing setup (Celery)
- Service layer architecture:
  - `AuthService`: Token management
  - `ReplayService`: Mock replay processing
  - `TrainingService`: Recommendation foundation

#### Frontend (React + TypeScript)
- React 18 with TypeScript setup
- React Router for navigation
- Authentication context and protected routes
- Tailwind CSS with custom gaming theme
- Responsive design for mobile/desktop
- Core pages:
  - Landing page with feature showcase
  - User dashboard with analytics
  - Login page with Steam integration
  - Profile management
  - Placeholder pages for replays/training
- Professional UI components:
  - Navigation bar with user menu
  - Protected route wrapper
  - Loading states and error handling
- Custom styling with gaming aesthetics

#### Database & Data
- Database seeding script with 10+ real training packs
- Training packs from popular creators (Poquito, Wayprotein, etc.)
- Categorized by skill level and difficulty
- Proper metadata and community ratings
- Time-series data structure for analytics

#### Testing & Quality
- Pytest test suite for backend
- React Testing Library for frontend
- GitHub Actions automated testing
- Code formatting and linting (Black, ESLint)
- Security scanning with Trivy
- Test coverage reporting
- Docker image building and caching

#### Documentation
- Comprehensive project documentation
- API documentation with Swagger/ReDoc
- Development setup instructions
- Architecture diagrams and explanations
- Progression tracking documentation

### Technical Specifications
- **Backend**: Python 3.9, FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Frontend**: React 18, TypeScript, Tailwind CSS, Axios
- **Infrastructure**: Docker, Docker Compose, GitHub Actions
- **Database**: PostgreSQL 14 with TimescaleDB extension
- **Authentication**: JWT tokens with Steam OAuth
- **Testing**: Pytest, React Testing Library, Coverage reporting

### Development Environment
- One-command setup with `make setup`
- Hot reload for both backend and frontend
- Database migrations and seeding
- Comprehensive logging and debugging
- Health checks for all services

### Security
- JWT token-based authentication
- CORS configuration
- Input validation and sanitization
- SQL injection prevention
- Security headers and middleware
- Vulnerability scanning in CI/CD

## [0.0.0] - 2024-09-24

### Added
- Initial project conception and planning
- Product Requirements Document (PRD)
- Technical specification document
- Implementation roadmap
- Project structure definition
