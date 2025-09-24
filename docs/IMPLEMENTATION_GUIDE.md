# RocketTrainer - Implementation Guide

## Project Structure

```
RocketTrainer/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database connection
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── replays.py
│   │   │   └── training.py
│   │   ├── services/          # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── replay_service.py
│   │   │   ├── ml_service.py
│   │   │   └── training_service.py
│   │   ├── ml/                # Machine learning models
│   │   │   ├── models/
│   │   │   ├── preprocessing/
│   │   │   └── training/
│   │   └── utils/             # Utility functions
│   ├── tests/                 # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API services
│   │   ├── utils/            # Utility functions
│   │   ├── types/            # TypeScript types
│   │   └── styles/           # CSS/styling
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── ml/                       # ML training scripts
│   ├── data/                 # Training data
│   ├── notebooks/            # Jupyter notebooks
│   ├── scripts/              # Training scripts
│   └── models/               # Trained models
├── docs/                     # Documentation
├── docker-compose.yml        # Development environment
├── .github/                  # GitHub Actions
└── README.md
```

## Phase 1: Foundation & Infrastructure (Weeks 1-4)

### Week 1: Project Setup

#### Day 1-2: Environment Setup
```bash
# Initialize project structure
mkdir -p backend/app/{models,schemas,api,services,ml,utils}
mkdir -p frontend/src/{components,pages,hooks,services,utils,types,styles}
mkdir -p ml/{data,notebooks,scripts,models}
mkdir -p docs tests

# Set up version control
git init
git remote add origin <repository-url>

# Create development environment
docker-compose up -d
```

#### Day 3-5: Backend Foundation
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, replays, training
from app.database import engine
from app.models import Base

app = FastAPI(title="RocketTrainer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(replays.router, prefix="/replays", tags=["replays"])
app.include_router(training.router, prefix="/training", tags=["training"])

@app.on_event("startup")
async def startup():
    # Create database tables
    Base.metadata.create_all(bind=engine)
```

#### Day 6-7: Frontend Foundation
```bash
# Initialize React app
cd frontend
npx create-react-app . --template typescript
npm install @tailwindcss/forms @headlessui/react
npm install axios react-router-dom @types/react-router-dom
npm install d3 @types/d3 three @types/three
```

### Week 2: Database & Authentication

#### Database Models
```python
# backend/app/models/user.py
from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    steam_id = Column(String(20), unique=True, nullable=False)
    epic_id = Column(String(50), nullable=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    current_rank = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### Authentication Service
```python
# backend/app/services/auth_service.py
import jwt
from datetime import datetime, timedelta
from app.config import settings

class AuthService:
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def verify_steam_token(steam_token: str):
        # Implement Steam OpenID verification
        pass
```

### Week 3: API Development

#### Core API Endpoints
```python
# backend/app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update user profile logic
    pass
```

### Week 4: Basic Frontend

#### React Components
```tsx
// frontend/src/components/Dashboard.tsx
import React from 'react';
import { useAuth } from '../hooks/useAuth';
import StatsOverview from './StatsOverview';
import RecentMatches from './RecentMatches';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.username}
          </h1>
          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <StatsOverview />
            <RecentMatches />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
```

## Phase 2: Data Pipeline & ML Core (Weeks 5-8)

### Week 5: Ballchasing API Integration

```python
# backend/app/services/ballchasing_service.py
import requests
from typing import Optional, Dict, Any
from app.config import settings

class BallchasingService:
    BASE_URL = "https://ballchasing.com/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {settings.BALLCHASING_API_KEY}'
        })
    
    async def upload_replay(self, replay_file: bytes) -> Dict[str, Any]:
        """Upload replay file to Ballchasing.com"""
        files = {'file': ('replay.replay', replay_file, 'application/octet-stream')}
        response = self.session.post(f"{self.BASE_URL}/v2/upload", files=files)
        response.raise_for_status()
        return response.json()
    
    async def get_replay_data(self, replay_id: str) -> Dict[str, Any]:
        """Get detailed replay data"""
        response = self.session.get(f"{self.BASE_URL}/replays/{replay_id}")
        response.raise_for_status()
        return response.json()
```

### Week 6: Replay Parser

```python
# backend/app/services/replay_service.py
from typing import Dict, List, Any
import numpy as np

class ReplayAnalyzer:
    def __init__(self, replay_data: Dict[str, Any]):
        self.replay_data = replay_data
        self.players = replay_data.get('players', [])
    
    def extract_features(self, player_id: str) -> Dict[str, float]:
        """Extract ML features from replay data"""
        player_data = self._get_player_data(player_id)
        
        features = {
            'aerial_accuracy': self._calculate_aerial_accuracy(player_data),
            'save_percentage': self._calculate_save_percentage(player_data),
            'shot_accuracy': self._calculate_shot_accuracy(player_data),
            'positioning_score': self._calculate_positioning_score(player_data),
            'rotation_efficiency': self._calculate_rotation_efficiency(player_data),
            'boost_efficiency': self._calculate_boost_efficiency(player_data)
        }
        
        return features
    
    def _calculate_aerial_accuracy(self, player_data: Dict) -> float:
        """Calculate aerial hit accuracy"""
        # Implementation for aerial analysis
        pass
```

### Week 7-8: ML Model Development

```python
# backend/app/ml/models/weakness_detector.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import numpy as np

class WeaknessDetector:
    def __init__(self):
        self.models = {}
        self.feature_names = [
            'aerial_accuracy', 'save_percentage', 'shot_accuracy',
            'positioning_score', 'rotation_efficiency', 'boost_efficiency'
        ]
    
    def train(self, training_data: np.ndarray, labels: Dict[str, np.ndarray]):
        """Train weakness detection models"""
        for weakness_type, y in labels.items():
            X_train, X_test, y_train, y_test = train_test_split(
                training_data, y, test_size=0.2, random_state=42
            )
            
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate model
            accuracy = model.score(X_test, y_test)
            print(f"{weakness_type} model accuracy: {accuracy:.3f}")
            
            self.models[weakness_type] = model
    
    def predict_weaknesses(self, features: np.ndarray) -> Dict[str, float]:
        """Predict weakness scores for a player"""
        weaknesses = {}
        for weakness_type, model in self.models.items():
            score = model.predict_proba(features.reshape(1, -1))[0][1]
            weaknesses[weakness_type] = score
        return weaknesses
    
    def save_models(self, path: str):
        """Save trained models to disk"""
        joblib.dump(self.models, f"{path}/weakness_models.pkl")
```

## Implementation Priority & Next Steps

### Immediate Actions (Week 1)
1. **Set up development environment** with Docker
2. **Initialize project structure** as outlined above
3. **Configure CI/CD pipeline** with GitHub Actions
4. **Set up basic FastAPI application** with health check endpoint

### Critical Path Dependencies
1. **Ballchasing.com API access** - Apply for API key early
2. **Training data collection** - Need 1000+ replays for ML training
3. **Steam/Epic OAuth setup** - Register applications for authentication

### Risk Mitigation
1. **Start with mock data** if API access is delayed
2. **Implement file upload** as backup to API integration
3. **Use simple heuristics** before ML models are ready

### Success Metrics for Phase 1
- [ ] Docker environment running successfully
- [ ] Basic API endpoints responding
- [ ] User authentication working
- [ ] Database schema implemented
- [ ] Frontend displaying mock data

---

**Next Document**: DEVELOPMENT_SETUP.md (detailed setup instructions)  
**Dependencies**: PRD.md, TECHNICAL_SPEC.md
