# 📚 PROJECT DOCUMENTATION HIERARCHY

**Understanding the Three Critical Files**

---

## 🏗️ The Three Pillars

```
┌─────────────────────────────────────────────────────────┐
│                    PROJECT_DOCUMENTATION.md                             │
│          (1815 lines - Master Reference)                │
│  • Complete project documentation                       │
│  • All features, APIs, database, design decisions      │
│  • Single source of truth                              │
│  • Updated after every feature/bug fix                 │
└─────────────────────────────────────────────────────────┘
           ↑                              ↑
           │                              │
           │ Reference                    │ Update after work
           │                              │
┌──────────────────────┐    ┌──────────────────────────────┐
│  documentation/.INSTRUCTIONS.md    │    │  documentation/PYCHARM_INSTRUCTIONS.md     │
│  (System Rules)      │    │  (PyCharm Integration Guide) │
│  • Golden rules      │    │  • How to use with PyCharm   │
│  • Always apply      │    │  • Chat starters             │
│  • Reference for AI  │    │  • Workflow examples         │
└──────────────────────┘    └──────────────────────────────┘
```

---

## 📖 What Each File Does

### **1. PROJECT_DOCUMENTATION.md** (1815 lines)
**Purpose:** Complete project documentation and reference

**Contains:**
- Executive summary
- Technology stack (20+ technologies)
- Complete database design (7 models)
- All API endpoints (40+)
- All features documented
- Special features (SensitiveMode, formats, i18n)
- Design decisions (15+)
- Bug fixes (3 documented)
- Security measures
- Performance optimization
- Deployment guide
- Troubleshooting

**Who uses it:**
- Developers (check before implementing)
- Architects (understand design)
- DevOps (deployment reference)
- New team members (learn system)

**When to update:**
- After every feature implementation
- After every bug fix
- After every design decision
- After every configuration change
- After database changes
- After API additions

**Location:** `/Users/matthiasschmid/Projects/finance/PROJECT_DOCUMENTATION.md`

---

### **2. documentation/.INSTRUCTIONS.md** (System Rules)
**Purpose:** Critical instructions that apply to EVERY chat

**Contains:**
- Golden rule: PROJECT_DOCUMENTATION.md is authoritative
- Before/during/after work checklist
- How to update PROJECT_DOCUMENTATION.md
- Sections in PROJECT_DOCUMENTATION.md to reference
- What NOT to do
- Key patterns from PROJECT_DOCUMENTATION.md
- Continuous update policy

**Who uses it:**
- Me (Claude) - to remember the rules
- You (developer) - to set expectations
- Team members - to understand workflow

**When to reference:**
- At the START of every chat
- When unsure about documentation
- When multiple chats are happening
- When onboarding team members

**Location:** `/Users/matthiasschmid/Projects/finance/documentation/.INSTRUCTIONS.md`

---

### **3. documentation/PYCHARM_INSTRUCTIONS.md** (PyCharm-Specific Guide)
**Purpose:** How to use these instructions with PyCharm Copilot integration

**Contains:**
- How to start PyCharm chats
- Chat templates for different scenarios
- How to reference PROJECT_DOCUMENTATION.md sections
- Example chat starters (new feature, bug fix, enhancement)
- Tips for PyCharm sessions
- Complete workflow examples
- Checklist for PyCharm chat sessions

**Who uses it:**
- You (using PyCharm Copilot)
- Any team member using PyCharm integration
- When setting up PyCharm with Copilot

**When to reference:**
- Before starting a new PyCharm chat
- When unsure how to start a conversation
- When setting up PyCharm for first time
- When creating chat templates

**Location:** `/Users/matthiasschmid/Projects/finance/documentation/PYCHARM_INSTRUCTIONS.md`

---

## 🔄 How They Work Together

### **The Workflow**

```
1. You Start PyCharm Chat
   └─> Read documentation/PYCHARM_INSTRUCTIONS.md for template
       └─> Use chat template from file
           └─> Mention documentation/.INSTRUCTIONS.md rules

2. I (Claude) Receive Chat
   └─> Check documentation/.INSTRUCTIONS.md to understand rules
       └─> Read relevant PROJECT_DOCUMENTATION.md sections
           └─> Follow patterns from PROJECT_DOCUMENTATION.md
               └─> Implement work

3. Implementation Complete
   └─> Update PROJECT_DOCUMENTATION.md with:
       • New sections if major feature
       • Updated API endpoints
       • Updated database schema
       • Design decision documented
       • Bug fix documented
       • Features listed
       └─> Show you what changed in PROJECT_DOCUMENTATION.md

4. Next Chat (Day/Week Later)
   └─> Check documentation/PYCHARM_INSTRUCTIONS.md again
       └─> Reference current PROJECT_DOCUMENTATION.md
           └─> Continue building on previous work
               └─> PROJECT_DOCUMENTATION.md is always current reference
```

---

## 🎯 How to Use Them

### **Scenario 1: New Feature Implementation**

```
Step 1: Read documentation/PYCHARM_INSTRUCTIONS.md
        ↓
Step 2: Open PyCharm chat with template:
        "I want to implement [Feature]
         Following documentation/PYCHARM_INSTRUCTIONS.md and documentation/.INSTRUCTIONS.md rules"
        ↓
Step 3: Me checks:
        - documentation/.INSTRUCTIONS.md rules
        - PROJECT_DOCUMENTATION.md relevant sections
        - Similar patterns in PROJECT_DOCUMENTATION.md
        ↓
Step 4: Me implements following PROJECT_DOCUMENTATION.md patterns
        ↓
Step 5: Me updates PROJECT_DOCUMENTATION.md with:
        - New section/documentation
        - New API endpoints
        - Database changes
        - Design decision
        ↓
Step 6: PROJECT_DOCUMENTATION.md is now current reference for next work
```

### **Scenario 2: Bug Fix in Ongoing Chat**

```
Step 1: In PyCharm chat:
        "I found a bug in [area]
         Please update PROJECT_DOCUMENTATION.md Critical Bugs Fixed section"
        ↓
Step 2: Me checks:
        - documentation/.INSTRUCTIONS.md rule: update PROJECT_DOCUMENTATION.md
        - PROJECT_DOCUMENTATION.md Critical Bugs section
        - Root cause understanding
        ↓
Step 3: Me fixes the bug
        ↓
Step 4: Me updates PROJECT_DOCUMENTATION.md:
        - Adds to "Critical Bugs Fixed" section
        - Documents root cause
        - Explains solution
        ↓
Step 5: PROJECT_DOCUMENTATION.md bug section is updated for future reference
```

### **Scenario 3: Multiple Chats Over Time**

```
Chat 1 (Monday):
  Implement Feature A
  └─> Update PROJECT_DOCUMENTATION.md

Chat 2 (Wednesday):
  Implement Feature B
  └─> Reference Feature A docs in updated PROJECT_DOCUMENTATION.md
  └─> Update PROJECT_DOCUMENTATION.md with Feature B

Chat 3 (Friday):
  Fix bug in Feature A
  └─> Reference updated PROJECT_DOCUMENTATION.md docs
  └─> Update PROJECT_DOCUMENTATION.md Critical Bugs section
  └─> PROJECT_DOCUMENTATION.md always current!
```

---

## 📋 Reference Guide

### **Before Starting Work**
→ Check **documentation/PYCHARM_INSTRUCTIONS.md** for chat template

### **At Start of Chat**
→ Mention **documentation/.INSTRUCTIONS.md** rules

### **During Implementation**
→ Reference **PROJECT_DOCUMENTATION.md** for patterns and decisions

### **After Implementation**
→ Update **PROJECT_DOCUMENTATION.md** with all changes

### **For Next Work**
→ Read updated **PROJECT_DOCUMENTATION.md** for current state

---

## ✅ Quality Assurance

### **How to Verify Everything Works**

**1. Check PROJECT_DOCUMENTATION.md is Current**
```
- Latest features documented? ✅
- API endpoints listed? ✅
- Database schema current? ✅
- Design decisions explained? ✅
- Bug fixes documented? ✅
```

**2. Check documentation/.INSTRUCTIONS.md is Followed**
```
- Every chat checks PROJECT_DOCUMENTATION.md? ✅
- Every feature updates PROJECT_DOCUMENTATION.md? ✅
- Every bug documented? ✅
- Every design decision recorded? ✅
```

**3. Check documentation/PYCHARM_INSTRUCTIONS.md is Used**
```
- New chats use templates? ✅
- References PROJECT_DOCUMENTATION.md sections? ✅
- Mentions documentation/.INSTRUCTIONS.md rules? ✅
- Chats result in PROJECT_DOCUMENTATION.md updates? ✅
```

---

## 🎊 The Complete Picture

```
Your Development Workflow:
  1. Start PyCharm chat (documentation/PYCHARM_INSTRUCTIONS.md as guide)
  2. Apply documentation/.INSTRUCTIONS.md rules (PROJECT_DOCUMENTATION.md is authority)
  3. Implement feature following PROJECT_DOCUMENTATION.md patterns
  4. Update PROJECT_DOCUMENTATION.md with all changes
  5. Next chat reads current PROJECT_DOCUMENTATION.md
  6. Cycle repeats with PROJECT_DOCUMENTATION.md always current
```

---

## 📍 File Locations

| File | Purpose | Location |
|------|---------|----------|
| PROJECT_DOCUMENTATION.md | Master Reference (1815 lines) | `/Users/matthiasschmid/Projects/finance/PROJECT_DOCUMENTATION.md` |
| documentation/.INSTRUCTIONS.md | System Rules | `/Users/matthiasschmid/Projects/finance/documentation/.INSTRUCTIONS.md` |
| documentation/PYCHARM_INSTRUCTIONS.md | PyCharm Guide | `/Users/matthiasschmid/Projects/finance/documentation/PYCHARM_INSTRUCTIONS.md` |

---

## 🚀 Quick Start

1. **For New Chat:**
   - Open documentation/PYCHARM_INSTRUCTIONS.md
   - Copy chat template
   - Paste into PyCharm
   - Mention both files

2. **For Me (Claude):**
   - Check documentation/.INSTRUCTIONS.md rules
   - Check PROJECT_DOCUMENTATION.md relevant sections
   - Implement work
   - Update PROJECT_DOCUMENTATION.md

3. **For Verification:**
   - PROJECT_DOCUMENTATION.md is current ✅
   - All sections updated ✅
   - No contradictions ✅

---

## 💡 The Golden Rule (All Three Files Agree)

> **PROJECT_DOCUMENTATION.md is the single authoritative source of truth for the Finance Forecast project. Every decision, every feature, every bug fix flows through PROJECT_DOCUMENTATION.md. Every chat updates it. Every developer references it.**

---

**Version 1.0 | January 14, 2026**

**All three files created and ready to use!** ✅

