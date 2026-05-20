# Iteration Plan 1 – Campus Hub

## Team: Campus Hub Team

## Iteration Dates:
May 18 – May 25, 2026

## Plan Date:
May 20, 2026

---

## Team Members

- Lorenz Hunter

---

## Iteration Goal

Make sure the program is working as intended.

---

## User Stories Included (Partial Progress – Priority 1)

- Login / account system (structure only)
- View all events (basic page setup)
- Filter events (UI only)

---

## Planned Tasks

### 1. Backend: App Setup and Routing (Lorenz)

- Create `app.py`
- Initialize Flask app
- Add basic routes:
  - `/`
  - `/login`

Estimated: 10–12 hours

---

### 2. Backend + Structure (Su Noble Aung)

- Connect routes to templates
- Prepare structure for event data

Estimated: 6–8 hours

---

### 3. Frontend: Base Templates (Kevin)

- Create `layout.html`
- Create `main.html`
- Create `login.html`
- Apply layout inheritance

Estimated: 8–10 hours

---

### 4. Frontend: Page Structure (Rokin)

- Add sections to `main.html`
- Add placeholder event list
- Add basic filter UI

Estimated: 6 hours

---

## Key Metrics

- Total Estimated Hours: ~32–36 hours
- Total Tasks Planned: 4

---

## Assumptions

- Focus is on structure, not full functionality
- Database and full logic will be added later

---

## Risks

- Merge conflicts during initial setup
- Routing or template errors
- Time constraints

---

## Success Criteria

- Flask app runs successfully
- Main page and login page load correctly
- Layout template is applied
- Basic UI for events and filter exists