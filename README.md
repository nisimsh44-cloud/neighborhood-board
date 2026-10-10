# Neighborhood Board (לוח מודעות שכונתי) 🏘️

אפליקציית Full-Stack קהילתית המאפשרת לתושבי השכונה לצפות במודעות, לפרסם תכנים, לסנן לפי קטגוריות ולנהל תכנים בצורה מאובטחת. הפרויקט פותח במסגרת הקורס "פרויקט יישומי בפיתוח אפליקציות" (8500026).

---

## 📌 תכונות עיקריות (Core Features)

- צפייה ציבורית: כל אורח יכול לצפות בכלל המודעות בלוח ללא צורך בהתחברות.
- סינון מודעות מתקדם: סינון מהיר לפי קטגוריות (ועד, עזרה הדדית, פעילויות, כללי) בליווי ניווט עוגן חלק (#posts-container).
- אימות והרשאה כפולים:
  * הרשמה והתחברות מקומית מבוססת גיבוב סיסמאות חזק (Bcrypt).
  * התחברות חברתית באמצעות Google OAuth 2.0 עם השלמת פרופיל מותאם (דייר / בעל עסק מקומי).
- ניהול תוכן (CRUD): משתמשים רשומים יכולים לפרסם, לערוך ולמחוק מודעות פרי עטם.
- הרשאות מנהל (Admin): מחיקת כל מודעה בלוח וחסימת/מחיקת משתמשים בעייתיים לטובת שמירה על הסדר הציבורי.
- ממשק משתמש רספונסיבי: עיצוב RTL מלא המותאם למובייל ולדסקטופ באמצעות Bootstrap 5, אנימציות Ken Burns, ותיקוני תצוגה ייעודיים למניעת גלילה אופקית (overflow-x: hidden).

---

## 🏗️ ארכיטקטורת המערכת (System Architecture)

המערכת בנויה בארכיטקטורת שכבות מודולרית (MVC):
- Frontend: תבניות Jinja2 מעוצבות ב-HTML5, CSS3 מותאם אישית, ספריית Bootstrap 5 ו-JavaScript לשליטה דינמית.
- Backend: שרת Flask (Python) המספק ניתובים (Routing), אימות משתמשים וניהול סשנים.
- Database & ORM: בסיס נתונים רלציוני SQLite המנוהל באמצעות SQLAlchemy ORM.
- Production Web Server: שרת יישומי Gunicorn בתצורת Multi-threading עם 2 עובדים ו-4 תהליכונים (threads) למניעת Worker Starvation בעת הזרמת מדיה סטטית.
- Cloud Infrastructure: שרת ענן AWS EC2 (מערכת הפעלה Ubuntu 24.04 LTS).

---

## 🗄️ סכמת בסיס הנתונים (Database Schema)

### 1. טבלת משתמשים (users)
| עמודה | סוג נתון | אילוצים | תיאור |
| :--- | :--- | :--- | :--- |
| id | Integer | Primary Key | מזהה ייחודי |
| username | String(50) | Unique, Not Null | שם משתמש |
| email | String(120) | Unique, Not Null | כתובת אימייל ייחודית |
| password_hash | String(200) | Nullable | סיסמה מגובבת Bcrypt (מאפשר ריק למשתמשי Google) |
| role | String(20) | Default: resident | תפקיד: resident / business / admin |
| is_approved | Boolean | Default: True | סטטוס השלמת פרופיל |
| business_name | String(100) | Nullable | שם העסק (לחשבון עסקי) |
| business_category | String(50) | Nullable | קטגוריית העסק |
| created_at | DateTime | Default: UTC | תאריך הרשמה |

### 2. טבלת מודעות (posts)
| עמודה | סוג נתון | אילוצים | תיאור |
| :--- | :--- | :--- | :--- |
| id | Integer | Primary Key | מזהה ייחודי |
| title | String(100) | Not Null | כותרת המודעה |
| content | Text | Not Null | תוכן המודעה המלא |
| category | String(50) | Nullable, Default: כללי | קטגוריית המודעה לסינון |
| created_at | DateTime | Default: UTC | מועד פרסום המודעה |
| user_id | Integer | Foreign Key (users.id) | מזהה המשתמש שפרסם |

---

## 🔒 אבטחת מידע (Security Implementation)

1. אחסון סיסמאות מאובטח (Password Hashing): שימוש בספריית Flask-Bcrypt ליצירת Salt וגיבוב בלתי-הפיך (bcrypt.generate_password_hash). סיסמאות לעולם אינן נשמרות כטקסט גלוי.
2. מניעת SQL Injection: שימוש עקבי ב-SQLAlchemy ORM המבצע שאילתות פרמטריות (Prepared Statements) כברירת מחדל ומבודד לחלוטין את קלט המשתמש מפקודות ה-SQL.
3. הגנה מפני XSS (Cross-Site Scripting): סינון וחיטוי קלט אוטומטי באמצעות מנוע התבניות Jinja2 (Auto-escaping), ומניעת הזרקת קוד זדוני בשדות הכותרת והתוכן.
4. ניהול סודות ומפתחות (Secrets Management): מפתחות ה-API ונתוני ה-OAuth מנוהלים דרך משתני סביבה ומבודדים בקובץ .env שאינו מנוהל ב-Git.

---

## 🚀 הוראות התקנה והרצה מקומית (Local Setup)

דרישות מוקדמות:
- Python 3.10 ומעלה
- Git

שלבי הרצה:
1. שכפול המאגר וכניסה לתיקיית השרת:
   git clone https://github.com/nisimsh44-cloud/neighborhood-board.git
   cd neighborhood-board/backend

2. יצירת סביבה וירטואלית והפעלתה:
   python3 -m venv venv
   source venv/bin/activate

3. התקנת חבילות ותלויות:
   pip install -r requirements.txt

4. הגדרת משתני סביבה:
   יצירת קובץ .env בתיקיית backend עם המפתחות:
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret

5. הפעלת שרת הפיתוח:
   python3 app.py
   האתר יהיה זמין בדפדפן בכתובת: http://127.0.0.1:5000

---

## ☁️ פריסה בשרת ייצור (AWS EC2 Deployment)

המערכת מאוחסנת ורצה בשרת ענן:
- שרת: AWS EC2 (Ubuntu 24.04.4 LTS)
- כתובת ציבורית חיה: http://13.62.11.208:5000
- פקודת הרצת ייצור (Gunicorn Multi-threading):
  gunicorn -w 2 --threads 4 --timeout 60 -b 0.0.0.0:5000 app:app --daemon
