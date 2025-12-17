# SHL Assessment Recommendation Engine

## 📋 Overview

The SHL Assessment Recommendation Engine is a designed to help individuals discover the most suitable assessment tools from SHL's product catalogue . The system combines multiple recommendation techniques including content-based filtering, collaborative filtering, and adaptive learning to provide personalized, high-quality recommendations. It learns from user interactions and feedback to continuously improve recommendation quality over time.

## 🌟 Key Features

### 1. Intelligent Recommendation System
- **Multi-Strategy Approach**: Combines content-based filtering (TF-IDF), collaborative filtering (item-item similarity), rule-based matching, and feedback-driven learning
- **Semantic Understanding**: Uses TF-IDF vectorization with n-gram support and query expansion via synonym mapping for better text matching
- **Match Scoring**: Provides percentage-based match scores (0-100%) with detailed breakdowns showing content, collaborative, feedback, and popularity components
- **Quality Validation**: Automatic assessment of recommendation quality (high/medium/low/no match) with actionable suggestions for improvement

### 2. User Personalization
- **User Profiling**: Tracks individual user preferences, interaction history, and temporal patterns
- **Collaborative Signals**: Leverages item-item similarities computed from user interaction matrices to recommend assessments liked by similar users
- **Cold Start Handling**: Uses popularity-based boosting for new users without interaction history
- **Session Management**: Automatic user ID generation and session persistence

### 3. Adaptive Learning
- **Online Learning**: Real-time weight updates using gradient descent on user feedback
- **Dynamic Feature Weights**: Automatically adjusts importance of different scoring features (role match, semantic similarity, etc.) based on user ratings
- **Feedback Integration**: Incorporates explicit ratings (1-5 stars) and implicit interactions (views, clicks, selections)
- **Model Evolution**: Continuously refines recommendations as more user data becomes available

### 4. Data Persistence & Management
- **SQLite Database**: Robust persistence layer for feedback and interaction data
- **Automatic Recovery**: Detects and recovers from database corruption with timestamped backups
- **Data Cleanup**: TTL-based removal of stale user profiles (configurable, default 30 days)
- **Circular Buffers**: Memory-efficient storage with configurable limits for users and feedback items

### 5. API & Integration
- **RESTful API**: Clean Flask-based API with endpoints for recommendations, feedback, interactions, and insights
- **Rate Limiting**: Built-in protection against abuse (200/day, 50/hour default)
- **CORS Support**: Cross-origin resource sharing enabled for web integration
- **Health Checks**: Dedicated endpoints for monitoring system and database health
- **Prometheus Metrics**: Built-in metrics export for monitoring and observability

### 6. Performance & Scalability
- **Query Expansion**: Synonym-based query enhancement for better semantic matching
- **LRU Caching**: Caches expanded queries to reduce repeated computation
- **Thread Safety**: Lock-based concurrency control for safe multi-threaded operations
- **Configurable Limits**: Environment-based configuration for users, feedback, and model parameters
- **Incremental Updates**: Similarity computations triggered at strategic interaction thresholds

### 7. Quality Assurance
- **Input Validation**: Decorator-based validation for API requests with comprehensive error handling
- **Comprehensive Logging**: Structured logging throughout the application for debugging and monitoring
- **Database Health Monitoring**: Regular integrity checks with detailed statistics reporting
- **Error Recovery**: Graceful degradation and automatic recovery from common failure scenarios

## 🛠️ Tech Stack

### Core Framework
- **Flask 3.x**: Lightweight WSGI web application framework for Python
- **Python 3.8+**: Core programming language

### Machine Learning & Data Science
- **scikit-learn**: Machine learning library for TF-IDF vectorization, cosine similarity, and model evaluation
- **NumPy**: Numerical computing for matrix operations and mathematical functions
- **TfidfVectorizer**: Text feature extraction with configurable n-grams (1-3) and 500 max features

### Database & Persistence
- **SQLite3**: Embedded relational database for storing feedback and interactions
- **Custom DatabasePersistence Layer**: Thread-safe database abstraction with connection pooling and error handling

### API & Web Services
- **Flask-CORS**: Cross-Origin Resource Sharing support
- **Flask-Limiter**: Rate limiting and throttling for API protection
- **prometheus-flask-exporter**: Metrics collection and export for Prometheus monitoring

### Configuration & Environment
- **python-dotenv**: Environment variable management from `.env` files
- **Environment-based Config**: Centralized configuration with sensible defaults

### Development & Logging
- **Python logging module**: Structured logging with configurable levels and formatters
- **functools**: LRU cache for performance optimization
- **threading**: Lock-based concurrency control
- **contextlib**: Context managers for database connections

### Data Structures
- **collections.defaultdict**: Efficient default dictionary implementations for user interactions and profiles
- **datetime**: Temporal tracking and TTL management

## 🏗️ Architecture Highlights

### Recommendation Algorithm
The system uses a weighted scoring approach that combines:
- **Role/Goal Matching** (weights: 3.0): Exact matches with user-specified roles and hiring goals
- **Semantic Similarity** (weight: 4.0): TF-IDF cosine similarity between query and assessment descriptions
- **Collaborative Score** (weight: 3.5): Item-item similarity based on user interaction patterns
- **Feedback Boost** (weight: 2.0): Positive/negative adjustments from user ratings
- **Level/Industry Match** (weights: 2.0): Binary matches for seniority and industry filters

Scores are normalized using sigmoid function for better distribution and converted to intuitive percentage-based match scores.

### Data Flow
1. User submits criteria (role, level, industry, goal, or free-text query)
2. Query expansion applies synonyms for better coverage
3. TF-IDF vectorization computes semantic similarity scores
4. Collaborative filtering generates item-item similarity scores
5. Rule-based matching evaluates exact criterion matches
6. Feature weights combine all signals into unified score
7. Results validated for quality and sorted by total score
8. User interactions recorded and trigger incremental model updates

### Learning Mechanism
- Gradient descent updates on explicit feedback (ratings 1-5)
- Error computed as difference between predicted and actual normalized ratings
- Feature weights adjusted proportionally to their contribution and error magnitude
- Weights clamped between 0.1 and 10.0 to prevent extreme values
- Similarity matrices recomputed at strategic interaction thresholds (5, 10, 20, 30, 50, 100+)

## 🗃️ Project Structure

<pre><code class="bash">
 Recommendation_Engine/
    │
    ├── backend/
    │ ├── init.py               # Marks backend as a Python package
    │ ├── flask_app.py          # Flask application entry point
    │ ├── recommender.py        # Recommendation logic 
    │ ├── database.py           # SQLite database operations
    │ ├── config.py             # Application configuration
    │ └── test_script.py        # External testing and validation
    │
    ├── frontend/
    │ ├── templates/
    │ │   └── index.html        # Main UI template
    │ └── static/
    │     ├── styles.css        # Application styling
    │     └── script.js         # Frontend logic & API calls
    │
    ├── data/                   # Auto-created runtime data (ignored by git)
    ├── requirements.txt        # Python dependencies
    ├── .gitignore              # Git ignore rules
    ├── README.md               # Project documentation
    └── CODE_EXCEUTION_FLOW.md  # Code Execution Flow
  
</code></pre>

## 🌐 Configuration

Key environment variables (see `.env`):
- `SECRET_KEY`: Flask session secret
- `MAX_USERS`: Maximum users to track (default: 1000)
- `MAX_FEEDBACK`: Maximum feedback items in memory (default: 5000)
- `USER_TTL_DAYS`: Days before inactive user cleanup (default: 30)
- `LEARNING_RATE`: Online learning rate (default: 0.01)
- `TFIDF_MAX_FEATURES`: Maximum TF-IDF features (default: 500)
- `FLASK_ENV`: Set to 'development' for debug mode

## 🔌 API Endpoints

- `POST /api/recommend` - Get personalized recommendations
- `POST /api/feedback` - Submit user rating (1-5)
- `POST /api/interaction` - Record implicit interaction (view/click/select)
- `GET /api/insights` - Retrieve model performance metrics
- `GET /health` - System health check
- `GET /api/db/health` - Database health and statistics

## 🛢 Database Schema

### feedback table
- `id`: Auto-increment primary key
- `user_id`: User identifier
- `assessment_id`: Assessment ID (1-12)
- `rating`: Integer rating (1-5)
- `timestamp`: ISO format timestamp
- `context`: JSON-serialized context data

### interactions table
- `user_id`: User identifier (composite key)
- `assessment_id`: Assessment ID (composite key)
- `score`: Accumulated interaction score
- `last_activity`: Last interaction timestamp

Indexed on user_id, assessment_id, and timestamp for query optimization.

## 🕵🏼‍♂️ Monitoring & Observability

- Prometheus metrics exposed via `/metrics` endpoint
- Structured logging with timestamps, levels, and component identification
- Real-time metrics tracking: recommendations count, feedback volume, average ratings, model updates
- Database health monitoring with integrity checks and table validation
- Performance statistics available via `/api/insights`

---