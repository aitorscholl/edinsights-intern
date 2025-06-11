# NCAA Soccer Data API Design Document and Flask Implementation

---

## 1. API Overview

The NCAA Soccer Data API provides a comprehensive interface for accessing college soccer statistics, team information, player data, match results, and historical trends.  
Built as a RESTful API with JSON responses, it follows modern API design principles while accommodating the unique requirements of NCAA sports data.

**Base URL:**  
`https://api.ncaasoccer.com/api/v1`

### Key Features

- RESTful architecture with intuitive endpoint structure
- JSON response format with consistent schemas
- Rate limiting: 5 requests per second
- No authentication required for public endpoints
- Comprehensive error handling with meaningful error codes
- Response caching for optimal performance

---

## 2. API Endpoints

### Teams Endpoints

- **GET `/api/v1/teams`**  
  Retrieve all teams with optional filtering  
  **Query Parameters:**  
  - `division` (string): Filter by division (d1, d2, d3)
  - `conference` (string): Filter by conference name
  - `state` (string): Filter by state
  - `page` (integer): Page number (default: 1)
  - `per_page` (integer): Items per page (default: 20, max: 100)  
  **Example:** `/api/v1/teams?division=d1&conference=acc&page=1`

- **GET `/api/v1/teams/{team_id}`**  
  Get detailed information for a specific team  
  **Path Parameters:**  
  - `team_id` (integer): Unique team identifier  
  **Example:** `/api/v1/teams/123`

- **GET `/api/v1/teams/{team_id}/roster`**  
  Get current roster for a team  
  **Query Parameters:**  
  - `position` (string): Filter by position
  - `class` (string): Filter by academic class  
  **Example:** `/api/v1/teams/123/roster?position=forward`

- **GET `/api/v1/teams/{team_id}/schedule`**  
  Get team's game schedule  
  **Query Parameters:**  
  - `season` (integer): Season year (default: current)
  - `status` (string): Filter by game status  
  **Example:** `/api/v1/teams/123/schedule?season=2024`

---

### Players Endpoints

- **GET `/api/v1/players`**  
  Search and filter players across all teams  
  **Query Parameters:**  
  - `name` (string): Search by player name
  - `team_id` (integer): Filter by team
  - `position` (string): Filter by position
  - `class` (string): Filter by academic class
  - `sort_by` (string): Sort field (goals, assists, minutes)
  - `sort_order` (string): asc or desc  
  **Example:** `/api/v1/players?position=goalkeeper&sort_by=saves`

- **GET `/api/v1/players/{player_id}`**  
  Get detailed player profile and statistics  
  **Example:** `/api/v1/players/456`

- **GET `/api/v1/players/{player_id}/statistics`**  
  Get player's detailed statistics  
  **Query Parameters:**  
  - `season` (integer): Season year
  - `conference_only` (boolean): Conference stats only  
  **Example:** `/api/v1/players/456/statistics?season=2024`

---

### Games/Matches Endpoints

- **GET `/api/v1/games`**  
  Retrieve games with comprehensive filtering  
  **Query Parameters:**  
  - `date` (string): Game date (YYYY-MM-DD)
  - `date_from` (string): Start date for range
  - `date_to` (string): End date for range
  - `team_id` (integer): Games involving specific team
  - `conference` (string): Conference games only
  - `division` (string): Division filter
  - `status` (string): scheduled, live, completed  
  **Example:** `/api/v1/games?date=2024-10-15&division=d1`

- **GET `/api/v1/games/{game_id}`**  
  Get detailed information for a specific game  
  **Example:** `/api/v1/games/789`

- **GET `/api/v1/games/{game_id}/events`**  
  Get game timeline with all events  
  **Example:** `/api/v1/games/789/events`

- **POST `/api/v1/games`**  
  Submit game results (admin only)  
  **Required Fields:** home_team_id, away_team_id, game_date  
  **Optional Fields:** home_score, away_score, status

---

### Rankings & Standings Endpoints

- **GET `/api/v1/standings`**  
  Get conference standings  
  **Query Parameters:**  
  - `division` (string): Division (d1, d2, d3)
  - `conference` (string): Specific conference
  - `season` (integer): Season year  
  **Example:** `/api/v1/standings?division=d1&conference=big-ten`

- **GET `/api/v1/rankings`**  
  Get national rankings/polls  
  **Query Parameters:**  
  - `division` (string): Division
  - `poll_type` (string): coaches, media, rpi
  - `week` (integer): Week number  
  **Example:** `/api/v1/rankings?division=d1&poll_type=coaches`

---

### Statistics Endpoints

- **GET `/api/v1/statistics/leaders`**  
  Get statistical leaders  
  **Query Parameters:**  
  - `category` (string): goals, assists, saves, shutouts
  - `division` (string): Division filter
  - `conference` (string): Conference filter
  - `limit` (integer): Number of results  
  **Example:** `/api/v1/statistics/leaders?category=goals&limit=10`

- **GET `/api/v1/statistics/team`**  
  Get aggregated team statistics  
  **Query Parameters:**  
  - `season` (integer): Season year
  - `division` (string): Division filter
  - `metric` (string): Specific metric  
  **Example:** `/api/v1/statistics/team?metric=goals_per_game`

---

## 3. Data Models

### Team Model

```json
{
  "id": 123,
  "name": "Wake Forest Demon Deacons",
  "short_name": "Wake Forest",
  "mascot": "Demon Deacons",
  "division": "d1",
  "conference": {
    "id": 5,
    "name": "Atlantic Coast Conference",
    "abbreviation": "ACC"
  },
  "location": {
    "city": "Winston-Salem",
    "state": "NC",
    "venue": "Spry Stadium",
    "capacity": 3000
  },
  "colors": ["black", "gold"],
  "logo_url": "https://example.com/logos/wake-forest.png",
  "website": "https://godeacs.com",
  "coaching_staff": {
    "head_coach": "Tony da Luz",
    "assistant_coaches": ["Assistant 1", "Assistant 2"]
  },
  "current_ranking": 3,
  "record": {
    "overall": {
      "wins": 17,
      "losses": 2,
      "ties": 1
    },
    "conference": {
      "wins": 8,
      "losses": 1,
      "ties": 1
    }
  }
}
```

### Player Model

```json
{
  "id": 456,
  "first_name": "John",
  "last_name": "Smith",
  "jersey_number": 10,
  "position": "Forward",
  "team": {
    "id": 123,
    "name": "Wake Forest Demon Deacons"
  },
  "eligibility": {
    "class": "Junior",
    "years_remaining": 2,
    "academic_year": "2024-2025"
  },
  "physical_attributes": {
    "height": "5'11\"",
    "weight": 170,
    "hometown": "Charlotte, NC",
    "high_school": "Myers Park High School"
  },
  "statistics": {
    "career": {
      "games_played": 45,
      "games_started": 40,
      "goals": 25,
      "assists": 15,
      "points": 65,
      "shots": 120,
      "shots_on_goal": 65
    },
    "current_season": {
      "games_played": 20,
      "games_started": 20,
      "goals": 18,
      "assists": 7,
      "points": 43,
      "shots": 75,
      "shots_on_goal": 45,
      "minutes_played": 1650,
      "yellow_cards": 2,
      "red_cards": 0
    }
  }
}
```

### Game Model

```json
{
  "id": 789,
  "game_date": "2024-10-15T19:00:00Z",
  "status": "completed",
  "tournament_context": {
    "type": "regular_season",
    "tournament_name": null,
    "round": null
  },
  "teams": {
    "home": {
      "id": 123,
      "name": "Wake Forest Demon Deacons",
      "score": 3,
      "formation": "4-3-3"
    },
    "away": {
      "id": 124,
      "name": "Duke Blue Devils",
      "score": 1,
      "formation": "4-4-2"
    }
  },
  "venue": {
    "name": "Spry Stadium",
    "city": "Winston-Salem",
    "state": "NC",
    "attendance": 2500
  },
  "officials": {
    "referee": "John Doe",
    "assistant_referees": ["Jane Smith", "Bob Johnson"]
  },
  "weather": {
    "temperature": 72,
    "conditions": "Clear",
    "wind": "5 mph NW"
  },
  "statistics": {
    "home": {
      "shots": 15,
      "shots_on_goal": 8,
      "corner_kicks": 6,
      "fouls": 12,
      "yellow_cards": 1,
      "red_cards": 0,
      "possession_percentage": 58
    },
    "away": {
      "shots": 10,
      "shots_on_goal": 4,
      "corner_kicks": 3,
      "fouls": 15,
      "yellow_cards": 2,
      "red_cards": 0,
      "possession_percentage": 42
    }
  }
}
```

---

## 4. HTTP Methods and Status Codes

### Supported HTTP Methods

- **GET:** Retrieve resources
- **POST:** Create new resources (limited endpoints)
- **PUT:** Update entire resources (future implementation)
- **PATCH:** Partial updates (future implementation)
- **DELETE:** Remove resources (admin only)

### HTTP Status Codes

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: External API error

---

## 5. Request/Response Examples

### Example 1: Get Teams with Filtering

**Request:**
```http
GET /api/v1/teams?division=d1&conference=acc&page=1&per_page=10
Accept: application/json
```
**Response:**
```json
{
  "data": [
    {
      "id": 123,
      "name": "Wake Forest Demon Deacons",
      "short_name": "Wake Forest",
      "division": "d1",
      "conference": {
        "id": 5,
        "name": "Atlantic Coast Conference",
        "abbreviation": "ACC"
      },
      "current_ranking": 3,
      "record": {
        "overall": {"wins": 17, "losses": 2, "ties": 1}
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 15,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "version": "v1",
    "timestamp": "2024-10-15T14:30:00Z"
  }
}
```

### Example 2: Create New Game

**Request:**
```http
POST /api/v1/games
Content-Type: application/json

{
  "home_team_id": 123,
  "away_team_id": 124,
  "game_date": "2024-10-20T19:00:00Z",
  "venue_name": "Spry Stadium",
  "status": "scheduled"
}
```
**Response:**
```json
{
  "id": 790,
  "home_team_id": 123,
  "away_team_id": 124,
  "game_date": "2024-10-20T19:00:00Z",
  "status": "scheduled",
  "created_at": "2024-10-15T14:35:00Z"
}
```

---

## 6. Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "division",
      "value": "d4",
      "constraint": "Must be one of: d1, d2, d3"
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-10-15T14:40:00Z"
  }
}
```

---

## 7. Rate Limiting

Rate limits are enforced per IP address:

- **Default:** 5 requests per second
- **Hourly limit:** 1000 requests per hour

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1697382000
```

---

## Flask Implementation

### Main Application (`app.py`)

```python
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from datetime import datetime
import requests
from functools import wraps
import json

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configure CORS
CORS(app, origins="*")

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "5 per second"]
)

# NCAA API configuration
NCAA_API_BASE = "https://ncaa-api.henrygd.me"
CACHE_TIMEOUT = 300  # 5 minutes

# Simple in-memory cache
cache = {}

def cached(timeout=300):
    """Simple caching decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if cached
            if cache_key in cache:
                cached_data, cached_time = cache[cache_key]
                if (datetime.now() - cached_time).seconds < timeout:
                    return cached_data
            
            # Get fresh data
            result = f(*args, **kwargs)
            cache[cache_key] = (result, datetime.now())
            return result
        return decorated_function
    return decorator

def error_response(message, status_code, details=None):
    """Generate consistent error responses"""
    response = {
        "error": {
            "code": "API_ERROR",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    if details:
        response["error"]["details"] = details
    return jsonify(response), status_code

def paginate_response(data, page=1, per_page=20, total=None):
    """Add pagination metadata to response"""
    if total is None:
        total = len(data)
    
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "data": data[start:end],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "meta": {
            "version": "v1",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }

# External API integration
def fetch_ncaa_data(endpoint):
    """Fetch data from NCAA API with error handling"""
    try:
        url = f"{NCAA_API_BASE}/{endpoint}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None

# Routes

@app.route('/api/v1/teams', methods=['GET'])
@limiter.limit("50 per minute")
@cached(timeout=600)
def get_teams():
    """Get all teams with optional filtering"""
    # Get query parameters
    division = request.args.get('division', 'd1')
    conference = request.args.get('conference')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    
    # Validate division
    if division not in ['d1', 'd2', 'd3']:
        return error_response(
            "Invalid division",
            400,
            {"field": "division", "value": division, "constraint": "Must be one of: d1, d2, d3"}
        )
    
    # Mock data for demonstration
    teams = [
        {
            "id": 123,
            "name": "Wake Forest Demon Deacons",
            "short_name": "Wake Forest",
            "division": "d1",
            "conference": {
                "id": 5,
                "name": "Atlantic Coast Conference",
                "abbreviation": "ACC"
            },
            "location": {
                "city": "Winston-Salem",
                "state": "NC",
                "venue": "Spry Stadium"
            },
            "current_ranking": 3,
            "record": {
                "overall": {"wins": 17, "losses": 2, "ties": 1},
                "conference": {"wins": 8, "losses": 1, "ties": 1}
            }
        },
        {
            "id": 124,
            "name": "Duke Blue Devils",
            "short_name": "Duke",
            "division": "d1",
            "conference": {
                "id": 5,
                "name": "Atlantic Coast Conference",
                "abbreviation": "ACC"
            },
            "location": {
                "city": "Durham",
                "state": "NC",
                "venue": "Koskinen Stadium"
            },
            "current_ranking": 8,
            "record": {
                "overall": {"wins": 14, "losses": 4, "ties": 2},
                "conference": {"wins": 6, "losses": 3, "ties": 1}
            }
        }
    ]
    
    # Apply filters
    filtered_teams = teams
    if conference:
        filtered_teams = [t for t in teams if t['conference']['abbreviation'].lower() == conference.lower()]
    
    return jsonify(paginate_response(filtered_teams, page, per_page))

@app.route('/api/v1/teams/<int:team_id>', methods=['GET'])
@limiter.limit("100 per minute")
@cached(timeout=600)
def get_team(team_id):
    """Get detailed information for a specific team"""
    # Mock detailed team data
    if team_id == 123:
        team = {
            "id": 123,
            "name": "Wake Forest Demon Deacons",
            "short_name": "Wake Forest",
            "mascot": "Demon Deacons",
            "division": "d1",
            "conference": {
                "id": 5,
                "name": "Atlantic Coast Conference",
                "abbreviation": "ACC"
            },
            "location": {
                "city": "Winston-Salem",
                "state": "NC",
                "venue": "Spry Stadium",
                "capacity": 3000
            },
            "colors": ["black", "gold"],
            "website": "https://godeacs.com",
            "coaching_staff": {
                "head_coach": "Tony da Luz",
                "assistant_coaches": ["Bobby Muuss", "Steve Armas"]
            },
            "current_ranking": 3,
            "record": {
                "overall": {"wins": 17, "losses": 2, "ties": 1},
                "conference": {"wins": 8, "losses": 1, "ties": 1},
                "home": {"wins": 10, "losses": 0, "ties": 0},
                "away": {"wins": 7, "losses": 2, "ties": 1}
            },
            "statistics": {
                "goals_scored": 58,
                "goals_allowed": 18,
                "shutouts": 12,
                "yellow_cards": 25,
                "red_cards": 1
            }
        }
        return jsonify(team)
    
    return error_response("Team not found", 404)

@app.route('/api/v1/games', methods=['GET', 'POST'])
@limiter.limit("50 per minute")
def games():
    """Handle game endpoints"""
    if request.method == 'GET':
        return get_games()
    elif request.method == 'POST':
        return create_game()

@cached(timeout=300)
def get_games():
    """Get games with filtering"""
    # Get query parameters
    date = request.args.get('date')
    team_id = request.args.get('team_id', type=int)
    status = request.args.get('status')
    division = request.args.get('division', 'd1')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    
    # Mock game data
    games = [
        {
            "id": 789,
            "game_date": "2024-10-15T19:00:00Z",
            "status": "completed",
            "teams": {
                "home": {
                    "id": 123,
                    "name": "Wake Forest Demon Deacons",
                    "score": 3
                },
                "away": {
                    "id": 124,
                    "name": "Duke Blue Devils",
                    "score": 1
                }
            },
            "venue": {
                "name": "Spry Stadium",
                "city": "Winston-Salem",
                "state": "NC"
            }
        },
        {
            "id": 790,
            "game_date": "2024-10-20T19:00:00Z",
            "status": "scheduled",
            "teams": {
                "home": {
                    "id": 123,
                    "name": "Wake Forest Demon Deacons",
                    "score": None
                },
                "away": {
                    "id": 125,
                    "name": "NC State Wolfpack",
                    "score": None
                }
            },
            "venue": {
                "name": "Spry Stadium",
                "city": "Winston-Salem",
                "state": "NC"
            }
        }
    ]
    
    # Apply filters
    filtered_games = games
    if status:
        filtered_games = [g for g in games if g['status'] == status]
    if team_id:
        filtered_games = [g for g in filtered_games 
                         if g['teams']['home']['id'] == team_id or 
                         g['teams']['away']['id'] == team_id]
    
    return jsonify(paginate_response(filtered_games, page, per_page))

def create_game():
    """Create a new game entry"""
    # Validate request data
    data = request.get_json()
    
    required_fields = ['home_team_id', 'away_team_id', 'game_date']
    for field in required_fields:
        if field not in data:
            return error_response(
                f"Missing required field: {field}",
                400,
                {"field": field, "constraint": "This field is required"}
            )
    
    # Create new game (mock implementation)
    new_game = {
        "id": 791,
        "home_team_id": data['home_team_id'],
        "away_team_id": data['away_team_id'],
        "game_date": data['game_date'],
        "status": data.get('status', 'scheduled'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return jsonify(new_game), 201

@app.route('/api/v1/standings', methods=['GET'])
@limiter.limit("30 per minute")
@cached(timeout=3600)
def get_standings():
    """Get conference standings"""
    division = request.args.get('division', 'd1')
    conference = request.args.get('conference', 'all')
    
    # Mock standings data
    standings = {
        "division": division,
        "conference": "ACC",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "teams": [
            {
                "position": 1,
                "team": {
                    "id": 123,
                    "name": "Wake Forest Demon Deacons"
                },
                "conference_record": {"wins": 8, "losses": 1, "ties": 1},
                "overall_record": {"wins": 17, "losses": 2, "ties": 1},
                "points": 25,
                "goal_difference": 15
            },
            {
                "position": 2,
                "team": {
                    "id": 124,
                    "name": "Duke Blue Devils"
                },
                "conference_record": {"wins": 6, "losses": 3, "ties": 1},
                "overall_record": {"wins": 14, "losses": 4, "ties": 2},
                "points": 19,
                "goal_difference": 8
            }
        ]
    }
    
    return jsonify(standings)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return error_response("Resource not found", 404)

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return error_response(
        "Rate limit exceeded",
        429,
        {"retry_after": error.description}
    )

@app.errorhandler(500)
def internal_error(error):
    return error_response("Internal server error", 500)

# Health check endpoint
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

### Requirements File (`requirements.txt`)

```
Flask==2.3.3
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
requests==2.31.0
```

---

### Running the Application

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the Flask application:**
```bash
python app.py
```

**Test the endpoints:**
```bash
# Get all teams
curl http://localhost:5000/api/v1/teams

# Get specific team
curl http://localhost:5000/api/v1/teams/123

# Get games with filtering
curl http://localhost:5000/api/v1/games?status=completed

# Create a new game (POST)
curl -X POST http://localhost:5000/api/v1/games \
  -H "Content-Type: application/json" \
  -d '{"home_team_id": 123, "away_team_id": 124, "game_date": "2024-11-01T19:00:00Z"}'

# Get standings
curl http://localhost:5000/api/v1/standings?division=d1
```

---

## Key Features Implemented

1. **RESTful API Design**
   - Clean, intuitive URL patterns
   - Proper HTTP method usage
   - Consistent JSON response format
   - Comprehensive error handling

2. **Data Models**
   - Team model with conference, location, and statistics
   - Player model with eligibility and performance data
   - Game model with venue and match statistics
   - Flexible schema design for future expansion

3. **Error Handling**
   - Consistent error response format
   - Meaningful error codes and messages
   - Proper HTTP status codes
   - Rate limit handling

4. **Performance Optimization**
   - Response caching with configurable timeouts
   - Rate limiting to prevent abuse
   - Pagination for large datasets
   - Efficient query parameter filtering

5. **Developer Experience**
   - Clear API documentation
   - Example requests and responses
   - Logical endpoint organization
   - CORS enabled for web clients

---

## Next Steps for Enhancement

- Database Integration: Replace mock data with PostgreSQL database
- Authentication: Add API key authentication for admin endpoints
- WebSocket Support: Real-time updates for live games
- Advanced Caching: Redis integration for distributed caching
- Data Enrichment: Integration with weather APIs and betting odds
- Analytics Dashboard: Admin interface for usage statistics
- Batch Operations: Bulk data import/export capabilities
- GraphQL Layer: Alternative query interface for complex data needs

---

This implementation provides a solid foundation for your NCAA Soccer Data capstone project, with clean architecture, best practices, and room for growth as your requirements evolve.

