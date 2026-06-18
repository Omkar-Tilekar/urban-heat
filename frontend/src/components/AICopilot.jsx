import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Loader } from 'lucide-react';

export default function AICopilot({ selectedCellsDetails }) {
  const [messages, setMessages] = useState([
    {
      sender: 'system',
      text: '### Welcome to the ISRO Heat Mitigation Advisor! \n\nI am your AI Copilot. Ask me queries about: \n- Why certain districts are experiencing extreme Heat Risk.\n- How interventions like **Miyawaki Forests** or **Cool Roofs** compare in cost and efficiency.\n- Successful case studies in Indian cities (e.g., Ahmedabad or Bengaluru).'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Scroll to bottom when chat updates
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input;
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg,
          selected_cells: selectedCellsDetails
        }),
      });

      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      
      setMessages((prev) => [...prev, { sender: 'system', text: data.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { 
          sender: 'system', 
          text: '⚠️ **Connection Error**: Could not connect to the backend AI agent. Please ensure the FastAPI AI server is running on port 8001.' 
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Basic renderer for simple markdown tags in the mock response
  const formatMessageText = (text) => {
    return text.split('\n').map((line, lineIdx) => {
      let content = line;
      
      // Headers
      if (content.startsWith('### ')) {
        return <h4 key={lineIdx} style={{ fontSize: '1rem', fontWeight: 700, margin: '12px 0 6px 0', color: '#00f2fe' }}>{content.replace('### ', '')}</h4>;
      }
      if (content.startsWith('**') && content.endsWith('**')) {
        return <strong key={lineIdx} style={{ display: 'block', margin: '6px 0', color: '#fff' }}>{content.replace(/\*\*/g, '')}</strong>;
      }
      
      // Bullet points
      if (content.startsWith('- ') || content.startsWith('* ')) {
        const item = content.substring(2);
        // Bold parsing inside list items
        const boldParts = item.split('**');
        return (
          <li key={lineIdx} style={{ marginLeft: '16px', listStyleType: 'disc', margin: '4px 0' }}>
            {boldParts.map((part, pIdx) => pIdx % 2 === 1 ? <strong key={pIdx} style={{ color: '#00f2fe' }}>{part}</strong> : part)}
          </li>
        );
      }
      
      // Bold text replacements inline
      const boldParts = content.split('**');
      if (boldParts.length > 1) {
        return (
          <p key={lineIdx} style={{ marginBottom: '8px' }}>
            {boldParts.map((part, pIdx) => pIdx % 2 === 1 ? <strong key={pIdx} style={{ color: '#00f2fe' }}>{part}</strong> : part)}
          </p>
        );
      }
      
      return content.trim() === '' ? <div key={lineIdx} style={{ height: '8px' }} /> : <p key={lineIdx} style={{ marginBottom: '8px' }}>{content}</p>;
    });
  };

  return (
    <div className="chat-container">
      <div className="chat-history">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble ${msg.sender}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', fontSize: '0.75rem', fontWeight: 'bold', color: msg.sender === 'user' ? '#00f2fe' : '#4facfe' }}>
              {msg.sender === 'user' ? <User size={12} /> : <Bot size={12} />}
              {msg.sender === 'user' ? 'Urban Planner' : 'ISRO Climate AI'}
            </div>
            <div>{formatMessageText(msg.text)}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble system" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Loader size={16} className="hotspot-pulse" style={{ color: '#00f2fe' }} />
            <span>Consulting mitigation knowledge bases...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about cool roofs, Miyawaki, costs..."
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" style={{ width: '48px', padding: '10px' }} disabled={loading}>
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
