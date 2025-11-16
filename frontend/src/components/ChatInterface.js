import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './ChatInterface.css';

const API_BASE = 'http://localhost:5001/api';

function ChatInterface({ studentId, onCoursesReceived, messages, setMessages }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Use provided messages or fallback to local state (backward compatibility)
  const [localMessages, setLocalMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm CourseMatch AI. I can help you find the perfect courses. Tell me what you're looking for - your interests, schedule, career goals, or any specific requirements!"
    }
  ]);
  
  const chatMessages = messages || localMessages;
  const setChatMessages = setMessages || setLocalMessages;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setChatMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        studentId,
        message: input
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.message
      };

      setChatMessages(prev => [...prev, assistantMessage]);
      
      if (response.data.courses && response.data.courses.length > 0) {
        onCoursesReceived(response.data.courses);
      }
    } catch (error) {
      console.error('Error:', error);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {chatMessages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me about courses... (e.g., 'I want a course that fits my SIS schedule, helps me break into banking, includes SQL practice, and has a 4.0+ rated professor')"
          className="chat-input"
          disabled={loading}
        />
        <button 
          type="submit" 
          className="send-button"
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;

