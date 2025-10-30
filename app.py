# """
# Enhanced Habit Tracker - Production Ready
# Features: Modern UI, AI Integration (Ollama/OpenAI), PWA, Analytics
# """

# import os
# import sqlite3
# import json
# import datetime
# import secrets
# from functools import wraps
# from typing import List, Optional
# import io
# import csv
# import csrf
# from flask_wtf.csrf import CSRFError



# from flask import (
#     Flask, g, redirect, render_template, request, session, 
#     url_for, jsonify, send_file, abort, Response
# )
# from flask_wtf import FlaskForm
# from flask_wtf.csrf import CSRFProtect
# from wtforms import StringField, PasswordField, SelectField, BooleanField
# from wtforms.validators import InputRequired, Length, Email
# from werkzeug.security import generate_password_hash, check_password_hash

# # AI Integration
# try:
#     import requests
#     REQUESTS_AVAILABLE = True
# except ImportError:
#     REQUESTS_AVAILABLE = False

# # Configuration
# class Config:
#     SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
#     DATABASE = os.path.join(os.path.dirname(__file__), "data", "habit_tracker.db")
    
#     # AI Configuration - Toggle between Ollama (local/free) and OpenAI
#     USE_OLLAMA = os.environ.get("USE_OLLAMA", "1") == "1"  # Default: Ollama
#     OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
#     OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2")
    
#     OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # Set when deploying
#     OPENAI_MODEL = "gpt-3.5-turbo"
    
#     AI_TIMEOUT = 15
#     MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# app = Flask(__name__)
# app.config.from_object(Config)
# csrf = CSRFProtect(app)

# # Ensure data directory exists
# os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)

# # ============================================================================
# # DATABASE SETUP
# # ============================================================================

# def get_db():
#     """Get database connection."""
#     db = getattr(g, "_db", None)
#     if db is None:
#         db = g._db = sqlite3.connect(
#             Config.DATABASE, 
#             detect_types=sqlite3.PARSE_DECLTYPES
#         )
#         db.row_factory = sqlite3.Row
#     return db

# def init_db():
#     """Initialize database with enhanced schema."""
#     schema = """
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT UNIQUE NOT NULL,
#         email TEXT UNIQUE,
#         password TEXT NOT NULL,
#         profile TEXT NOT NULL,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         theme TEXT DEFAULT 'light',
#         notifications_enabled INTEGER DEFAULT 1
#     );
    
#     CREATE TABLE IF NOT EXISTS habits (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER NOT NULL,
#         title TEXT NOT NULL,
#         description TEXT,
#         category TEXT DEFAULT 'personal',
#         frequency INTEGER DEFAULT 1,
#         reminder_time TEXT,
#         color TEXT DEFAULT '#6366f1',
#         icon TEXT DEFAULT '⭐',
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         share_token TEXT UNIQUE,
#         archived INTEGER DEFAULT 0,
#         FOREIGN KEY(user_id) REFERENCES users(id)
#     );
    
#     CREATE TABLE IF NOT EXISTS checkins (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         habit_id INTEGER NOT NULL,
#         check_date DATE NOT NULL,
#         done INTEGER NOT NULL DEFAULT 1,
#         note TEXT,
#         mood TEXT,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY(habit_id) REFERENCES habits(id),
#         UNIQUE(habit_id, check_date)
#     );
    
#     CREATE TABLE IF NOT EXISTS ai_suggestions (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         profile TEXT,
#         suggestion TEXT,
#         category TEXT
#     );
    
#     CREATE TABLE IF NOT EXISTS user_stats (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER NOT NULL,
#         stat_date DATE NOT NULL,
#         total_habits INTEGER DEFAULT 0,
#         completed_habits INTEGER DEFAULT 0,
#         streak INTEGER DEFAULT 0,
#         FOREIGN KEY(user_id) REFERENCES users(id),
#         UNIQUE(user_id, stat_date)
#     );
#     """
    
#     db = get_db()
#     db.executescript(schema)
    
#     # Insert default suggestions if empty
#     cur = db.cursor()
#     cur.execute("SELECT COUNT(*) as c FROM ai_suggestions")
#     if cur.fetchone()["c"] == 0:
#         suggestions = [
#             ("student", "Morning review: 15 minutes", "learning"),
#             ("student", "Exercise between study sessions", "health"),
#             ("student", "Read 20 pages daily", "learning"),
#             ("businessman", "Morning planning ritual", "productivity"),
#             ("businessman", "Network: 3 contacts daily", "career"),
#             ("businessman", "Evening reflection: 10 minutes", "productivity"),
#             ("normal", "Walk 10,000 steps", "health"),
#             ("normal", "Drink 8 glasses of water", "health"),
#             ("normal", "Gratitude journal", "mindfulness"),
#             ("normal", "7+ hours sleep", "health"),
#         ]
#         cur.executemany(
#             "INSERT INTO ai_suggestions(profile, suggestion, category) VALUES (?,?,?)", 
#             suggestions
#         )
#         db.commit()

# @app.teardown_appcontext
# def close_connection(exc):
#     """Close database connection."""
#     db = getattr(g, "_db", None)
#     if db is not None:
#         db.close()

# # ============================================================================
# # FORMS
# # ============================================================================

# class RegisterForm(FlaskForm):
#     username = StringField("Username", validators=[
#         InputRequired(), 
#         Length(min=3, max=50)
#     ])
#     email = StringField("Email (optional)", validators=[Length(max=120)])
#     password = PasswordField("Password", validators=[
#         InputRequired(), 
#         Length(min=6, max=200)
#     ])
#     profile = SelectField("Profile", choices=[
#         ("student", "Student"),
#         ("businessman", "Professional"),
#         ("normal", "Personal")
#     ])

# class LoginForm(FlaskForm):
#     username = StringField("Username", validators=[InputRequired()])
#     password = PasswordField("Password", validators=[InputRequired()])
#     remember = BooleanField("Remember me")

# # ============================================================================
# # AUTH DECORATORS
# # ============================================================================

# def login_required(f):
#     """Require user to be logged in."""
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if "user_id" not in session:
#             return redirect(url_for("index"))
#         return f(*args, **kwargs)
#     return decorated_function

# # ============================================================================
# # AI INTEGRATION
# # ============================================================================

# class AIService:
#     """Handle AI suggestions using Ollama or OpenAI."""
    
#     @staticmethod
#     def generate_suggestions(profile: str, prompt: str, count: int = 6) -> List[str]:
#         """Generate habit suggestions using AI."""
        
#         if not REQUESTS_AVAILABLE:
#             return AIService._fallback_suggestions(profile, count)
        
#         # Try Ollama first (free, local)
#         if Config.USE_OLLAMA:
#             suggestions = AIService._ollama_generate(profile, prompt, count)
#             if suggestions:
#                 return suggestions
        
#         # Try OpenAI if configured
#         if Config.OPENAI_API_KEY:
#             suggestions = AIService._openai_generate(profile, prompt, count)
#             if suggestions:
#                 return suggestions
        
#         # Fallback to database
#         return AIService._fallback_suggestions(profile, count)
    
#     @staticmethod
#     def _ollama_generate(profile: str, prompt: str, count: int) -> Optional[List[str]]:
#         """Generate using Ollama (local LLM)."""
#         try:
#             full_prompt = f"""You are a habit formation expert. Generate {count} specific, actionable habit suggestions for a {profile}.

# User request: {prompt}

# Rules:
# - Each habit should be clear and specific
# - Include time/quantity when relevant
# - Make them achievable
# - One habit per line
# - No numbering or bullets

# Generate {count} habits:"""

#             payload = {
#                 "model": Config.OLLAMA_MODEL,
#                 "prompt": full_prompt,
#                 "stream": False,
#                 "options": {
#                     "temperature": 0.7,
#                     "top_p": 0.9
#                 }
#             }
            
#             response = requests.post(
#                 Config.OLLAMA_URL,
#                 json=payload,
#                 timeout=Config.AI_TIMEOUT
#             )
#             response.raise_for_status()
            
#             data = response.json()
#             text = data.get("response", "")
            
#             # Parse suggestions
#             suggestions = [
#                 line.strip().lstrip("123456789.-•") 
#                 for line in text.split("\n") 
#                 if line.strip() and len(line.strip()) > 10
#             ]
            
#             return suggestions[:count] if suggestions else None
            
#         except Exception as e:
#             print(f"Ollama error: {e}")
#             return None
    
#     @staticmethod
#     def _openai_generate(profile: str, prompt: str, count: int) -> Optional[List[str]]:
#         """Generate using OpenAI API."""
#         try:
#             headers = {
#                 "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
#                 "Content-Type": "application/json"
#             }
            
#             payload = {
#                 "model": Config.OPENAI_MODEL,
#                 "messages": [{
#                     "role": "user",
#                     "content": f"Generate {count} specific habit suggestions for a {profile}. Request: {prompt}. Return only the habits, one per line, no numbering."
#                 }],
#                 "temperature": 0.7,
#                 "max_tokens": 300
#             }
            
#             response = requests.post(
#                 "https://api.openai.com/v1/chat/completions",
#                 headers=headers,
#                 json=payload,
#                 timeout=Config.AI_TIMEOUT
#             )
#             response.raise_for_status()
            
#             data = response.json()
#             text = data["choices"][0]["message"]["content"]
            
#             suggestions = [
#                 line.strip().lstrip("123456789.-•") 
#                 for line in text.split("\n") 
#                 if line.strip() and len(line.strip()) > 10
#             ]
            
#             return suggestions[:count] if suggestions else None
            
#         except Exception as e:
#             print(f"OpenAI error: {e}")
#             return None
    
#     @staticmethod
#     def _fallback_suggestions(profile: str, count: int) -> List[str]:
#         """Fallback to database suggestions."""
#         db = get_db()
#         cur = db.execute(
#             "SELECT suggestion FROM ai_suggestions WHERE profile = ? ORDER BY RANDOM() LIMIT ?",
#             (profile, count)
#         )
#         suggestions = [row["suggestion"] for row in cur.fetchall()]
        
#         # Add generic ones if needed
#         generic = [
#             "Drink 8 glasses of water daily",
#             "10 minutes morning meditation",
#             "Evening gratitude journal",
#             "20-minute daily walk",
#             "Read 20 pages",
#             "7+ hours quality sleep"
#         ]
        
#         return (suggestions + generic)[:count]

# # ============================================================================
# # ROUTES - AUTH
# # ============================================================================

# @app.route("/", methods=["GET", "POST"])
# def index():
#     """Landing page with modern auth."""
#     if "user_id" in session:
#         return redirect(url_for("dashboard"))
    
#     register_form = RegisterForm()
#     login_form = LoginForm()
    
#     # Handle registration
#     if register_form.validate_on_submit() and request.form.get("form_type") == "register":
#         db = get_db()
#         try:
#             hashed = generate_password_hash(register_form.password.data, method='pbkdf2:sha256')
#             db.execute(
#                 "INSERT INTO users (username, email, password, profile) VALUES (?,?,?,?)",
#                 (
#                     register_form.username.data,
#                     register_form.email.data or None,
#                     hashed,
#                     register_form.profile.data
#                 )
#             )
#             db.commit()
#             return jsonify({"success": True, "redirect": url_for("index")})
#         except sqlite3.IntegrityError:
#             return jsonify({"success": False, "error": "Username already exists"}), 400
    
#     # Handle login
#     if login_form.validate_on_submit() and request.form.get("form_type") == "login":
#         db = get_db()
#         user = db.execute(
#             "SELECT * FROM users WHERE username = ?", 
#             (login_form.username.data,)
#         ).fetchone()
        
#         if user and check_password_hash(user["password"], login_form.password.data):
#             session.permanent = login_form.remember.data
#             session["user_id"] = user["id"]
#             session["username"] = user["username"]
#             session["profile"] = user["profile"]
#             return jsonify({"success": True, "redirect": url_for("dashboard")})
#         else:
#             return jsonify({"success": False, "error": "Invalid credentials"}), 401
    
#     return render_template("index.html", register=register_form, login=login_form)

# @app.route("/logout")
# def logout():
#     """Logout user."""
#     session.clear()
#     return redirect(url_for("index"))

# # ============================================================================
# # ROUTES - DASHBOARD
# # ============================================================================

# @app.route("/dashboard")
# @login_required
# def dashboard():
#     """Main dashboard."""
#     user_id = session["user_id"]
#     db = get_db()
    
#     # Get habits with stats
#     habits = db.execute("""
#         SELECT h.*, 
#                COUNT(DISTINCT c.check_date) as total_checkins,
#                SUM(CASE WHEN c.check_date >= date('now', '-30 days') THEN 1 ELSE 0 END) as recent_checkins
#         FROM habits h
#         LEFT JOIN checkins c ON h.id = c.habit_id AND c.done = 1
#         WHERE h.user_id = ? AND h.archived = 0
#         GROUP BY h.id
#         ORDER BY h.created_at DESC
#     """, (user_id,)).fetchall()
    
#     habit_stats = []
#     for h in habits:
#         # Calculate streak
#         streak = 0
#         check_date = datetime.date.today()
#         while True:
#             row = db.execute(
#                 "SELECT done FROM checkins WHERE habit_id = ? AND check_date = ?",
#                 (h["id"], check_date.isoformat())
#             ).fetchone()
            
#             if row and row["done"] == 1:
#                 streak += 1
#                 check_date -= datetime.timedelta(days=1)
#             else:
#                 break
        
#         completion_rate = (h["recent_checkins"] / 30 * 100) if h["recent_checkins"] else 0
        
#         habit_stats.append({
#             "id": h["id"],
#             "title": h["title"],
#             "description": h["description"],
#             "category": h["category"],
#             "color": h["color"],
#             "icon": h["icon"],
#             "streak": streak,
#             "completion_rate": round(completion_rate, 1),
#             "total_checkins": h["total_checkins"],
#             "reminder_time": h["reminder_time"]
#         })
    
#     # Get AI suggestions
#     suggestions = AIService.generate_suggestions(
#         session.get("profile", "normal"),
#         f"Suggest habits for {session.get('profile', 'normal')}",
#         6
#     )
    
#     # Overall stats
#     total_habits = len(habit_stats)
#     today = datetime.date.today().isoformat()
#     completed_today = db.execute("""
#         SELECT COUNT(DISTINCT habit_id) 
#         FROM checkins 
#         WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
#         AND check_date = ? AND done = 1
#     """, (user_id, today)).fetchone()[0]
    
#     return render_template(
#         "dashboard.html",
#         habits=habit_stats,
#         suggestions=suggestions,
#         username=session.get("username"),
#         total_habits=total_habits,
#         completed_today=completed_today
#     )

# # ============================================================================
# # ROUTES - HABITS
# # ============================================================================
# @csrf.exempt
# @app.route("/habits/create", methods=["POST"])
# @login_required
# def create_habit():
#     """Create new habit."""
#     user_id = session["user_id"]
#     data = request.get_json() if request.is_json else request.form
    
#     title = data.get("title", "").strip()
#     if not title:
#         return jsonify({"error": "Title required"}), 400
    
#     db = get_db()
#     cursor = db.execute("""
#         INSERT INTO habits (user_id, title, description, category, frequency, reminder_time, color, icon)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#     """, (
#         user_id,
#         title,
#         data.get("description", "").strip(),
#         data.get("category", "personal"),
#         int(data.get("frequency", 1)),
#         data.get("reminder_time"),
#         data.get("color", "#6366f1"),
#         data.get("icon", "⭐")
#     ))
#     db.commit()
    
#     return jsonify({"success": True, "habit_id": cursor.lastrowid})

# # @app.route("/habits/<int:habit_id>")
# # @login_required
# # def habit_detail(habit_id):
# #     """Habit detail page."""
# #     db = get_db()
# #     habit = db.execute(
# #         "SELECT * FROM habits WHERE id = ? AND user_id = ?",
# #         (habit_id, session["user_id"])
# #     ).fetchone()
    
# #     if not habit:
# #         abort(404)
    
# #     # Get recent checkins
# #     checkins = db.execute("""
# #         SELECT check_date, done, note, mood
# #         FROM checkins
# #         WHERE habit_id = ?
# #         ORDER BY check_date DESC
# #         LIMIT 90
# #     """, (habit_id,)).fetchall()
    
# #     return render_template("habit_detail.html", habit=habit, checkins=checkins)




# @app.route("/habits/<int:habit_id>")
# @login_required
# def habit_detail(habit_id):
#     """Habit detail page."""
#     db = get_db()
#     habit = db.execute(
#         "SELECT * FROM habits WHERE id = ? AND user_id = ?",
#         (habit_id, session["user_id"])
#     ).fetchone()
    
#     if not habit:
#         abort(404)
    
#     # Get recent checkins
#     checkins = db.execute("""
#         SELECT check_date, done, note, mood
#         FROM checkins
#         WHERE habit_id = ?
#         ORDER BY check_date DESC
#         LIMIT 90
#     """, (habit_id,)).fetchall()
    
#     # Calculate streak
#     streak = 0
#     check_date = datetime.date.today()
#     while True:
#         row = db.execute(
#             "SELECT done FROM checkins WHERE habit_id = ? AND check_date = ?",
#             (habit_id, check_date.isoformat())
#         ).fetchone()
        
#         if row and row["done"] == 1:
#             streak += 1
#             check_date -= datetime.timedelta(days=1)
#         else:
#             break
    
#     return render_template("habit_detail.html", habit=habit, checkins=checkins, streak=streak)






# @app.route("/habits/<int:habit_id>/checkin", methods=["POST"])
# @login_required
# def checkin(habit_id):
#     """Check in a habit."""
#     db = get_db()
    
#     # Verify ownership
#     habit = db.execute(
#         "SELECT id FROM habits WHERE id = ? AND user_id = ?",
#         (habit_id, session["user_id"])
#     ).fetchone()
    
#     if not habit:
#         return jsonify({"error": "Not found"}), 404
    
#     data = request.get_json() if request.is_json else request.form
#     check_date = data.get("date", datetime.date.today().isoformat())
#     done = 1 if data.get("done", "1") in ("1", "true", "on", True) else 0
#     note = data.get("note", "")
#     mood = data.get("mood", "")
    
#     db.execute("""
#         INSERT INTO checkins (habit_id, check_date, done, note, mood)
#         VALUES (?, ?, ?, ?, ?)
#         ON CONFLICT(habit_id, check_date) 
#         DO UPDATE SET done=?, note=?, mood=?, created_at=CURRENT_TIMESTAMP
#     """, (habit_id, check_date, done, note, mood, done, note, mood))
    
#     db.commit()
    
#     return jsonify({"success": True})






# @app.route("/habits/<int:habit_id>/delete", methods=["POST"])
# @login_required
# def delete_habit(habit_id):
#     """Delete/archive a habit."""
#     db = get_db()
#     db.execute(
#         "UPDATE habits SET archived = 1 WHERE id = ? AND user_id = ?",
#         (habit_id, session["user_id"])
#     )
#     db.commit()
    
#     return jsonify({"success": True})

# # ============================================================================
# # ROUTES - AI & ANALYTICS
# # ============================================================================

# @app.route("/api/ai/suggestions", methods=["POST"])
# @login_required
# def api_ai_suggestions():
#     """Get AI suggestions."""
#     data = request.get_json()
#     prompt = data.get("prompt", "Suggest habits")
#     profile = session.get("profile", "normal")
    
#     suggestions = AIService.generate_suggestions(profile, prompt, 8)
    
#     return jsonify({
#         "suggestions": suggestions,
#         "using_ai": Config.USE_OLLAMA or bool(Config.OPENAI_API_KEY)
#     })

# @app.route("/api/analytics")
# @login_required
# def api_analytics():
#     """Get user analytics."""
#     user_id = session["user_id"]
#     db = get_db()
    
#     # Last 30 days completion rate
#     stats = db.execute("""
#         SELECT 
#             DATE(check_date) as date,
#             COUNT(DISTINCT habit_id) as completed
#         FROM checkins
#         WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
#         AND check_date >= date('now', '-30 days')
#         AND done = 1
#         GROUP BY DATE(check_date)
#         ORDER BY date
#     """, (user_id,)).fetchall()
    
#     return jsonify({
#         "daily_completion": [{"date": s["date"], "count": s["completed"]} for s in stats]
#     })

# # ============================================================================
# # ROUTES - EXPORT & SHARE
# # ============================================================================

# @app.route("/export/csv")
# @login_required
# def export_csv():
#     """Export habits to CSV."""
#     user_id = session["user_id"]
#     db = get_db()
    
#     habits = db.execute(
#         "SELECT * FROM habits WHERE user_id = ?", 
#         (user_id,)
#     ).fetchall()
    
#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(["Habit", "Description", "Category", "Date", "Completed", "Note"])
    
#     for habit in habits:
#         checkins = db.execute(
#             "SELECT * FROM checkins WHERE habit_id = ? ORDER BY check_date",
#             (habit["id"],)
#         ).fetchall()
        
#         if not checkins:
#             writer.writerow([habit["title"], habit["description"], habit["category"], "", "", ""])
#         else:
#             for c in checkins:
#                 writer.writerow([
#                     habit["title"],
#                     habit["description"],
#                     habit["category"],
#                     c["check_date"],
#                     "Yes" if c["done"] else "No",
#                     c["note"] or ""
#                 ])
    
#     output.seek(0)
#     buf = io.BytesIO(output.read().encode("utf-8"))
    
#     filename = f"habits_{session['username']}_{datetime.date.today()}.csv"
#     return send_file(buf, as_attachment=True, download_name=filename, mimetype="text/csv")

# # ============================================================================
# # PWA ROUTES
# # ============================================================================

# @app.route("/manifest.json")
# def manifest():
#     """PWA manifest."""
#     return jsonify({
#         "name": "HabitFlow - Track Your Progress",
#         "short_name": "HabitFlow",
#         "start_url": "/",
#         "display": "standalone",
#         "background_color": "#ffffff",
#         "theme_color": "#6366f1",
#         "icons": [
#             {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
#             {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}
#         ]
#     })

# @app.route("/service-worker.js")
# def service_worker():
#     """Service worker for PWA."""
#     sw = """
# self.addEventListener('install', (e) => {
#   self.skipWaiting();
# });

# self.addEventListener('activate', (e) => {
#   self.clients.claim();
# });

# self.addEventListener('fetch', (e) => {
#   e.respondWith(
#     fetch(e.request).catch(() => caches.match(e.request))
#   );
# });
# """
#     return Response(sw, mimetype="application/javascript")

# # ============================================================================
# # ERROR HANDLERS
# # ============================================================================

# @app.errorhandler(404)
# def not_found(e):
#     """404 handler."""
#     return render_template("404.html"), 404

# @app.errorhandler(500)
# def server_error(e):
#     """500 handler."""
#     return render_template("500.html"), 500

# # ============================================================================
# # INITIALIZATION
# # ============================================================================

# with app.app_context():
#     if not os.path.exists(Config.DATABASE):
#         open(Config.DATABASE, "a").close()
#     init_db()

# if __name__ == "__main__":
#     print("=" * 60)
#     print("🚀 HabitFlow Tracker Starting...")
#     print("=" * 60)
#     print(f"📊 Database: {Config.DATABASE}")
#     print(f"🤖 AI Mode: {'Ollama (Local)' if Config.USE_OLLAMA else 'OpenAI'}")
#     if Config.USE_OLLAMA:
#         print(f"🔗 Ollama URL: {Config.OLLAMA_URL}")
#     print("=" * 60)
    
#     app.run(
#         debug=True,
#         host="0.0.0.0",
#         port=int(os.environ.get("PORT", 5000))
#     )














# New version of Code

"""
Enhanced Habit Tracker - Production Ready
Features: Modern UI, AI Integration (Ollama/OpenAI), PWA, Analytics
"""

import os
import sqlite3
import json
import datetime
import secrets
from functools import wraps
from typing import List, Optional
import io
import csv
import csrf 

from flask import (
    Flask, g, redirect, render_template, request, session, 
    url_for, jsonify, send_file, abort, Response
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError , CSRF
from flask_wtf.csrf import CSRF as csrf_exempt
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import InputRequired, Length, Email
from werkzeug.security import generate_password_hash, check_password_hash

# AI Integration
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configuration
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    DATABASE = os.path.join(os.path.dirname(__file__), "data", "habit_tracker.db")
    
    # AI Configuration - Toggle between Ollama (local/free) and OpenAI
    USE_OLLAMA = os.environ.get("USE_OLLAMA", "1") == "1"  # Default: Ollama
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2")
    
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # Set when deploying
    OPENAI_MODEL = "gpt-3.5-turbo"
    
    AI_TIMEOUT = 15
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    # WTF_CSRF_ENABLED = True
    WTF_CSRF_ENABLED = False
    WTF_CSRF_TIME_LIMIT = None

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app) 
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Add this line

# csrf.exempt_views.add('checkin')
# csrf.exempt_views.add('create_habit')
# csrf.exempt_views.add('delete_habit')
# csrf.exempt_views.add('api_ai_suggestions')
# csrf.exempt_views.add('checkin')

# Ensure data directory exists
os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)

# ============================================================================
# DATABASE SETUP
# ============================================================================

def get_db():
    """Get database connection."""
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(
            Config.DATABASE, 
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with enhanced schema."""
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password TEXT NOT NULL,
        profile TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        theme TEXT DEFAULT 'light',
        notifications_enabled INTEGER DEFAULT 1
    );
    
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'personal',
        frequency INTEGER DEFAULT 1,
        reminder_time TEXT,
        color TEXT DEFAULT '#6366f1',
        icon TEXT DEFAULT '⭐',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        share_token TEXT UNIQUE,
        archived INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    
    CREATE TABLE IF NOT EXISTS checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        check_date DATE NOT NULL,
        done INTEGER NOT NULL DEFAULT 1,
        note TEXT,
        mood TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(habit_id) REFERENCES habits(id),
        UNIQUE(habit_id, check_date)
    );
    
    CREATE TABLE IF NOT EXISTS ai_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile TEXT,
        suggestion TEXT,
        category TEXT
    );
    
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stat_date DATE NOT NULL,
        total_habits INTEGER DEFAULT 0,
        completed_habits INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id),
        UNIQUE(user_id, stat_date)
    );
    """
    
    db = get_db()
    db.executescript(schema)
    
    # Insert default suggestions if empty
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) as c FROM ai_suggestions")
    if cur.fetchone()["c"] == 0:
        suggestions = [
            ("student", "Morning review: 15 minutes", "learning"),
            ("student", "Exercise between study sessions", "health"),
            ("student", "Read 20 pages daily", "learning"),
            ("businessman", "Morning planning ritual", "productivity"),
            ("businessman", "Network: 3 contacts daily", "career"),
            ("businessman", "Evening reflection: 10 minutes", "productivity"),
            ("normal", "Walk 10,000 steps", "health"),
            ("normal", "Drink 8 glasses of water", "health"),
            ("normal", "Gratitude journal", "mindfulness"),
            ("normal", "7+ hours sleep", "health"),
        ]
        cur.executemany(
            "INSERT INTO ai_suggestions(profile, suggestion, category) VALUES (?,?,?)", 
            suggestions
        )
        db.commit()

@app.teardown_appcontext
def close_connection(exc):
    """Close database connection."""
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

# ============================================================================
# FORMS
# ============================================================================

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        InputRequired(), 
        Length(min=3, max=50)
    ])
    email = StringField("Email (optional)", validators=[Length(max=120)])
    password = PasswordField("Password", validators=[
        InputRequired(), 
        Length(min=6, max=200)
    ])
    profile = SelectField("Profile", choices=[
        ("student", "Student"),
        ("businessman", "Professional"),
        ("normal", "Personal")
    ])

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    remember = BooleanField("Remember me")

# ============================================================================
# AUTH DECORATORS
# ============================================================================

def login_required(f):
    """Require user to be logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# AI INTEGRATION
# ============================================================================

class AIService:
    """Handle AI suggestions using Ollama or OpenAI."""
    
    @staticmethod
    def generate_suggestions(profile: str, prompt: str, count: int = 6) -> List[str]:
        """Generate habit suggestions using AI."""
        
        if not REQUESTS_AVAILABLE:
            return AIService._fallback_suggestions(profile, count)
        
        # Try Ollama first (free, local)
        if Config.USE_OLLAMA:
            suggestions = AIService._ollama_generate(profile, prompt, count)
            if suggestions:
                return suggestions
        
        # Try OpenAI if configured
        if Config.OPENAI_API_KEY:
            suggestions = AIService._openai_generate(profile, prompt, count)
            if suggestions:
                return suggestions
        
        # Fallback to database
        return AIService._fallback_suggestions(profile, count)
    
    @staticmethod
    def _ollama_generate(profile: str, prompt: str, count: int) -> Optional[List[str]]:
        """Generate using Ollama (local LLM)."""
        try:
            full_prompt = f"""You are a habit formation expert. Generate {count} specific, actionable habit suggestions for a {profile}.

User request: {prompt}

Rules:
- Each habit should be clear and specific
- Include time/quantity when relevant
- Make them achievable
- One habit per line
- No numbering or bullets

Generate {count} habits:"""

            payload = {
                "model": Config.OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                Config.OLLAMA_URL,
                json=payload,
                timeout=Config.AI_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            text = data.get("response", "")
            
            # Parse suggestions
            suggestions = [
                line.strip().lstrip("123456789.-•") 
                for line in text.split("\n") 
                if line.strip() and len(line.strip()) > 10
            ]
            
            return suggestions[:count] if suggestions else None
            
        except Exception as e:
            print(f"Ollama error: {e}")
            return None
    
    @staticmethod
    def _openai_generate(profile: str, prompt: str, count: int) -> Optional[List[str]]:
        """Generate using OpenAI API."""
        try:
            headers = {
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": Config.OPENAI_MODEL,
                "messages": [{
                    "role": "user",
                    "content": f"Generate {count} specific habit suggestions for a {profile}. Request: {prompt}. Return only the habits, one per line, no numbering."
                }],
                "temperature": 0.7,
                "max_tokens": 300
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=Config.AI_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            
            suggestions = [
                line.strip().lstrip("123456789.-•") 
                for line in text.split("\n") 
                if line.strip() and len(line.strip()) > 10
            ]
            
            return suggestions[:count] if suggestions else None
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            return None
    
    @staticmethod
    def _fallback_suggestions(profile: str, count: int) -> List[str]:
        """Fallback to database suggestions."""
        db = get_db()
        cur = db.execute(
            "SELECT suggestion FROM ai_suggestions WHERE profile = ? ORDER BY RANDOM() LIMIT ?",
            (profile, count)
        )
        suggestions = [row["suggestion"] for row in cur.fetchall()]
        
        # Add generic ones if needed
        generic = [
            "Drink 8 glasses of water daily",
            "10 minutes morning meditation",
            "Evening gratitude journal",
            "20-minute daily walk",
            "Read 20 pages",
            "7+ hours quality sleep"
        ]
        
        return (suggestions + generic)[:count]

# ============================================================================
# ROUTES - AUTH
# ============================================================================

@app.route("/", methods=["GET", "POST"])
def index():
    """Landing page with modern auth."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    
    register_form = RegisterForm()
    login_form = LoginForm()
    
    # Handle registration
    if register_form.validate_on_submit() and request.form.get("form_type") == "register":
        db = get_db()
        try:
            hashed = generate_password_hash(register_form.password.data, method='pbkdf2:sha256')
            db.execute(
                "INSERT INTO users (username, email, password, profile) VALUES (?,?,?,?)",
                (
                    register_form.username.data,
                    register_form.email.data or None,
                    hashed,
                    register_form.profile.data
                )
            )
            db.commit()
            return jsonify({"success": True, "redirect": url_for("index")})
        except sqlite3.IntegrityError:
            return jsonify({"success": False, "error": "Username already exists"}), 400
    
    # Handle login
    if login_form.validate_on_submit() and request.form.get("form_type") == "login":
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", 
            (login_form.username.data,)
        ).fetchone()
        
        if user and check_password_hash(user["password"], login_form.password.data):
            session.permanent = login_form.remember.data
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["profile"] = user["profile"]
            return jsonify({"success": True, "redirect": url_for("dashboard")})
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
    
    return render_template("index.html", register=register_form, login=login_form)

@app.route("/logout")
def logout():
    """Logout user."""
    session.clear()
    return redirect(url_for("index"))

# ============================================================================
# ROUTES - DASHBOARD
# ============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard."""
    user_id = session["user_id"]
    db = get_db()
    
    # Get habits with stats
    habits = db.execute("""
        SELECT h.*, 
               COUNT(DISTINCT c.check_date) as total_checkins,
               SUM(CASE WHEN c.check_date >= date('now', '-30 days') THEN 1 ELSE 0 END) as recent_checkins
        FROM habits h
        LEFT JOIN checkins c ON h.id = c.habit_id AND c.done = 1
        WHERE h.user_id = ? AND h.archived = 0
        GROUP BY h.id
        ORDER BY h.created_at DESC
    """, (user_id,)).fetchall()
    
    habit_stats = []
    for h in habits:
        # Calculate streak
        streak = 0
        check_date = datetime.date.today()
        while True:
            row = db.execute(
                "SELECT done FROM checkins WHERE habit_id = ? AND check_date = ?",
                (h["id"], check_date.isoformat())
            ).fetchone()
            
            if row and row["done"] == 1:
                streak += 1
                check_date -= datetime.timedelta(days=1)
            else:
                break
        
        completion_rate = (h["recent_checkins"] / 30 * 100) if h["recent_checkins"] else 0
        
        habit_stats.append({
            "id": h["id"],
            "title": h["title"],
            "description": h["description"],
            "category": h["category"],
            "color": h["color"],
            "icon": h["icon"],
            "streak": streak,
            "completion_rate": round(completion_rate, 1),
            "total_checkins": h["total_checkins"],
            "reminder_time": h["reminder_time"]
        })
    
    # Get AI suggestions
    suggestions = AIService.generate_suggestions(
        session.get("profile", "normal"),
        f"Suggest habits for {session.get('profile', 'normal')}",
        6
    )
    
    # Overall stats
    total_habits = len(habit_stats)
    today = datetime.date.today().isoformat()
    completed_today = db.execute("""
        SELECT COUNT(DISTINCT habit_id) 
        FROM checkins 
        WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
        AND check_date = ? AND done = 1
    """, (user_id, today)).fetchone()[0]
    
    return render_template(
        "dashboard.html",
        habits=habit_stats,
        suggestions=suggestions,
        username=session.get("username"),
        total_habits=total_habits,
        completed_today=completed_today
    )

# ============================================================================
# ROUTES - HABITS
# ============================================================================

@app.route("/habits/create", methods=["POST"])
@login_required
@csrf.exempt
def create_habit():
    """Create new habit."""
    user_id = session["user_id"]
    data = request.get_json() if request.is_json else request.form
    
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title required"}), 400
    
    db = get_db()
    cursor = db.execute("""
        INSERT INTO habits (user_id, title, description, category, frequency, reminder_time, color, icon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        title,
        data.get("description", "").strip(),
        data.get("category", "personal"),
        int(data.get("frequency", 1)),
        data.get("reminder_time"),
        data.get("color", "#6366f1"),
        data.get("icon", "⭐")
    ))
    db.commit()
    
    return jsonify({"success": True, "habit_id": cursor.lastrowid})

# @app.route("/habits/<int:habit_id>")
# @login_required
# def habit_detail(habit_id):
#     """Habit detail page."""
#     db = get_db()
#     habit = db.execute(
#         "SELECT * FROM habits WHERE id = ? AND user_id = ?",
#         (habit_id, session["user_id"])
#     ).fetchone()
    
#     if not habit:
#         abort(404)
    
#     # Get recent checkins
#     checkins = db.execute("""
#         SELECT check_date, done, note, mood
#         FROM checkins
#         WHERE habit_id = ?
#         ORDER BY check_date DESC
#         LIMIT 90
#     """, (habit_id,)).fetchall()
    
#     # Calculate streak
#     streak = 0
#     check_date = datetime.date.today()
#     while True:
#         row = db.execute(
#             "SELECT done FROM checkins WHERE habit_id = ? AND check_date = ?",
#             (habit_id, check_date.isoformat())
#         ).fetchone()
        
#         if row and row["done"] == 1:
#             streak += 1
#             check_date -= datetime.timedelta(days=1)
#         else:
#             break
    
#     # Get today's date
#     today = datetime.date.today().isoformat()
    
#     return render_template("habit-detail.html", habit=habit, checkins=checkins, streak=streak, today=today)
@app.route("/habits/<int:habit_id>")
@login_required
def habit_detail(habit_id):
    """Habit detail page."""
    db = get_db()
    habit = db.execute(
        "SELECT * FROM habits WHERE id = ? AND user_id = ?",
        (habit_id, session["user_id"])
    ).fetchone()
    
    if not habit:
        abort(404)
    
    # Get recent checkins
    checkins = db.execute("""
        SELECT check_date, done, note, mood
        FROM checkins
        WHERE habit_id = ?
        ORDER BY check_date DESC
        LIMIT 90
    """, (habit_id,)).fetchall()
    
    # Calculate streak
    streak = 0
    check_date = datetime.date.today()
    while True:
        row = db.execute(
            "SELECT done FROM checkins WHERE habit_id = ? AND check_date = ?",
            (habit_id, check_date.isoformat())
        ).fetchone()
        
        if row and row["done"] == 1:
            streak += 1
            check_date -= datetime.timedelta(days=1)
        else:
            break
    
    # Get today's date
    import datetime as dt
    today = dt.date.today().isoformat()
    
    return render_template("habit-detail.html", habit=habit, checkins=checkins, streak=streak, today=today)

@app.route("/habits/<int:habit_id>/checkin", methods=["POST"])
@login_required
@csrf.exempt
def checkin(habit_id):
    """Check in a habit."""
    db = get_db()
    
    # Verify ownership
    habit = db.execute(
        "SELECT id FROM habits WHERE id = ? AND user_id = ?",
        (habit_id, session["user_id"])
    ).fetchone()
    
    if not habit:
        return jsonify({"error": "Not found"}), 404
    
    data = request.get_json() if request.is_json else request.form
    check_date = data.get("date", datetime.date.today().isoformat())
    done = 1 if data.get("done", "1") in ("1", "true", "on", True) else 0
    note = data.get("note", "")
    mood = data.get("mood", "")
    
    db.execute("""
        INSERT INTO checkins (habit_id, check_date, done, note, mood)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(habit_id, check_date) 
        DO UPDATE SET done=?, note=?, mood=?, created_at=CURRENT_TIMESTAMP
    """, (habit_id, check_date, done, note, mood, done, note, mood))
    
    db.commit()
    
    return jsonify({"success": True})
# except Exception as e:
#     print(f"Checking error: {e}")
#     return jsonify({"success" : False, "error": str(e)}), 500




@app.route("/habits/<int:habit_id>/delete", methods=["POST"])
@login_required
@csrf.exempt
def delete_habit(habit_id):
    """Delete/archive a habit."""
    db = get_db()
    db.execute(
        "UPDATE habits SET archived = 1 WHERE id = ? AND user_id = ?",
        (habit_id, session["user_id"])
    )
    db.commit()
    
    return jsonify({"success": True})

# ============================================================================
# ROUTES - AI & ANALYTICS
# ============================================================================

@app.route("/api/ai/suggestions", methods=["POST"])
@login_required
@csrf.exempt
def api_ai_suggestions():
    """Get AI suggestions."""
    data = request.get_json()
    prompt = data.get("prompt", "Suggest habits")
    profile = session.get("profile", "normal")
    
    suggestions = AIService.generate_suggestions(profile, prompt, 8)
    
    return jsonify({
        "suggestions": suggestions,
        "using_ai": Config.USE_OLLAMA or bool(Config.OPENAI_API_KEY)
    })

@app.route("/api/analytics")
@login_required
def api_analytics():
    """Get user analytics."""
    user_id = session["user_id"]
    db = get_db()
    
    # Last 30 days completion rate
    stats = db.execute("""
        SELECT 
            DATE(check_date) as date,
            COUNT(DISTINCT habit_id) as completed
        FROM checkins
        WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
        AND check_date >= date('now', '-30 days')
        AND done = 1
        GROUP BY DATE(check_date)
        ORDER BY date
    """, (user_id,)).fetchall()
    
    return jsonify({
        "daily_completion": [{"date": s["date"], "count": s["completed"]} for s in stats]
    })

@app.route("/api/upcoming_reminders")
@login_required
def api_upcoming_reminders():
    """Get upcoming reminders."""
    user_id = session["user_id"]
    db = get_db()
    minutes = int(request.args.get("minutes", 60))
    
    # Get habits with reminders
    habits = db.execute("""
        SELECT id, title, reminder_time
        FROM habits
        WHERE user_id = ? AND archived = 0 AND reminder_time IS NOT NULL
    """, (user_id,)).fetchall()
    
    now = datetime.datetime.now()
    reminders = []
    
    for habit in habits:
        if habit["reminder_time"]:
            try:
                # Parse reminder time
                reminder_time = datetime.datetime.strptime(habit["reminder_time"], "%H:%M").time()
                reminder_datetime = datetime.datetime.combine(datetime.date.today(), reminder_time)
                
                # Calculate minutes until reminder
                time_diff = (reminder_datetime - now).total_seconds() / 60
                
                if 0 <= time_diff <= minutes:
                    reminders.append({
                        "id": habit["id"],
                        "title": habit["title"],
                        "time": habit["reminder_time"],
                        "minutes": int(time_diff)
                    })
            except ValueError:
                continue
    
    return jsonify(reminders)

# ============================================================================
# ROUTES - EXPORT & SHARE
# ============================================================================

@app.route("/export/csv")
@login_required
def export_csv():
    """Export habits to CSV."""
    user_id = session["user_id"]
    db = get_db()
    
    habits = db.execute(
        "SELECT * FROM habits WHERE user_id = ?", 
        (user_id,)
    ).fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Habit", "Description", "Category", "Date", "Completed", "Note"])
    
    for habit in habits:
        checkins = db.execute(
            "SELECT * FROM checkins WHERE habit_id = ? ORDER BY check_date",
            (habit["id"],)
        ).fetchall()
        
        if not checkins:
            writer.writerow([habit["title"], habit["description"], habit["category"], "", "", ""])
        else:
            for c in checkins:
                writer.writerow([
                    habit["title"],
                    habit["description"],
                    habit["category"],
                    c["check_date"],
                    "Yes" if c["done"] else "No",
                    c["note"] or ""
                ])
    
    output.seek(0)
    buf = io.BytesIO(output.read().encode("utf-8"))
    
    filename = f"habits_{session['username']}_{datetime.date.today()}.csv"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="text/csv")

# ============================================================================
# PWA ROUTES
# ============================================================================

@app.route("/manifest.json")
def manifest():
    """PWA manifest."""
    return jsonify({
        "name": "HabitFlow - Track Your Progress",
        "short_name": "HabitFlow",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#6366f1",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    })

@app.route("/service-worker.js")
def service_worker():
    """Service worker for PWA."""
    sw = """
self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
"""
    return Response(sw, mimetype="application/javascript")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 handler."""
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    """500 handler."""
    return render_template("500.html"), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """CSRF error handler."""
    return jsonify({"error": "CSRF validation failed"}), 400

# ============================================================================
# INITIALIZATION
# ============================================================================

with app.app_context():
    if not os.path.exists(Config.DATABASE):
        open(Config.DATABASE, "a").close()
    init_db()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 HabitFlow Tracker Starting...")
    print("=" * 60)
    print(f"📊 Database: {Config.DATABASE}")
    print(f"🤖 AI Mode: {'Ollama (Local)' if Config.USE_OLLAMA else 'OpenAI'}")
    if Config.USE_OLLAMA:
        print(f"🔗 Ollama URL: {Config.OLLAMA_URL}")
    print("=" * 60)
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )