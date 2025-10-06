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


### AI Analysis Dashboard
- **Weakness Detection**: Upload replays and get AI-powered analysis of your gameplay weaknesses
- **Skill Breakdown**: Detailed scoring across 8 skill categories (mechanical, positioning, game sense, etc.)
- **Training Recommendations**: Personalized training pack suggestions based on your weaknesses
- **Progress Tracking**: Monitor improvement over time with confidence scoring


### Development Features
- Environment-aware configuration (lower requirements for testing)
- Comprehensive error handling with user-friendly messages
- Redis caching for improved performance
- Rate limiting for API protection

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
- Check the documentation in `/docs`

---

Built with ❤️ for the Rocket League community
