import React, { useState } from 'react';
import axios from 'axios';
import './CourseCard.css';

const API_BASE = 'http://localhost:5001/api';

function CourseCard({ course, studentId }) {
  const [feedback, setFeedback] = useState(null);

  const handleFeedback = async (action) => {
    try {
      await axios.post(`${API_BASE}/feedback`, {
        courseId: course.id,
        action,
        studentId
      });
      setFeedback(action);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const getDifficultyStars = (difficulty) => {
    return '⭐'.repeat(difficulty) + '☆'.repeat(5 - difficulty);
  };

  const getDifficultyLabel = (difficulty) => {
    const labels = ['', 'Very Easy', 'Easy', 'Moderate', 'Challenging', 'Very Challenging'];
    return labels[difficulty] || 'Moderate';
  };

  return (
    <div className="course-card">
      <div className="course-header">
        <div>
          <h3 className="course-title">{course.title}</h3>
          <p className="course-id">{course.id} • {course.department} • {course.credits} credits</p>
        </div>
        <div className="match-score">
          <span className="score-value">{course.matchScore}%</span>
          <span className="score-label">match</span>
        </div>
      </div>

      <p className="course-description">{course.description}</p>

      <div className="course-details">
        <div className="detail-row">
          <span className="detail-label">Difficulty:</span>
          <span className="detail-value">
            {getDifficultyStars(course.difficulty)} {getDifficultyLabel(course.difficulty)}
          </span>
        </div>
        
        <div className="detail-row">
          <span className="detail-label">Typical Grade:</span>
            <span className="detail-value">
              {course.averageGPA ? `${course.averageGPA.toFixed(2)} GPA` : course.typicalGrade}
              {course.averageGPA && course.typicalGrade && ` (${course.typicalGrade})`}
            </span>
        </div>

        {course.instructor && (
          <>
            <div className="detail-row">
              <span className="detail-label">Instructor:</span>
              <span className="detail-value">
                {course.instructor.name}
                {course.instructor.rating && (
                  <span className="rating"> ⭐ {course.instructor.rating}</span>
                )}
              </span>
            </div>
            {course.instructor.entrepreneurship && (
              <div className="badge entrepreneurship">🚀 Entrepreneurial Background</div>
            )}
          </>
        )}

        {course.gened && course.gened.length > 0 && (
          <div className="badge gened">📚 GenEd: {course.gened.join(', ')}</div>
        )}

        {course.careerRelevance && course.careerRelevance.length > 0 && (
          <div className="career-relevance">
            <span className="detail-label">Career Relevance:</span>
            <div className="career-tags">
              {course.careerRelevance.map((career, idx) => (
                <span key={idx} className="career-tag">{career}</span>
              ))}
            </div>
          </div>
        )}

        {course.prerequisites && course.prerequisites.length > 0 && (
          <div className="detail-row">
            <span className="detail-label">Prerequisites:</span>
            <span className="detail-value">{course.prerequisites.join(', ')}</span>
          </div>
        )}

        {course.matchReasons && course.matchReasons.length > 0 && (
          <div className="match-reasons">
            <strong>Why this course fits:</strong>
            <ul>
              {course.matchReasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        )}

        {course.schedule && (
          <div className="schedule">
            <span className="detail-label">Schedule:</span>
            <div className="schedule-times">
              {Array.isArray(course.schedule) && course.schedule[0] && typeof course.schedule[0] === 'object' ? (
                course.schedule.map((slot, idx) => (
                  <div key={idx} className="schedule-slot">
                    {slot.time} {slot.location && `• ${slot.location}`}
                  </div>
                ))
              ) : (
                <div className="schedule-slot">{course.schedule[0]}</div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="course-actions">
        <button 
          className={`action-button like ${feedback === 'like' ? 'active' : ''}`}
          onClick={() => handleFeedback('like')}
        >
          👍 Like
        </button>
        <button 
          className={`action-button cart ${feedback === 'add_to_cart' ? 'active' : ''}`}
          onClick={() => handleFeedback('add_to_cart')}
        >
          🛒 Add to Cart
        </button>
        <button 
          className={`action-button dislike ${feedback === 'dislike' ? 'active' : ''}`}
          onClick={() => handleFeedback('dislike')}
        >
          👎 Pass
        </button>
      </div>
    </div>
  );
}

export default CourseCard;

