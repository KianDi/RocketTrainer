"""
Natural language generation service for coaching insights and feedback.
"""
import random
from typing import Dict, List, Optional
import structlog

from app.schemas.coaching import PerformanceArea, AnalysisContext

logger = structlog.get_logger()


class NaturalLanguageService:
    """Service for generating natural language coaching feedback."""
    
    # Coaching feedback templates organized by area and performance level
    COACHING_TEMPLATES = {
        'positioning': {
            'poor': [
                "Your positioning needs significant improvement. You're often caught out of position, which leaves your teammates vulnerable to counterattacks.",
                "Focus on field awareness - you're frequently in awkward positions that limit your defensive options and team support.",
                "Your spatial awareness could use work. Try to maintain better positioning relative to both the ball and your teammates."
            ],
            'average': [
                "Your positioning is decent but has room for improvement. Work on reading the play earlier to get into better positions.",
                "You're generally in okay positions, but could be more proactive about positioning for the next play.",
                "Your positioning shows promise - focus on being more consistent and anticipating play development."
            ],
            'good': [
                "Your positioning is solid! You're consistently in good spots to support your team.",
                "Excellent spatial awareness - you're usually where you need to be when your team needs you.",
                "Your positioning is a real strength, helping your team maintain good field presence."
            ]
        },
        'rotation': {
            'poor': [
                "Your rotation timing needs significant work. You're often disrupting team flow by rotating at the wrong times.",
                "Focus on the 'third man back' principle - ensure someone is always covering the defensive position when you rotate up.",
                "Your rotation decisions are causing gaps in team coverage. Work on reading your teammates' positions better."
            ],
            'average': [
                "Your rotation is improving but could be more consistent. Focus on communication and reading your teammates' positions.",
                "You understand rotation basics but need to work on timing and decision-making.",
                "Your rotation shows good fundamentals - now focus on refining the timing and flow."
            ],
            'good': [
                "Excellent rotation! You're maintaining good team flow and coverage.",
                "Your rotation timing is spot-on, helping your team maintain constant pressure and defense.",
                "Great job with rotation - you're reading the game well and positioning accordingly."
            ]
        },
        'mechanics': {
            'poor': [
                "Your mechanical skills need development. Focus on car control fundamentals and aerial training.",
                "Work on basic mechanics like powershots, aerial control, and ball touches to improve your overall play.",
                "Your mechanical execution is limiting your gameplay potential. Consistent practice will help significantly."
            ],
            'average': [
                "Your mechanics are developing well. Continue practicing advanced techniques to take your game to the next level.",
                "You have solid mechanical fundamentals - now work on consistency and advanced techniques.",
                "Your car control is decent, but refining your mechanics will unlock more gameplay options."
            ],
            'good': [
                "Your mechanical skills are impressive! You're executing advanced techniques consistently.",
                "Excellent car control and mechanical execution - this is clearly a strength in your gameplay.",
                "Your mechanics are solid and reliable, giving you good options in most situations."
            ]
        },
        'game_sense': {
            'poor': [
                "Your decision-making needs improvement. Focus on reading the game state and making smarter choices.",
                "Work on game awareness - understanding when to challenge, when to rotate, and when to be patient.",
                "Your game sense could use development. Try to think one step ahead and anticipate play development."
            ],
            'average': [
                "Your game sense is developing. Continue working on reading the game and making quicker decisions.",
                "You're making generally good decisions but could be more consistent and proactive.",
                "Your game awareness shows promise - focus on reading plays earlier and reacting faster."
            ],
            'good': [
                "Excellent game sense! You're reading plays well and making smart decisions consistently.",
                "Your decision-making is a real asset to your team - you understand the flow of the game well.",
                "Great game awareness - you're anticipating plays and positioning accordingly."
            ]
        },
        'boost_management': {
            'poor': [
                "Your boost management needs significant improvement. You're often caught without boost in crucial moments.",
                "Focus on boost efficiency - collect small pads more often and avoid wasting boost on unnecessary actions.",
                "Work on boost awareness. Plan your boost collection routes and avoid boost-starved situations."
            ],
            'average': [
                "Your boost management is decent but could be more efficient. Focus on small pad collection and conservation.",
                "You understand boost basics but could be more strategic about collection and usage.",
                "Your boost management shows improvement - now focus on efficiency and planning ahead."
            ],
            'good': [
                "Excellent boost management! You're rarely caught without boost when you need it.",
                "Your boost efficiency is impressive - you're making smart collection and usage decisions.",
                "Great boost awareness - you're maintaining good boost levels throughout the match."
            ]
        }
    }
    
    # Specific recommendations for each performance area
    RECOMMENDATIONS = {
        'positioning': [
            "Practice the 'Shadow Defense' training pack to improve defensive positioning",
            "Watch replays from your teammate's perspective to understand positioning impact",
            "Focus on maintaining proper spacing - not too close, not too far from teammates",
            "Work on reading the play 2-3 seconds ahead to position proactively",
            "Practice the 'Defensive Positioning' workshop maps"
        ],
        'rotation': [
            "Use the 'Rotation Trainer' workshop map to practice team rotations",
            "Learn the '3rd man back' rule - always ensure defensive coverage",
            "Practice quick decision-making: when to challenge vs when to rotate back",
            "Watch professional gameplay to see proper rotation patterns",
            "Focus on communication with teammates about rotation intentions"
        ],
        'mechanics': [
            "Practice aerial training packs daily for car control improvement",
            "Work on powershot accuracy and consistency",
            "Use the 'Dribbling Challenge #2' workshop map for ball control",
            "Practice wall-to-air dribbles and aerial car control",
            "Focus on first touch consistency and ball placement"
        ],
        'game_sense': [
            "Analyze your replays to identify decision-making patterns",
            "Practice reading opponent movements and predicting their actions",
            "Work on boost management to enable better decision-making",
            "Study game flow and learn when to be aggressive vs passive",
            "Focus on team play and supporting your teammates' actions"
        ],
        'boost_management': [
            "Practice small boost pad collection routes on each map",
            "Learn to conserve boost by using momentum and positioning",
            "Avoid unnecessary boost usage like holding boost while supersonic",
            "Practice boost-starved scenarios to improve efficiency",
            "Focus on boost awareness - always know where the nearest boost is"
        ]
    }
    
    # Positive feedback templates for strengths
    STRENGTH_TEMPLATES = {
        'positioning': [
            "Your positioning is excellent! You consistently put yourself in advantageous spots.",
            "Great spatial awareness - you're always where your team needs you to be.",
            "Your positioning discipline is paying off with better team coordination."
        ],
        'rotation': [
            "Outstanding rotation! You're maintaining perfect team flow and coverage.",
            "Your rotation timing is spot-on, creating seamless team transitions.",
            "Excellent rotation awareness - you're reading your teammates perfectly."
        ],
        'mechanics': [
            "Your mechanical skills are impressive and consistent!",
            "Excellent car control - your mechanics are clearly well-developed.",
            "Your technical execution is solid and reliable in pressure situations."
        ],
        'game_sense': [
            "Fantastic game sense! Your decision-making is consistently smart.",
            "You're reading the game beautifully and making excellent choices.",
            "Your game awareness is a real asset - you anticipate plays perfectly."
        ],
        'boost_management': [
            "Excellent boost management! You're never caught without boost when needed.",
            "Your boost efficiency is outstanding - very strategic usage.",
            "Great boost awareness - you're maximizing your boost potential."
        ]
    }
    
    # Leverage suggestions for strengths
    LEVERAGE_SUGGESTIONS = {
        'positioning': [
            "Use your positioning advantage to set up more plays for teammates",
            "Your good positioning allows you to be more aggressive in challenges",
            "Leverage your positioning to control the pace of the game"
        ],
        'rotation': [
            "Your rotation skills enable more aggressive team strategies",
            "Use your rotation awareness to help guide less experienced teammates",
            "Your rotation allows your team to maintain constant pressure"
        ],
        'mechanics': [
            "Your mechanical skills open up advanced play options",
            "Use your mechanics to create scoring opportunities in tight situations",
            "Your technical ability allows for more creative and unpredictable plays"
        ],
        'game_sense': [
            "Your game sense allows you to be a playmaker for your team",
            "Use your awareness to call plays and direct team strategy",
            "Your decision-making can help your team capitalize on opponent mistakes"
        ],
        'boost_management': [
            "Your boost efficiency allows for more aggressive positioning",
            "Use your boost advantage to maintain pressure on opponents",
            "Your boost management enables consistent high-level play"
        ]
    }
    
    def __init__(self):
        """Initialize the natural language service."""
        self.logger = logger.bind(service="natural_language")
    
    def generate_coaching_feedback(self, area: PerformanceArea, context: AnalysisContext) -> str:
        """Generate natural language coaching feedback for a performance area."""
        try:
            # Determine performance level
            if area.score >= 0.7:
                level = 'good'
            elif area.score >= 0.4:
                level = 'average'
            else:
                level = 'poor'
            
            # Get base template
            templates = self.COACHING_TEMPLATES.get(area.name, {}).get(level, [])
            if not templates:
                return f"Your {area.name} performance shows room for improvement."
            
            base_feedback = random.choice(templates)
            
            # Add context-specific details
            contextual_feedback = self._add_contextual_details(base_feedback, area, context)
            
            return contextual_feedback
            
        except Exception as e:
            self.logger.error("Failed to generate coaching feedback", area=area.name, error=str(e))
            return f"Your {area.name} performance has room for improvement."
    
    def generate_positive_feedback(self, area: PerformanceArea) -> str:
        """Generate positive feedback for a strength area."""
        templates = self.STRENGTH_TEMPLATES.get(area.name, [])
        if not templates:
            return f"Your {area.name} is performing well!"
        
        return random.choice(templates)
    
    def get_recommendations(self, area_name: str) -> List[str]:
        """Get specific recommendations for improving a performance area."""
        recommendations = self.RECOMMENDATIONS.get(area_name, [])
        # Return 3-4 most relevant recommendations
        return recommendations[:4] if len(recommendations) > 4 else recommendations
    
    def get_leverage_suggestions(self, area_name: str) -> List[str]:
        """Get suggestions for leveraging a strength area."""
        suggestions = self.LEVERAGE_SUGGESTIONS.get(area_name, [])
        return suggestions[:3] if len(suggestions) > 3 else suggestions
    
    def generate_key_takeaway(
        self, 
        primary_weakness: Optional[str], 
        primary_strength: Optional[str], 
        context: AnalysisContext
    ) -> str:
        """Generate a key takeaway message for the overall analysis."""
        if primary_weakness and primary_strength:
            return f"Focus on improving your {primary_weakness} while leveraging your strong {primary_strength} to elevate your overall game."
        elif primary_weakness:
            return f"Your primary focus should be improving {primary_weakness} - this will have the biggest impact on your performance."
        elif primary_strength:
            return f"Your {primary_strength} is excellent! Continue building on this strength while developing other areas."
        else:
            return "Your performance is well-balanced. Focus on consistent improvement across all areas."
    
    def _add_contextual_details(
        self, 
        base_feedback: str, 
        area: PerformanceArea, 
        context: AnalysisContext
    ) -> str:
        """Add context-specific details to base feedback."""
        # Add score-specific details
        score_percentage = int(area.score * 100)
        
        if area.score < 0.3:
            intensity = "significantly"
        elif area.score < 0.5:
            intensity = "noticeably"
        else:
            intensity = "somewhat"
        
        # Add match context
        if context.result == 'loss' and area.score < 0.5:
            context_note = f" This {intensity} impacted your team's performance in this loss."
        elif context.result == 'win' and area.score > 0.7:
            context_note = f" This strength contributed to your team's victory."
        else:
            context_note = ""
        
        return f"{base_feedback}{context_note}"
