# 📌 HOW TO USE WITH PYCHARM COPILOT

**For PyCharm Copilot Integration Users**

---

## 🎯 Quick Start

### **When Starting a New PyCharm Chat:**

**Copy and paste this template into your PyCharm chat:**

```
I'm working on the Finance Forecast project.

Following project instructions from documentation/.INSTRUCTIONS.md:
- documentation/PROJECT_DOCUMENTATION.md is the authoritative reference
- I will update documentation/PROJECT_DOCUMENTATION.md after implementation

Task: [Describe what you want to build/fix]

Relevant documentation/PROJECT_DOCUMENTATION.md sections: [List 2-3 sections you checked]

What needs to happen: [Requirements]

Success looks like: [Success criteria]
```

---

## 📖 How To Reference documentation/.INSTRUCTIONS.md

**In PyCharm chat, you can say:**

```
Remember the rules from documentation/.INSTRUCTIONS.md:
1. Check documentation/PROJECT_DOCUMENTATION.md first
2. Follow existing patterns
3. Update documentation/PROJECT_DOCUMENTATION.md after implementation
4. Update relevant sections (API, Database, etc.)
```

Or simply:

```
Following documentation/.INSTRUCTIONS.md rules for this work.
```

---

## 🔍 Where to Find Things in documentation/PROJECT_DOCUMENTATION.md

**Before your PyCharm chat, you might need to check documentation/PROJECT_DOCUMENTATION.md sections:**

- **"How do I add a new API endpoint?"** 
  → Check documentation/PROJECT_DOCUMENTATION.md "API Architecture" section

- **"How do I add a new database model?"**
  → Check documentation/PROJECT_DOCUMENTATION.md "Database Design" section

- **"What's our pattern for React components?"**
  → Check documentation/PROJECT_DOCUMENTATION.md "Frontend Architecture" section

- **"How do we handle errors?"**
  → Check documentation/PROJECT_DOCUMENTATION.md "Security Measures" section

- **"What's our Docker setup?"**
  → Check documentation/PROJECT_DOCUMENTATION.md "Docker Compose Setup" section

---

## 💬 Example PyCharm Chat Starters

### **New Feature**
```
I want to implement [feature name].

From documentation/.INSTRUCTIONS.md: Following documentation/PROJECT_DOCUMENTATION.md rules.

Checked documentation/PROJECT_DOCUMENTATION.md sections:
- Design Decisions (to understand patterns)
- [Feature area] section
- API Architecture (for endpoint design)

Feature: [Description]

Success: [Criteria]
```

### **Bug Fix**
```
I found a bug in [area].

From documentation/.INSTRUCTIONS.md: Will update documentation/PROJECT_DOCUMENTATION.md "Critical Bugs Fixed" section.

Bug: [Description]
Where: [Location in code]
Impact: [What breaks]

What I need: [Fix approach]
```

### **Enhancement**
```
I want to improve [area] performance/feature.

From documentation/.INSTRUCTIONS.md: Checking documentation/PROJECT_DOCUMENTATION.md patterns first.

Current issue: [What's wrong]
Proposed fix: [How to improve]
Impact: [Performance/feature gain]

Success: [Criteria]
```

---

## ✅ During Your PyCharm Chat

**The agent (me) should:**
1. ✅ Reference documentation/PROJECT_DOCUMENTATION.md sections
2. ✅ Follow patterns from documentation/PROJECT_DOCUMENTATION.md
3. ✅ Implement the work
4. ✅ Show you what's being added to documentation/PROJECT_DOCUMENTATION.md
5. ✅ Ask clarifying questions if needed

**You should:**
1. ✅ Provide clear requirements
2. ✅ Mention documentation/.INSTRUCTIONS.md / documentation/PROJECT_DOCUMENTATION.md
3. ✅ Ask questions about design decisions
4. ✅ Request documentation updates

---

## 📝 After Your PyCharm Chat

**The agent should have:**
1. ✅ Implemented the feature/fix
2. ✅ Updated documentation/PROJECT_DOCUMENTATION.md (shown you what changed)
3. ✅ Added new sections if major feature
4. ✅ Updated relevant API/Database/Design sections
5. ✅ Tested the work

**You should:**
1. ✅ Check the updated documentation/PROJECT_DOCUMENTATION.md
2. ✅ Verify documentation is clear
3. ✅ Test the implementation
4. ✅ Keep documentation/PROJECT_DOCUMENTATION.md in version control

---

## 🔗 How They Work Together

```
Your PyCharm Chat
        ↓
Uses documentation/.INSTRUCTIONS.md as reference
        ↓
Me: "I'll check documentation/PROJECT_DOCUMENTATION.md for patterns"
        ↓
I implement following documentation/PROJECT_DOCUMENTATION.md patterns
        ↓
I update documentation/PROJECT_DOCUMENTATION.md with new documentation
        ↓
Chat completes with documentation updated
        ↓
documentation/PROJECT_DOCUMENTATION.md is now current reference for next chat
```

---

## 🚨 Important Note

**Each PyCharm chat is separate, BUT:**

✅ documentation/.INSTRUCTIONS.md is persistent (in your repo)  
✅ documentation/PROJECT_DOCUMENTATION.md is persistent (in your repo)  
✅ I can read instructions from documentation/.INSTRUCTIONS.md  
✅ I will reference documentation/PROJECT_DOCUMENTATION.md  
✅ I will update documentation/PROJECT_DOCUMENTATION.md  

**So even though each chat is isolated, the instructions and documentation are shared!**

---

## 💡 Tips for PyCharm Chats

1. **Always mention documentation/PROJECT_DOCUMENTATION.md** 
   ```
   "I'm following documentation/PROJECT_DOCUMENTATION.md patterns from section X"
   ```

2. **Reference documentation/.INSTRUCTIONS.md rules**
   ```
   "Following documentation/.INSTRUCTIONS.md rules"
   ```

3. **Be specific about what changed**
   ```
   "Please update documentation/PROJECT_DOCUMENTATION.md [section] with [details]"
   ```

4. **Ask for documentation updates explicitly**
   ```
   "Make sure to update documentation/PROJECT_DOCUMENTATION.md API Architecture section"
   ```

5. **Check documentation/PROJECT_DOCUMENTATION.md before chatting**
   ```
   "I checked documentation/PROJECT_DOCUMENTATION.md and need to add a new endpoint"
   ```

---

## 🎯 The Golden Rule

**Every PyCharm chat should result in:**

1. ✅ Working code/feature
2. ✅ Updated documentation/PROJECT_DOCUMENTATION.md
3. ✅ Documented design decisions
4. ✅ No confusion about what changed

**documentation/PROJECT_DOCUMENTATION.md stays current. documentation/PROJECT_DOCUMENTATION.md is truth.**

---

## 📋 Checklist for PyCharm Chat Sessions

**Before chat:**
- [ ] Know what you want to build/fix
- [ ] Have read relevant documentation/PROJECT_DOCUMENTATION.md sections
- [ ] Have documentation/.INSTRUCTIONS.md handy for reference
- [ ] Have clear success criteria

**During chat:**
- [ ] Mention documentation/.INSTRUCTIONS.md rules
- [ ] Reference documentation/PROJECT_DOCUMENTATION.md sections
- [ ] Ask for specific documentation/PROJECT_DOCUMENTATION.md updates
- [ ] Verify documentation will be updated

**After chat:**
- [ ] Review updated documentation/PROJECT_DOCUMENTATION.md
- [ ] Verify all sections updated
- [ ] Test the implementation
- [ ] Commit changes to git

---

## 🔄 Using Multiple PyCharm Chats

**If you have multiple PyCharm chats open:**

1. Each can reference documentation/.INSTRUCTIONS.md
2. Each can reference current documentation/PROJECT_DOCUMENTATION.md
3. Each should update documentation/PROJECT_DOCUMENTATION.md
4. Each builds on the same documentation/PROJECT_DOCUMENTATION.md

**The documentation/PROJECT_DOCUMENTATION.md state is the single source of truth between chats!**

---

## ✨ Example: Complete Workflow

```
Chat 1 (New Feature):
1. "I want to add Budget tracking feature"
2. Me: Check documentation/PROJECT_DOCUMENTATION.md Design Decisions
3. Me: Implement feature
4. Me: Update documentation/PROJECT_DOCUMENTATION.md with Budget model, API endpoints, design decision
5. documentation/PROJECT_DOCUMENTATION.md is now updated

Chat 2 (Next Day - Bug Fix):
1. "Budget feature has a calculation bug"
2. Me: Read documentation/PROJECT_DOCUMENTATION.md Budget section (updated from Chat 1)
3. Me: Find and fix bug
4. Me: Update documentation/PROJECT_DOCUMENTATION.md "Critical Bugs Fixed" section
5. documentation/PROJECT_DOCUMENTATION.md is now current again

Chat 3 (Enhancement):
1. "Add budget alerts to notifications"
2. Me: Read documentation/PROJECT_DOCUMENTATION.md Budget section (current from Chat 2)
3. Me: Check documentation/PROJECT_DOCUMENTATION.md design patterns for similar features
4. Me: Implement enhancement
5. Me: Update documentation/PROJECT_DOCUMENTATION.md with new feature details
6. documentation/PROJECT_DOCUMENTATION.md is now the most current reference
```

---

## 🎊 You're All Set!

**Your workflow is now:**

1. 📌 Have `documentation/.INSTRUCTIONS.md` in your repo
2. 📌 Have `documentation/PROJECT_DOCUMENTATION.md` as your authority
3. 💬 Start PyCharm chats mentioning these files
4. 🔧 I implement following the patterns
5. ���� documentation/PROJECT_DOCUMENTATION.md gets updated
6. ✅ Everything is documented and consistent

**The instructions persist. The documentation stays current. Everything flows through documentation/PROJECT_DOCUMENTATION.md.**

---

**Happy coding!** 🚀

---

**Version 1.0 | January 14, 2026**

