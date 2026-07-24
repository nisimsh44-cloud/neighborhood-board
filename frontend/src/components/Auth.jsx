import { useState } from 'react';
import axios from 'axios';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    const endpoint = isLogin ? '/api/login' : '/api/register';
    const payload = isLogin
      ? { username, password }
      : { username, email, password, role };

    try {
      const response = await axios.post(`http://127.0.0.1:5000${endpoint}`, payload);
      setMessage(response.data.message || 'הפעולה בוצעה בהצלחה!');
      if (isLogin && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
      }
    } catch (err) {
      setMessage(err.response?.data?.error || 'אירעה שגיאה בתקשורת מול השרת');
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '40px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px', direction: 'rtl' }}>
      <h2>{isLogin ? 'התחברות ללוח המודעות' : 'הרשמה למערכת'}</h2>
      
      {message && <p style={{ color: message.includes('שגיאה') ? 'red' : 'green' }}>{message}</p>}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <input
          type="text"
          placeholder="שם משתמש"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        {!isLogin && (
          <>
            <input
              type="email"
              placeholder="אימייל"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="user">משתמש רגיל</option>
              <option value="admin">מנהל (Admin)</option>
            </select>
          </>
        )}

        <input
          type="password"
          placeholder="סיסמה"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit">{isLogin ? 'התחבר' : 'הירשם'}</button>
      </form>

      <button
        onClick={() => { setIsLogin(!isLogin); setMessage(''); }}
        style={{ marginTop: '15px', background: 'none', border: 'none', color: '#0066cc', cursor: 'pointer' }}
      >
        {isLogin ? 'אין לך חשבון? הירשם כאן' : 'כבר רשום? התחבר כאן'}
      </button>
    </div>
  );
}
