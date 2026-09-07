# Django MVP Backlog

This backlog turns the project plan into a small, dependency-ordered MVP sequence.

## 1. Establish the domain model and project configuration

**Priority:** High  
**Depends on:** None

- Configure a custom `User` model with `role` values for Admin and Member.
- Add `Household`, `Chore`, and `ChoreCompletion` models based on the plan.
- Define relationships, choices, validation, timestamps, and useful indexes.
- Create and apply migrations.

**Done when:** The models support one household per user, chore assignment, recurring-task metadata, and completion history, with automated model tests for the key constraints.

## 2. Build authentication and household membership

**Priority:** High  
**Depends on:** 1

- Implement sign up, login, logout, and password validation using Django auth.
- Create the initial household flow for an Admin.
- Let an Admin add Members and generate an invite code.
- Let a user join the Admin's household with a valid invite code.

**Done when:** Users can authenticate, belong to one household, and invalid or reused invite codes are rejected.

## 3. Add role-based permissions

**Priority:** High  
**Depends on:** 1, 2

- Restrict household management and chore administration to Admin users.
- Restrict Member actions to chores assigned to them.
- Add shared permission helpers or decorators and test unauthorized access.

**Done when:** Admin and Member workflows are enforced server-side, including direct URL and POST requests.

## 4. Implement chore management

**Priority:** High  
**Depends on:** 1, 2, 3

- Add Admin create, edit, and delete flows for chores.
- Support name, description, assignee, due date, priority, category, and status.
- Support one-time and daily, weekly, or monthly recurring chores.
- Allow Members to claim or request unassigned chores when permitted.

**Done when:** An Admin can manage the household chore list and a Member can see only relevant actions for their role.

## 5. Implement completion and recurring-task behavior

**Priority:** High  
**Depends on:** 4

- Let an assigned Member mark a chore complete.
- Record who completed it and when in `ChoreCompletion`.
- Derive or update overdue status from the due date.
- Define the MVP behavior for creating the next occurrence of a recurring chore.

**Done when:** Completion is permission-checked, history is retained, overdue chores are correct, and recurring chores continue according to their schedule.

## 6. Build the dashboard and chore discovery

**Priority:** Medium  
**Depends on:** 4, 5

- Show today's chores, overdue chores, and completion rate.
- Show per-member completed chore counts.
- Add filtering by status, priority, assignee, and category.
- Add name search.

**Done when:** Users can quickly find their work and the dashboard metrics match the underlying completion records.

## 7. Add reminders, responsive templates, and release checks

**Priority:** Medium  
**Depends on:** 2, 3, 4, 5, 6

- Add in-app reminders for overdue and upcoming chores.
- Build consistent Django templates with minimal responsive CSS for desktop and mobile.
- Add integration tests for the primary Admin and Member journeys.
- Document local setup, migrations, and the test command.

**Done when:** The primary workflows are usable on desktop and mobile, tests pass, and a new developer can run the project from the documentation.

## Explicitly excluded from this MVP

Push or email notifications, chat, payments, gamification, multiple households per user, social features, complex analytics, file uploads, and third-party authentication.
