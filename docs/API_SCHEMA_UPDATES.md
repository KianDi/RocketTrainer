# API Schema Updates - September 2025

## Overview
This document tracks recent schema changes and fixes to ensure frontend/backend compatibility.

## Training Recommendations API

### Endpoint: `POST /api/ml/recommend-training`

#### Schema Changes (Fixed 2025-09-27)
**Issue**: Frontend TypeScript interfaces didn't match actual backend response schema.

**Backend Response Schema (Actual)**:
```json
{
  "user_id": "uuid",
  "recommendations": [
    {
      "training_pack": {
        "id": "uuid",
        "name": "string",
        "code": "string",
        "category": "string",
        "difficulty": 3,  // number (1-5 scale)
        "description": "string",
        "creator": "string"
      },
      "relevance_score": 0.85,
      "difficulty_match": 0.92,
      "quality_score": 0.83,
      "overall_score": 0.641
    }
  ],
  "skill_level_detected": "silver",  // NOT "skill_level"
  "total_packs_evaluated": 2,        // NOT "total_recommendations"
  "generation_time": "2025-09-27T...", // NOT "generated_at"
  "cache_hit": false
}
```

**Frontend Interface (Updated)**:
```typescript
interface TrainingRecommendationResponse {
  user_id: string;
  recommendations: TrainingRecommendation[];
  skill_level_detected: string;  // Fixed: was "skill_level"
  total_packs_evaluated: number; // Fixed: was "total_recommendations"
  generation_time: string;       // Fixed: was "generated_at"
  cache_hit: boolean;
}

interface TrainingRecommendation {
  training_pack: TrainingPack;
  relevance_score: number;
  difficulty_match: number;
  quality_score: number;
  overall_score: number;
}
```

## Weakness Analysis API

### Endpoint: `POST /api/ml/analyze-weaknesses`

#### Environment-Aware Requirements (Added 2025-09-27)
**Feature**: Minimum match requirements now depend on environment.

**Configuration**:
- **Development**: 1 processed match minimum
- **Production**: 3 processed matches minimum

**Error Handling**:
```json
// Insufficient data error response
{
  "detail": "Need at least 1 processed matches for analysis. Upload more replays to get started!",
  "required_matches": 1,
  "available_matches": 0
}
```

**Frontend Error Detection**:
```typescript
// Added to mlService.ts
isInsufficientDataError(error: any): boolean {
  return error && (
    error.message?.includes('Insufficient match data') ||
    error.message?.includes('Need at least') ||
    (error.details && error.details.required_matches && error.details.available_matches)
  );
}

getErrorMessage(error: any): string {
  if (this.isInsufficientDataError(error)) {
    const details = error.details || {};
    const required = details.required_matches || 3;
    const available = details.available_matches || 0;
    
    return `Need at least ${required} processed replays for AI analysis. You currently have ${available}. Upload more replays in the Replays tab to get started!`;
  }
  // ... other error types
}
```

## Breaking Changes Summary

### Fixed Schema Mismatches
1. **Training Recommendations**:
   - `skill_level` → `skill_level_detected`
   - `total_recommendations` → `total_packs_evaluated`
   - `generated_at` → `generation_time`

2. **Error Handling**:
   - Added user-friendly error messages
   - Environment-aware minimum requirements
   - Better guidance for insufficient data scenarios

### Backward Compatibility
- All changes are backward compatible
- Frontend gracefully handles missing fields with null checks
- Error messages provide clear user guidance

## Testing
All schema changes have been tested with:
- Direct API calls via curl
- Frontend React components
- Error scenarios and edge cases
- Development and production configurations

## Next Steps
- Monitor for any additional schema mismatches
- Consider API versioning for future breaking changes
- Document any new endpoints or schema changes here
