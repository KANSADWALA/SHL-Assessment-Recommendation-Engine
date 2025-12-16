// Global state
let currentUserId = null;
let currentAssessmentId = null;
let currentRating = 0;
let lastRecommendations = [];

// Star rating interaction
document.querySelectorAll('.star').forEach(star => {
    star.addEventListener('click', function() {
        currentRating = parseInt(this.dataset.rating);
        document.querySelectorAll('.star').forEach((s, i) => {
            s.classList.toggle('active', i < currentRating);
        });
    });
});

// Get recommendations
async function getRecommendations() {
    const role = document.getElementById('role').value;
    const level = document.getElementById('level').value;
    const industry = document.getElementById('industry').value;
    const goal = document.getElementById('goal').value;
    const query = document.getElementById('query').value;
    const userId = document.getElementById('userId').value.trim();

    document.querySelector('.loading').style.display = 'block';
    document.querySelector('.results').style.display = 'none';

    try {
        const requestBody = { role, level, industry, goal, query };
        if (userId) {
            requestBody.user_id = userId;
        }
        
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        
        // DEBUG: Log the response
        console.log('=== DEBUG: Recommendation Data ===');
        console.log('Full response:', data);
        console.log('First recommendation:', data.recommendations?.[0]);
        console.log('Score breakdown:', data.recommendations?.[0]?.score_breakdown);
        console.log('Content:', data.recommendations?.[0]?.score_breakdown?.content);
        console.log('Collaborative:', data.recommendations?.[0]?.score_breakdown?.collaborative);
        console.log('Feedback:', data.recommendations?.[0]?.score_breakdown?.feedback);
        console.log('Popularity:', data.recommendations?.[0]?.score_breakdown?.popularity);
        console.log('================================');
        
        if (data.status === 'success') {
            currentUserId = data.user_id;
            lastRecommendations = data.recommendations;
            displayResults(data.recommendations);
        }
    } catch (error) {
        alert('Error getting recommendations: ' + error.message);
    } finally {
        document.querySelector('.loading').style.display = 'none';
    }
}

// Display recommendations
function displayResults(recommendations) {
    const resultsDiv = document.querySelector('.results');
    resultsDiv.innerHTML = '<h2 style="margin-bottom: 20px;">✨ Top Recommendations</h2>';

    recommendations.forEach((rec, index) => {
        const a = rec.assessment;
        const scores = rec.score_breakdown || {};
        
        // Helper to format scores with color coding
        const formatScore = (value) => {
            const val = (value || 0).toFixed(2);
            const color = value > 0 ? '#28a745' : '#6c757d';
            const weight = value > 0 ? 'bold' : 'normal';
            return `<span style="color: ${color}; font-weight: ${weight}">${val}</span>`;
        };
        
        // Calculate what percentage each component contributes
        const totalBreakdown = scores.content + scores.collaborative + scores.feedback + scores.popularity;
        const getPercentage = (value) => {
            if (totalBreakdown === 0) return 0;
            return ((value / totalBreakdown) * 100).toFixed(0);
        };
        
        const card = `
            <div class="result-card">
                <div class="result-header">
                    <div class="result-title">${index + 1}. ${a.name}</div>
                    <div class="match-badge">${rec.match_percentage}% Match</div>
                </div>
                <div>
                    <span class="category-badge">${a.category}</span>
                    ${rec.is_new_user ? '<span class="category-badge" style="background: #fff3cd; color: #856404;">🆕 New User</span>' : '<span class="category-badge" style="background: #d1ecf1; color: #0c5460;">🔁 Returning</span>'}
                </div>
                <div class="description">${a.description}</div>
                <div class="features">
                    ${a.key_features.slice(0, 5).map(f => `<span class="feature-tag">${f}</span>`).join('')}
                </div>
                
                <div style="margin-top: 15px; margin-bottom: 10px;">
                    <strong style="font-size: 0.95em;">📊 Score Breakdown</strong>
                    <div style="font-size: 0.85em; color: #6c757d; margin-top: 4px;">
                        How this recommendation was calculated:
                    </div>
                </div>
                
                <div class="score-breakdown">
                    <div class="score-item">
                        <div class="score-label">
                            📄 Content Match
                            <div style="font-size: 0.75em; color: #6c757d;">Role, goals & semantic fit</div>
                        </div>
                        <div class="score-value">
                            ${formatScore(scores.content)}
                            ${scores.content > 0 ? `<span style="font-size: 0.8em; color: #6c757d;">(${getPercentage(scores.content)}%)</span>` : ''}
                        </div>
                    </div>
                    <div class="score-item">
                        <div class="score-label">
                            🤝 Collaborative
                            <div style="font-size: 0.75em; color: #6c757d;">${scores.collaborative > 0 ? 'Similar users liked this' : 'Building profile...'}</div>
                        </div>
                        <div class="score-value">
                            ${formatScore(scores.collaborative)}
                            ${scores.collaborative > 0 ? `<span style="font-size: 0.8em; color: #6c757d;">(${getPercentage(scores.collaborative)}%)</span>` : ''}
                        </div>
                    </div>
                    <div class="score-item">
                        <div class="score-label">
                            💬 Feedback Score
                            <div style="font-size: 0.75em; color: #6c757d;">${scores.feedback > 0 ? 'Highly rated by others' : scores.feedback < 0 ? 'Lower ratings' : 'No ratings yet'}</div>
                        </div>
                        <div class="score-value">
                            ${formatScore(scores.feedback)}
                            ${scores.feedback !== 0 ? `<span style="font-size: 0.8em; color: #6c757d;">(${getPercentage(Math.abs(scores.feedback))}%)</span>` : ''}
                        </div>
                    </div>
                    <div class="score-item">
                        <div class="score-label">
                            🔥 Popularity
                            <div style="font-size: 0.75em; color: #6c757d;">${scores.popularity > 0 ? 'Trending choice' : 'Standard item'}</div>
                        </div>
                        <div class="score-value">
                            ${formatScore(scores.popularity)}
                            ${scores.popularity > 0 ? `<span style="font-size: 0.8em; color: #6c757d;">(${getPercentage(scores.popularity)}%)</span>` : ''}
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 12px; padding: 8px 12px; background: #f1f3f9; border-radius: 6px; font-size: 0.9em; font-weight: 600; color: #333; display: inline-block;">
                    Total Weighted Score: ${rec.total_score.toFixed(2)}
                </div>
                
                ${rec.is_new_user ? `
                <div style="margin-top: 10px; padding: 8px; background: #fff3cd; border-left: 3px solid #ffc107; border-radius: 4px; font-size: 0.85em;">
                    <strong>💡 New User:</strong> Recommendations will improve as you interact and rate assessments!
                </div>
                ` : ''}
                
                <div class="actions">
                    <button class="btn btn-primary btn-small" onclick="openRatingModal('${a.id}', ${rec.total_score})">⭐ Rate This</button>
                    <button class="btn btn-secondary btn-small"
                            onclick="recordInteraction('${a.id}', 'click'); this.innerText='✓ Selected'; this.disabled=true;">
                        👆 Select
                    </button>

                    <a href="${a.link}" target="_blank" class="btn btn-secondary btn-small" 
                    style="text-decoration: none;">🔗 Learn More</a>
                </div>
            </div>
        `;
        resultsDiv.innerHTML += card;
    });

    resultsDiv.style.display = 'block';
}

// Rating modal functions
function openRatingModal(assessmentId, score) {
    currentAssessmentId = assessmentId;
    currentRating = 0;
    document.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
    
    const modal = document.getElementById('ratingModal');
    modal.style.display = 'flex';
    
    // Store context for learning
    const rec = lastRecommendations.find(r => r.assessment.id === assessmentId);
    modal.dataset.context = JSON.stringify({
        predicted_score: score,
        features: rec.score_breakdown
    });
}

// Close rating modal
function closeRatingModal() {
    document.getElementById('ratingModal').style.display = 'none';
}

// Submit rating
async function submitRating() {
    if (currentRating === 0) {
        alert('Please select a rating');
        return;
    }

    const modal = document.getElementById('ratingModal');
    const context = JSON.parse(modal.dataset.context || '{}');

    try {
        await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                assessment_id: currentAssessmentId,
                rating: currentRating,
                context: context
            })
        });

        alert('Thank you for your feedback! This helps improve recommendations.');
        closeRatingModal();
    } catch (error) {
        alert('Error submitting feedback: ' + error.message);
    }
}

// Record interaction
async function recordInteraction(assessmentId, type) {
    try {
        await fetch('/api/interaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                assessment_id: assessmentId,
                interaction_type: type
            })
        });
    } catch (error) {
        console.error('Interaction error:', error);
    }
}

// Show insights
async function showInsights() {
    try {
        const response = await fetch('/api/insights');
        const data = await response.json();
        
        if (data.status === 'success') {
            const section = document.querySelector('.insights-section');
            const grid = section.querySelector('.insights-grid');
            
            const insights = data.insights;
            grid.innerHTML = `
                <div class="insight-card">
                    <div class="insight-value">${insights.metrics.total_recommendations}</div>
                    <div class="insight-label">Total Recommendations</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${insights.metrics.unique_users}</div>
                    <div class="insight-label">Unique Users</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${insights.metrics.total_feedback}</div>
                    <div class="insight-label">Feedback Items</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${insights.metrics.avg_rating.toFixed(1)}⭐</div>
                    <div class="insight-label">Avg Rating</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${insights.metrics.model_updates}</div>
                    <div class="insight-label">Model Updates</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${insights.collaborative_filtering.status}</div>
                    <div class="insight-label">CF Status</div>
                </div>
            `;
            
            section.style.display = 'block';
            section.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        alert('Error loading insights: ' + error.message);
    }
}