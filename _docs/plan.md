# Shared Household Chores Manager — Project Specification

## Overview
A Django web application for managing chores in a single shared household.
Goal: a small, professional, ship-ready MVP with authentication, permissions,
recurring tasks, assignment logic, dashboards, and history.

---

## Core Scope

### Users & Authentication
- Email + password authentication (Django auth)
- Roles: **Admin** and **Member**
- One household per user (single-household app)

### Household & Members
- Admin can add members manually
- Admin can generate an invite code to join the household

### Chores
- Fields: name, description, assignee, due date, priority
- Type: one-time and recurring (daily, weekly, monthly)
- Priority: Low / Medium / High
- Status: Pending / Completed / Overdue
- Categories: Cleaning, Cooking, Shopping, Maintenance, Other### Assignment
- Manual assignment by admin
- Optional rotation between members
- Members can claim/request unassigned chores

### Permissions
- Admin: create / edit / delete chores manage members
- Member: update status of chores assigned to them

### Completion & History
- Members mark chores as done
- Completion history retained (who completed what, and when)

### Dashboard
- Today's chores
- Overdue chores
- Household completion rate
- Individual member statistics (completed chore counts)

### Extras
- In-app reminders (no push/email notifications)
- Filtering: status, priority, assignee, category
- Search chores by name
- Responsive (desktop + mobile)

---

## Explicitly Out of Scope
- ❌ Push notifications- ❌ Chat / messaging
- ❌ Payments
- ❌ Gamification / points
- ❌ Multiple households per user
- ❌ Social features
- ❌ Complex analytics
- ❌ File image uploads
-  Third-party authentication (e.g., Google sign-in)

---

## Tech Stack
- **Backend:** Django (Python)
- **Database:** SQLite (or PostgreSQL if preferred)
- **Frontend:** Django templates + minimal CSS (responsive)

---

## Suggested Django Models (starting point)
- `User` (extends AbstractUser, role field)
- `Household` (name, invite)
- `Chore` (name, description, assignee, due_date, priority, category, recurrence, is_recurring)
- `ChoreCompletion` (chore, completed_by, completed_at)
