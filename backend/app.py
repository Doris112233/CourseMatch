from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
import re
from datetime import datetime
import google.generativeai as genai

load_dotenv()

# Initialize Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Try available models in order of preference
    # Using aliases that automatically point to latest stable versions
    model_names = [
        'gemini-flash-latest',      # Alias to latest flash (fast, cost-effective)
        'gemini-2.5-flash',         # Stable flash model
        'gemini-2.0-flash',         # Alternative flash
        'gemini-pro-latest',        # Alias to latest pro (more capable)
        'gemini-2.5-pro',           # Stable pro model
        'gemini-2.0-pro-exp',       # Experimental pro
    ]
    
    gemini_model = None
    for model_name in model_names:
        try:
            gemini_model = genai.GenerativeModel(model_name)
            print(f"✓ Using Gemini model: {model_name}")
            break
        except Exception as e:
            continue
    
    if gemini_model is None:
        print("Error: Could not initialize any Gemini model.")
        print("Please check your API key and available models.")
else:
    gemini_model = None
    print("Warning: GEMINI_API_KEY not found. AI explanations will use fallback mode.")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Load data files
def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

COURSES = load_json(os.path.join(DATA_DIR, 'courses.json'))
PROFESSORS = load_json(os.path.join(DATA_DIR, 'professors.json'))
STUDENT_PROFILES = load_json(os.path.join(DATA_DIR, 'student_profiles.json'))
FEEDBACK = load_json(os.path.join(DATA_DIR, 'feedback.json'))

# Save feedback
def save_feedback():
    with open(os.path.join(DATA_DIR, 'feedback.json'), 'w') as f:
        json.dump(FEEDBACK, f, indent=2)

# Save student profiles
def save_student_profiles():
    with open(os.path.join(DATA_DIR, 'student_profiles.json'), 'w') as f:
        json.dump(STUDENT_PROFILES, f, indent=2)

# Save courses
def save_courses():
    with open(os.path.join(DATA_DIR, 'courses.json'), 'w') as f:
        json.dump(COURSES, f, indent=2)

# Course matching logic
def calculate_match_score_with_gemini(course, student_profile, query, query_intent):
    """Use Gemini to calculate intelligent match score based on semantic understanding"""
    if not gemini_model:
        # Fallback to rule-based scoring
        return calculate_match_score(course, student_profile, query_intent.get('keywords', []))
    
    try:
        # Build course context
        instructor = next((p for p in PROFESSORS if p['id'] == course.get('instructor')), None)
        instructor_info = ""
        if instructor:
            instructor_info = f"Instructor: {instructor.get('name', 'TBA')}, Rating: {instructor.get('rating', 'N/A')}, Background: {instructor.get('background', 'N/A')}"
        
        # Include syllabus content if available (more comprehensive)
        syllabus_info = ""
        syllabus_available = False
        if course.get('syllabus'):
            syllabus_available = True
            syllabus_full = course['syllabus']
            # Include more syllabus content for better analysis (up to 3000 chars)
            syllabus_info = f"""
Syllabus Content (available - use this for detailed analysis):
{syllabus_full[:3000]}{'...' if len(syllabus_full) > 3000 else ''}

Syllabus Topics: {', '.join(course.get('syllabusTopics', []))}
Syllabus Skills: {', '.join(course.get('syllabusSkills', []))}
"""
        
        course_context = f"""
Course: {course.get('title', 'N/A')} ({course.get('id', 'N/A')})
Department: {course.get('department', 'N/A')}
Description: {course.get('description', 'N/A')}
Keywords: {', '.join(course.get('keywords', []))}
Credits: {course.get('credits', 'N/A')}
Difficulty: {course.get('difficulty', 'N/A')}/5
Prerequisites: {', '.join(course.get('prerequisites', []))}
GenEd: {', '.join(course.get('gened', []))}
Career Relevance: {', '.join(course.get('careerRelevance', []))}
Schedule: {', '.join([s.get('time', '') for s in course.get('schedule', [])])}
{syllabus_info}
{instructor_info}
"""
        
        student_context = f"""
Student Profile:
- Major: {', '.join(student_profile.get('major', []))}
- Minor: {', '.join(student_profile.get('minor', []))}
- Career Goals: {', '.join(student_profile.get('careerGoals', []))}
- Interests: {', '.join(student_profile.get('interests', []))}
- Completed Courses: {', '.join(student_profile.get('completedCourses', []))}
- GPA: {student_profile.get('gpa', 'N/A')}
- Difficulty Preference: {student_profile.get('typicalDifficultyPreference', 3)}/5
- GenEd Remaining: {', '.join(student_profile.get('genedRemaining', []))}
"""
        
        # Build enhanced prompt with syllabus emphasis
        syllabus_instruction = ""
        if syllabus_available:
            syllabus_instruction = """
IMPORTANT: This course has a syllabus available. When providing match reasons, include specific insights from the syllabus content such as:
- Specific topics covered that align with the student's query
- Skills taught that match career goals
- Learning outcomes mentioned in the syllabus
- Course structure or teaching methods that fit the student's preferences
- Any specific requirements or focus areas mentioned in the syllabus
"""
        
        prompt = f"""You are an intelligent course recommendation system. Evaluate how well this course matches the student's query and profile.

Student Query: "{query}"

Query Intent:
{json.dumps(query_intent, indent=2)}

{student_context}

{course_context}
{syllabus_instruction}

Rate this course match on a scale of 0-100 and provide 2-4 specific, detailed reasons why it's a good or poor match.

Return a JSON object with:
{{
  "score": <number 0-100>,
  "reasons": ["reason1", "reason2", "reason3", "reason4"]
}}

Consider:
- Semantic relevance to the query (not just keyword matching)
- Career alignment
- Prerequisites and student readiness
- Difficulty match
- Schedule preferences
- Instructor quality
- GenEd requirements
- Overall fit with student goals
- If syllabus is available: specific topics, skills, learning outcomes, and course structure from the syllabus

When syllabus is available, make your reasons more specific and detailed by referencing actual syllabus content.

Return ONLY valid JSON, no additional text."""

        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        score = result.get('score', 0)
        reasons = result.get('reasons', [])
        
        return score, reasons
        
    except Exception as e:
        print(f"Error calculating match score with Gemini: {e}")
        # Fallback to rule-based
        return calculate_match_score(course, student_profile, query_intent.get('keywords', []))

def calculate_match_score(course, student_profile, query_keywords=None):
    """Calculate how well a course matches a student profile (rule-based fallback)"""
    score = 0
    reasons = []
    
    # Career relevance
    student_careers = student_profile.get('careerGoals', [])
    course_careers = course.get('careerRelevance', [])
    career_overlap = set(student_careers) & set(course_careers)
    if career_overlap:
        score += 30
        reason_text = f"Relevant for your {', '.join(career_overlap)} goals"
        
        # Add syllabus insights if available
        if course.get('syllabus') and course.get('syllabusSkills'):
            # Check if syllabus skills align with career goals
            syllabus_skills = course.get('syllabusSkills', [])
            career_related_skills = [s for s in syllabus_skills if any(career.lower() in s.lower() or s.lower() in career.lower() for career in career_overlap)]
            if career_related_skills:
                reason_text += f" (syllabus emphasizes skills: {', '.join(career_related_skills[:2])})"
        
        reasons.append(reason_text)
    
    # Keyword matching with query (including syllabus content and department codes)
    if query_keywords:
        course_keywords = ' '.join(course.get('keywords', [])).lower()
        course_text = (course.get('title', '') + ' ' + course.get('description', '')).lower()
        course_dept = course.get('department', '').lower()
        
        # Include syllabus content if available for better matching
        if course.get('syllabus'):
            syllabus_text = course.get('syllabus', '').lower()
            course_text += ' ' + syllabus_text[:2000]  # Include first 2000 chars of syllabus
        
        # Also check syllabus topics and skills if available
        if course.get('syllabusTopics'):
            course_text += ' ' + ' '.join(course.get('syllabusTopics', [])).lower()
        if course.get('syllabusSkills'):
            course_text += ' ' + ' '.join(course.get('syllabusSkills', [])).lower()
        
        matched_keywords = []
        matches = 0
        
        # Check each keyword
        for kw in query_keywords:
            kw_lower = kw.lower()
            # Check if keyword matches department code (exact or partial)
            if kw_lower == course_dept or course_dept.startswith(kw_lower) or kw_lower.startswith(course_dept):
                matches += 1
                matched_keywords.append(kw)
                score += 20  # Higher score for department match
            # Check if keyword is in course text
            elif kw_lower in course_text or kw_lower in course_keywords:
                matches += 1
                matched_keywords.append(kw)
                score += 15
        
        if matches > 0:
            reason_text = f"Matches your search for: {', '.join(matched_keywords[:5])}"
            
            # Add syllabus-specific insights if available
            if course.get('syllabus'):
                # Check if syllabus topics match
                syllabus_topics = course.get('syllabusTopics', [])
                matching_topics = [t for t in syllabus_topics if any(kw.lower() in t.lower() for kw in query_keywords)]
                if matching_topics:
                    reason_text += f" (syllabus covers: {', '.join(matching_topics[:2])})"
                
                # Check if syllabus skills match
                syllabus_skills = course.get('syllabusSkills', [])
                matching_skills = [s for s in syllabus_skills if any(kw.lower() in s.lower() for kw in query_keywords)]
                if matching_skills:
                    reason_text += f" (teaches: {', '.join(matching_skills[:2])})"
            
            reasons.append(reason_text)
    
    # Difficulty preference
    course_diff = course.get('difficulty', 3)
    preferred_diff = student_profile.get('typicalDifficultyPreference', 3)
    diff_diff = abs(course_diff - preferred_diff)
    if diff_diff == 0:
        score += 15
        reasons.append("Difficulty matches your preference")
    elif diff_diff == 1:
        score += 10
    
    # Prerequisites check
    completed = set(student_profile.get('completedCourses', []))
    prereqs = set(course.get('prerequisites', []))
    if prereqs.issubset(completed):
        score += 20
        reasons.append("You meet all prerequisites")
    elif len(prereqs & completed) > 0:
        score += 10
        reasons.append(f"Partial prerequisites met: {', '.join(prereqs & completed)}")
    else:
        score -= 10
    
    # GenEd relevance
    gened_needed = set(student_profile.get('genedRemaining', []))
    course_gened = set(course.get('gened', []))
    if gened_needed & course_gened:
        score += 20
        reasons.append(f"Satisfies GenEd requirement: {', '.join(gened_needed & course_gened)}")
    
    # Department alignment
    student_major = student_profile.get('major', [])
    student_minor = student_profile.get('minor', [])
    if course.get('department') in student_major or course.get('department') in student_minor:
        score += 15
        reasons.append("Aligned with your major/minor")
    
    # Instructor rating
    instructor_id = course.get('instructor')
    instructor = next((p for p in PROFESSORS if p['id'] == instructor_id), None)
    if instructor:
        if instructor.get('rating', 0) >= 4.5:
            score += 10
            reasons.append(f"Highly rated professor ({instructor['rating']})")
        
        # Entrepreneurship background match
        if query_keywords and any('entrepreneur' in kw.lower() or 'startup' in kw.lower() for kw in query_keywords):
            if instructor.get('entrepreneurship'):
                score += 15
                reasons.append("Professor has entrepreneurial background")
    
    # Add syllabus availability as a positive factor
    if course.get('syllabus'):
        # Only add if we have meaningful syllabus insights
        syllabus_topics = course.get('syllabusTopics', [])
        syllabus_skills = course.get('syllabusSkills', [])
        if syllabus_topics or syllabus_skills:
            syllabus_insight = "Detailed syllabus available"
            if syllabus_topics:
                syllabus_insight += f" covering {', '.join(syllabus_topics[:2])}"
            if syllabus_skills:
                syllabus_insight += f" with focus on {', '.join(syllabus_skills[:2])}"
            reasons.append(syllabus_insight)
    
    return max(0, score), reasons

def extract_keywords_from_query(query):
    """Extract relevant keywords from natural language query (fallback method)"""
    query_lower = query.lower()
    keywords = []
    
    # Department code mappings (common abbreviations to full department names)
    dept_mappings = {
        'art': 'arts', 'arts': 'arts', 'artistic': 'arts',
        'comm': 'comm', 'communication': 'comm', 'communications': 'comm',
        'cs': 'cs', 'computer science': 'cs', 'comp sci': 'cs',
        'econ': 'econ', 'economics': 'econ',
        'math': 'math', 'mathematics': 'math',
        'eng': 'engl', 'english': 'engl',
        'hist': 'hist', 'history': 'hist',
        'bio': 'biol', 'biology': 'biol',
        'chem': 'chem', 'chemistry': 'chem',
        'phys': 'phys', 'physics': 'phys',
        'psych': 'psyc', 'psychology': 'psyc',
        'phil': 'phil', 'philosophy': 'phil',
        'soc': 'soci', 'sociology': 'soci',
        'anth': 'anth', 'anthropology': 'anth',
        'span': 'span', 'spanish': 'span',
        'fr': 'fren', 'french': 'fren',
        'german': 'germ',
        'music': 'musc',
        'thea': 'thea', 'theater': 'thea', 'theatre': 'thea',
        'dance': 'danc',
        'film': 'fstd',
        'govt': 'govt', 'government': 'govt', 'politics': 'govt',
        'relg': 'relg', 'religion': 'relg',
        'arch': 'arch', 'architecture': 'arch'
    }
    
    # Extract department keywords
    for dept_key, dept_code in dept_mappings.items():
        if dept_key in query_lower:
            keywords.append(dept_code.upper())  # Add as uppercase department code
            keywords.append(dept_key)  # Also keep the original keyword
    
    # Career terms
    career_terms = ['banking', 'consulting', 'finance', 'tech', 'coding', 'data science', 'grad school', 'research']
    for term in career_terms:
        if term in query_lower:
            keywords.append(term)
    
    # Course attributes
    if 'sql' in query_lower:
        keywords.append('sql')
    if 'philosophy' in query_lower or 'philosophical' in query_lower:
        keywords.append('philosophy')
    if 'entrepreneur' in query_lower or 'startup' in query_lower:
        keywords.append('entrepreneurship')
    if '9am' in query_lower or 'morning' in query_lower or '9-3' in query_lower:
        keywords.append('morning')
    if 'gened' in query_lower or 'general education' in query_lower:
        keywords.append('gened')
    if '4.0' in query_lower or 'highly rated' in query_lower:
        keywords.append('high rating')
    
    # Difficulty terms
    if 'easy' in query_lower or 'easier' in query_lower:
        keywords.append('easy')
    if 'challenging' in query_lower or 'hard' in query_lower:
        keywords.append('hard')
    
    return keywords

def extract_query_intent_with_gemini(query, student_profile):
    """Use Gemini to extract structured intent and requirements from natural language query"""
    if not gemini_model:
        # Fallback to simple keyword extraction
        return {
            'keywords': extract_keywords_from_query(query),
            'career_goals': [],
            'topics': [],
            'schedule_preferences': [],
            'difficulty_preference': None,
            'instructor_preferences': []
        }
    
    try:
        prompt = f"""Analyze this student's course search query and extract structured information.

Student Query: "{query}"

Student Profile:
- Major: {', '.join(student_profile.get('major', []))}
- Minor: {', '.join(student_profile.get('minor', []))}
- Career Goals: {', '.join(student_profile.get('careerGoals', []))}
- Interests: {', '.join(student_profile.get('interests', []))}
- Completed Courses: {', '.join(student_profile.get('completedCourses', []))}

Extract and return a JSON object with:
1. keywords: List of important keywords/topics mentioned (including department names like "art", "comm", "CS", etc.)
2. career_goals: Career-related goals mentioned (e.g., "banking", "consulting", "tech")
3. topics: Specific subjects/topics they want to learn (e.g., "SQL", "philosophy", "data science", "art", "communication")
   - IMPORTANT: If the query mentions multiple topics (e.g., "art classes and comm classes"), include ALL topics in this list
4. schedule_preferences: Time preferences (e.g., "morning", "afternoon", "evening", specific times)
5. difficulty_preference: "easy", "moderate", "challenging", or null
6. instructor_preferences: Any instructor-related preferences (e.g., "highly rated", "entrepreneurial background")
7. gened_requirements: If they mention GenEd requirements
8. course_type: Preferred course type (e.g., "lecture", "seminar", "lab")
9. departments: List of department codes mentioned (e.g., ["ARTS", "COMM"] for "art and comm classes")

Pay special attention to:
- Department names: "art" -> ARTS, "comm" -> COMM, "cs" -> CS, etc.
- Multiple topics: If user asks for "art and comm classes", extract both topics
- Course types: "classes", "courses", "seminars" should be recognized

Return ONLY valid JSON, no additional text."""

        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        intent = json.loads(response_text)
        return intent
        
    except Exception as e:
        print(f"Error extracting query intent with Gemini: {e}")
        # Fallback
        return {
            'keywords': extract_keywords_from_query(query),
            'career_goals': [],
            'topics': [],
            'schedule_preferences': [],
            'difficulty_preference': None,
            'instructor_preferences': []
        }

def get_course_recommendations(student_id, query):
    """Get personalized course recommendations using Gemini AI for intelligent matching"""
    student_profile = next((s for s in STUDENT_PROFILES if s['id'] == student_id), STUDENT_PROFILES[0])
    
    # Use Gemini to extract query intent (semantic understanding)
    query_intent = extract_query_intent_with_gemini(query, student_profile)
    
    # Hybrid approach: Pre-filter with rule-based, then use Gemini for intelligent scoring
    query_keywords = query_intent.get('keywords', extract_keywords_from_query(query))
    
    # Step 1: Quick pre-filtering with rule-based scoring to get candidates
    prefiltered_courses = []
    for course in COURSES:
        score, _ = calculate_match_score(course, student_profile, query_keywords)
        if score > 0:
            prefiltered_courses.append((course, score))
    
    # Sort by rule-based score and take top 20 candidates
    prefiltered_courses.sort(key=lambda x: x[1], reverse=True)
    candidates = [course for course, _ in prefiltered_courses[:20]]
    
    # Step 2: Use Gemini for intelligent semantic scoring of top candidates
    scored_courses = []
    
    if gemini_model and candidates:
        print(f"Using Gemini to intelligently score {len(candidates)} candidate courses...")
        for course in candidates:
            # Use Gemini for intelligent scoring
            score, reasons = calculate_match_score_with_gemini(course, student_profile, query, query_intent)
            
            if score > 0:
                instructor = next((p for p in PROFESSORS if p['id'] == course.get('instructor')), None)
                scored_courses.append({
                    'course': course,
                    'score': score,
                    'reasons': reasons,
                    'instructor': instructor
                })
    else:
        # Fallback: use rule-based scoring for all prefiltered courses
        for course, _ in prefiltered_courses:
            score, reasons = calculate_match_score(course, student_profile, query_keywords)
            if score > 0:
                instructor = next((p for p in PROFESSORS if p['id'] == course.get('instructor')), None)
                scored_courses.append({
                    'course': course,
                    'score': score,
                    'reasons': reasons,
                    'instructor': instructor
                })
    
    # Sort by score
    scored_courses.sort(key=lambda x: x['score'], reverse=True)
    
    # Ensure diversity: if query mentions multiple topics, try to return courses from different departments/topics
    if len(query_intent.get('topics', [])) > 1 or len(query_keywords) > 2:
        # Group courses by department
        courses_by_dept = {}
        for item in scored_courses:
            dept = item['course'].get('department', 'OTHER')
            if dept not in courses_by_dept:
                courses_by_dept[dept] = []
            courses_by_dept[dept].append(item)
        
        # Try to get diverse results (at least one from each relevant department)
        diverse_results = []
        used_departments = set()
        
        # First pass: get top course from each department
        for item in scored_courses[:10]:  # Look at top 10
            dept = item['course'].get('department', 'OTHER')
            if dept not in used_departments:
                diverse_results.append(item)
                used_departments.add(dept)
                if len(diverse_results) >= 5:
                    break
        
        # Second pass: fill remaining slots with highest scoring courses
        for item in scored_courses:
            if item not in diverse_results and len(diverse_results) < 5:
                diverse_results.append(item)
        
        # Sort diverse results by score again
        diverse_results.sort(key=lambda x: x['score'], reverse=True)
        return diverse_results[:5]
    
    # If single topic or fewer keywords, just return top 5
    return scored_courses[:5]

def generate_ai_explanation(courses_data, query, student_profile):
    """Generate AI-powered explanation for recommendations using Gemini"""
    
    # Fallback explanation if Gemini is not available
    if not gemini_model:
        explanation = f"Based on your query '{query}', I found {len(courses_data)} great matches for you. "
        if courses_data:
            top_course = courses_data[0]
            explanation += f"\n\n**{top_course['course']['title']}** is the top match because: "
            explanation += "; ".join(top_course['reasons'][:3])
            if len(courses_data) > 1:
                explanation += f"\n\nHere are {len(courses_data)} courses ranked by how well they fit your profile:"
        else:
            explanation += "I couldn't find perfect matches, but I've suggested some relevant alternatives."
        return explanation
    
    # Build context for Gemini
    courses_summary = []
    for i, rec in enumerate(courses_data[:5], 1):  # Top 5 courses
        course = rec['course']
        courses_summary.append({
            'rank': i,
            'title': course['title'],
            'department': course['department'],
            'match_score': rec['score'],
            'reasons': rec['reasons'],
            'description': course.get('description', '')[:200],  # Truncate for context
            'difficulty': course.get('difficulty'),
            'instructor_rating': rec['instructor']['rating'] if rec['instructor'] else None
        })
    
    student_context = f"""
    Student Profile:
    - Major: {', '.join(student_profile.get('major', []))}
    - Minor: {', '.join(student_profile.get('minor', []))}
    - Career Goals: {', '.join(student_profile.get('careerGoals', []))}
    - GPA: {student_profile.get('gpa', 'N/A')}
    """
    
    prompt = f"""You are a helpful course advisor for university students. Generate a natural, conversational explanation for course recommendations.

Student Query: "{query}"

{student_context}

Recommended Courses:
{json.dumps(courses_summary, indent=2)}

Please generate a friendly, personalized explanation (2-3 paragraphs) that:
1. Acknowledges the student's query
2. Highlights why the top course(s) are good matches
3. Mentions key factors like match score, prerequisites, career relevance, or instructor quality
4. Encourages the student to explore the recommendations

Keep it conversational and helpful, as if you're a friendly academic advisor."""

    try:
        response = gemini_model.generate_content(prompt)
        explanation = response.text
        return explanation
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Fallback to template-based explanation
        explanation = f"Based on your query '{query}', I found {len(courses_data)} great matches for you. "
        if courses_data:
            top_course = courses_data[0]
            explanation += f"\n\n**{top_course['course']['title']}** is the top match because: "
            explanation += "; ".join(top_course['reasons'][:3])
        return explanation

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information"""
    return jsonify({
        'message': 'Welcome to CourseMatch AI API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/chat': 'Get course recommendations based on natural language query',
            'GET /api/profile?studentId=<id>': 'Get student profile',
            'POST /api/profile': 'Update student profile',
            'POST /api/feedback': 'Submit feedback on courses',
            'GET /api/analytics': 'Get aggregated analytics for dashboard',
            'GET /api/courses': 'Get all courses',
            'GET /api/professors': 'Get all professors',
            'POST /api/syllabus/upload': 'Upload course syllabus (faculty)',
            'GET /api/syllabus/<course_id>': 'Get syllabus for a course'
        },
        'status': 'running'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint for course recommendations"""
    data = request.json
    student_id = data.get('studentId', 'student_demo')
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    # Get recommendations
    recommendations = get_course_recommendations(student_id, message)
    
    # Format response
    courses_response = []
    for rec in recommendations:
        course = rec['course']
        instructor = rec['instructor']
        courses_response.append({
            'id': course['id'],
            'title': course['title'],
            'department': course['department'],
            'credits': course['credits'],
            'description': course['description'],
            'difficulty': course['difficulty'],
            'typicalGrade': course.get('typicalGrade', 'N/A'),
            'averageGPA': course.get('averageGPA'),
            'schedule': course['schedule'],
            'gened': course.get('gened', []),
            'careerRelevance': course.get('careerRelevance', []),
            'prerequisites': course.get('prerequisites', []),
            'matchScore': rec['score'],
            'matchReasons': rec['reasons'],
            'instructor': {
                'name': instructor['name'] if instructor else 'TBA',
                'rating': instructor['rating'] if instructor else None,
                'background': instructor['background'] if instructor else '',
                'teachingStyle': instructor.get('teachingStyle', ''),
                'entrepreneurship': instructor.get('entrepreneurship', False) if instructor else False
            } if instructor else None
        })
    
    student_profile = next((s for s in STUDENT_PROFILES if s['id'] == student_id), STUDENT_PROFILES[0])
    explanation = generate_ai_explanation(recommendations, message, student_profile)
    
    return jsonify({
        'message': explanation,
        'courses': courses_response,
        'count': len(courses_response)
    })

@app.route('/api/profile', methods=['GET', 'POST'])
def profile():
    """Get or update student profile"""
    if request.method == 'GET':
        student_id = request.args.get('studentId', 'student_demo')
        profile = next((s for s in STUDENT_PROFILES if s['id'] == student_id), STUDENT_PROFILES[0])
        return jsonify(profile)
    
    elif request.method == 'POST':
        data = request.json
        student_id = data.get('id', 'student_demo')
        
        # Find the profile to update
        profile_index = next((i for i, p in enumerate(STUDENT_PROFILES) if p['id'] == student_id), None)
        
        if profile_index is not None:
            # Update existing profile
            # Keep the id and update all other fields
            updated_profile = {
                'id': student_id,
                'major': data.get('major', STUDENT_PROFILES[profile_index].get('major', [])),
                'minor': data.get('minor', STUDENT_PROFILES[profile_index].get('minor', [])),
                'gpa': data.get('gpa', STUDENT_PROFILES[profile_index].get('gpa', 0.0)),
                'completedCourses': data.get('completedCourses', STUDENT_PROFILES[profile_index].get('completedCourses', [])),
                'interests': data.get('interests', STUDENT_PROFILES[profile_index].get('interests', [])),
                'careerGoals': data.get('careerGoals', STUDENT_PROFILES[profile_index].get('careerGoals', [])),
                'timePreferences': data.get('timePreferences', STUDENT_PROFILES[profile_index].get('timePreferences', [])),
                'learningStyle': data.get('learningStyle', STUDENT_PROFILES[profile_index].get('learningStyle', '')),
                'genedRemaining': data.get('genedRemaining', STUDENT_PROFILES[profile_index].get('genedRemaining', [])),
                'typicalDifficultyPreference': data.get('typicalDifficultyPreference', STUDENT_PROFILES[profile_index].get('typicalDifficultyPreference', 3))
            }
            STUDENT_PROFILES[profile_index] = updated_profile
        else:
            # Create new profile if it doesn't exist
            new_profile = {
                'id': student_id,
                'major': data.get('major', []),
                'minor': data.get('minor', []),
                'gpa': data.get('gpa', 0.0),
                'completedCourses': data.get('completedCourses', []),
                'interests': data.get('interests', []),
                'careerGoals': data.get('careerGoals', []),
                'timePreferences': data.get('timePreferences', []),
                'learningStyle': data.get('learningStyle', ''),
                'genedRemaining': data.get('genedRemaining', []),
                'typicalDifficultyPreference': data.get('typicalDifficultyPreference', 3)
            }
            STUDENT_PROFILES.append(new_profile)
        
        # Save to file
        save_student_profiles()
        
        # Get the updated profile
        updated_profile = STUDENT_PROFILES[profile_index] if profile_index is not None else STUDENT_PROFILES[-1]
        
        return jsonify({'success': True, 'message': 'Profile updated', 'profile': updated_profile})

@app.route('/api/feedback', methods=['POST'])
def feedback():
    """Submit feedback on course recommendations"""
    data = request.json
    feedback_entry = {
        'courseId': data.get('courseId'),
        'action': data.get('action'),  # 'like', 'dislike', 'add_to_cart'
        'studentId': data.get('studentId', 'anonymous'),
        'timestamp': datetime.now().isoformat()
    }
    FEEDBACK.append(feedback_entry)
    save_feedback()
    return jsonify({'success': True})

@app.route('/api/analytics', methods=['GET'])
def analytics():
    """Get aggregated analytics for faculty dashboard"""
    # Count feedback by course
    course_counts = {}
    for entry in FEEDBACK:
        course_id = entry.get('courseId')
        action = entry.get('action')
        if course_id:
            if course_id not in course_counts:
                course_counts[course_id] = {'likes': 0, 'dislikes': 0, 'cart_adds': 0, 'total': 0}
            if action == 'like':
                course_counts[course_id]['likes'] += 1
            elif action == 'dislike':
                course_counts[course_id]['dislikes'] += 1
            elif action == 'add_to_cart':
                course_counts[course_id]['cart_adds'] += 1
            course_counts[course_id]['total'] += 1
    
    # Get top courses by engagement
    top_courses = sorted(course_counts.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
    
    return jsonify({
        'courseEngagement': course_counts,
        'topCourses': [{'courseId': k, **v} for k, v in top_courses],
        'totalFeedback': len(FEEDBACK)
    })

@app.route('/api/courses', methods=['GET'])
def courses():
    """Get all courses"""
    return jsonify(COURSES)

@app.route('/api/professors', methods=['GET'])
def professors():
    """Get all professors"""
    return jsonify(PROFESSORS)

def match_syllabus_to_course(syllabus_text, suggested_course_id=None):
    """Use Gemini to match uploaded syllabus to the correct course"""
    if not gemini_model:
        # Fallback: if course_id is provided, use it
        if suggested_course_id:
            return suggested_course_id
        return None
    
    try:
        # Get list of courses for matching
        courses_list = []
        for course in COURSES[:100]:  # Limit to first 100 for efficiency
            courses_list.append({
                'id': course.get('id'),
                'title': course.get('title'),
                'department': course.get('department'),
                'description': course.get('description', '')
            })
        
        prompt = f"""You are a course matching system. Match this syllabus to the correct course from the list.

Syllabus Content (first 2000 characters):
{syllabus_text[:2000]}

Available Courses:
{json.dumps(courses_list, indent=2)}

If a course ID was suggested: {suggested_course_id if suggested_course_id else 'None'}

Analyze the syllabus and determine which course it belongs to. Consider:
- Course title and number mentioned in syllabus
- Department code
- Course description
- Topics covered
- Prerequisites mentioned

Return a JSON object with:
{{
  "courseId": "<matched_course_id>",
  "confidence": <0-100>,
  "reason": "Brief explanation of why this course matches"
}}

If no good match is found, set courseId to null. Return ONLY valid JSON."""

        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        course_id = result.get('courseId')
        confidence = result.get('confidence', 0)
        
        # Only return if confidence is reasonable
        if course_id and confidence >= 50:
            return {
                'courseId': course_id,
                'confidence': confidence,
                'reason': result.get('reason', '')
            }
        elif suggested_course_id:
            # Fallback to suggested course if provided
            return {
                'courseId': suggested_course_id,
                'confidence': 70,
                'reason': 'Using suggested course ID'
            }
        else:
            return None
            
    except Exception as e:
        print(f"Error matching syllabus: {e}")
        # Fallback to suggested course if provided
        if suggested_course_id:
            return {
                'courseId': suggested_course_id,
                'confidence': 60,
                'reason': 'Fallback to suggested course'
            }
        return None

@app.route('/api/syllabus/upload', methods=['POST'])
def upload_syllabus():
    """Upload and match a syllabus to a course"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        suggested_course_id = request.form.get('courseId')  # Optional: faculty can suggest a course
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content
        # Support both text and PDF (basic text extraction)
        filename = file.filename.lower()
        syllabus_text = ""
        
        if filename.endswith('.txt') or filename.endswith('.md'):
            syllabus_text = file.read().decode('utf-8')
        elif filename.endswith('.pdf'):
            # For PDF, we'd need PyPDF2 or similar - for now, return error
            return jsonify({'error': 'PDF support coming soon. Please upload as .txt or .md'}), 400
        else:
            # Try to read as text anyway
            try:
                syllabus_text = file.read().decode('utf-8')
            except:
                return jsonify({'error': 'Unsupported file format. Please upload .txt or .md'}), 400
        
        if not syllabus_text.strip():
            return jsonify({'error': 'File is empty'}), 400
        
        # Use Gemini to match syllabus to course
        match_result = match_syllabus_to_course(syllabus_text, suggested_course_id)
        
        if not match_result:
            return jsonify({
                'error': 'Could not match syllabus to any course',
                'suggestion': 'Please specify a course ID'
            }), 400
        
        course_id = match_result['courseId']
        
        # Find the course and update it with syllabus
        course_index = next((i for i, c in enumerate(COURSES) if c['id'] == course_id), None)
        
        if course_index is None:
            return jsonify({'error': f'Course {course_id} not found'}), 404
        
        # Store syllabus content (truncate if too long)
        syllabus_content = syllabus_text[:10000]  # Limit to 10k chars
        
        # Update course with syllabus
        COURSES[course_index]['syllabus'] = syllabus_content
        COURSES[course_index]['syllabusUploaded'] = True
        COURSES[course_index]['syllabusUploadDate'] = datetime.now().isoformat()
        
        # Extract keywords and topics from syllabus using Gemini
        if gemini_model:
            try:
                extract_prompt = f"""Extract key information from this course syllabus:

{syllabus_text[:3000]}

Return a JSON object with:
{{
  "topics": ["topic1", "topic2", ...],
  "skills": ["skill1", "skill2", ...],
  "keywords": ["keyword1", "keyword2", ...],
  "prerequisites": ["prereq1", "prereq2", ...] if mentioned,
  "careerRelevance": ["career1", "career2", ...] if mentioned
}}

Return ONLY valid JSON."""

                extract_response = gemini_model.generate_content(extract_prompt)
                extract_text = extract_response.text.strip()
                
                if extract_text.startswith('```'):
                    extract_text = extract_text.split('```')[1]
                    if extract_text.startswith('json'):
                        extract_text = extract_text[4:]
                    extract_text = extract_text.strip()
                
                extracted = json.loads(extract_text)
                
                # Update course with extracted information
                if extracted.get('keywords'):
                    existing_keywords = COURSES[course_index].get('keywords', [])
                    COURSES[course_index]['keywords'] = list(set(existing_keywords + extracted['keywords']))
                
                if extracted.get('topics'):
                    COURSES[course_index]['syllabusTopics'] = extracted['topics']
                
                if extracted.get('skills'):
                    COURSES[course_index]['syllabusSkills'] = extracted['skills']
                
                if extracted.get('prerequisites'):
                    existing_prereqs = COURSES[course_index].get('prerequisites', [])
                    COURSES[course_index]['prerequisites'] = list(set(existing_prereqs + extracted['prerequisites']))
                
                if extracted.get('careerRelevance'):
                    existing_careers = COURSES[course_index].get('careerRelevance', [])
                    COURSES[course_index]['careerRelevance'] = list(set(existing_careers + extracted['careerRelevance']))
                    
            except Exception as e:
                print(f"Error extracting syllabus info: {e}")
        
        # Save courses
        save_courses()
        
        return jsonify({
            'success': True,
            'message': f'Syllabus uploaded and matched to {course_id}',
            'courseId': course_id,
            'courseTitle': COURSES[course_index]['title'],
            'matchConfidence': match_result['confidence'],
            'matchReason': match_result['reason']
        })
        
    except Exception as e:
        print(f"Error uploading syllabus: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/syllabus/<course_id>', methods=['GET'])
def get_syllabus(course_id):
    """Get syllabus for a specific course"""
    course = next((c for c in COURSES if c['id'] == course_id), None)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    if 'syllabus' not in course:
        return jsonify({'error': 'No syllabus available for this course'}), 404
    
    return jsonify({
        'courseId': course_id,
        'syllabus': course['syllabus'],
        'uploaded': course.get('syllabusUploaded', False),
        'uploadDate': course.get('syllabusUploadDate')
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
