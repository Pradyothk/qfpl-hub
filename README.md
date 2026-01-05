# 🏆 QFPL Hub

A consolidated tool for QFPL managers to analyze squads, validate lineups, and check chip eligibility.

## Features

### 1. Differential Calculator (Diffx)
- Compare your QFPL squad against an opponent using **live FPL data**.
- Shows "Effective Ownership" (EO) differences.
- Automatically fetches current or last-known squads for future gameweeks.

### 2. Lineup Submission Helper
- Validates your lineup before submission.
- **Bench Streak Rule:** Warns if a player has been benched 2x in a row (Must Start rule).
- **Captaincy Rule:** Tracks if a player has already captained in the current phase.

### 3. Chip Submission Helper
- Checks eligibility for all chips.
- **Red Hot Form:** Validates 4 consecutive wins.
- **Stay Humble:** Validates that you are playing an opponent you previously lost to.
- **Usage Limits:** Checks "Once per season" and "2 chips per Phase" rules.

## How to Run Locally
1. Clone the repo.
2. Install requirements: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`
