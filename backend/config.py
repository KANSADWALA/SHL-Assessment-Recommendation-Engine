import os
from dotenv import load_dotenv

load_dotenv()

# Determine base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    """Application configuration container.

    Loads configuration values from environment variables with sensible
    defaults. Values are used by the Flask app and recommender internals.
    """
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    MAX_USERS = int(os.getenv('MAX_USERS', 1000))
    MAX_FEEDBACK = int(os.getenv('MAX_FEEDBACK', 5000))
    USER_TTL_DAYS = int(os.getenv('USER_TTL_DAYS', 30))
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'recommender.db')
    LEARNING_RATE = float(os.getenv('LEARNING_RATE', 0.01))
    TFIDF_MAX_FEATURES = int(os.getenv('TFIDF_MAX_FEATURES', 500))


# Comprehensive Assessment Database from SHL
ASSESSMENTS = [
    {
        "id": 1,
        "name": "SHL Occupational Personality Questionnaire (OPQ)",
        "category": "Personality Assessment",
        "description": "Align individual working preferences to business requirements with accurate, fair assessments of potential",
        "detailed_info": "The OPQ is SHL's flagship personality assessment, widely used to predict workplace behavior. Measures 32 personality dimensions.",
        "use_cases": ["Recruitment & Selection", "Team Building", "Development", "Succession Planning", "Transitions"],
        "benefits": [
            "Predicts workplace behavior patterns",
            "Science-backed with strong predictive accuracy",
            "Assesses remote work capability",
            "Reduces turnover by 25%",
            "Available in 40+ languages"
        ],
        "suitable_for": {
            "roles": ["Manager", "Professional", "Graduate", "Executive", "Sales", "Technical"],
            "levels": ["Entry", "Mid", "Senior", "Executive"],
            "industries": ["All Industries", "Technology", "Finance", "Healthcare", "Retail", "Manufacturing"],
            "goals": ["Quality of Hire", "Cultural Fit", "Team Performance", "Leadership Development", "Retention"]
        },
        "key_features": [
            "32 personality dimensions",
            "Mobile-first design",
            "Multiple automated reports",
            "Global normative data",
            "15-25 minute completion"
        ],
        "metrics": {
            "completion_time": "15-25 minutes",
            "validity": "High predictive validity",
            "reliability": "0.80+ reliability coefficient",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/personality-assessment/shl-occupational-personality-questionnaire-opq/"
    },
    {
        "id": 2,
        "name": "SHL Verify Interactive - Cognitive Assessment",
        "category": "Cognitive Assessment",
        "description": "Measure candidates' potential to learn, adapt, and perform with interactive cognitive assessments",
        "detailed_info": "Interactive cognitive assessment measuring numerical reasoning, deductive reasoning, and inductive reasoning with engaging drag-and-drop interactions.",
        "use_cases": ["Graduate Hiring", "Technology Hiring", "Manager Development", "High Volume Hiring", "Professional Roles"],
        "benefits": [
            "Automated scoring and proctoring",
            "60% reduction in time-to-hire",
            "Engaging gamified experience",
            "Fewer questions with partial scoring",
            "Predicts learning potential"
        ],
        "suitable_for": {
            "roles": ["Graduate", "Technology", "Professional", "Manager", "Analyst", "Engineer"],
            "levels": ["Entry", "Mid", "Senior"],
            "industries": ["Technology", "Finance", "Healthcare", "Manufacturing", "Consulting", "All Industries"],
            "goals": ["Learning Potential", "Problem Solving", "Quality of Hire", "Adaptability", "Critical Thinking"]
        },
        "key_features": [
            "Verify G+ (General Mental Ability)",
            "Numerical Reasoning",
            "Deductive Reasoning",
            "Inductive Reasoning",
            "Interactive drag-and-drop",
            "Remote proctoring"
        ],
        "metrics": {
            "completion_time": "10-30 minutes",
            "validity": "Strong criterion validity",
            "reliability": "0.85+ reliability",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/cognitive-assessments/"
    },
    {
        "id": 3,
        "name": "Situational Judgment Tests (SJT)",
        "category": "Behavioral Assessment",
        "description": "Match candidate behavioral fit with immersive, interactive scenarios and effective screening at scale",
        "detailed_info": "Interactive scenarios that evaluate how candidates would handle real workplace situations, measuring behavioral fit and judgment.",
        "use_cases": ["Early Stage Screening", "Behavioral Fit", "Volume Hiring", "Graduate Programs", "Customer Service"],
        "benefits": [
            "Reduces mis-hires by 40%",
            "Increases candidate engagement",
            "Interactive video-based scenarios",
            "Scalable for high volume",
            "89% candidate satisfaction"
        ],
        "suitable_for": {
            "roles": ["Customer Service", "Sales", "Manager", "Graduate", "Professional", "Contact Center"],
            "levels": ["Entry", "Mid"],
            "industries": ["Retail", "BPO", "Contact Center", "Healthcare", "Finance", "All Industries"],
            "goals": ["Behavioral Fit", "Cultural Alignment", "Customer Service", "Decision Making", "Teamwork"]
        },
        "key_features": [
            "Video-based scenarios",
            "Real workplace situations",
            "Match score reporting",
            "Mobile optimized",
            "5-15 minute completion"
        ],
        "metrics": {
            "completion_time": "5-15 minutes",
            "validity": "High construct validity",
            "reliability": "0.75+ reliability",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/behavioral-assessments/situation-judgement-tests-sjt/"
    },
    {
        "id": 4,
        "name": "Realistic Job Previews (RJP)",
        "category": "Behavioral Assessment",
        "description": "Preview roles with scenario-based quizzes that give candidates a feel for the job before they commit",
        "detailed_info": "Interactive previews that showcase your opportunities with animation, video, and branded multimedia to increase self-selection and commitment.",
        "use_cases": ["Early Attraction", "Self-Selection", "Employer Branding", "Volume Hiring", "Reduce Attrition"],
        "benefits": [
            "Increases commitment by 30%",
            "Reduces early attrition",
            "Branded candidate experience",
            "Sets realistic expectations",
            "Improves quality of applicant pool"
        ],
        "suitable_for": {
            "roles": ["All Roles", "Entry Level", "Contact Center", "Retail", "Graduate", "Volume"],
            "levels": ["Entry", "Mid"],
            "industries": ["Retail", "BPO", "Contact Center", "Hospitality", "Manufacturing", "All Industries"],
            "goals": ["Candidate Engagement", "Self-Selection", "Reduce Attrition", "Employer Brand", "Cultural Fit"]
        },
        "key_features": [
            "Customizable scenarios",
            "Multimedia content",
            "Brand integration",
            "Mobile-first",
            "10-15 minute experience"
        ],
        "metrics": {
            "completion_time": "10-15 minutes",
            "impact": "30% increase in commitment",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/behavioral-assessments/realistic-job-and-culture-previews-rjp/"
    },
    {
        "id": 5,
        "name": "SHL Motivational Questionnaire (MQ)",
        "category": "Personality Assessment",
        "description": "Match individual motivation to team and organizational goals to build an engaged, high-performing workforce",
        "detailed_info": "Measures what drives and energizes individuals at work across 18 motivational dimensions aligned to organizational goals.",
        "use_cases": ["Employee Engagement", "Team Building", "Development", "Retention", "Career Planning"],
        "benefits": [
            "Identifies motivational drivers",
            "Improves engagement by 35%",
            "Predicts retention",
            "Enables personalized development",
            "Supports career conversations"
        ],
        "suitable_for": {
            "roles": ["All Roles", "Manager", "Professional", "Graduate", "Sales"],
            "levels": ["Entry", "Mid", "Senior"],
            "industries": ["All Industries", "Technology", "Finance", "Healthcare", "Retail"],
            "goals": ["Employee Engagement", "Retention", "Development", "Team Performance", "Career Development"]
        },
        "key_features": [
            "18 motivational dimensions",
            "Team motivation reports",
            "Development recommendations",
            "Mobile accessible",
            "15-20 minute completion"
        ],
        "metrics": {
            "completion_time": "15-20 minutes",
            "validity": "High predictive validity for engagement",
            "reliability": "0.80+ reliability",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/personality-assessment/shl-motivation-questionnaire-mq/"
    },
    {
        "id": 6,
        "name": "Job-Focused Assessments (JFA)",
        "category": "Skills Assessment",
        "description": "Comprehensive role-specific assessments measuring job-relevant hard and soft skills",
        "detailed_info": "Predicts job success by evaluating key competencies tailored to specific roles using patented Apta technology.",
        "use_cases": ["Role-Specific Hiring", "Skills-Based Selection", "Fair Hiring", "Volume Hiring", "Frontline Roles"],
        "benefits": [
            "40% less likely to hire tardy workers",
            "73% better customer handling",
            "Reduces bias in selection",
            "Job-relevant content",
            "Fast deployment"
        ],
        "suitable_for": {
            "roles": ["Contact Center", "Retail", "Manufacturing", "Sales", "Professional", "Manager"],
            "levels": ["Entry", "Mid"],
            "industries": ["Retail", "Contact Center", "Manufacturing", "Industrial", "BPO", "All Industries"],
            "goals": ["Job Performance", "Quality of Hire", "Fair Selection", "Customer Service", "Productivity"]
        },
        "key_features": [
            "Patented Apta technology",
            "Role-specific competencies",
            "Hard and soft skills",
            "Pre-packaged assessments",
            "Reduces faking"
        ],
        "metrics": {
            "completion_time": "20-30 minutes",
            "validity": "Strong job performance prediction",
            "reliability": "0.80+ reliability",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/job-focused-assessments/"
    },
    {
        "id": 7,
        "name": "Coding Simulations",
        "category": "Skills & Simulations",
        "description": "AI-powered online coding simulations measuring accuracy, logical correctness, and technical capability",
        "detailed_info": "Assess tech candidates with real IDE environments covering 30+ programming languages and frameworks.",
        "use_cases": ["Technology Hiring", "Developer Assessment", "Technical Screening", "Graduate Tech Programs"],
        "benefits": [
            "Real coding environment",
            "AI-powered evaluation",
            "30+ languages supported",
            "Automated scoring",
            "Measures coding quality"
        ],
        "suitable_for": {
            "roles": ["Software Developer", "Engineer", "Data Scientist", "DevOps", "Technical Roles"],
            "levels": ["Entry", "Mid", "Senior"],
            "industries": ["Technology", "Finance", "Consulting", "Startups", "All Industries"],
            "goals": ["Technical Skills", "Code Quality", "Problem Solving", "Technical Fit"]
        },
        "key_features": [
            "Integrated Development Environment",
            "30+ programming languages",
            "AI-powered scoring",
            "Real-world problems",
            "Plagiarism detection"
        ],
        "metrics": {
            "completion_time": "30-90 minutes",
            "validity": "High technical validity",
            "mobile_friendly": False
        },
        "link": "https://www.shl.com/products/assessments/skills-and-simulations/coding-simulations/"
    },
    {
        "id": 8,
        "name": "Technical Skills Assessments",
        "category": "Skills & Simulations",
        "description": "Comprehensive evaluation of technical concepts, knowledge, and application across 200+ IT skills",
        "detailed_info": "Expert-validated questions covering databases, cloud, networking, cybersecurity, and more.",
        "use_cases": ["IT Hiring", "Technical Screening", "Skills Validation", "Upskilling Assessment"],
        "benefits": [
            "200+ IT skills covered",
            "Expert-validated content",
            "Automated proctoring",
            "Scalable assessment",
            "Current technology stack"
        ],
        "suitable_for": {
            "roles": ["IT Professional", "System Admin", "Network Engineer", "Cloud Architect", "Security Analyst"],
            "levels": ["Entry", "Mid", "Senior"],
            "industries": ["Technology", "Finance", "Healthcare", "Manufacturing", "All Industries"],
            "goals": ["Technical Skills", "Knowledge Validation", "Certification", "Upskilling"]
        },
        "key_features": [
            "200+ specific IT skills",
            "Cloud technologies",
            "Database expertise",
            "Cybersecurity",
            "Network administration"
        ],
        "metrics": {
            "completion_time": "20-45 minutes",
            "validity": "Expert-validated content",
            "reliability": "0.80+ reliability",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/skills-and-simulations/technical-skills/"
    },
    {
        "id": 9,
        "name": "Language Evaluation",
        "category": "Skills & Simulations",
        "description": "AI-powered language assessments to build a strong, multilingual workforce",
        "detailed_info": "Measures speaking, writing, reading, and listening proficiency in multiple languages with AI evaluation.",
        "use_cases": ["Multilingual Roles", "Customer Service", "Global Teams", "BPO Hiring"],
        "benefits": [
            "AI-powered scoring",
            "Multiple languages",
            "Speaking assessment",
            "Writing evaluation",
            "Fast results"
        ],
        "suitable_for": {
            "roles": ["Customer Service", "Sales", "Contact Center", "Translator", "Global Roles"],
            "levels": ["Entry", "Mid", "Senior"],
            "industries": ["BPO", "Contact Center", "Hospitality", "Airlines", "Global Companies"],
            "goals": ["Communication Skills", "Language Proficiency", "Customer Service", "Global Readiness"]
        },
        "key_features": [
            "AI speech recognition",
            "Writing assessment",
            "Multiple languages",
            "CEFR alignment",
            "Automated scoring"
        ],
        "metrics": {
            "completion_time": "15-30 minutes",
            "validity": "CEFR-aligned",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/skills-and-simulations/language-evaluation/"
    },
    {
        "id": 10,
        "name": "Contact Center Simulations",
        "category": "Skills & Simulations",
        "description": "Job simulations that emulate a real call center environment to pressure-test agent capability",
        "detailed_info": "Realistic scenarios including customer calls, email responses, and chat interactions to assess readiness.",
        "use_cases": ["Contact Center Hiring", "Customer Service", "BPO Selection", "Agent Assessment"],
        "benefits": [
            "Realistic job preview",
            "Multi-channel assessment",
            "Reduces training time",
            "Predicts performance",
            "Engaging experience"
        ],
        "suitable_for": {
            "roles": ["Contact Center Agent", "Customer Service Rep", "Technical Support", "BPO Agent"],
            "levels": ["Entry", "Mid"],
            "industries": ["BPO", "Contact Center", "Telecommunications", "E-commerce", "Financial Services"],
            "goals": ["Customer Service", "Communication Skills", "Problem Solving", "Multi-tasking"]
        },
        "key_features": [
            "Call simulations",
            "Email handling",
            "Chat scenarios",
            "Multi-tasking assessment",
            "Customer empathy"
        ],
        "metrics": {
            "completion_time": "20-35 minutes",
            "validity": "High job simulation fidelity",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/skills-and-simulations/call-center-simulations/"
    },
    {
        "id": 11,
        "name": "Business Skills Assessments",
        "category": "Skills & Simulations",
        "description": "Assess essential business skills and computer literacy for enterprise teams",
        "detailed_info": "Evaluates Microsoft Office proficiency, business communication, data analysis, and digital literacy.",
        "use_cases": ["Office Roles", "Administrative Hiring", "Graduate Programs", "Digital Literacy"],
        "benefits": [
            "Microsoft Office assessment",
            "Business communication",
            "Data analysis skills",
            "Digital literacy",
            "Practical application"
        ],
        "suitable_for": {
            "roles": ["Administrative", "Analyst", "Coordinator", "Graduate", "Professional"],
            "levels": ["Entry", "Mid"],
            "industries": ["All Industries", "Corporate", "Finance", "Healthcare", "Consulting"],
            "goals": ["Computer Literacy", "Business Skills", "Productivity", "Communication"]
        },
        "key_features": [
            "MS Office (Word, Excel, PowerPoint)",
            "Email etiquette",
            "Data interpretation",
            "Business writing",
            "Practical simulations"
        ],
        "metrics": {
            "completion_time": "15-40 minutes",
            "validity": "Job-relevant content",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/skills-and-simulations/business-skills/"
    },
    {
        "id": 12,
        "name": "Virtual Assessment & Development Centers",
        "category": "Assessment Centers",
        "description": "End-to-end digital assessment and development centers for identifying potential from anywhere",
        "detailed_info": "Comprehensive multi-method assessment including exercises, simulations, interviews, and psychometrics.",
        "use_cases": ["Senior Hiring", "Leadership Assessment", "Development Centers", "Graduate Assessment"],
        "benefits": [
            "60% faster time-to-hire",
            "75% reduction in assessment time",
            "Comprehensive evaluation",
            "Remote capability",
            "Expert facilitators"
        ],
        "suitable_for": {
            "roles": ["Manager", "Senior Manager", "Executive", "Graduate", "High Potential"],
            "levels": ["Mid", "Senior", "Executive"],
            "industries": ["All Industries", "Finance", "Corporate", "Government", "Healthcare"],
            "goals": ["Leadership Assessment", "Comprehensive Evaluation", "Development", "Succession"]
        },
        "key_features": [
            "Group exercises",
            "Role-play simulations",
            "Presentations",
            "Psychometric tests",
            "Expert assessment"
        ],
        "metrics": {
            "completion_time": "Half day to 2 days",
            "validity": "Multi-method validation",
            "mobile_friendly": True
        },
        "link": "https://www.shl.com/products/assessments/assessment-and-development-centers/"
    }
]