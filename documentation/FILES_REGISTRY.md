# 📋 PROJECT FILES REGISTRY

**Complete list of all critical project files**

---

## 🎯 Core Documentation Files

### **1. PROJECT_DOCUMENTATION.md** 📚
- **Purpose:** Master reference for entire project
- **Size:** 1815 lines
- **Type:** Comprehensive documentation
- **Location:** ``documentation/PROJECT_DOCUMENTATION.md`
- **Read by:** Developers, architects, DevOps, new team members
- **Updated:** After every feature/bug fix
- **Contains:** Architecture, APIs, database, features, design decisions, security, performance

**Key Sections (27 total):**
1. Executive Summary
2. Technology Stack
3. Project Structure
4. Database Design
5. API Architecture
6. Authentication & Users
7. Bank Accounts & Transactions
8. Categories & Rules
9. Recurring Transactions
10. AI Insights
11. Analytics
12. Frontend Architecture
13. UI Components & Features
14. Sensitive Mode
15. Format Preferences
16. Internationalization
17. Docker Compose Setup
18. Environment Configuration
19. Background Tasks (Celery)
20. Database Migrations
21. Design Decisions
22. Critical Bugs Fixed
23. Security Measures
24. Performance Optimization
25. Future Enhancements
26. Development Guide
27. Support & Troubleshooting

---

### **2. .INSTRUCTIONS.md** 🔒
- **Purpose:** System instructions that apply to EVERY chat
- **Size:** ~2000 words
- **Type:** Rules and guidelines
- **Location:** ``documentation/.INSTRUCTIONS.md`
- **Read by:** Claude AI (me), developers
- **Updated:** Rarely (foundational rules)
- **Contains:** Golden rule, checklists, patterns, don'ts

**Key Content:**
- Golden rule: PROJECT_DOCUMENTATION.md is authoritative
- Before/during/after work checklist
- How to update PROJECT_DOCUMENTATION.md
- Key patterns from PROJECT_DOCUMENTATION.md
- What NOT to do
- Continuous update policy

---

### **3. PYCHARM_INSTRUCTIONS.md** 💻
- **Purpose:** How to use PyCharm Copilot with these instructions
- **Size:** ~2000 words
- **Type:** Integration guide
- **Location:** ``documentation/PYCHARM_INSTRUCTIONS.md`
- **Read by:** You (developer using PyCharm)
- **Updated:** Only for PyCharm-specific improvements
- **Contains:** Templates, workflow examples, tips

**Key Content:**
- Quick start guide
- Chat templates (3 types: feature, bug, enhancement)
- How to reference PROJECT_DOCUMENTATION.md
- Complete workflow examples
- Checklists for PyCharm sessions
- Tips and tricks

---

### **4. DOCUMENTATION_HIERARCHY.md** 🏗️
- **Purpose:** Overview of how all three files work together
- **Size:** ~1500 words
- **Type:** Architecture guide
- **Location:** ``documentation/DOCUMENTATION_HIERARCHY.md`
- **Read by:** Anyone wanting to understand the system
- **Updated:** Only if relationships change
- **Contains:** Diagrams, workflows, reference guide

**Key Content:**
- The three pillars explained
- How they work together
- Workflow diagrams
- Quality assurance checks
- Quick start guide
- Complete picture

---

## 📁 Project Structure Files

### **Backend Files**
- `backend/requirements.txt` - Python dependencies (18 packages)
- `backend/manage.py` - Django CLI
- `backend/finance_project/settings_base.py` - Base settings (246 lines)
- `backend/finance_project/settings_local.py` - Local overrides (gitignored)
- `backend/finance_project/settings.py` - Settings loader
- `backend/finance_project/celery.py` - Celery configuration
- `backend/finance_project/urls.py` - URL routing
- `backend/finance_project/wsgi.py` - WSGI entry point
- `backend/finance_project/asgi.py` - ASGI entry point
- `backend/finance_project/middleware.py` - Custom middleware
- `backend/docker/Dockerfile` - Docker image definition

### **Frontend Files**
- `frontend/package.json` - Node dependencies (10+ packages)
- `frontend/src/index.jsx` - Main app (496 lines)
- `frontend/src/index.css` - Global styles
- `frontend/tailwind.config.js` - Tailwind configuration
- `frontend/postcss.config.js` - PostCSS configuration
- `frontend/src/components/` - React components (12+)
- `frontend/src/utils/` - Utility functions (format, i18n, etc.)
- `frontend/src/hooks/` - React hooks (useLanguage, etc.)
- `frontend/src/locales/` - Translation files (en.json, de.json)

### **Database Files**
- `backend/finance_project/apps/banking/models.py` - Data models (178 lines)
- `backend/finance_project/apps/banking/migrations/` - Schema migrations
- `backend/finance_project/apps/accounts/models.py` - User models (21 lines)
- `backend/finance_project/apps/analytics/models.py` - Analytics models

### **API Files**
- `backend/finance_project/apps/banking/views.py` - API endpoints (200+ lines)
- `backend/finance_project/apps/banking/serializers.py` - Data serializers
- `backend/finance_project/apps/banking/urls.py` - URL routing
- `backend/finance_project/apps/accounts/views.py` - Account APIs
- `backend/finance_project/apps/analytics/views.py` - Analytics APIs
- `backend/finance_project/apps/ai/views.py` - AI API endpoints

### **Deployment Files**
- `deploy/docker-compose.yml` - Service orchestration (101 lines)
- `deploy/.env.example` - Environment template
- `deploy/.env.local` - Actual secrets (gitignored)
- `dc.sh` - Docker Compose shorthand script

### **Configuration Files**
- `.gitignore` - Git ignore rules
- `.dockerignore` - Docker ignore rules
- `.github/workflows/ci.yml` - GitHub Actions CI
- `pytest.ini` - Test configuration

### **Documentation Files**
- `README.md` - Quick start guide
- `DESIGN.md` - System design details
- Various feature-specific markdown files

---

## 🎯 File Relationship Map

```
Core Documentation Files:
├── PROJECT_DOCUMENTATION.md (Master Reference - 1815 lines)
│   └── Referenced by: .INSTRUCTIONS.md, PYCHARM_INSTRUCTIONS.md
│   └── Updated by: Every chat/feature implementation
│   └── Contains: Everything about the project
│
├── .INSTRUCTIONS.md (System Rules)
│   └── References: PROJECT_DOCUMENTATION.md sections
│   └── Read by: Claude AI
│   └── Purpose: Enforce consistent documentation
│   └── Contains: Rules and patterns
│
├── PYCHARM_INSTRUCTIONS.md (Integration Guide)
│   └── References: .INSTRUCTIONS.md, PROJECT_DOCUMENTATION.md
│   └── Read by: Developers using PyCharm
│   └── Purpose: How to start effective chats
│   └── Contains: Templates and workflows
│
└── DOCUMENTATION_HIERARCHY.md (Overview)
    └── References: All three files above
    └── Purpose: Understand the system
    └── Contains: Diagrams and relationships

Project Files:
├── Backend
│   ├── Python/Django files
│   ├── API endpoints
│   ├── Database models
│   └── Docker setup
├── Frontend
│   ├── React components
│   ├── Styles (Tailwind)
│   └── Translations
└── Deployment
    ├── Docker Compose
    └── Environment config
```

---

## 📊 File Sizes & Statistics

| File | Type | Size | Lines | Purpose |
|------|------|------|-------|---------|
| PROJECT_DOCUMENTATION.md | Documentation | ~220 KB | 1815 | Master reference |
| .INSTRUCTIONS.md | Rules | ~50 KB | ~2000 words | System rules |
| PYCHARM_INSTRUCTIONS.md | Guide | ~50 KB | ~2000 words | PyCharm guide |
| DOCUMENTATION_HIERARCHY.md | Overview | ~40 KB | ~1500 words | Overview |
| settings_base.py | Python | ~10 KB | 246 | Django config |
| index.jsx | JavaScript | ~50 KB | 496 | React app |
| models.py | Python | ~8 KB | 178 | Database |
| docker-compose.yml | YAML | ~5 KB | 101 | Deployment |

---

## 🎯 When to Use Each File

| Need | File | Action |
|------|------|--------|
| Understand architecture | PROJECT_DOCUMENTATION.md | Read relevant section |
| Add new API endpoint | PROJECT_DOCUMENTATION.md + .INSTRUCTIONS.md | Check patterns, update docs |
| Start PyCharm chat | PYCHARM_INSTRUCTIONS.md | Copy template |
| System rules | .INSTRUCTIONS.md | Reference for consistency |
| Understand relationships | DOCUMENTATION_HIERARCHY.md | Read overview |
| Deploy application | PROJECT_DOCUMENTATION.md + docker-compose.yml | Follow guide |
| Database questions | PROJECT_DOCUMENTATION.md Database Design | Check schema |
| Frontend development | PROJECT_DOCUMENTATION.md Frontend Architecture | Understand structure |
| Configuration | PROJECT_DOCUMENTATION.md Environment Configuration | See all variables |

---

## ✅ Checklist: All Files Present

- [x] PROJECT_DOCUMENTATION.md (1815 lines)
- [x] .INSTRUCTIONS.md (system rules)
- [x] PYCHARM_INSTRUCTIONS.md (PyCharm guide)
- [x] DOCUMENTATION_HIERARCHY.md (overview)
- [x] Backend files (Django app)
- [x] Frontend files (React app)
- [x] Deployment files (Docker)
- [x] Configuration files (.env, settings)
- [x] Database migrations (schema)

---

## 🚀 Ready to Use

All files are in place and ready to use:

1. ✅ **PROJECT_DOCUMENTATION.md** - Complete project documentation
2. ✅ **.INSTRUCTIONS.md** - System rules for all chats
3. ✅ **PYCHARM_INSTRUCTIONS.md** - PyCharm integration guide
4. ✅ **DOCUMENTATION_HIERARCHY.md** - System overview
5. ✅ **Project files** - All source code and config

---

## 📍 Quick Access

```bash
# View master documentation
cat `documentation/PROJECT_DOCUMENTATION.md

# View system rules
cat `documentation/.INSTRUCTIONS.md

# View PyCharm guide
cat `documentation/PYCHARM_INSTRUCTIONS.md

# View system overview
cat `documentation/DOCUMENTATION_HIERARCHY.md
```

---

**All critical documentation files created and organized!** ✅

Ready for development with PyCharm Copilot integration! 🚀

