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
```
Access the app at http://localhost:8501

Option 2: Standard Python (Windows/Linux/Intel Mac)

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```
📖 How to Use

1) Staff & Rules: Enter your employees in the "Staff List". Use the "Availability Exceptions" tab to block off specific shifts (e.g., "Bob is off Tuesday").
2) Define Demand: Set how many staff you need for Morning, Lunch, and Dinner in the "Demand" table.
3) Role Rules: (Optional) In the sidebar, set minimum counts (e.g., "Manager: 1") to ensure leadership coverage.
4) Generate: Click the 🚀 button.
5) Refine: If the "Scorecard" shows a high penalty, check the breakdown (Understaffing vs. Missing Roles) and adjust your inputs.

☁️ Deployment
This app is ready for Streamlit Community Cloud.

1) Fork this repo.
2) Log in to share.streamlit.io.
3) Select the repo and deploy!

📄 License
This project is open-source. Feel free to use it for your own business!

### 3. Final Checklist Before "Push"

1.  **`requirements.txt`**: Ensure it looks exactly like this (critical for the cloud):
    ```text
    streamlit>=1.28.0
    pandas>=2.0.0
    ortools>=9.7.0
    pydantic>=2.0.0
    plotly
    numpy
    ```
2.  **`.gitignore`**: Create a file named `.gitignore` and add these lines so you don't upload junk files:
    ```text
    venv/
    __pycache__/
    .DS_Store
    *.pyc
    *.json
    *.csv
    ```
Once you push this, your project is officially "Portfolio Ready" and "Deploy Ready."
