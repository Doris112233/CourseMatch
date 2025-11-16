import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './StudentProfile.css';

const API_BASE = 'http://localhost:5001/api';

function StudentProfile({ studentId }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  // Store raw string values for array fields during editing
  const [arrayFieldStrings, setArrayFieldStrings] = useState({});

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        console.log('Fetching profile for studentId:', studentId);
        const response = await axios.get(`${API_BASE}/profile`, {
          params: { studentId }
        });
        console.log('Profile response:', response.data);
        console.log('Response status:', response.status);
        
        // Handle the response - it should be a profile object
        const profileData = response.data;
        if (profileData && (profileData.id || profileData.major)) {
          // Valid profile data
          setProfile(profileData);
          setEditedProfile({ ...profileData });
        } else {
          console.error('Invalid profile data received:', profileData);
          console.error('Response type:', typeof profileData);
          setProfile(null);
        }
      } catch (error) {
        console.error('Error fetching profile:', error);
        if (error.response) {
          // Server responded with error status
          console.error('Error status:', error.response.status);
          console.error('Error data:', error.response.data);
        } else if (error.request) {
          // Request made but no response
          console.error('No response received. Is the backend running?');
          console.error('Request URL:', `${API_BASE}/profile?studentId=${studentId}`);
        } else {
          // Something else happened
          console.error('Error message:', error.message);
        }
        setProfile(null);
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      fetchProfile();
    } else {
      setLoading(false);
      setProfile(null);
    }
  }, [studentId]);

  const handleEdit = () => {
    console.log('Edit button clicked');
    setIsEditing(true);
    setEditedProfile({ ...profile });
    // Initialize array field strings for editing
    const fieldStrings = {};
    const arrayFields = ['major', 'minor', 'completedCourses', 'careerGoals', 'interests', 'timePreferences', 'genedRemaining'];
    arrayFields.forEach(field => {
      if (profile[field]) {
        fieldStrings[field] = Array.isArray(profile[field]) ? profile[field].join(', ') : profile[field];
      } else {
        fieldStrings[field] = '';
      }
    });
    setArrayFieldStrings(fieldStrings);
    setSaveMessage('');
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedProfile({ ...profile });
    setArrayFieldStrings({});
    setSaveMessage('');
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage('');
    
    try {
      // Convert array field strings back to arrays before saving
      const profileToSave = { ...editedProfile };
      const arrayFields = ['major', 'minor', 'completedCourses', 'careerGoals', 'interests', 'timePreferences', 'genedRemaining'];
      arrayFields.forEach(field => {
        if (arrayFieldStrings[field] !== undefined) {
          const value = arrayFieldStrings[field];
          if (typeof value === 'string' && value.trim()) {
            profileToSave[field] = value.split(',').map(item => item.trim()).filter(item => item);
          } else if (Array.isArray(value)) {
            profileToSave[field] = value;
          } else {
            profileToSave[field] = [];
          }
        }
      });
      
      const response = await axios.post(`${API_BASE}/profile`, {
        ...profileToSave,
        id: studentId
      });
      
      setProfile(response.data.profile);
      setIsEditing(false);
      setArrayFieldStrings({});
      setSaveMessage('Profile updated successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Error saving profile:', error);
      setSaveMessage('Error saving profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleArrayChange = (field, value) => {
    // Store the raw string value during editing (don't convert to array yet)
    setArrayFieldStrings({ ...arrayFieldStrings, [field]: value });
  };

  const handleInputChange = (field, value) => {
    setEditedProfile({ ...editedProfile, [field]: value });
  };

  const getArrayFieldValue = (field) => {
    // Return the string value if editing, otherwise convert array to string
    if (isEditing && arrayFieldStrings[field] !== undefined) {
      return arrayFieldStrings[field];
    }
    const value = displayProfile[field];
    return Array.isArray(value) ? value.join(', ') : (value || '');
  };

  if (loading) {
    return (
      <div className="profile-container">
        <div className="profile-card">
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="profile-container">
        <div className="profile-card">
          <h2>Profile not found</h2>
          <p>Unable to load profile for student ID: <strong>{studentId}</strong></p>
          <p style={{ color: '#666', fontSize: '0.9rem', marginTop: '1rem' }}>
            Please check:
          </p>
          <ul style={{ color: '#666', fontSize: '0.9rem', marginLeft: '1.5rem' }}>
            <li>Backend server is running on http://localhost:5001</li>
            <li>API endpoint is accessible</li>
            <li>Student profile exists in the database</li>
          </ul>
          <button 
            className="edit-btn" 
            onClick={() => window.location.reload()}
            style={{ marginTop: '1rem' }}
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  const displayProfile = isEditing ? editedProfile : profile;

  return (
    <div className="profile-container">
      <div className={`profile-card ${isEditing ? 'editing' : ''}`}>
        <div className="profile-header">
          <div>
            <h2>Student Profile</h2>
            {isEditing && (
              <p className="edit-mode-indicator">✏️ Edit Mode - Make your changes below</p>
            )}
          </div>
          {!isEditing ? (
            <button 
              className="edit-btn" 
              onClick={handleEdit}
              style={{ display: 'flex', visibility: 'visible' }}
            >
              <span className="btn-icon">✏️</span>
              Edit Profile
            </button>
          ) : (
            <div className="edit-actions">
              <button className="cancel-btn" onClick={handleCancel} disabled={saving}>
                <span className="btn-icon">✕</span>
                Cancel
              </button>
              <button className="save-btn" onClick={handleSave} disabled={saving}>
                <span className="btn-icon">{saving ? '⏳' : '💾'}</span>
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>

        {saveMessage && (
          <div className={`save-message ${saveMessage.includes('Error') ? 'error' : 'success'}`}>
            <span className="message-icon">{saveMessage.includes('Error') ? '⚠️' : '✓'}</span>
            {saveMessage}
          </div>
        )}
        
        <div className="profile-section">
          <h3>📚 Academic Information</h3>
          {isEditing && (
            <p className="section-help">Separate multiple values with commas (e.g., "Commerce, Computer Science")</p>
          )}
          <div className="profile-grid">
            <div className="profile-item">
              <label className="label">
                Major(s):
                {isEditing && <span className="required-indicator"> *</span>}
              </label>
              {isEditing ? (
                <>
                  <input
                    type="text"
                    className="profile-input"
                    value={getArrayFieldValue('major')}
                    onChange={(e) => handleArrayChange('major', e.target.value)}
                    placeholder="e.g., Commerce, Computer Science"
                  />
                  <span className="input-hint">Separate multiple majors with commas</span>
                </>
              ) : (
                <span className="value">{displayProfile.major?.join(', ') || 'N/A'}</span>
              )}
            </div>
            <div className="profile-item">
              <label className="label">Minor(s):</label>
              {isEditing ? (
                <>
                  <input
                    type="text"
                    className="profile-input"
                    value={getArrayFieldValue('minor')}
                    onChange={(e) => handleArrayChange('minor', e.target.value)}
                    placeholder="e.g., Data Science, Philosophy"
                  />
                  <span className="input-hint">Leave empty if no minor</span>
                </>
              ) : (
                <span className="value">{displayProfile.minor?.join(', ') || 'None'}</span>
              )}
            </div>
            <div className="profile-item">
              <label className="label">
                GPA:
                {isEditing && <span className="required-indicator"> *</span>}
              </label>
              {isEditing ? (
                <>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="4.0"
                    className="profile-input"
                    value={displayProfile.gpa || ''}
                    onChange={(e) => handleInputChange('gpa', parseFloat(e.target.value) || 0)}
                    placeholder="0.00 - 4.00"
                  />
                  <span className="input-hint">Enter your current GPA</span>
                </>
              ) : (
                <span className="value">{displayProfile.gpa}</span>
              )}
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h3>📋 Completed Courses</h3>
          {isEditing ? (
            <>
              <textarea
                className="profile-textarea"
                value={getArrayFieldValue('completedCourses')}
                onChange={(e) => handleArrayChange('completedCourses', e.target.value)}
                placeholder="e.g., COMM2010, DS2001, CS2110, MATH1310"
                rows="4"
              />
              <span className="input-hint">Enter course codes separated by commas. This helps us check prerequisites.</span>
            </>
          ) : (
            <div className="courses-list">
              {displayProfile.completedCourses?.length > 0 ? (
                displayProfile.completedCourses.map((course, idx) => (
                  <span key={idx} className="course-badge">{course}</span>
                ))
              ) : (
                <span className="empty-state">No courses entered yet</span>
              )}
            </div>
          )}
        </div>

        <div className="profile-section">
          <h3>🎯 Career Goals</h3>
          {isEditing ? (
            <>
              <input
                type="text"
                className="profile-input"
                value={getArrayFieldValue('careerGoals')}
                onChange={(e) => handleArrayChange('careerGoals', e.target.value)}
                placeholder="e.g., banking, consulting, tech"
              />
              <span className="input-hint">This helps us recommend courses aligned with your career path</span>
            </>
          ) : (
            <div className="tags-list">
              {displayProfile.careerGoals?.length > 0 ? (
                displayProfile.careerGoals.map((goal, idx) => (
                  <span key={idx} className="tag">{goal}</span>
                ))
              ) : (
                <span className="empty-state">No career goals specified</span>
              )}
            </div>
          )}
        </div>

        <div className="profile-section">
          <h3>💡 Interests</h3>
          {isEditing ? (
            <>
              <input
                type="text"
                className="profile-input"
                value={getArrayFieldValue('interests')}
                onChange={(e) => handleArrayChange('interests', e.target.value)}
                placeholder="e.g., AI, finance, banking"
              />
              <span className="input-hint">What topics or fields interest you?</span>
            </>
          ) : (
            <div className="tags-list">
              {displayProfile.interests?.length > 0 ? (
                displayProfile.interests.map((interest, idx) => (
                  <span key={idx} className="tag">{interest}</span>
                ))
              ) : (
                <span className="empty-state">No interests specified</span>
              )}
            </div>
          )}
        </div>

        <div className="profile-section">
          <h3>⚙️ Preferences</h3>
          <div className="profile-grid">
            <div className="profile-item">
              <label className="label">Time Preference:</label>
              {isEditing ? (
                <>
                  <input
                    type="text"
                    className="profile-input"
                    value={getArrayFieldValue('timePreferences')}
                    onChange={(e) => handleArrayChange('timePreferences', e.target.value)}
                    placeholder="e.g., morning, mid-day, afternoon"
                  />
                  <span className="input-hint">When do you prefer classes?</span>
                </>
              ) : (
                <span className="value">{displayProfile.timePreferences?.join(', ') || 'No preference'}</span>
              )}
            </div>
            <div className="profile-item">
              <label className="label">Learning Style:</label>
              {isEditing ? (
                <>
                  <input
                    type="text"
                    className="profile-input"
                    value={displayProfile.learningStyle || ''}
                    onChange={(e) => handleInputChange('learningStyle', e.target.value)}
                    placeholder="e.g., hands-on, project-based"
                  />
                  <span className="input-hint">How do you learn best?</span>
                </>
              ) : (
                <span className="value">{displayProfile.learningStyle || 'N/A'}</span>
              )}
            </div>
            <div className="profile-item">
              <label className="label">Difficulty Preference:</label>
              {isEditing ? (
                <>
                  <select
                    className="profile-input"
                    value={displayProfile.typicalDifficultyPreference || 3}
                    onChange={(e) => handleInputChange('typicalDifficultyPreference', parseInt(e.target.value))}
                  >
                    <option value={1}>Easy (1)</option>
                    <option value={2}>Moderate-Easy (2)</option>
                    <option value={3}>Moderate (3)</option>
                    <option value={4}>Moderate-Hard (4)</option>
                    <option value={5}>Hard (5)</option>
                  </select>
                  <span className="input-hint">Preferred course difficulty level</span>
                </>
              ) : (
                <span className="value">{displayProfile.typicalDifficultyPreference || 'Moderate'}</span>
              )}
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h3>📜 Remaining GenEd Requirements</h3>
          {isEditing ? (
            <>
              <textarea
                className="profile-textarea"
                value={getArrayFieldValue('genedRemaining')}
                onChange={(e) => handleArrayChange('genedRemaining', e.target.value)}
                placeholder="e.g., Natural Sciences & Mathematics, Social Sciences"
                rows="3"
              />
              <span className="input-hint">Which general education requirements do you still need to fulfill?</span>
            </>
          ) : (
            <div className="tags-list">
              {displayProfile.genedRemaining && displayProfile.genedRemaining.length > 0 ? (
                displayProfile.genedRemaining.map((gened, idx) => (
                  <span key={idx} className="tag gened-tag">{gened}</span>
                ))
              ) : (
                <span className="tag success-tag">✓ All GenEd requirements completed!</span>
              )}
            </div>
          )}
        </div>

        {!isEditing && (
          <div className="info-box">
            <strong>💡 Note:</strong> CourseMatch AI uses this profile to personalize recommendations. 
            The system learns your preferences over time to provide better matches.
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentProfile;
