#!/usr/bin/env python3
"""
Seed script to populate the database with initial training packs and sample data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, TrainingPack
import structlog

logger = structlog.get_logger()

def create_training_packs(db: Session):
    """Create initial training packs."""
    training_packs = [
        # Aerial Training Packs
        {
            "name": "Aerial Shots - Beginner",
            "code": "8D93-C997-0C72-B2AB",
            "description": "Basic aerial shots to get you started with aerial mechanics",
            "creator": "Poquito",
            "category": "aerials",
            "subcategory": "basic_aerials",
            "difficulty": 3,
            "skill_level": "gold",
            "tags": ["aerials", "beginner", "shots"],
            "shots_count": 50,
            "estimated_duration": 20,
            "rating": 4.5,
            "rating_count": 1250,
            "is_official": True,
            "is_featured": True
        },
        {
            "name": "Advanced Aerial Training",
            "code": "C7E0-9E0B-B739-A899",
            "description": "Challenging aerial shots for advanced players",
            "creator": "Wayprotein",
            "category": "aerials",
            "subcategory": "advanced_aerials",
            "difficulty": 8,
            "skill_level": "champion",
            "tags": ["aerials", "advanced", "challenging"],
            "shots_count": 40,
            "estimated_duration": 30,
            "rating": 4.7,
            "rating_count": 890,
            "is_official": True
        },
        
        # Saves Training Packs
        {
            "name": "Saves - Consistency",
            "code": "2E23-ABD2-0B87-4D8D",
            "description": "Improve your save consistency with these essential saves",
            "creator": "VirgeRL",
            "category": "saves",
            "subcategory": "basic_saves",
            "difficulty": 4,
            "skill_level": "platinum",
            "tags": ["saves", "consistency", "defense"],
            "shots_count": 60,
            "estimated_duration": 25,
            "rating": 4.3,
            "rating_count": 2100,
            "is_official": True,
            "is_featured": True
        },
        {
            "name": "Awkward Saves",
            "code": "5A65-4073-F310-5495",
            "description": "Practice difficult and awkward save situations",
            "creator": "Uncomfortable",
            "category": "saves",
            "subcategory": "awkward_saves",
            "difficulty": 7,
            "skill_level": "diamond",
            "tags": ["saves", "awkward", "difficult"],
            "shots_count": 35,
            "estimated_duration": 20,
            "rating": 4.1,
            "rating_count": 750
        },
        
        # Shooting Training Packs
        {
            "name": "Shooting Consistency",
            "code": "A503-264C-A7EB-D282",
            "description": "Master basic shooting mechanics and accuracy",
            "creator": "Biddles",
            "category": "shooting",
            "subcategory": "basic_shots",
            "difficulty": 3,
            "skill_level": "gold",
            "tags": ["shooting", "accuracy", "consistency"],
            "shots_count": 45,
            "estimated_duration": 18,
            "rating": 4.4,
            "rating_count": 1800,
            "is_official": True
        },
        {
            "name": "Redirect Training",
            "code": "8F6B-4C0D-925C-B1F3",
            "description": "Learn to redirect the ball with power and precision",
            "creator": "Musty",
            "category": "shooting",
            "subcategory": "redirects",
            "difficulty": 6,
            "skill_level": "diamond",
            "tags": ["shooting", "redirects", "power"],
            "shots_count": 30,
            "estimated_duration": 25,
            "rating": 4.6,
            "rating_count": 950
        },
        
        # Dribbling Training Packs
        {
            "name": "Ground Dribbling",
            "code": "BC4B-0F9C-A25D-8E7F",
            "description": "Improve your ground dribbling and ball control",
            "creator": "French Fries",
            "category": "dribbling",
            "subcategory": "ground_dribbling",
            "difficulty": 5,
            "skill_level": "platinum",
            "tags": ["dribbling", "ball_control", "ground"],
            "shots_count": 25,
            "estimated_duration": 30,
            "rating": 4.2,
            "rating_count": 1100
        },
        {
            "name": "Air Dribble Setup",
            "code": "9F2D-4387-B1C5-E890",
            "description": "Learn to set up and execute air dribbles",
            "creator": "Fluump",
            "category": "dribbling",
            "subcategory": "air_dribbling",
            "difficulty": 7,
            "skill_level": "champion",
            "tags": ["dribbling", "air_dribble", "advanced"],
            "shots_count": 20,
            "estimated_duration": 35,
            "rating": 4.5,
            "rating_count": 680
        },
        
        # Wall Play Training Packs
        {
            "name": "Wall Shots",
            "code": "9C54-6D8A-B2F1-E037",
            "description": "Master shots coming off the wall",
            "creator": "Mason",
            "category": "wall_play",
            "subcategory": "wall_shots",
            "difficulty": 6,
            "skill_level": "diamond",
            "tags": ["wall", "shots", "mechanics"],
            "shots_count": 40,
            "estimated_duration": 22,
            "rating": 4.0,
            "rating_count": 820
        },
        
        # Positioning Training Packs
        {
            "name": "Shadow Defense",
            "code": "5CCE-FB29-7B05-A0B1",
            "description": "Learn proper shadow defense positioning",
            "creator": "Gregan",
            "category": "positioning",
            "subcategory": "defense",
            "difficulty": 5,
            "skill_level": "diamond",
            "tags": ["positioning", "defense", "shadow"],
            "shots_count": 15,
            "estimated_duration": 15,
            "rating": 4.3,
            "rating_count": 1400,
            "is_featured": True
        }
    ]
    
    for pack_data in training_packs:
        # Check if pack already exists
        existing_pack = db.query(TrainingPack).filter(TrainingPack.code == pack_data["code"]).first()
        if existing_pack:
            logger.info("Training pack already exists", code=pack_data["code"])
            continue
        
        pack = TrainingPack(**pack_data)
        db.add(pack)
        logger.info("Created training pack", name=pack_data["name"], code=pack_data["code"])
    
    db.commit()
    logger.info("Training packs seeded successfully")

def main():
    """Main seeding function."""
    logger.info("Starting database seeding")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        create_training_packs(db)
        logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error("Database seeding failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
