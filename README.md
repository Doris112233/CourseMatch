# 🎓 UVA CourseMatch AI

**A Personalized Course & Instructor Recommender**

CourseMatch AI is a generative AI chat advisor that helps students pick courses AND gives faculty/data teams actionable insights for curriculum planning.

## Features

### For Students
- 🗣️ **Natural Language Interface**: Describe what you want in plain English
- 🎯 **Personalized Recommendations**: AI matches courses based on your profile, career goals, and preferences
- 📊 **Smart Matching**: Considers prerequisites, GenEd requirements, difficulty, schedule, and professor ratings
- 🚀 **Entrepreneurial Background Filter**: Find professors with startup/industry experience
- 📈 **Progress Tracking**: See how courses fit into your degree plan

### For Faculty & Administrators
- 📊 **Analytics Dashboard**: Real-time insights into student course preferences
- 📉 **Demand Intelligence**: Understand what courses students are interested in
- 💡 **Curriculum Planning**: Data-driven decisions for course development
- 📈 **Engagement Metrics**: Track likes, dislikes, and cart additions

## Tech Stack

- **Frontend**: React with modern CSS
- **Backend**: Flask (Python) REST API
- **AI**: Google Gemini Pro for natural language explanations and personalized recommendations
- **Data Visualization**: Recharts for analytics dashboard
- **Data**: Mock JSON datasets (courses, professors, student profiles)

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Upgrade pip, setuptools, and wheel (important for Python 3.13+):
```bash
pip install --upgrade pip setuptools wheel
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up environment variables:
```bash
# Create a .env file in the backend directory
echo "GEMINI_API_KEY=your_api_key_here" > .env
# Get your API key from: https://makersuite.google.com/app/apikey
# Edit .env and add your Gemini API key for AI-powered explanations
```

6. Run the Flask server:
```bash
python app.py
```

The backend will run on `http://localhost:5001` (port 5000 is often used by macOS AirPlay)

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

### As a Student

1. **Start Chatting**: Navigate to the Chat tab and describe what you're looking for:
   ```
   "I want a course that fits my SIS schedule, helps me break into banking, 
   includes SQL practice, and has a 4.0+ rated professor with an entrepreneurial background"
   ```

2. **Review Recommendations**: See course matches with:
   - Match score and reasons
   - Instructor information and ratings
   - Difficulty and typical grades
   - Schedule and prerequisites
   - Career relevance

3. **Provide Feedback**: Like, add to cart, or pass on courses to improve future recommendations

4. **View Profile**: Check your student profile to see how recommendations are personalized

### As Faculty/Administrator

1. **View Analytics**: Navigate to the Analytics tab
2. **See Engagement Data**: View which courses students are most interested in
3. **Track Sentiment**: Understand positive/negative feedback patterns
4. **Make Data-Driven Decisions**: Use insights for curriculum planning

## Project Structure

```
CourseMatch/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── requirements.txt       # Python dependencies
│   ├── data/
│   │   ├── courses.json       # Mock course data
│   │   ├── professors.json    # Mock professor data
│   │   ├── student_profiles.json  # Student profile templates
│   │   └── feedback.json      # Feedback/analytics data
│   └── .env.example          # Environment variables template
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.js      # Main chat UI
│   │   │   ├── CourseCard.js         # Course recommendation cards
│   │   │   ├── StudentProfile.js     # Profile view
│   │   │   └── AnalyticsDashboard.js # Faculty analytics
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
└── README.md
```

## API Endpoints

- `POST /api/chat` - Get course recommendations based on natural language query
- `GET /api/profile?studentId=<id>` - Get student profile
- `POST /api/profile` - Update student profile
- `POST /api/feedback` - Submit feedback on courses
- `GET /api/analytics` - Get aggregated analytics for dashboard
- `GET /api/courses` - Get all courses
- `GET /api/professors` - Get all professors

## Matching Algorithm

The recommendation engine scores courses based on:
- **Career Relevance** (30 points): Alignment with student's career goals
- **Query Matching** (15 points per keyword): Match with search terms
- **Difficulty Fit** (10-15 points): Alignment with student's difficulty preference
- **Prerequisites** (10-20 points): Whether student meets course requirements
- **GenEd Requirements** (20 points): If course satisfies remaining GenEd needs
- **Department Alignment** (15 points): Match with major/minor
- **Instructor Rating** (10 points): Professor rating quality
- **Special Attributes** (15 points): Entrepreneurship background, etc.

## Future Enhancements

- Integration with real SIS (Student Information System)
- Enhanced Gemini integration for better query understanding and course matching
- Real-time course availability checking
- Degree planner integration
- Advanced analytics with machine learning
- Student community features
- Syllabus parsing and keyword extraction

## Demo Student Profile

The MVP includes a demo student profile:
- **Major**: Commerce
- **Minor**: Data Science
- **GPA**: 3.7
- **Interests**: AI, finance
- **Career Goals**: Banking, consulting

Try queries like:
- "Courses for banking with SQL"
- "Philosophy courses that satisfy GenEd"
- "Highly rated professors with startup experience"
- "Easy courses in the morning"

## Notes for Hackathon Judges

This is a **conceptual prototype** demonstrating:
- ✅ Personalized course recommendation system
- ✅ Natural language query processing
- ✅ Multi-factor matching algorithm
- ✅ Faculty analytics dashboard
- ✅ Student feedback system

In production, this would integrate with:
- UVA SIS through secure APIs
- De-identified analytics pipelines
- Real-time course availability
- Student academic records (with proper privacy controls)

## License

MIT License - Feel free to use this project for educational purposes.

## Contributing

This is an MVP built for hackathon demonstration. Contributions welcome!

---

**Built with ❤️ for UVA Students**