import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [posts, setPosts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('הכל');
  const [isRegistering, setIsRegistering] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState('');
  const [message, setMessage] = useState('');
  
  // מזהה המודעה שנמצאת במצב עריכה כרגע
  const [editingPostId, setEditingPostId] = useState(null);
  const [editFormData, setEditFormData] = useState({ title: '', content: '', category: 'כללי' });

  // נתוני טופס הרשמה / התחברות
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user'
  });

  // נתוני טופס מודעה חדשה
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    category: 'כללי'
  });

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5000/api/posts');
      const data = await res.json();
      setPosts(data);
    } catch (err) {
      console.error('שגיאה בטעינת המודעות:', err);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleNewPostChange = (e) => {
    setNewPost({ ...newPost, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');

    const endpoint = isRegistering ? '/api/register' : '/api/login';

    try {
      const response = await fetch(`http://127.0.0.1:5000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.message);
        if (!isRegistering) {
          setIsLoggedIn(true);
          setCurrentUser(data.username);
          localStorage.setItem('token', data.access_token);
        }
      } else {
        setMessage(data.error || 'אירעה שגיאה');
      }
    } catch (err) {
      setMessage('שגיאת תקשורת עם השרת');
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await fetch('http://127.0.0.1:5000/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newPost,
          author: currentUser || 'אורח'
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('המודעה פורסמה בהצלחה!');
        setNewPost({ title: '', content: '', category: 'כללי' });
        fetchPosts();
      } else {
        setMessage(data.error || 'אירעה שגיאה בפרסום המודעה');
      }
    } catch (err) {
      setMessage('שגיאת תקשורת עם השרת');
    }
  };

  // מחיקת מודעה
  const handleDeletePost = async (postId) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק מודעה זו?')) return;

    try {
      const response = await fetch(`http://127.0.0.1:5000/api/posts/${postId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: currentUser })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('המודעה נמחקה בהצלחה!');
        fetchPosts();
      } else {
        setMessage(data.error || 'אירעה שגיאה במחיקה');
      }
    } catch (err) {
      setMessage('שגיאת תקשורת עם השרת');
    }
  };

  // התחלת מצב עריכה
  const handleStartEdit = (post) => {
    setEditingPostId(post.id);
    setEditFormData({
      title: post.title,
      content: post.content,
      category: post.category
    });
  };

  // שמירת עריכה
  const handleSaveEdit = async (postId) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/posts/${postId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...editFormData,
          username: currentUser
        })
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('המודעה עודכנה בהצלחה!');
        setEditingPostId(null);
        fetchPosts();
      } else {
        setMessage(data.error || 'אירעה שגיאה בעדכון המודעה');
      }
    } catch (err) {
      setMessage('שגיאת תקשורת עם השרת');
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentUser('');
    localStorage.removeItem('token');
    setMessage('התנתקת בהצלחה!');
  };

  const categories = ['הכל', ...Array.from(new Set(posts.map((post) => post.category)))];

  const filteredPosts = selectedCategory === 'הכל'
    ? posts
    : posts.filter((post) => post.category === selectedCategory);

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      <header style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1>📢 לוח מודעות שכונתי</h1>
        {isLoggedIn && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span>שלום, <strong>{currentUser}</strong>! 👋</span>
            <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#dc3545', color: '#fff', border: 'none', borderRadius: '4px' }}>
              התנתק
            </button>
          </div>
        )}
      </header>

      {/* טופס התחברות / הרשמה */}
      {!isLoggedIn ? (
        <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginBottom: '30px', backgroundColor: '#f9f9f9' }}>
          <h2>{isRegistering ? 'הרשמה למערכת' : 'התחברות ללוח המודעות'}</h2>
          
          {message && <p style={{ color: message.includes('בהצלחה') ? 'green' : 'red' }}>{message}</p>}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <input
              type="text"
              name="username"
              placeholder="שם משתמש"
              value={formData.username}
              onChange={handleChange}
              required
            />

            {isRegistering && (
              <>
                <input
                  type="email"
                  name="email"
                  placeholder="אימייל"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
                <select name="role" value={formData.role} onChange={handleChange}>
                  <option value="user">משתמש רגיל</option>
                  <option value="admin">מנהל (Admin)</option>
                </select>
              </>
            )}

            <input
              type="password"
              name="password"
              placeholder="סיסמה"
              value={formData.password}
              onChange={handleChange}
              required
            />

            <button type="submit" style={{ padding: '10px', cursor: 'pointer' }}>
              {isRegistering ? 'הירשם' : 'התחבר'}
            </button>
          </form>

          <p style={{ marginTop: '15px', fontSize: '14px' }}>
            {isRegistering ? 'כבר רשום? ' : 'אין לך חשבון? '}
            <span 
              onClick={() => { setIsRegistering(!isRegistering); setMessage(''); }} 
              style={{ color: 'blue', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {isRegistering ? 'התחבר כאן' : 'הירשם כאן'}
            </span>
          </p>
        </div>
      ) : (
        /* טופס יצירת מודעה חדשה */
        <div style={{ border: '1px solid #28a745', padding: '20px', borderRadius: '8px', marginBottom: '30px', backgroundColor: '#f4fff4' }}>
          <h2>✍️ פרסום מודעה חדשה</h2>
          
          {message && <p style={{ color: message.includes('בהצלחה') ? 'green' : 'red' }}>{message}</p>}

          <form onSubmit={handleCreatePost} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <input
              type="text"
              name="title"
              placeholder="כותרת המודעה"
              value={newPost.title}
              onChange={handleNewPostChange}
              required
            />

            <select name="category" value={newPost.category} onChange={handleNewPostChange}>
              <option value="כללי">כללי</option>
              <option value="ריהוט">ריהוט</option>
              <option value="לימודים">לימודים</option>
              <option value="אלקטרוניקה">אלקטרוניקה</option>
              <option value="דרושים">דרושים</option>
            </select>

            <textarea
              name="content"
              placeholder="תוכן המודעה..."
              rows="4"
              value={newPost.content}
              onChange={handleNewPostChange}
              required
              style={{ fontFamily: 'inherit', padding: '8px' }}
            />

            <button type="submit" style={{ padding: '10px', cursor: 'pointer', backgroundColor: '#28a745', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}>
              פרסם מודעה
            </button>
          </form>
        </div>
      )}

      {/* אזור הצגת המודעות */}
      <section>
        <h2>📋 מודעות אחרונות</h2>

        {/* סרגל סינון קטגוריות */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span>סינון לפי קטגוריה:</span>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              style={{
                padding: '5px 12px',
                borderRadius: '16px',
                border: '1px solid #007bff',
                backgroundColor: selectedCategory === category ? '#007bff' : '#fff',
                color: selectedCategory === category ? '#fff' : '#007bff',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: selectedCategory === category ? 'bold' : 'normal'
              }}
            >
              {category}
            </button>
          ))}
        </div>

        {/* רשימת המודעות המסוננות */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {filteredPosts.length === 0 ? (
            <p>אין מודעות בקטגוריה זו.</p>
          ) : (
            filteredPosts.map((post) => (
              <div key={post.id} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '15px', backgroundColor: '#fff', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                
                {/* מצב עריכה עבור מודעה זו */}
                {editingPostId === post.id ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <input
                      type="text"
                      value={editFormData.title}
                      onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                    />
                    <select
                      value={editFormData.category}
                      onChange={(e) => setEditFormData({ ...editFormData, category: e.target.value })}
                    >
                      <option value="כללי">כללי</option>
                      <option value="ריהוט">ריהוט</option>
                      <option value="לימודים">לימודים</option>
                      <option value="אלקטרוניקה">אלקטרוניקה</option>
                      <option value="דרושים">דרושים</option>
                    </select>
                    <textarea
                      rows="3"
                      value={editFormData.content}
                      onChange={(e) => setEditFormData({ ...editFormData, content: e.target.value })}
                    />
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button onClick={() => handleSaveEdit(post.id)} style={{ backgroundColor: '#28a745', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>
                        שמור
                      </button>
                      <button onClick={() => setEditingPostId(null)} style={{ backgroundColor: '#6c757d', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>
                        ביטול
                      </button>
                    </div>
                  </div>
                ) : (
                  /* תצוגה רגילה של המודעה */
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h3 style={{ margin: '0 0 10px 0' }}>{post.title}</h3>
                      <span style={{ backgroundColor: '#e0e0e0', padding: '4px 8px', borderRadius: '4px', fontSize: '12px' }}>
                        {post.category}
                      </span>
                    </div>
                    <p style={{ margin: '0 0 10px 0' }}>{post.content}</p>
                    <div style={{ fontSize: '12px', color: '#666', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>פורסם על ידי: <strong>{post.author}</strong> ({post.created_at})</span>
                      
                      {/* כפתורי עריכה ומחיקה יופיעו רק אם המשתמש המחובר הוא היוצר */}
                      {isLoggedIn && currentUser === post.author && (
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => handleStartEdit(post)}
                            style={{ backgroundColor: '#ffc107', color: '#000', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                          >
                            ✏️ ערוך
                          </button>
                          <button
                            onClick={() => handleDeletePost(post.id)}
                            style={{ backgroundColor: '#dc3545', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                          >
                            🗑️ מחק
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

export default App;
