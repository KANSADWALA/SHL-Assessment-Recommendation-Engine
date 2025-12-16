"""
Testing Script for SHL Assessment Recommendation Engine
Comprehensive test suite covering collaborative filtering, feedback loops, 
interactions, and score progression with detailed verification.
"""

import requests
import time
from typing import Dict, List

BASE_URL = "http://127.0.0.1:5000"

class Color:
    """Terminal colors for better output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Color.HEADER}{Color.BOLD}{'='*80}")
    print(f"{text.center(80)}")
    print(f"{'='*80}{Color.END}")

def print_section(text: str):
    """Print a formatted section"""
    print(f"\n{Color.CYAN}{Color.BOLD}▶ {text}{Color.END}")

def print_success(text: str):
    """Print success message"""
    print(f"{Color.GREEN}✓ {text}{Color.END}")

def print_info(text: str, indent: int = 2):
    """Print info message"""
    print(f"{' ' * indent}{text}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Color.YELLOW}⚠ {text}{Color.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Color.RED}❌ {text}{Color.END}")

def print_score_breakdown(scores: Dict, indent: int = 6):
    """Print score breakdown with colors"""
    score_items = [
        ("Content", scores.get('content', 0), "📄"),
        ("Collaborative", scores.get('collaborative', 0), "🤝"),
        ("Feedback", scores.get('feedback', 0), "💬"),
        ("Popularity", scores.get('popularity', 0), "🔥")
    ]
    
    for name, value, emoji in score_items:
        color = Color.GREEN if value > 0 else Color.RED if value < 0 else Color.END
        print(f"{' ' * indent}{emoji} {name}: {color}{value:.2f}{Color.END}")

# API Helper Functions
def get_recommendations(user_id: str, role: str = "Developer", 
                       level: str = "Graduate", goal: str = "Hiring") -> Dict:
    """Get recommendations for a user"""
    response = requests.post(f"{BASE_URL}/api/recommend", json={
        "user_id": user_id,
        "role": role,
        "level": level,
        "goal": goal
    })
    return response.json()

def submit_feedback(user_id: str, assessment_id: str, rating: int, 
                   context: Dict = None):
    """Submit feedback for an assessment"""
    requests.post(f"{BASE_URL}/api/feedback", json={
        "user_id": user_id,
        "assessment_id": assessment_id,
        "rating": rating,
        "context": context or {}
    })

def record_interaction(user_id: str, assessment_id: str, 
                      interaction_type: str = "click"):
    """Record user interaction"""
    requests.post(f"{BASE_URL}/api/interaction", json={
        "user_id": user_id,
        "assessment_id": assessment_id,
        "interaction_type": interaction_type
    })

def get_insights() -> Dict:
    """Get system insights"""
    response = requests.get(f"{BASE_URL}/api/insights")
    return response.json()['insights']


# Test Functions
def test_new_user_cold_start(user_id: str, name: str):
    """Test 1: New user with no history (cold start)"""
    print_header(f"TEST 1: New User Cold Start - {name}")
    
    print_section("Getting initial recommendations (cold start)")
    data = get_recommendations(user_id)
    recs = data['recommendations']
    
    print_info(f"User ID: {data['user_id']}")
    print_info(f"Is New User: {recs[0].get('is_new_user', 'N/A')}")
    print_info(f"Recommendations received: {len(recs)}")
    
    print_section("Top 3 Recommendations:")
    for i, rec in enumerate(recs[:3], 1):
        a = rec['assessment']
        print_info(f"{i}. {a['name']}", indent=2)
        print_info(f"   Match: {rec['match_percentage']}% | Total Score: {rec['total_score']:.2f}", indent=2)
        print_score_breakdown(rec['score_breakdown'])
    
    return recs


def test_feedback_loop(user_id: str, name: str, recs: List[Dict]):
    """Test 2: Submit feedback and see score changes"""
    print_header(f"TEST 2: Feedback Loop - {name}")
    
    ratings = [
        (0, 5, "loved it"),
        (1, 4, "quite good"),
        (2, 2, "not impressed")
    ]
    
    print_section("Submitting ratings")
    for idx, rating, comment in ratings:
        assessment = recs[idx]['assessment']
        print_info(f"Rating '{assessment['name']}' → {rating}⭐ ({comment})", indent=2)
        
        submit_feedback(
            user_id=user_id,
            assessment_id=assessment['id'],
            rating=rating,
            context={
                "features": recs[idx].get('score_breakdown', {}),
                "predicted_score": recs[idx]['total_score']
            }
        )
        time.sleep(0.2)
    
    print_success("All feedback submitted")
    
    print_section("Getting recommendations after feedback")
    new_data = get_recommendations(user_id)
    new_recs = new_data['recommendations']
    
    print_section("Updated Top 3 Recommendations:")
    for i, rec in enumerate(new_recs[:3], 1):
        a = rec['assessment']
        print_info(f"{i}. {a['name']}", indent=2)
        print_info(f"   Match: {rec['match_percentage']}% | Total Score: {rec['total_score']:.2f}", indent=2)
        print_score_breakdown(rec['score_breakdown'])
    
    return new_recs


def test_interactions(user_id: str, name: str, recs: List[Dict]):
    """Test 3: Record various interactions"""
    print_header(f"TEST 3: User Interactions - {name}")
    
    interactions = [
        (0, "click", "Selected top recommendation"),
        (1, "view", "Viewed details"),
        (3, "click", "Explored alternative")
    ]
    
    print_section("Recording interactions")
    for idx, int_type, description in interactions:
        assessment = recs[idx]['assessment']
        print_info(f"{description}: '{assessment['name']}' ({int_type})", indent=2)
        record_interaction(user_id, assessment['id'], int_type)
        time.sleep(0.1)
    
    print_success("Interactions recorded")


def test_collaborative_filtering_detailed():
    """Test 4: Detailed collaborative filtering verification"""
    print_header("TEST 4: Collaborative Filtering - Detailed Verification")
    
    # Step 1: Create User A and get recommendations
    print_section("STEP 1: User A gets recommendations")
    user_a = "collab_test_user_a"
    recs_a = get_recommendations(user_a)
    
    print_info(f"User A got {len(recs_a['recommendations'])} recommendations", indent=2)
    print_info("\nUser A's Top 3:", indent=2)
    for i, rec in enumerate(recs_a['recommendations'][:3], 1):
        print_info(f"{i}. {rec['assessment']['name']}", indent=4)
        print_info(f"   Collab Score: {rec['score_breakdown']['collaborative']:.2f}", indent=4)
    
    # Step 2: User A rates assessments
    print_section("STEP 2: User A rates 3 assessments highly")
    for i in range(3):
        assessment_id = recs_a['recommendations'][i]['assessment']['id']
        assessment_name = recs_a['recommendations'][i]['assessment']['name']
        print_info(f"⭐⭐⭐⭐⭐ Rating '{assessment_name}'", indent=2)
        submit_feedback(user_a, assessment_id, 5, {
            "features": recs_a['recommendations'][i].get('score_breakdown', {}),
            "predicted_score": recs_a['recommendations'][i]['total_score']
        })
        time.sleep(0.2)
    
    print_success("User A has established preferences")
    
    # Step 3: Create User B and get recommendations
    print_section("STEP 3: User B gets initial recommendations")
    user_b = "collab_test_user_b"
    recs_b_initial = get_recommendations(user_b)
    
    print_info(f"User B got {len(recs_b_initial['recommendations'])} recommendations", indent=2)
    print_info("\nUser B's Initial Top 3:", indent=2)
    for i, rec in enumerate(recs_b_initial['recommendations'][:3], 1):
        print_info(f"{i}. {rec['assessment']['name']}", indent=4)
        print_info(f"   Collab Score: {rec['score_breakdown']['collaborative']:.2f}", indent=4)
    
    # Step 4: User B rates SAME first assessment as User A
    print_section("STEP 4: User B rates the SAME assessment as User A")
    first_assessment_a = recs_a['recommendations'][0]['assessment']['id']
    first_name = recs_a['recommendations'][0]['assessment']['name']
    print_info(f"⭐⭐⭐⭐⭐ User B also rates '{first_name}' highly", indent=2)
    submit_feedback(user_b, first_assessment_a, 5)
    
    # Step 5: Check if similarities were computed
    print_section("STEP 5: Checking if item similarities were computed")
    time.sleep(1)
    
    insights = get_insights()
    cf_info = insights['collaborative_filtering']
    
    print_info(f"Users tracked: {cf_info['users_tracked']}", indent=2)
    print_info(f"Items with similarities: {cf_info['items_with_similarities']}", indent=2)
    print_info(f"CF Status: {cf_info['status']}", indent=2)
    print_info(f"Total interactions: {insights['metrics']['total_interactions']}", indent=2)
    
    # Step 6: User B gets NEW recommendations
    print_section("STEP 6: User B gets UPDATED recommendations")
    time.sleep(0.5)
    recs_b_updated = get_recommendations(user_b)
    
    print_info("\nUser B's Updated Top 5:", indent=2)
    found_collab = False
    for i, rec in enumerate(recs_b_updated['recommendations'][:5], 1):
        collab_score = rec['score_breakdown']['collaborative']
        name = rec['assessment']['name']
        
        status = ""
        if collab_score > 0:
            status = f" {Color.GREEN}🔥 COLLABORATIVE BOOST!{Color.END}"
            found_collab = True
        
        print_info(f"\n{i}. {name}{status}", indent=4)
        print_info(f"   Content: {rec['score_breakdown']['content']:.2f}", indent=4)
        print_info(f"   Collaborative: {collab_score:.2f}", indent=4)
        print_info(f"   Feedback: {rec['score_breakdown']['feedback']:.2f}", indent=4)
        print_info(f"   Popularity: {rec['score_breakdown']['popularity']:.2f}", indent=4)
        print_info(f"   Total Score: {rec['total_score']:.2f}", indent=4)
    
    # Step 7: Verify collaborative filtering worked
    print_section("STEP 7: Verification Results")
    
    if cf_info['status'] == 'active':
        print_success("Collaborative Filtering Status: ACTIVE")
    else:
        print_warning(f"CF Status: {cf_info['status']}")
    
    if cf_info['items_with_similarities'] > 0:
        print_success(f"Item similarities computed: {cf_info['items_with_similarities']} items")
    else:
        print_warning("No item similarities computed yet")
    
    if found_collab:
        print_success("Collaborative scores > 0 found in recommendations!")
    else:
        print_warning("No collaborative scores > 0 yet")
        print_info("\nPossible reasons:", indent=2)
        print_info("1. Need more interactions (try running again)", indent=4)
        print_info("2. Similarities not computed yet (check thresholds)", indent=4)
        print_info("3. Users haven't interacted with enough common items", indent=4)
    
    # Step 8: Create more users to strengthen collaborative filtering
    print_section("STEP 8: Creating more users for stronger CF signal")
    
    for i in range(3):
        user_id = f"collab_test_user_{chr(67+i)}"  # C, D, E
        print_info(f"\nUser {chr(67+i)}:", indent=2)
        
        recs = get_recommendations(user_id)
        
        for j in range(2):
            assessment_id = recs['recommendations'][j]['assessment']['id']
            submit_feedback(user_id, assessment_id, 4 + (i % 2))
            print_info(f"  Rated: {recs['recommendations'][j]['assessment']['name']}", indent=4)
        
        time.sleep(0.3)
    
    # Final check
    print_section("FINAL CHECK: User B's recommendations after more CF data")
    time.sleep(1)
    
    recs_b_final = get_recommendations(user_b)
    insights_final = get_insights()
    
    print_info(f"\nCF Status: {insights_final['collaborative_filtering']['status']}", indent=2)
    print_info(f"Total users: {insights_final['metrics']['unique_users']}", indent=2)
    print_info(f"Total feedback: {insights_final['metrics']['total_feedback']}", indent=2)
    print_info(f"Items with similarities: {insights_final['collaborative_filtering']['items_with_similarities']}", indent=2)
    
    print_info(f"\nUser B's Final Top 3:", indent=2)
    max_collab = 0
    for i, rec in enumerate(recs_b_final['recommendations'][:3], 1):
        collab_score = rec['score_breakdown']['collaborative']
        max_collab = max(max_collab, collab_score)
        
        print_info(f"\n{i}. {rec['assessment']['name']}", indent=4)
        print_info(f"   Collaborative: {collab_score:.2f}", indent=4)
        print_info(f"   Total: {rec['total_score']:.2f}", indent=4)
    
    print_section("="*80)
    if max_collab > 0:
        print_success(f"🎉 SUCCESS! Collaborative filtering is working! Max score: {max_collab:.2f}")
    else:
        print_warning("⚠️  Collaborative scores still at 0")
        print_info("\nDebug info:", indent=2)
        print_info(f"Total interactions: {insights_final['metrics']['total_interactions']}", indent=4)
        print_info(f"Need at least 2 users with overlapping interactions", indent=4)
        print_info(f"Current users tracked: {insights_final['collaborative_filtering']['users_tracked']}", indent=4)


def test_diverse_users():
    """Test 5: Multiple users with different preferences"""
    print_header("TEST 5: Diverse User Base")
    
    users = [
        ("user_manager_1", "Manager Sarah", "Manager", "Mid-Level", "Development"),
        ("user_exec_1", "Executive John", "Executive", "Senior", "Development"),
        ("user_analyst_1", "Analyst Emma", "Analyst", "Graduate", "Hiring"),
    ]
    
    print_section("Creating diverse user profiles")
    
    for user_id, name, role, level, goal in users:
        print_info(f"\n{name} ({role}, {level}, {goal}):", indent=2)
        recs = get_recommendations(user_id, role=role, level=level, goal=goal)
        
        top = recs['recommendations'][0]
        print_info(f"  Top: {top['assessment']['name']} ({top['match_percentage']}% match)", indent=4)
        
        rating = 4 if "Manager" in name else 5
        submit_feedback(user_id, top['assessment']['id'], rating)
        print_info(f"  Rated: {rating}⭐", indent=4)
        time.sleep(0.2)


def test_system_insights():
    """Test 6: Check system insights"""
    print_header("TEST 6: System Insights & Metrics")
    
    insights = get_insights()
    
    print_section("Overall Metrics")
    metrics = insights['metrics']
    print_info(f"Total Recommendations: {metrics['total_recommendations']}", indent=2)
    print_info(f"Unique Users: {metrics['unique_users']}", indent=2)
    print_info(f"Total Interactions: {metrics['total_interactions']}", indent=2)
    print_info(f"Total Feedback: {metrics['total_feedback']}", indent=2)
    print_info(f"Average Rating: {metrics['avg_rating']:.2f}⭐", indent=2)
    print_info(f"Model Updates: {metrics['model_updates']}", indent=2)
    
    print_section("Collaborative Filtering Status")
    cf = insights['collaborative_filtering']
    print_info(f"Users Tracked: {cf['users_tracked']}", indent=2)
    print_info(f"Items with Similarities: {cf['items_with_similarities']}", indent=2)
    
    status = cf['status']
    status_color = Color.GREEN if status == 'active' else Color.YELLOW
    print_info(f"Status: {status_color}{status.upper()}{Color.END}", indent=2)
    
    print_section("Feature Weights (Learned)")
    weights = insights['feature_weights']
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    for feature, weight in sorted_weights:
        bar_length = int(weight * 2)
        bar = '█' * bar_length
        print_info(f"{feature:.<25} {weight:.3f} {Color.BLUE}{bar}{Color.END}", indent=2)
    
    print_section("Model Information")
    model_info = insights['model_info']
    print_info(f"Embedding Method: {model_info['embedding_method']}", indent=2)
    print_info(f"Embeddings Count: {model_info['embeddings_count']}", indent=2)
    print_info(f"Popular Items: {model_info['popular_items']}", indent=2)


def test_feedback_impact():
    """Test 7: Show how feedback affects future recommendations"""
    print_header("TEST 7: Feedback Impact Analysis")
    
    user_id = "test_feedback_user"
    
    print_section("Baseline Recommendations")
    initial_recs = get_recommendations(user_id)
    baseline = initial_recs['recommendations'][2]
    
    print_info(f"Target Assessment: {baseline['assessment']['name']}", indent=2)
    print_info(f"Initial Score: {baseline['total_score']:.2f}", indent=2)
    print_score_breakdown(baseline['score_breakdown'])
    
    print_section("Submitting high ratings for similar assessments")
    for i in [0, 1]:
        submit_feedback(user_id, initial_recs['recommendations'][i]['assessment']['id'], 5)
        print_info(f"  Rated '{initial_recs['recommendations'][i]['assessment']['name']}' → 5⭐", indent=2)
        time.sleep(0.1)
    
    print_section("Updated Recommendations")
    time.sleep(0.5)
    new_recs = get_recommendations(user_id)
    
    updated = next((r for r in new_recs['recommendations'] 
                   if r['assessment']['id'] == baseline['assessment']['id']), None)
    
    if updated:
        print_info(f"Target Assessment: {updated['assessment']['name']}", indent=2)
        print_info(f"New Score: {updated['total_score']:.2f}", indent=2)
        score_change = updated['total_score'] - baseline['total_score']
        
        if score_change > 0:
            print_info(f"Score Change: {Color.GREEN}+{score_change:.2f} ↗{Color.END}", indent=2)
        else:
            print_info(f"Score Change: {Color.RED}{score_change:.2f} ↘{Color.END}", indent=2)
        
        print_score_breakdown(updated['score_breakdown'])


def run_all_tests():
    """Run complete comprehensive test suite"""
    print_header("🚀 SHL ASSESSMENT RECOMMENDER - COMPREHENSIVE TEST SUITE 🚀")
    
    print_info(f"\n{Color.CYAN}{Color.BOLD}💡 TO VIEW RESULTS IN UI:{Color.END}", indent=0)
    print_info(f"   1. Open {Color.GREEN}http://127.0.0.1:5000{Color.END} in your browser", indent=0)
    print_info(f"   2. Enter User ID: {Color.YELLOW}test_alice_123{Color.END} or {Color.YELLOW}test_bob_456{Color.END}", indent=0)
    print_info(f"   3. Click 'Get Recommendations' to see their data", indent=0)
    print_info(f"   4. Or leave User ID blank for a fresh session\n", indent=0)
    
    try:
        # Test 1: Cold Start
        print_info("Starting comprehensive test suite...", indent=0)
        alice_recs = test_new_user_cold_start("test_alice_123", "Alice")
        time.sleep(0.5)
        
        bob_recs = test_new_user_cold_start("test_bob_456", "Bob")
        time.sleep(0.5)
        
        # Test 2: Feedback Loop
        test_feedback_loop("test_alice_123", "Alice", alice_recs)
        time.sleep(0.5)
        
        # Test 3: Interactions
        test_interactions("test_bob_456", "Bob", bob_recs)
        time.sleep(0.5)
        
        # Test 4: Detailed Collaborative Filtering
        test_collaborative_filtering_detailed()
        time.sleep(0.5)
        
        # Test 5: Diverse Users
        test_diverse_users()
        time.sleep(0.5)
        
        # Test 6: System Insights
        test_system_insights()
        time.sleep(0.5)
        
        # Test 7: Feedback Impact
        test_feedback_impact()
        
        # Final Summary
        print_header("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        insights = get_insights()
        
        print_section("Final System Status")
        print_success(f"Total recommendations processed: {insights['metrics']['total_recommendations']}")
        print_success(f"Total feedback collected: {insights['metrics']['total_feedback']}")
        print_success(f"Unique users tracked: {insights['metrics']['unique_users']}")
        print_success(f"Average rating: {insights['metrics']['avg_rating']:.2f}⭐")
        
        cf_status = insights['collaborative_filtering']['status']
        if cf_status == 'active':
            print_success(f"Collaborative filtering: {Color.GREEN}{Color.BOLD}ACTIVE{Color.END}")
            print_success(f"Items with similarities: {insights['collaborative_filtering']['items_with_similarities']}")
        else:
            print_warning(f"Collaborative filtering status: {cf_status}")
        
        print_info("\n" + "="*80, indent=0)
        print_info(f"{Color.GREEN}🎉 Test suite completed! System is functioning correctly.{Color.END}", indent=0)
        print_info("="*80, indent=0)
        
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {BASE_URL}")
        print_info("Make sure the Flask server is running!", indent=2)
    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()