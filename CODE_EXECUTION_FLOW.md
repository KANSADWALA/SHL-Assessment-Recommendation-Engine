# SHL Assessment Recommender - Code Execution Flow

## 📋 Table of Contents
1. [System Initialization](#1-system-initialization)
2. [Request Processing Flow](#2-request-processing-flow)
3. [Recommendation Generation](#3-recommendation-generation)
4. [Feedback & Learning Loop](#4-feedback--learning-loop)
5. [Database Operations](#5-database-operations)
6. [Maintenance & Cleanup](#6-maintenance--cleanup)

---

## 1. System Initialization

### 1.1 Application Startup (`flask_app.py`)
```
START: python flask_app.py
  ↓
Load Configuration (config.py)
  ↓
Initialize Flask App
  ↓
Setup Middleware (CORS, Rate Limiter, Prometheus)
  ↓
Initialize AssessmentRecommender
```

### 1.2 Recommender Initialization (`recommender.py`)
```
AssessmentRecommender.__init__()
  ↓
├─ Setup Thread Locks (interaction_lock, feedback_lock)
├─ Initialize Memory Limits (MAX_USERS, MAX_FEEDBACK)
├─ Initialize Data Structures
│  ├─ user_interactions (defaultdict)
│  ├─ item_similarities (dict)
│  ├─ feature_weights (dict)
│  ├─ feedback_data (list)
│  └─ user_profiles (defaultdict)
│
├─ Build Synonym Map (_build_synonym_map)
├─ Initialize Database (DatabasePersistence)
│  └─ database.py: DatabasePersistence.__init__()
│     ├─ Validate Database (_ensure_valid_database)
│     ├─ Check Schema (sqlite_master query)
│     └─ Initialize Tables if needed (_init_db)
│
├─ Load Persisted Data (_load_persisted_data)
│  └─ Load recent feedback from database
│
└─ Initialize Models (_initialize_models)
   ├─ Initialize TF-IDF (_initialize_tfidf)
   │  ├─ Build corpus from ASSESSMENTS
   │  ├─ Fit TfidfVectorizer
   │  ├─ Generate assessment_vectors
   │  └─ Create assessment_embeddings
   └─ Update Popular Items (_update_popular_items)
```

---

## 2. Request Processing Flow

### 2.1 User Request Arrives
```
HTTP Request → Flask App
  ↓
Rate Limiter Check
  ↓
Route Handler (@app.route)
```

### 2.2 Main API Endpoints

#### A. `/api/recommend` (POST)
```
1. Receive Request
   ├─ Extract: role, level, industry, goal, query, top_k
   └─ Get/Create user_id (from request or session)

2. Validation (@validate_recommendation_request)
   ├─ Check if at least one criterion provided
   ├─ Validate role in valid_roles list
   └─ Validate top_k (1-50)

3. Call Recommender
   └─ validate_recommendations()
      ├─ get_advanced_recommendations()
      └─ Quality Analysis

4. Record View Interactions (top 3 results)
   └─ record_interaction(type='view')

5. Return Response
   └─ JSON: recommendations, quality, message, suggestions
```

#### B. `/api/feedback` (POST)
```
1. Receive Feedback
   ├─ user_id
   ├─ assessment_id
   ├─ rating (1-5)
   └─ context (features, predicted_score)

2. Record Interaction
   └─ record_interaction(type='rate')
      ├─ Save to memory
      ├─ Save to database
      └─ Trigger online learning

3. Return Success
```

#### C. `/api/interaction` (POST)
```
1. Receive Interaction
   ├─ user_id
   ├─ assessment_id
   └─ interaction_type (view/click/select)

2. Record Interaction
   └─ record_interaction()

3. Return Success
```

---

## 3. Recommendation Generation

### 3.1 High-Level Flow
```
validate_recommendations()
  ↓
get_advanced_recommendations()
  ↓
├─ 1. User Profile Check
├─ 2. Query Expansion
├─ 3. Content-Based Scoring
├─ 4. Collaborative Filtering
├─ 5. Rule-Based Scoring
├─ 6. Score Aggregation
└─ 7. Ranking & Return
  ↓
Quality Validation & Analysis
  ↓
Return Results with Suggestions
```

### 3.2 Detailed Recommendation Steps

#### Step 1: User Profile Check
```
Check if user_id exists in user_interactions
  ├─ YES → is_new = False (use collaborative filtering)
  └─ NO  → is_new = True (cold start, use popularity)

Update user_profiles
  ├─ first_seen (if new)
  └─ last_seen
```

#### Step 2: Query Expansion
```
Input: "developer python"
  ↓
expand_query()
  ↓
├─ Split into words: ["developer", "python"]
├─ Check synonym_map
│  └─ "developer" → add ["engineer", "programmer"]
└─ Return: "developer python engineer programmer"
```

#### Step 3: Content-Based Scoring (TF-IDF)
```
Build Query
  query = f"{role} {level} {industry} {goal}"
  expanded_query = expand_query(query)
  ↓
Transform Query → Vector
  q_vec = tfidf_vectorizer.transform([expanded_query])
  ↓
Calculate Similarity
  sems = cosine_similarity(q_vec, assessment_vectors)
  ↓
Normalize Scores (0-1)
  sems = sems / (sems.max() + 1e-10)
```

#### Step 4: Collaborative Filtering
```
IF user is NOT new:
  ↓
  For each assessment:
    ├─ Get user's interaction history
    ├─ Find similar items from item_similarities
    ├─ Calculate weighted score
    │  score = Σ(similarity × past_score)
    └─ Normalize by total similarity
ELSE:
  ↓
  Use popular_items for cold start boost
```

#### Step 5: Rule-Based Scoring
```
For each assessment:
  ↓
  Calculate Matches:
  ├─ role_match: +2 if role in assessment roles
  ├─ level_match: +1 if level matches
  ├─ industry_match: +1 if industry matches
  ├─ goal_match: +2 if goal matches
  └─ category_match: implicit via semantic similarity
```

#### Step 6: Feedback Boost
```
Get recent feedback (last 100 items)
  ↓
Filter by assessment_id
  ↓
Calculate average rating
  ↓
feedback_boost = (avg_rating - 3) × 0.3
```

#### Step 7: Score Aggregation
```
For each assessment:
  ↓
features = {
  'role_match': rule_score,
  'level_match': level_match,
  'industry_match': ind_match,
  'semantic_similarity': sems[i],
  'collaborative_score': collab[assessment_id],
  'feedback_boost': fb_boost
}
  ↓
total_score = Σ(feature_weights[k] × features[k])
  ↓
IF is_new AND assessment in popular_items:
  total_score += 2 (cold start boost)
  ↓
Calculate match_percentage:
  raw_pct = (total_score / max_possible_score) × 100
  match_pct = 100 / (1 + exp(-0.05 × (raw_pct - 50)))
  match_pct = clamp(match_pct, 0, 100)
```

#### Step 8: Ranking
```
Sort all assessments by total_score (descending)
  ↓
Return top_k results
```

### 3.3 Quality Validation
```
Analyze Results:
  ├─ top_score = recommendations[0].match_percentage
  └─ avg_top_3 = mean of top 3 match percentages
  ↓
Determine Quality:
  ├─ HIGH: top_score ≥ 70 AND avg_top_3 ≥ 60
  ├─ MEDIUM: top_score ≥ 50 AND avg_top_3 ≥ 40
  ├─ LOW: top_score ≥ 30
  └─ NO_MATCH: top_score < 30
  ↓
Generate Message & Suggestions
```

---

## 4. Feedback & Learning Loop

### 4.1 Record Interaction Flow
```
record_interaction(user_id, assessment_id, type, rating, context)
  ↓
1. Acquire Thread Lock (interaction_lock)
  ↓
2. Validate Inputs
   ├─ Check user_id and assessment_id exist
   └─ Validate rating (1-5 if provided)
  ↓
3. Calculate Interaction Weight
   weights = {'view': 0.1, 'click': 0.3, 'rate': 1.0, 'select': 0.5}
   weight = weights[type] × (rating / 5.0)
  ↓
4. Update User Interactions
   user_interactions[user_id]['items'][assessment_id] += weight
   user_interactions[user_id]['last_activity'] = now()
  ↓
5. IF rating provided:
   ├─ Create feedback_item
   ├─ Append to feedback_data
   ├─ Save to database (db.save_feedback)
   ├─ Update metrics
   └─ TRIGGER ONLINE LEARNING ↓
  ↓
6. Online Learning (if context provided)
   ├─ Calculate prediction error
   │  error = (actual_rating / 5) - (predicted_score / 20)
   ├─ Update feature_weights using gradient
   │  For each feature:
   │    gradient = error × feature_value
   │    weight += learning_rate × gradient
   │    weight = clamp(weight, 0.1, 10)
   └─ Increment model_updates counter
  ↓
7. Periodic Updates (at specific thresholds)
   total_interactions = sum of all user interactions
   ├─ At 5, 10, 20, 30, 50, 100, 200, 500 interactions:
   │  ├─ _compute_item_similarities()
   │  └─ _update_popular_items()
   ├─ Every 50 users: _cleanup_old_data()
   └─ Every 20 feedbacks: _update_popular_items()
  ↓
8. Release Thread Lock
```

### 4.2 Compute Item Similarities
```
_compute_item_similarities()
  ↓
1. Build User-Item Matrix
   ├─ Rows: users
   ├─ Columns: items (assessments)
   └─ Values: interaction scores
  ↓
2. Calculate Cosine Similarity
   similarity_matrix = cosine_similarity(matrix.T)
  ↓
3. Store Top 20 Similar Items for Each Item
   item_similarities[item_id] = {similar_id: score, ...}
```

### 4.3 Update Popular Items
```
_update_popular_items()
  ↓
1. Aggregate Interaction Scores
   For each user:
     For each item: scores[item] += interaction_score
  ↓
2. Add Feedback Scores
   For each feedback:
     scores[item] += rating / 5.0
  ↓
3. Sort by Total Score
  ↓
4. Store Top 10 as popular_items
```

---

## 5. Database Operations

### 5.1 Database Initialization
```
DatabasePersistence.__init__(db_path)
  ↓
_ensure_valid_database()
  ↓
├─ Try to open database
├─ Query sqlite_master
├─ Check if tables exist
│  ├─ YES → Continue
│  └─ NO → _init_db()
└─ IF ERROR → _handle_corrupted_database()
```

### 5.2 Handle Corrupted Database
```
_handle_corrupted_database()
  ↓
├─ Create backup file (.corrupted.timestamp)
├─ Remove corrupted file
└─ Recreate fresh database (_init_db)
```

### 5.3 Database Schema
```
_init_db()
  ↓
CREATE TABLE feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  assessment_id TEXT NOT NULL,
  rating INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  context TEXT
)
  ↓
CREATE TABLE interactions (
  user_id TEXT NOT NULL,
  assessment_id TEXT NOT NULL,
  score REAL NOT NULL,
  last_activity TEXT NOT NULL,
  PRIMARY KEY (user_id, assessment_id)
)
  ↓
CREATE INDEXES (user, assessment, timestamp)
```

### 5.4 Save Operations
```
save_feedback(feedback_item)
  ↓
├─ Extract: user_id, assessment_id, rating, timestamp, context
├─ Convert context to JSON
└─ INSERT INTO feedback table
  ↓
  Commit (via context manager)
```

```
save_interaction(user_id, assessment_id, score, last_activity)
  ↓
INSERT OR UPDATE interactions
  ├─ IF exists → score += new_score, update last_activity
  └─ IF not exists → create new row
```

### 5.5 Load Operations
```
load_recent_feedback(limit=5000)
  ↓
SELECT user_id, assessment_id, rating, timestamp
FROM feedback
ORDER BY id DESC
LIMIT ?
  ↓
Return list of feedback dictionaries
```

---

## 6. Maintenance & Cleanup

### 6.1 Cleanup Old Data
```
_cleanup_old_data()
  ↓
1. Calculate Cutoff Date
   cutoff = now() - USER_TTL_DAYS
  ↓
2. Find Old Users
   users with last_activity < cutoff
  ↓
3. Delete Old User Data
   ├─ Remove from user_interactions
   └─ Remove from user_profiles
  ↓
4. Trim Feedback Buffer
   IF len(feedback_data) > MAX_FEEDBACK:
     Keep only last MAX_FEEDBACK items
```

### 6.2 Health Checks

#### Application Health (`/health`)
```
1. Get model insights
2. Check:
   ├─ Model status (active/warming_up)
   ├─ Embeddings loaded (count > 0)
   └─ Timestamp
3. Return healthy/unhealthy status
```

#### Database Health (`/api/db/health`)
```
verify_database_health()
  ↓
├─ Run PRAGMA integrity_check
├─ Verify all expected tables exist
└─ Return statistics (feedback_count, interaction_count, unique_users)
```

---

## 7. Complete Request-Response Cycle Example

### Example: User Searches for "Python Developer Assessment"

```
1. USER SUBMITS FORM
   POST /api/recommend
   {
     role: "Developer",
     level: "Mid",
     query: "python developer assessment",
     top_k: 10
   }
   ↓
2. FLASK APP RECEIVES REQUEST
   ├─ Rate limiter: OK (within limits)
   ├─ Validation: PASS
   └─ Create/Get user_id: "abc123"
   ↓
3. RECOMMENDER PROCESSES
   ├─ Track user profile (first_seen, last_seen)
   ├─ Expand query: "python developer assessment engineer programmer"
   ├─ Transform to TF-IDF vector
   ├─ Calculate semantic similarity with all 12 assessments
   ├─ Check if user is new: YES → use popular_items
   ├─ Calculate rule-based scores (role="Developer")
   ├─ Aggregate all scores with feature_weights
   └─ Rank assessments by total_score
   ↓
4. QUALITY VALIDATION
   ├─ top_score = 78%
   ├─ avg_top_3 = 72%
   └─ Quality: HIGH
   ↓
5. RECORD VIEW INTERACTIONS (Top 3)
   For each of top 3 assessments:
     record_interaction(user="abc123", type="view")
   ↓
6. RETURN RESPONSE
   {
     status: "success",
     recommendations: [...],
     quality: "high",
     message: "Found 10 excellent matches!",
     suggestions: []
   }
   ↓
7. USER VIEWS RESULTS
   ↓
8. USER CLICKS ASSESSMENT #2
   POST /api/interaction
   {user_id: "abc123", assessment_id: 2, type: "click"}
   ↓
9. USER RATES ASSESSMENT #2
   POST /api/feedback
   {
     user_id: "abc123",
     assessment_id: 2,
     rating: 5,
     context: {features: {...}, predicted_score: 15.6}
   }
   ↓
10. ONLINE LEARNING TRIGGERED
    ├─ Calculate error: (5/5) - (15.6/20) = 0.22
    ├─ Update feature_weights using gradient descent
    └─ Save feedback to database
   ↓
11. PERIODIC UPDATE CHECK
    total_interactions = 12 (meets threshold)
    ├─ Recompute item_similarities
    └─ Update popular_items
```

---

## 8. Key Data Flow Diagrams

### Feature Weight Evolution
```
Initial Weights (config.py)
  ↓
User Interactions & Feedback
  ↓
Online Learning (gradient descent)
  ↓
Updated Weights
  ↓
Better Predictions
  ↓
More Accurate Recommendations
```

### Cold Start → Personalized Journey
```
NEW USER
  ↓
No interaction history
  ↓
Use: Popular Items + Content-Based
  ↓
USER INTERACTS (views, clicks, rates)
  ↓
Build interaction history
  ↓
Compute item similarities
  ↓
PERSONALIZED RECOMMENDATIONS
  ↓
Use: Collaborative Filtering + Content + Feedback
```

### Data Persistence Flow
```
IN-MEMORY (Fast Access)
├─ user_interactions
├─ feedback_data (recent)
├─ item_similarities
└─ feature_weights
  ↓ (periodic save)
DATABASE (Persistent)
├─ feedback table
└─ interactions table
  ↑ (on startup)
LOAD into memory
```

---

## 9. Performance Optimizations

### Caching
- `@lru_cache(maxsize=100)` on `expand_query()`
- Pre-computed TF-IDF vectors (assessment_vectors)
- Pre-computed item similarities (item_similarities)

### Batch Processing
- Feedback processed in circular buffer (MAX_FEEDBACK=5000)
- Item similarities computed at specific thresholds
- Old data cleanup every 50 users

### Thread Safety
- `interaction_lock` for concurrent interaction updates
- `feedback_lock` for concurrent feedback updates

---

## 10. Error Handling

### Database Errors
```
Try: Database operation
  ↓
Exception: sqlite3.DatabaseError
  ↓
├─ Log error
├─ Backup corrupted file
├─ Recreate database
└─ Return default/empty values
```

### API Errors
```
Try: Process request
  ↓
Exception: Any
  ↓
├─ Log exception (logger.exception)
├─ Rollback transaction (if DB)
└─ Return JSON error response (500)
```

---

## Summary

**Main Components:**
1. **Flask App** - HTTP layer, routing, validation
2. **Recommender** - Core ML logic, scoring, learning
3. **Database** - Persistence layer for feedback/interactions
4. **Config** - Central configuration and data definitions

**Key Flows:**
1. **Initialization** - Load data, build models, prepare for requests
2. **Recommendation** - Multi-factor scoring + ranking
3. **Feedback Loop** - Learn from user behavior, adapt weights
4. **Persistence** - Save/load from SQLite
5. **Maintenance** - Cleanup, health checks, monitoring

**Algorithms Used:**
- TF-IDF for semantic similarity
- Item-based collaborative filtering
- Rule-based matching
- Online gradient descent for feature weight learning
- Sigmoid normalization for score distribution

---

## 11. Testing & Verification (`test_script.py`)

### 11.1 Purpose
A comprehensive testing script that validates all system components by simulating real user behavior, interactions, and feedback loops **independently** from the main Flask application.

**Key Point:** `test_script.py` has **NO role in code execution** - it is purely for **external testing and validation**. It runs in a separate terminal and communicates with the Flask app via HTTP API calls.

### 11.2 Setup & Usage

```
Terminal 1:                    Terminal 2:
python flask_app.py     →      python test_script.py
(Server Running)               (Tests Running)
         ↓                              ↓
    Port 5000              HTTP Requests → Port 5000
```

**Requirements:**
- Flask app must be running on `http://127.0.0.1:5000`
- No code integration needed - pure API client

### 11.3 Test Suite Components

The script runs **7 comprehensive tests**:

#### Test 1: **Cold Start (New Users)**
- Creates users: `test_alice_123`, `test_bob_456`
- Validates recommendations for users with no history
- Verifies popular items boost for new users
- **What it tests:** Cold start algorithm, initial recommendations

#### Test 2: **Feedback Loop**
- Submits ratings (5★, 4★, 2★) for top recommendations
- Re-fetches recommendations to verify score changes
- **What it tests:** Online learning, feature weight updates, feedback persistence

#### Test 3: **User Interactions**
- Records clicks, views, and selections
- Tracks interaction weights (view: 0.1, click: 0.3, select: 0.5)
- **What it tests:** Interaction tracking, weight calculations

#### Test 4: **Collaborative Filtering (Detailed)**
- Creates User A → rates 3 assessments (5★)
- Creates User B → rates same assessment as User A (5★)
- Creates Users C, D, E → more overlapping interactions
- Verifies item-to-item similarities computed
- **What it tests:** CF algorithm, similarity computation, threshold triggers

#### Test 5: **Diverse User Base**
- Creates users with different roles (Manager, Executive, Analyst)
- Different levels (Mid-Level, Senior, Graduate)
- Different goals (Development, Hiring)
- **What it tests:** Multi-criteria matching, rule-based scoring

#### Test 6: **System Insights**
- Fetches `/api/insights` endpoint
- Displays metrics, feature weights, CF status
- **What it tests:** Monitoring endpoints, system health

#### Test 7: **Feedback Impact Analysis**
- Tracks score progression before/after feedback
- Shows score breakdown changes
- **What it tests:** Real-time learning, score recalculation

### 11.4 API Endpoints Used

```python
POST /api/recommend        # Get recommendations
POST /api/feedback         # Submit ratings
POST /api/interaction      # Record clicks/views
GET  /api/insights         # System metrics
```

### 11.5 Output Features

**Color-Coded Terminal Output:**
- 🟢 **Green:** Success messages, positive changes
- 🔵 **Blue:** Headers, section dividers
- 🟡 **Yellow:** Warnings, pending states
- 🔴 **Red:** Errors, negative scores
- 📊 **Formatted:** Score breakdowns with emojis (📄🤝💬🔥)

**Example Output:**
```
================================================================================
     TEST 4: Collaborative Filtering - Detailed Verification
================================================================================

▶ STEP 1: User A gets recommendations
  User A got 12 recommendations
  
  User A's Top 3:
    1. Verify G+ Intermediate
       Collab Score: 0.00

▶ STEP 2: User A rates 3 assessments highly
  ⭐⭐⭐⭐⭐ Rating 'Verify G+ Intermediate'

▶ STEP 6: User B gets UPDATED recommendations
  
  1. Verify G+ Intermediate 🔥 COLLABORATIVE BOOST!
     Content: 8.45
     Collaborative: 2.34  ← Increased!
     Feedback: 0.60
     Total Score: 14.92
```

### 11.6 Verification Checklist

After running tests, verify:

- ✅ **Cold Start:** New users get popular items
- ✅ **Feedback Learning:** Scores update after ratings
- ✅ **CF Activation:** Status changes to "active" after threshold
- ✅ **Score Changes:** Collaborative scores > 0 after overlapping interactions
- ✅ **Persistence:** Data saved to database (check `recommendations.db`)
- ✅ **Feature Weights:** Updated after feedback (view in insights)

### 11.7 How to Use Test Results in UI

After running tests, you can:
1. Open browser → `http://127.0.0.1:5000`
2. Enter User ID: `test_alice_123` or `test_bob_456`
3. See their personalized recommendations
4. Leave User ID blank to test as a new user

### 11.8 Key Helper Functions

| Function | Purpose |
|----------|---------|
| `get_recommendations()` | Fetch recommendations via API |
| `submit_feedback()` | Send rating + context for learning |
| `record_interaction()` | Track views/clicks |
| `get_insights()` | Fetch system metrics |
| `print_score_breakdown()` | Display colored score components |

### 11.9 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ConnectionError` | Start Flask app first: `python flask_app.py` |
| CF scores = 0 | Run test multiple times to build interaction history |
| No similarities computed | Need 5+ total interactions (automatic threshold) |
| Database locked | Close any DB browsers, restart Flask app |

### 11.10 Test Flow Diagram

```
test_script.py (Terminal 2)
       ↓
   HTTP Requests
       ↓
flask_app.py (Terminal 1)
       ↓
   API Routes
       ↓
AssessmentRecommender
       ↓
Database (recommendations.db)
       ↓
Response back to test_script.py
       ↓
Colored Terminal Output
```

---

## Modifications to Existing Sections

### In Section 2.2 (Main API Endpoints):

Add under each endpoint description:

```markdown
#### Testing Notes:
- **Tested in:** `test_script.py`
- **Test Functions:** 
  - `/api/recommend` → Tests 1, 2, 4, 5, 7
  - `/api/feedback` → Tests 2, 4, 5, 7
  - `/api/interaction` → Test 3
  - `/api/insights` → Test 6
```

### In Section 4.1 (Record Interaction Flow):

Add at the end of the section:

```markdown
#### Testing This Flow:
Run `test_script.py` → **Test 3** (User Interactions)

**Verifies:**
- Interaction weight calculations (view: 0.1, click: 0.3, rate: 1.0, select: 0.5)
- Database persistence of interactions
- Threshold-based triggers (similarity computation, popular items update)
- Thread-safe concurrent interaction recording
```

### In Section 6.2 (Health Checks):

Add after the existing health check descriptions:

```markdown
#### Testing Health Endpoints:
Run `test_script.py` → **Test 6** (System Insights)

**Validates:**
- Metrics accuracy (total recommendations, unique users, feedback count)
- CF status reporting (active/warming_up/cold_start)
- Feature weights correctness
- Model information completeness
```

### In Section 1.2 (Recommender Initialization):

Add at the end:

```markdown
> **Testing Note:** System initialization can be verified via `test_script.py`. 
> The script will fail with `ConnectionError` if initialization is incomplete.
```

---

## Quick Reference: What test_script.py Does NOT Do

❌ **Does NOT:**
- Execute as part of Flask application
- Integrate with recommender.py code
- Run automatically on server startup
- Modify any application logic
- Replace unit tests

✅ **Does:**
- Act as external API client
- Simulate real user behavior
- Validate end-to-end flows
- Test integration between components
- Provide visual verification of features

---

## Summary Table: Test Coverage

| Component | Test Number | What's Validated |
|-----------|-------------|------------------|
| Cold Start Algorithm | Test 1 | Popular items, new user handling |
| Online Learning | Test 2, 7 | Feature weight updates, score changes |
| Interaction Tracking | Test 3 | View/click/select recording |
| Collaborative Filtering | Test 4 | Item similarities, CF scoring |
| Multi-criteria Matching | Test 5 | Role/level/industry/goal matching |
| Monitoring | Test 6 | Metrics, insights, system health |
| Feedback Loop | Test 2, 7 | Rating persistence, score impact |

---

## Running Tests: Step-by-Step

1. **Start Flask Server** (Terminal 1):
   ```bash
   python flask_app.py
   ```
   Wait for: `Running on http://127.0.0.1:5000`

2. **Run Tests** (Terminal 2):
   ```bash
   python test_script.py
   ```

3. **Expected Output:**
   - 7 test sections with colored output
   - All tests should show ✅ SUCCESS
   - Final summary with system metrics

4. **Verify in Browser:**
   - Open `http://127.0.0.1:5000`
   - Use test user IDs to see their data
   - Check that recommendations reflect test interactions

5. **Verify in Database:**
   ```bash
   sqlite3 recommendations.db
   SELECT COUNT(*) FROM feedback;
   SELECT COUNT(*) FROM interactions;
   ```

---

## When to Run test_script.py

| Scenario | Reason |
|----------|--------|
| After code changes | Verify no breaking changes |
| Before deployment | Integration testing |
| Debugging CF issues | Check if similarities are computed |
| Performance testing | See response times for API calls |
| Demo preparation | Generate sample data for UI |
| New feature validation | Ensure end-to-end flow works |

---