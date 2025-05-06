# 🛣️ DevTask Tracker - Development Roadmap

This document outlines the planned features and development stages of the
**DevTask Tracker** project. It is part of my #60DaysOfCoding journey to learn
and build progressively.

Not sure what I'm trying to build at the moment, but this seem as a possble
roadMap to it ---->

---

## ✅ Stage 1: Core Features (MVP)

- [x] Project setup with FastAPI + SQLModel
- [x] Define Task model (name, status, timestamps)
- [ ] Create a task (POST /tasks)
- [ ] List all tasks (GET /tasks)
- [ ] Retrieve a single task by ID (GET /tasks/{id})
- [ ] Update task (PUT /tasks/{id})
- [ ] Delete task (DELETE /tasks/{id})
- [ ] Add priority (low, medium, high)
- [ ] Add due date field
- [ ] Add created_at and updated_at timestamps (auto-managed)

---

## 🔐 Stage 2: Authentication & Users

- [ ] User model (id, email, password)
- [ ] Password hashing
- [ ] JWT-based login & signup endpoints
- [ ] Restrict task access per user
- [ ] Link tasks to users (foreign key)
- [ ] Endpoint: Get current user's tasks only

---

## 🔧 Stage 3: Developer-Centric Features

- [ ] Tagging system (e.g., bug, feature, idea)
- [ ] Task dependencies (e.g., Task A before Task B)
- [ ] Track estimated time vs actual time
- [ ] Auto timestamp on status change
- [ ] Task history log (audit trail)

---

## 🤝 Stage 4: Team Collaboration Features

- [ ] Team or project model
- [ ] Invite users to a project
- [ ] Role-based access (Owner, Member)
- [ ] Comments per task
- [ ] Task watchers / assigned members
- [ ] Notifications (email or in-app)

---

## 📊 Stage 5: Productivity Enhancers

- [ ] Dashboard: total tasks, progress stats
- [ ] Filtering (by status, tag, priority)
- [ ] Search tasks by keyword
- [ ] Pagination for task lists
- [ ] Sorting by due date or priority
- [ ] Recurring tasks
- [ ] Reminders or due-soon alerts

---

## 🌐 Stage 6: Frontend / Integration

- [ ] Basic frontend using React or HTMX
- [ ] Integrate GitHub issues (optional)
- [ ] Mobile-friendly API responses
- [ ] Swagger/OpenAPI docs polishing

---

## 🚀 Stage 7: Deployment

- [ ] Prepare `.env` file and config setup
- [ ] Dockerize app (optional)
- [ ] Deploy to Render / Vercel / Railway / DigitalOcean
- [ ] Add README badges (build passing, hosted link)

---

## 🧠 Learning Milestones

- [ ] FastAPI basics
- [ ] SQLModel and migrations
- [ ] JWT Auth flow
- [ ] Clean project structure
- [ ] Database relationships
- [ ] Writing good API docs
- [ ] CI/CD basics (GitHub Actions)

---

**Progress Tracker**  
🟢 You are currently on **Stage 1** (MVP).  
Keep pushing — small wins daily make a big difference!
