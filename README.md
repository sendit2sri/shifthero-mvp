# shifthero-mvp
An AI-powered shift scheduling tool for restaurants. Built with Python, Streamlit, and Google OR-Tools. Generates optimized rosters while handling availability, roles, and fairness constraints

# ShiftHero 🦸 | AI Shift Scheduler for Restaurants

**ShiftHero** is a robust MVP tool designed to automate weekly employee scheduling. It moves beyond simple "slot filling" by prioritizing employee wellness (avoiding "clopens"), fairness (balancing hours), and strict role coverage (e.g., "Must have 1 Manager per shift").

![ShiftHero App](https://img.shields.io/badge/Status-Beta-blue) ![Python](https://img.shields.io/badge/Python-3.11-yellow) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red)

## 🚀 Features

* **Logic-First Solver:** Uses **Google OR-Tools (CP-SAT)** to guarantee a schedule is always found. It uses "soft constraints" with penalties rather than crashing on difficult inputs.
* **Smart Constraints:**
    * **Hard:** Respects "Unavailable" blocks (e.g., Alice cannot work Mon Morning).
    * **Soft:** Minimizes "Clopens" (Dinner shift followed by next-day Morning shift).
    * **Roles:** Ensures minimum coverage (e.g., "1 Chef required") per shift.
* **Interactive Dashboard:**
    * Drag-and-drop style editing of inputs.
    * Visual "Workload Charts" to spot burnout.
    * **WhatsApp Export:** One-click formatted text to copy-paste into staff groups.
* **Persistence:** Save and load your team configuration (JSON) week-to-week.

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (v1.28+)
* **Engine:** Google OR-Tools (Constraint Programming)
* **Data:** Pandas & Pydantic
* **Visualization:** Plotly

## 📦 How to Run Locally

### Option 1: Docker (Recommended for Mac/M1/M2)
This project includes a Docker setup to handle architecture incompatibilities with OR-Tools on Apple Silicon.

```bash
# Clone the repo
git clone [https://github.com/YOUR_USERNAME/shifthero-mvp.git](https://github.com/YOUR_USERNAME/shifthero-mvp.git)
cd shifthero-mvp

# Run with Docker Compose
docker compose up --build
