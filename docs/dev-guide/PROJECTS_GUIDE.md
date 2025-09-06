# GitHub Project Board Guide

This document describes the project board workflow, automation rules, and labeling strategy for our repository.

---

## 🎯 Workflow Overview

We use a **Kanban-style board** to manage tasks, features, and bugs throughout the development lifecycle.

**Board Columns:**

1. **Backlog**  
   - Ideas and tasks that are not yet prioritized.  
   - Anyone can add tasks here.  

2. **Ready**  
   - Well-defined and prioritized tasks.  
   - Contains issues with clear descriptions and acceptance criteria.  

3. **In Progress**  
   - Tasks currently being developed.  
   - **WIP Limit**: Max 2 tasks per developer.  

4. **In Review**  
   - Pull Requests awaiting code review.  

5. **Testing**  
   - Tasks merged into staging and pending QA/automated testing.  

6. **Done**  
   - Completed tasks, tested, and merged into the main branch.  

---

## ⚡ Automation Rules

We use GitHub Project **automation** to reduce manual updates:

- When an **issue** is labeled `ready` → Move to **Ready**  
- When a **pull request** is opened → Move to **In Review**  
- When a **pull request** is merged → Move to **Testing**  
- When an **issue** is closed → Move to **Done**  

---

## 🏷️ Labels

Labels are used for categorization, prioritization, and filtering on the board.

### Task Type
- `feature` → New feature implementation  
- `bug` → Bug fix  
- `enhancement` → Improvement to existing functionality  
- `documentation` → Docs and README updates  

### Priority
- `P0 - critical` → Must be addressed immediately  
- `P1 - high` → High priority, address soon  
- `P2 - medium` → Normal priority  
- `P3 - low` → Low priority / nice-to-have  

### Scope
- `frontend` → Frontend-related work  
- `backend` → Backend-related work  
- `infra` → Infrastructure / DevOps tasks  
- `design` → UI/UX design  

---

## 📌 Best Practices

- Always create an **Issue** for every feature/bug before starting work.  
- Keep issues **small and focused**, so they can move through the board quickly.  
- Review **In Review** tasks promptly to avoid bottlenecks.  
- Ensure all tasks in **Ready** have clear descriptions before moving to **In Progress**.  
- Regularly review the board during team meetings.  

---

## ✅ Summary

- Board Flow: **Backlog → Ready → In Progress → In Review → Testing → Done**  
- Use labels for **type, priority, and scope**  
- Follow automation rules to keep the board updated  
- Limit WIP and keep the workflow transparent  

This workflow helps the team maintain clarity, reduce context switching, and deliver features continuously.
