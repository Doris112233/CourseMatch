import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import CourseCard from './components/CourseCard';
import StudentProfile from './components/StudentProfile';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import SyllabusUpload from './components/SyllabusUpload';
import './App.css';

function App() {
  const [view, setView] = useState('chat'); // 'chat', 'profile', 'analytics', 'syllabus'
  const [courses, setCourses] = useState([]);
  const [studentId] = useState('student_demo');
  
  // Preserve conversation history across tab switches
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm CourseMatch AI. I can help you find the perfect courses. Tell me what you're looking for - your interests, schedule, career goals, or any specific requirements!"
    }
  ]);

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🎓 UVA CourseMatch AI</h1>
          <p className="subtitle">Personalized Course & Instructor Recommender</p>
        </div>
        <nav className="nav-tabs">
          <button 
            className={view === 'chat' ? 'active' : ''} 
            onClick={() => setView('chat')}
          >
            Chat
          </button>
          <button 
            className={view === 'profile' ? 'active' : ''} 
            onClick={() => setView('profile')}
          >
            Profile
          </button>
          <button 
            className={view === 'analytics' ? 'active' : ''} 
            onClick={() => setView('analytics')}
          >
            Analytics
          </button>
          <button 
            className={view === 'syllabus' ? 'active' : ''} 
            onClick={() => setView('syllabus')}
          >
            Upload Syllabus
          </button>
        </nav>
      </header>

      <main className="App-main">
        {view === 'chat' && (
          <div className="chat-container">
            <ChatInterface 
              studentId={studentId}
              onCoursesReceived={setCourses}
              messages={chatMessages}
              setMessages={setChatMessages}
            />
            <div className="courses-section">
              {courses.length > 0 && (
                <div className="courses-list">
                  <h2>Recommended Courses</h2>
                  {courses.map((course) => (
                    <CourseCard 
                      key={course.id} 
                      course={course}
                      studentId={studentId}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {view === 'profile' && (
          <StudentProfile studentId={studentId} />
        )}

        {view === 'analytics' && (
          <AnalyticsDashboard />
        )}

        {view === 'syllabus' && (
          <SyllabusUpload />
        )}
      </main>
    </div>
  );
}

export default App;

