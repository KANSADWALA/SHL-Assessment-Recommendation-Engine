"""
SHL Assessment Recommendation Engine
"""
# Standard library imports
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter    
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter import PrometheusMetrics
from datetime import datetime
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import os

# Local imports
from config import Config, BASE_DIR
from recommender import AssessmentRecommender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'frontend', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'frontend', 'static')
)

# Load configuration
app.config.from_object(Config)

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=2)

# Run expensive similarity calculations in background
def async_update_similarities():
    """Run expensive similarity calculations in background"""
    def _update():
        try:
            assessment_recommender._compute_item_similarities()
            assessment_recommender._update_popular_items()
            logger.info("Background update completed")
        except Exception as e:
            logger.error(f"Background update failed: {e}")
    
    executor.submit(_update)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Prometheus metrics
metrics = PrometheusMetrics(app)

recommendation_counter = metrics.counter(
    'recommendations_total', 'Total recommendations served',
    labels={'user_type': lambda: 'new' if session.get('is_new_user') else 'returning'}
)

# Secret key for sessions
app.secret_key = Config.SECRET_KEY

# Enable CORS
CORS(app)

# Initialize recommender
assessment_recommender = AssessmentRecommender()

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/feedback', methods=['POST'])
@limiter.limit("100 per hour")
def feedback():
    """Record user feedback"""
    try:
        data = request.json or {}
        user_id = data.get('user_id') or session.get('user_id')
        
        context = data.get('context') or {
            'features': {'semantic_similarity': 0.5},
            'predicted_score': 10.0
        }
    
        assessment_recommender.record_interaction(
            user_id=user_id,
            assessment_id=data.get('assessment_id'),
            interaction_type='rate',
            rating=data.get('rating'),
            context=context
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.exception("Feedback error")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/insights', methods=['GET'])
def insights():
    """Get model insights"""
    try:
        insights_data = assessment_recommender.get_model_insights()
        return jsonify({
            'status': 'success',
            'insights': insights_data
        })
    except Exception as e:
        logger.exception("Insights error")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/interaction', methods=['POST'])
def interaction():
    """Record user interaction"""
    try:
        data = request.json or {}
        user_id = data.get('user_id') or session.get('user_id')
        
        assessment_recommender.record_interaction(
            user_id=user_id,
            assessment_id=data.get('assessment_id'),
            interaction_type=data.get('interaction_type', 'view'),
            rating=None,
            context=None
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.exception("Interaction error")
        return jsonify({'error': str(e)}), 500

"""
Quick debug script to inspect CF state
"""
@app.route('/api/debug/cf', methods=['GET'])
def debug_cf():
    """Debug collaborative filtering state"""
    try:
        # Get internal state
        users = list(assessment_recommender.user_interactions.keys())
        
        debug_info = {
            'total_users': len(users),
            'users': users,
            'user_interactions': {},
            'item_similarities_count': len(assessment_recommender.item_similarities),
            'item_similarities_sample': {},
            'popular_items': assessment_recommender.popular_items
        }
        
        # Show what each user has interacted with
        for user_id in users[:5]:  # First 5 users
            items = dict(assessment_recommender.user_interactions[user_id]['items'])
            debug_info['user_interactions'][user_id] = items
        
        # Show sample similarities
        for item_id, sims in list(assessment_recommender.item_similarities.items())[:3]:
            debug_info['item_similarities_sample'][item_id] = sims
        
        return jsonify({
            'status': 'success',
            'debug': debug_info
        })
    except Exception as e:
        logger.exception("Debug error")
        return jsonify({'error': str(e)}), 500
# Then test with:
# curl http://127.0.0.1:5000/api/debug/cf | python -m json.tool


# Input validation decorator
def validate_recommendation_request(f):
    """Decorator to validate incoming recommendation requests.

    Ensures that provided `role` is one of the supported roles and that
    `top_k` is an integer within an acceptable range. Returns a 400 JSON
    response on validation failure; otherwise forwards the call to the
    wrapped function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.json or {}
        
        valid_roles = ['Developer', 'Manager', 'Analyst', 'Sales', 'Support', 'Executive']
        if data.get('role') and data['role'] not in valid_roles:
            return jsonify({'error': 'Invalid role'}), 400
        
        top_k = data.get('top_k', 10)
        if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
            return jsonify({'error': 'top_k must be between 1 and 50'}), 400
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/recommend', methods=['POST'])
@limiter.limit("30 per minute")
@validate_recommendation_request 
def recommend():
    """Get recommendations"""
    try:
        data = request.json or {}
        
        # VALIDATION: Require at least one criterion
        role = data.get('role', '')
        level = data.get('level', '')
        industry = data.get('industry', '')
        goal = data.get('goal', '')
        query = data.get('query', '')
        
        if not any([role, level, industry, goal, query]):
            return jsonify({
                'status': 'error',
                'error': 'Please select at least one criterion (role, level, industry, goal, or enter a description)'
            }), 400
        
        # Get/create user ID
        user_id = data.get('user_id')
        if not user_id:
            if 'user_id' not in session:
                session['user_id'] = str(uuid.uuid4())
            user_id = session['user_id']
        
        recommendations = assessment_recommender.get_advanced_recommendations(
            user_id=user_id,
            role=role,
            level=level,
            industry=industry,
            goal=goal,
            query=query,
            top_k=data.get('top_k', 10)
         )
        
        for rec in recommendations[:3]:
            assessment_recommender.record_interaction(
                user_id=user_id,
                assessment_id=rec['assessment']['id'],
                interaction_type='view',
                rating=None,
                context=None
            )
        
        return jsonify({
            'status': 'success',
            'user_id': user_id,
            'recommendations': recommendations
        })
    except Exception as e:
        logger.exception("Recommendation error")
        return jsonify({'error': str(e)}), 500
    
@app.route('/health', methods=['GET'])
def health_check():
    try:
        insights = assessment_recommender.get_model_insights()
        
        return jsonify({
            'status': 'healthy',
            'model_status': insights['collaborative_filtering']['status'],
            'embeddings_loaded': insights['model_info']['embeddings_count'] > 0,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.exception("Health check failed")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/api/db/health', methods=['GET'])
def database_health():
    """Check database health"""
    try:
        is_healthy = assessment_recommender.db.verify_database_health()
        stats = assessment_recommender.db.get_statistics()
        
        return jsonify({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.exception("Database health check failed")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        host='127.0.0.1',
        port=5000
    )


