# RocketTrainer 🚀

An AI-powered Rocket League coaching platform that analyzes your gameplay, identifies weaknesses, and creates personalized training routines to help you rank up faster.

## 🎯 What It Does

RocketTrainer uses machine learning to analyze your Rocket League replays and provides:

- **Smart Weakness Detection**: AI identifies your specific skill gaps
- **Personalized Training**: Custom training pack recommendations
- **Progress Tracking**: Detailed analytics and improvement metrics
- **Rank Prediction**: Forecasts your rank progression based on improvement

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd RocketTrainer
make setup
```

### 2. Start Development Environment
```bash
make start
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI**: Modern Python web framework
- **PostgreSQL + TimescaleDB**: Time-series data storage
- **Redis**: Caching and session management
- **Celery**: Background task processing
- **ML Models**: TensorFlow/Scikit-learn for analysis

### Frontend (React)
- **React 18 + TypeScript**: Modern UI framework
- **Tailwind CSS**: Utility-first styling
- **D3.js**: Data visualization
- **Three.js**: 3D replay viewer (planned)

## 📊 Features

### Phase 1: Foundation ✅
- [x] Project setup and infrastructure
- [x] User authentication (Steam OAuth)
- [x] Database schema and models
- [x] Basic API endpoints
- [x] React dashboard with mock data

### Phase 2: Core Analysis (In Progress)
- [ ] Ballchasing.com API integration
- [ ] Replay parsing and analysis
- [ ] ML models for weakness detection
- [ ] Training pack recommendations

### Phase 3: User Experience
- [ ] Advanced dashboard features
- [ ] Progress tracking system
- [ ] Mobile responsiveness
- [ ] User onboarding flow

### Phase 4: Advanced Features
- [ ] 3D replay viewer
- [ ] Player matching system
- [ ] Discord bot integration
- [ ] Performance optimization

## 🛠️ Development

### Available Commands
```bash
make help          # Show all available commands
make setup         # Initial project setup
make start         # Start development environment
make stop          # Stop all services
make test          # Run all tests
make logs          # Show service logs
make shell         # Open shell in API container
make migrate       # Run database migrations
make seed          # Seed database with training packs
```

### Project Structure
```
RocketTrainer/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── tests/        # Backend tests
│   └── scripts/      # Utility scripts
├── frontend/         # React frontend
│   ├── src/          # Source code
│   └── public/       # Static assets
├── docs/            # Documentation
└── ml/              # ML models and training
```

## 🧪 Testing

```bash
# Run all tests
make test

# Backend tests only
docker-compose run --rm api pytest

# Frontend tests only
docker-compose run --rm frontend npm test
```

## 📈 API Documentation

Once the development server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required for full functionality
BALLCHASING_API_KEY=your-ballchasing-api-key
STEAM_API_KEY=your-steam-api-key

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/rockettrainer

# Security
SECRET_KEY=your-secret-key-here
```

## 🚀 Deployment

### Production Build
```bash
make prod-build
```

### Recommended Platforms
- **Backend**: Railway, Heroku, or DigitalOcean
- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **Database**: Managed PostgreSQL (AWS RDS, DigitalOcean)
- **Cache**: Redis Cloud

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Ballchasing.com for replay data API
- Rocket League community for training pack creation
- Psyonix for creating an amazing game

## 📞 Support

- Create an issue for bug reports
- Join our Discord for community support
- Check the documentation in `/docs`

---

**Status**: Phase 1 Complete ✅ | Phase 2 In Progress 🚧

Built with ❤️ for the Rocket League community
