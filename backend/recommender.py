# Standard library imports
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from collections import defaultdict
import os
import logging
from functools import lru_cache
from threading import Lock

# Local imports
from backend.config import Config, ASSESSMENTS
from backend.database import DatabasePersistence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AssessmentRecommender:
    """
    AssessmentRecommender

    Production-ready recommendation engine that combines content-based
    (TF-IDF semantic similarity), simple collaborative filtering, rule-based
    heuristics, and feedback-driven online learning to produce ranked
    assessment recommendations.

    Attributes:
        tfidf_vectorizer: Fitted `TfidfVectorizer` instance used for semantic
            similarity calculations.
        assessment_vectors: Sparse matrix of TF-IDF vectors for assessments.
        assessment_embeddings: Dict mapping assessment id -> embedding array.
        user_interactions: In-memory mapping of user_id -> interaction data.
        feedback_data: Circular buffer list of recent feedback items.
        item_similarities: Precomputed item-item similarity lookup for CF.
        feature_weights: Weights applied to different scoring features.
        db: `DatabasePersistence` instance used to persist feedback/interactions.

    The class is thread-safe for interaction and feedback updates via locks.
    """
    
    def __init__(self):
        # Thread safety
        self.interaction_lock = Lock()
        self.feedback_lock = Lock()
        # Core components
        self.tfidf_vectorizer = None
        self.assessment_vectors = None
        self.sentence_model = None
        self.assessment_embeddings = {}
        
        # Memory limits
        self.max_users = Config.MAX_USERS
        self.max_feedback = Config.MAX_FEEDBACK
        
        self.user_ttl_days = Config.USER_TTL_DAYS

        # User data with TTL
        self.user_interactions = defaultdict(lambda: {
            'items': defaultdict(float),
            'last_activity': datetime.now()
        })
        
        # Collaborative filtering
        self.item_similarities = {}
        
        # Adaptive learning
        self.feature_weights = {
            'role_match': 3.0,
            'level_match': 2.0,
            'industry_match': 2.0,
            'goal_match': 3.0,
            'semantic_similarity': 4.0,
            'collaborative_score': 3.5,
            'feedback_boost': 2.0,
            'category_match': 2.5
        }
        self.learning_rate = Config.LEARNING_RATE
        
        # Feedback storage (circular buffer)
        self.feedback_data = []
        self.user_profiles = defaultdict(lambda: {
            'preferences': defaultdict(float),
            'first_seen': datetime.now(),
            'last_seen': datetime.now()
        })
        
        # Synonym map for query expansion
        self.synonym_map = self._build_synonym_map()
        
        # Popular items for cold start
        self.popular_items = []
        
        # Performance metrics
        self.metrics = {
            'total_recommendations': 0,
            'total_feedback': 0,
            'avg_rating': 0.0,
            'model_updates': 0
        }

        # Initialize database
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
        self.db = DatabasePersistence(Config.DATABASE_PATH)

        # Load existing data
        self._load_persisted_data()
        
        # Initialize
        self._initialize_models()
        logger.info("✓ AssessmentRecommender initialized")
    
    def _build_synonym_map(self):
        """Build a dictionary of synonyms used for query expansion.

        Returns:
            dict: mapping of canonical word -> list of synonym strings.
        """
        return {
            'developer': ['engineer', 'programmer', 'coder', 'software developer'],
            'engineer': ['developer', 'programmer', 'technical', 'software engineer'],
            'manager': ['supervisor', 'team lead', 'director', 'head', 'leadership'],
            'analyst': ['data analyst', 'business analyst', 'researcher'],
            'customer service': ['support', 'help desk', 'contact center', 'agent'],
            'sales': ['account manager', 'business development', 'sales rep'],
            'graduate': ['entry level', 'junior', 'trainee', 'fresh grad'],
            'technical skills': ['coding', 'programming', 'tech skills'],
            'leadership': ['management', 'executive', 'supervision'],
            'problem solving': ['critical thinking', 'analytical', 'reasoning'],
            'cognitive': ['reasoning', 'intelligence', 'aptitude'],
            'hiring': ['recruitment', 'selection', 'talent acquisition'],
            'development': ['learning', 'training', 'growth', 'upskilling']
        }
    
    def _initialize_models(self):
        """Initialize internal models and derived data.

        This currently fits the TF-IDF vectorizer on the assessment corpus and
        updates the popular items list. Additional initialization steps for
        other models can be added here.
        """
        logger.info("Initializing TF-IDF model...")
        self._initialize_tfidf()
        self._update_popular_items()
        logger.info("✓ TF-IDF model ready")
    
    def _initialize_tfidf(self):
        """Fit the TF-IDF vectorizer over the assessment corpus.

        Populates `self.tfidf_vectorizer`, `self.assessment_vectors` and
        `self.assessment_embeddings` used for semantic similarity scoring.
        """
        corpus = []
        for a in ASSESSMENTS:
            text = ' '.join([
                a['name'] * 3,
                a['description'] * 2,
                a['category'],
                ' '.join(a['suitable_for']['roles']) * 2,
                ' '.join(a['suitable_for']['goals']) * 2,
                ' '.join(a.get('key_features', [])),
                ' '.join(a.get('benefits', []))
            ]).lower()
            corpus.append(text)
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=Config.TFIDF_MAX_FEATURES,
            ngram_range=(1, 3),
            stop_words='english',
            sublinear_tf=True
        )

        self.assessment_vectors = self.tfidf_vectorizer.fit_transform(corpus)
        
        # Create TF-IDF embeddings
        for i, assessment in enumerate(ASSESSMENTS):
            embedding = self.assessment_vectors[i].toarray()[0]
            self.assessment_embeddings[assessment['id']] = embedding
    
    def _cleanup_old_data(self):
        """Remove stale user profiles and trim feedback buffer.

        Removes users whose `last_activity` is older than the configured TTL
        and keeps `self.feedback_data` within `self.max_feedback`.
        """
        cutoff = datetime.now() - timedelta(days=self.user_ttl_days)
        old_users = [uid for uid, data in self.user_interactions.items()
                     if data['last_activity'] < cutoff]
        
        for uid in old_users:
            del self.user_interactions[uid]
            if uid in self.user_profiles:
                del self.user_profiles[uid]
        
        if len(self.feedback_data) > self.max_feedback:
            self.feedback_data = self.feedback_data[-self.max_feedback:]
    
    def _update_popular_items(self):
        """Compute and store top popular assessment ids.

        Popularity is computed from accumulated interaction scores and recent
        feedback ratings. This list is used to boost recommendations for new
        (cold-start) users.
        """
        scores = defaultdict(float)
        for user_data in self.user_interactions.values():
            for item, score in user_data['items'].items():
                scores[item] += score
        
        for fb in self.feedback_data:
            scores[fb['assessment_id']] += fb['rating'] / 5.0
        
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        self.popular_items = [item for item, _ in sorted_items[:10]]
        
        if not self.popular_items:
            self.popular_items = [a['id'] for a in ASSESSMENTS[:10]]
    
    def _compute_item_similarities(self):
        """Compute item-item similarities using user-item interaction matrix.

        Builds a cosine-similarity matrix over items derived from the
        user-interaction matrix and stores the top similar items for each
        item in `self.item_similarities`.
        """
        users = list(self.user_interactions.keys())
        all_items = set()
        for data in self.user_interactions.values():
            all_items.update(data['items'].keys())
        items = list(all_items)
        
        if len(users) < 2 or len(items) < 2:
            return
        
        matrix = np.zeros((len(users), len(items)))
        user_idx = {u: i for i, u in enumerate(users)}
        item_idx = {it: i for i, it in enumerate(items)}
        
        for uid, data in self.user_interactions.items():
            for item, score in data['items'].items():
                if item in item_idx:
                    matrix[user_idx[uid]][item_idx[item]] = score
        
        if matrix.sum() > 0:
            sims = cosine_similarity(matrix.T + 1e-10)
            for i, item_i in enumerate(items):
                top = [(items[j], sims[i][j]) for j in range(len(items)) if i != j]
                top.sort(key=lambda x: x[1], reverse=True)
                self.item_similarities[item_i] = dict(top[:20])
    
    @lru_cache(maxsize=100)
    def expand_query(self, text):
        """Expand an input query by adding common synonyms.

        Args:
            text (str): The input text or short description to expand.

        Returns:
            str: Expanded query string with synonyms appended (de-duplicated).
        """
        if not text:
            return text
        words = text.lower().split()
        expanded = words.copy()
        for word in words:
            if word in self.synonym_map:
                expanded.extend(self.synonym_map[word][:2])
        return ' '.join(set(expanded))

    def get_advanced_recommendations(self, user_id, role='', level='', 
                                    industry='', goal='', query='', top_k=10):
        """Produce ranked assessment recommendations for a user.

        Scoring combines rule-based matches, semantic similarity (TF-IDF),
        collaborative signals (item similarities), and feedback-driven
        boosts. Feature weights are applied and normalized to compute a
        percentage match for each assessment.

        Args:
            user_id (str): Identifier for the requesting user.
            role (str): User role (optional) used for rule matching.
            level (str): Seniority/level (optional).
            industry (str): Industry filter (optional).
            goal (str): Hiring/development goal (optional).
            query (str): Free-text query to include in semantic matching.
            top_k (int): Maximum number of recommendations to return.

        Returns:
            list[dict]: List of recommendation dicts sorted by score.
        """
        self.metrics['total_recommendations'] += 1
        
        # Track user even for just recommendations
        if user_id not in self.user_profiles:
            self.user_profiles[user_id]['first_seen'] = datetime.now()
        self.user_profiles[user_id]['last_seen'] = datetime.now()
        
        is_new = user_id not in self.user_interactions
        
        # Build query
        q = query if query else f"{role} {level} {industry} {goal}"
        q_expanded = self.expand_query(q)
        
        # Get TF-IDF semantic scores
        q_vec = self.tfidf_vectorizer.transform([q_expanded])
        sems = cosine_similarity(q_vec, self.assessment_vectors).flatten()
        
        sems = sems / (sems.max() + 1e-10)
        
        # Collaborative scores
        collab = {}
        if not is_new and user_id in self.user_interactions:
            history = self.user_interactions[user_id]['items']
            for a in ASSESSMENTS:
                score = 0.0
                total_sim = 0.0
                for past_item, past_score in history.items():
                    if past_item in self.item_similarities:
                        sim = self.item_similarities[past_item].get(a['id'], 0)
                        score += sim * past_score
                        total_sim += abs(sim)
                collab[a['id']] = score / total_sim if total_sim > 0 else 0
        else:
            collab = {a['id']: 0 for a in ASSESSMENTS}
        
        # Score all assessments
        results = []
        for i, a in enumerate(ASSESSMENTS):
            # Rule-based
            rule_score = 0
            if role and any(role.lower() in r.lower() for r in a['suitable_for']['roles']):
                rule_score += 2
            if goal and any(goal.lower() in g.lower() for g in a['suitable_for']['goals']):
                rule_score += 2
            
            level_match = 1 if level and level in a['suitable_for']['levels'] else 0
            ind_match = 1 if industry and any(industry.lower() in ind.lower() 
                                             for ind in a['suitable_for']['industries']) else 0
            
            # Feedback boost
            recent_fb = [f for f in self.feedback_data[-100:] if f['assessment_id'] == a['id']]
            fb_boost = (np.mean([f['rating'] for f in recent_fb]) - 3) * 0.3 if recent_fb else 0
            
            # Combined score
            features = {
                'role_match': rule_score,
                'level_match': level_match,
                'industry_match': ind_match,
                'semantic_similarity': sems[i],
                'collaborative_score': collab[a['id']],
                'feedback_boost': fb_boost
            }
            
            total = sum(self.feature_weights.get(k, 1) * v for k, v in features.items())
            
            # Cold start boost
            if is_new and a['id'] in self.popular_items:
                total += 2
            
            max_possible_score = sum(self.feature_weights.values()) + 2
            raw_pct = (total / max_possible_score) * 100
            # Sigmoid normalization for better distribution
            match_pct = int(100 / (1 + np.exp(-0.05 * (raw_pct - 50))))
            match_pct = max(0, min(100, match_pct))
            
            results.append({
                'assessment': a,
                'total_score': round(total, 2),
                'match_percentage': match_pct,
                'score_breakdown': {
                    'content': round(rule_score * 2 + sems[i] * 4, 2),
                    'collaborative': round(collab[a['id']] * 3.5, 2),
                    'feedback': round(fb_boost * 2, 2),
                    'popularity': 2 if (is_new and a['id'] in self.popular_items) else 0
                },
                'is_new_user': is_new
            })
        
        results.sort(key=lambda x: x['total_score'], reverse=True)
        return results[:top_k]
    
    def validate_recommendations(self, user_id, role='', level='', 
                                     industry='', goal='', query='', top_k=10):
        """
        Get recommendations with validation and quality checks.
        
        Returns a dict with:
        - recommendations: list of recommendations
        - quality: 'high', 'medium', 'low', or 'no_match'
        - message: user-facing message about results
        - suggestions: list of suggestions to improve results
        """
        
        # Get raw recommendations
        recommendations = self.get_advanced_recommendations(
            user_id=user_id,
            role=role,
            level=level,
            industry=industry,
            goal=goal,
            query=query,
            top_k=top_k
        )
        
        # Analyze recommendation quality
        if not recommendations:
            return {
                'recommendations': [],
                'quality': 'no_match',
                'message': 'No relevant assessments found for the selected criteria.',
                'suggestions': [
                    "Try adjusting role, level, goal, or provide a clearer description.",
                    'Use more general terms in your description'
                ]
            }
        
        # Check score distribution
        top_score = recommendations[0]['match_percentage']
        avg_top_3 = sum(r['match_percentage'] for r in recommendations[:3]) / min(3, len(recommendations))
        
        # Determine quality and craft message
        if top_score >= 70 and avg_top_3 >= 60:
            quality = 'high'
            message = f"Found {len(recommendations)} excellent matches for your criteria!"
            suggestions = []
            
        elif top_score >= 50 and avg_top_3 >= 40:
            quality = 'medium'
            message = f"Found {len(recommendations)} assessments."
            suggestions = []
            # suggestions = [s for s in suggestions if s]  # Remove None values
            
        elif top_score >= 30:
            quality = 'low'
            message = "We found some assessments, but they may not be a perfect fit."
            suggestions = [
                'Try different role or industry selections',
                'Use simpler, more common terms in your description',
                'Remove very specific requirements to see more options',
                'Consider browsing all assessments in a category'
            ]
            
        else:
            quality = 'no_match'
            message = "No strong matches found for your current criteria."
            suggestions = [
                'Try selecting different options from the dropdowns',
                'Use more general terms (e.g., "leadership skills" instead of specific job titles)',
                'Clear some filters to see broader results',
                'Check if your description contains typos or very specific jargon'
            ]
            
            # Only return top recommendations if quality is very low
            recommendations = recommendations[:3]
        
        return {
            'recommendations': recommendations,
            'quality': quality,
            'message': message,
            'suggestions': suggestions,
            'metadata': {
                'top_score': top_score,
                'avg_score': avg_top_3,
                'total_found': len(recommendations)
            }
        }
    
    def _load_persisted_data(self):
        """Load recent feedback and persisted state from the database.

        Populates `self.feedback_data` from persistent storage. Any errors
        during loading are logged and do not raise to the caller.
        """
        try:
            self.feedback_data = self.db.load_recent_feedback(limit=self.max_feedback)
            logger.info(f"Loaded {len(self.feedback_data)} feedback items from database")
        except Exception as e:
            logger.error(f"Error loading data from database: {e}")

    def record_interaction(self, user_id, assessment_id, interaction_type, 
                        rating=None, context=None):
        """Record a user interaction and optionally update model weights.

        Args:
            user_id (str): Unique user identifier.
            assessment_id (str|int): Assessment identifier.
            interaction_type (str): One of 'view', 'click', 'rate', 'select'.
            rating (int|None): Optional rating 1-5 representing explicit feedback.
            context (dict|None): Optional context containing prediction and
                feature contributions for online learning.

        Raises:
            ValueError: If required parameters are missing or rating is invalid.
        """

        # Acquire lock
        with self.interaction_lock: 
            # Validate inputs
            if not user_id or not assessment_id:
                raise ValueError("user_id and assessment_id are required")
            
            if rating is not None and not (1 <= rating <= 5):
                raise ValueError("Rating must be between 1 and 5")

        weights = {'view': 0.1, 'click': 0.3, 'rate': 1.0, 'select': 0.5}
        w = weights.get(interaction_type, 0.1)
        if rating:
            w *= (rating / 5.0)
        
        self.user_interactions[user_id]['items'][assessment_id] += w
        self.user_interactions[user_id]['last_activity'] = datetime.now()
        
        if rating:
            feedback_item = {
                'user_id': user_id,
                'assessment_id': assessment_id,
                'rating': rating,
                'timestamp': datetime.now().isoformat()
            }
            self.feedback_data.append(feedback_item)
            self.db.save_feedback(feedback_item)  # Save to database

            self.metrics['total_feedback'] += 1
            self.metrics['avg_rating'] = np.mean([f['rating'] for f in self.feedback_data])
            
            # Online learning
            if context and 'features' in context and 'predicted_score' in context:
                error = (rating / 5.0) - (context['predicted_score'] / 20.0)
                for feat, val in context['features'].items():
                    if feat in self.feature_weights and val != 0:
                        grad = error * val
                        self.feature_weights[feat] += self.learning_rate * grad
                        self.feature_weights[feat] = max(0.1, min(10, self.feature_weights[feat]))
                self.metrics['model_updates'] += 1
        
        # ========== IMPORTANT CHANGE HERE ==========
        # Compute similarities more frequently for testing/demo
        total_interactions = sum(len(d['items']) for d in self.user_interactions.values())
        
        # Run updates at these thresholds: 5, 10, 20, 30, 50, 100...
        update_thresholds = [5, 10, 20, 30, 50, 100, 200, 500]
        if total_interactions in update_thresholds or total_interactions % 50 == 0:
            logger.info(f"Computing similarities at {total_interactions} total interactions")
            self._compute_item_similarities()
            self._update_popular_items()
        # ==========================================
        
        if len(self.user_interactions) % 50 == 0:
            self._cleanup_old_data()
        
        if self.metrics['total_feedback'] % 20 == 0:
            self._update_popular_items()

    def get_model_insights(self):
        """Return a snapshot of internal model metrics and state.

        The returned dictionary contains learned `feature_weights`, aggregate
        metrics, collaborative filtering statistics and basic model info.

        Returns:
            dict: Insight summary suitable for telemetry or debugging.
        """
        total_int = sum(len(d['items']) for d in self.user_interactions.values())
        unique_users = len(set(
            [fb['user_id'] for fb in self.feedback_data] + 
            list(self.user_interactions.keys())
        ))
        return {
            'feature_weights': {k: round(v, 3) for k, v in self.feature_weights.items()},
            'metrics': {
                'total_recommendations': self.metrics['total_recommendations'],
                'total_interactions': total_int,
                'unique_users': unique_users,
                'total_feedback': self.metrics['total_feedback'],
                'avg_rating': round(self.metrics['avg_rating'], 2),
                'model_updates': self.metrics['model_updates']
            },
            'collaborative_filtering': {
                'users_tracked': len(self.user_interactions),
                'items_with_similarities': len(self.item_similarities),
                'status': 'active' if len(self.user_interactions) >= 1 else 'warming_up'
            },
            'model_info': {
                'embedding_method': 'TF-IDF',
                'embeddings_count': len(self.assessment_embeddings),
                'popular_items': len(self.popular_items)
            }
        }