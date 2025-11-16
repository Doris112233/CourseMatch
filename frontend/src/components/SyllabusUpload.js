import React, { useState } from 'react';
import axios from 'axios';
import './SyllabusUpload.css';

const API_BASE = 'http://localhost:5001/api';

function SyllabusUpload() {
  const [file, setFile] = useState(null);
  const [suggestedCourseId, setSuggestedCourseId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Check file type
      const filename = selectedFile.name.toLowerCase();
      if (!filename.endsWith('.txt') && !filename.endsWith('.md') && !filename.endsWith('.pdf')) {
        setError('Please upload a .txt, .md, or .pdf file');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError('');
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (suggestedCourseId.trim()) {
        formData.append('courseId', suggestedCourseId.trim());
      }

      const response = await axios.post(`${API_BASE}/syllabus/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
      setFile(null);
      setSuggestedCourseId('');
      // Reset file input
      document.getElementById('syllabus-file-input').value = '';
    } catch (err) {
      setError(err.response?.data?.error || 'Error uploading syllabus');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="syllabus-upload-container">
      <div className="syllabus-upload-card">
        <h2>📄 Upload Course Syllabus</h2>
        <p className="upload-description">
          Upload a syllabus file (.txt, .md, or .pdf) and our AI will automatically match it to the correct course.
          The syllabus content will be used to improve course matching for students.
        </p>

        <div className="upload-form">
          <div className="form-group">
            <label htmlFor="syllabus-file-input" className="file-label">
              <span className="file-label-text">Choose Syllabus File</span>
              <input
                id="syllabus-file-input"
                type="file"
                accept=".txt,.md,.pdf"
                onChange={handleFileChange}
                className="file-input"
              />
            </label>
            {file && (
              <div className="file-info">
                <span className="file-name">📎 {file.name}</span>
                <span className="file-size">({(file.size / 1024).toFixed(2)} KB)</span>
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="course-id-input" className="input-label">
              Course ID (Optional)
            </label>
            <input
              id="course-id-input"
              type="text"
              className="course-id-input"
              placeholder="e.g., CS3102, COMM3020"
              value={suggestedCourseId}
              onChange={(e) => setSuggestedCourseId(e.target.value.toUpperCase())}
            />
            <span className="input-hint">
              If you know the course ID, enter it here to help with matching. Otherwise, AI will automatically detect it.
            </span>
          </div>

          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? '⏳ Uploading...' : '📤 Upload Syllabus'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {result && (
          <div className="success-message">
            <div className="success-header">
              <span className="success-icon">✓</span>
              <h3>Syllabus Uploaded Successfully!</h3>
            </div>
            <div className="success-details">
              <p><strong>Course:</strong> {result.courseTitle} ({result.courseId})</p>
              <p><strong>Match Confidence:</strong> {result.matchConfidence}%</p>
              <p><strong>Match Reason:</strong> {result.matchReason}</p>
            </div>
            <p className="success-note">
              The syllabus has been added to the course and will now be used in AI-powered course matching.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default SyllabusUpload;

