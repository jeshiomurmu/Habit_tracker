# Habit_tracker
# ⭐ HabitFlow - Premium Habit Tracker (100% Free)

A modern, AI-powered habit tracking web application with all premium features completely free. Built with Flask, featuring both local AI (Ollama) and cloud AI (OpenAI) support.

![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![GitHub stars](https://img.shields.io/github/stars/YOUR-USERNAME/habit-tracker)
![GitHub forks](https://img.shields.io/github/forks/YOUR-USERNAME/habit-tracker)

## 📑 Table of Contents

- [Features](#-features)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [AI Setup](#-ai-setup)
- [Mobile Setup](#-mobile-setup-pwa)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🎯 Core Features
- ✅ **Modern Google-style Authentication** - Beautiful, secure login/register
- ✅ **AI-Powered Suggestions** - Free Ollama or OpenAI integration
- ✅ **Advanced Analytics** - Track streaks, completion rates, trends
- ✅ **Beautiful Dashboard** - Clean, Notion-inspired design
- ✅ **Offline Support** - PWA with offline capabilities
- ✅ **Dark Mode** - Eye-friendly themes
- ✅ **Data Export** - Full CSV export of all your data
- ✅ **Smart Reminders** - Browser notifications for habits
- ✅ **Custom Categories** - Organize habits your way
- ✅ **Privacy First** - Your data stays local or on your server

### 💎 Premium Features (All FREE!)
- Unlimited habits
- Advanced analytics dashboard
- AI habit suggestions
- Data export (CSV)
- Custom themes
- No ads, no tracking
- Open source

## 📸 Screenshots

> **Note**: Add your screenshots to a `screenshots/` folder and update these paths

![Login Page](screenshots/login.png)
*Beautiful authentication page*

![Dashboard](screenshots/dashboard.png)
*Track your habits at a glance*

![Habit Detail](screenshots/detail.png)
*Detailed analytics and history*

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- 100MB free disk space
- (Optional) Ollama for local AI

Check your Python version:
```bash
python --version
```

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/YOUR-USERNAME/habit-tracker.git
cd habit-tracker
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up configuration** (optional):
```bash
cp .env.example .env
# Edit .env with your preferences (or use defaults)
```

4. **Run the application**:
```bash
python app.py
```

5. **Open in browser**:
```
http://localhost:5000
```

That's it! 🎉

## 🤖 AI Setup

### Option 1: Ollama (Recommended - FREE & Local)

1. **Install Ollama**:
   - macOS/Linux: `curl https://ollama.ai/install.sh | sh`
   - Windows: Download from [https://ollama.ai](https://ollama.ai)

2. **Download a model**:
```bash
ollama pull llama2
# Or try: mistral, codellama, phi
```

3. **Start Ollama**:
```bash
ollama serve
```

4. **Configure** (already default in app):
```bash
# In .env file:
USE_OLLAMA=1
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama2
```

### Option 2: OpenAI (Paid - Cloud)

1. **Get API key** from [OpenAI](https://platform.openai.com/api-keys)

2. **Configure**:
```bash
# In .env file:
USE_OLLAMA=0
OPENAI_API_KEY=sk-your-api-key-here
```

### Option 3: No AI (Fallback)

Don't have either? No problem! The app will use pre-built suggestions from the database automatically.

## 📱 Mobile Setup (PWA)

### Install as App on Phone

1. **Find your computer's IP address**:
```bash
# Windows
ipconfig

# Mac/Linux
ifconfig | grep inet
```

2. **On your phone's browser**, visit:
```
http://YOUR_IP_ADDRESS:5000
```

3. **Install the app**:
   - **iPhone**: Tap Share → Add to Home Screen
   - **Android**: Tap Menu → Install App

Now you have a native-like app! 📱

## 🗂️ Project Structure

```
habit-tracker/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env.example             # Configuration template
├── .gitignore               # Git ignore rules
├── README.md                # This file
│
├── data/
│   └── habit_tracker.db     # SQLite database (auto-created)
│
├── templates/
│   ├── index.html           # Login/Register page
│   ├── dashboard.html       # Main dashboard
│   ├── habit_detail.html    # Habit details & analytics
│   ├── settings.html        # User settings
│   ├── 404.html            # Not found page
│   └── 500.html            # Error page
│
└── static/
    ├── css/
    │   └── style.css        # Custom styles
    ├── js/
    │   └── main.js          # Frontend JavaScript
    ├── icons/
    │   ├── icon-192.png     # PWA icon (small)
    │   └── icon-512.png     # PWA icon (large)
    └── fonts/              # Custom fonts (optional)
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Security
SECRET_KEY=your-secret-key-here

# AI Configuration
USE_OLLAMA=1                                    # 1 for Ollama, 0 for OpenAI
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama2
OPENAI_API_KEY=                                 # Optional

# Database
DATABASE_PATH=                                   # Leave empty for default

# Server
PORT=5000
DEBUG=1
```

### Important: .gitignore

Make sure your `.gitignore` includes:
```
.env
data/habit_tracker.db
__pycache__/
*.pyc
*.pyo
*.log
```

## 📊 Usage

### Creating Your First Habit

1. **Login/Register** with any username and password
2. Click **"Create Habit"** on dashboard
3. Fill in:
   - Title (e.g., "Morning Run")
   - Description (optional)
   - Category
   - Reminder time (optional)
   - Custom color & icon
4. Click **"Create"**

### Tracking Progress

1. Click on any habit card
2. Select date (defaults to today)
3. Mark as **Done** or **Not Done**
4. Add optional notes
5. Save!

### Using AI Suggestions

1. Click **"Ask AI"** in dashboard
2. Type what kind of habits you want
3. AI generates personalized suggestions
4. Click to add them as habits!

### Viewing Analytics

- **Dashboard**: See overall stats
- **Habit Detail**: View 90-day calendar, streaks, completion rates
- **Export**: Download all data as CSV

## 🌐 Deployment

### Deploy to Render (Free)

1. **Push to GitHub** (if not already done)

2. **Create Render account**: [render.com](https://render.com)

3. **New Web Service**:
   - Connect GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`

4. **Add environment variables**:
   - `SECRET_KEY`: Generate random string
   - `USE_OLLAMA`: Set to `0` (use OpenAI instead)
   - `OPENAI_API_KEY`: Your OpenAI key

5. **Deploy!** 🚀

### Deploy to Railway (Free)

1. Visit [railway.app](https://railway.app)
2. Click **"Deploy from GitHub"**
3. Select your repo
4. Add environment variables
5. Deploy automatically! 🎉

### Deploy to Your Own Server

```bash
# On your server
git clone https://github.com/YOUR-USERNAME/habit-tracker.git
cd habit-tracker
pip install -r requirements.txt

# Install and start Ollama
curl https://ollama.ai/install.sh | sh
ollama pull llama2
ollama serve &

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Optional: Set up Nginx reverse proxy
# Optional: Get free SSL with Let's Encrypt
```

## 🔒 Security Features

- ✅ Password hashing (pbkdf2:sha256)
- ✅ CSRF protection
- ✅ SQL injection prevention
- ✅ Secure session management
- ✅ Input validation
- ✅ No data tracking

## 🛠 Troubleshooting

### Database locked error
```bash
# Delete the database and restart
rm data/habit_tracker.db
python app.py
```

### Ollama not connecting
```bash
# Make sure Ollama is running
ollama serve

# Test manually
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Hello"
}'
```

### Port already in use
```bash
# Change port in .env
PORT=8000
```

### PWA not installing
- Must use HTTPS (except localhost)
- Make sure manifest.json is accessible
- Check browser console for errors

## 📈 Performance

- Page load: < 2 seconds
- Database queries: < 100ms
- AI responses: 3-10 seconds (Ollama) / 1-3 seconds (OpenAI)
- Supports 100+ concurrent users

## 🛣️ Roadmap

### Version 1.1 (Next)
- [ ] Social features (share habits)
- [ ] Team challenges
- [ ] Habit templates marketplace
- [ ] Email notifications

### Version 2.0 (Future)
- [ ] Mobile app (React Native)
- [ ] Gamification (points, badges)
- [ ] Integration with Apple Health/Google Fit
- [ ] Community forum

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

MIT License - feel free to use for personal or commercial projects!

See [LICENSE](LICENSE) file for details.

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR-USERNAME/habit-tracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR-USERNAME/habit-tracker/discussions)

## ⭐ Star History

If you find this project helpful, please give it a star! ⭐

## 🙏 Acknowledgments

- Inspired by Notion's beautiful design
- AI powered by Ollama/OpenAI
- Built with Flask and modern web technologies
- Icons from Lucide Icons
- Fonts from Google Fonts

---

**Made with ❤️ by [Your GitHub Username]**

*Building better habits, one day at a time* ⭐
