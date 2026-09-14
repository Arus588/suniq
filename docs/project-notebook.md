# SunIQ Project Notebook

This notebook records the design, testing, learning, and evidence for the SunIQ project.

## Project question

How can SunIQ help a small off-grid solar system use energy more wisely?

## Clear goal

SunIQ helps small off-grid solar systems use energy wisely by extending useful battery operating time. The project will measure solar power, track historical data, and test whether informed load decisions conserve energy compared with normal operation.

## Weekly entry template

```text
Week/date:

Goal:

What I learned:

What I built:

Test conditions:

Measurements:

What worked:

What failed:

What I changed:

Evidence saved:

Next week's goal:
```

---

## Week 1: Learn and set up

### Date

Week of September 8–14, 2026 — in progress

### Goal

Set up the SunIQ Flask project, learn the basics of solar electricity, and record the first solar-panel voltage measurement.

### What I learned

- Voltage is electrical potential.
- Current is the flow of electric charge.
- Power is calculated as voltage × current.
- A solar panel produces different amounts of energy depending on sunlight and panel angle.
- Flask can serve a Python-powered web dashboard locally.

### What I built

- A GitHub repository for SunIQ.
- A Flask web-dashboard foundation.
- A starter dashboard homepage with an About the Creator section.
- A Python 3.12 virtual environment with Flask and Gunicorn installed.

### Test conditions

The first solar-panel test has not been performed yet.

- Date and time: Pending
- Weather: Pending
- Panel angle: Pending
- Test location: Pending

### Measurements

| Measurement | Result |
| --- | --- |
| Open-circuit voltage | Not measured yet |
| Unit | V |

### What worked

- The GitHub repository was created and connected to the local project.
- The Flask dashboard foundation runs locally and returned a successful HTTP 200 response.
- The project structure, README, and project notebook are in place.

### What failed

- No solar hardware testing has been completed yet because the measurement setup is still pending.

### What I changed

- Started with a Flask dashboard rather than a standalone HTML page so the project can later accept sensor readings and CSV data.

## Work log: September 13, 2026

### What I completed today

- Reviewed the Week 1 plan and identified the remaining hardware tasks.
- Created a CSV build tracker in `docs/sunsmart-build-tracker.csv` with week, item, status, completion date, ETA, and notes columns.
- Broke the Week 1 hardware work into individual checklist items for each part and each measurement step.
- Recorded that the Arduino, solar panel, INA219 sensor, breadboard, jumper wires, multimeter, resistors/LEDs/switches, and USB power supply are available.
- Built the Week 2 simulated dashboard with voltage, current, power, and battery-level readings.
- Added Sunny, Cloudy, and Shaded controls that update the dashboard.
- Added a solar-power chart based on simulated readings.
- Added a manual measurement table and safety guidance for the daylight hardware test.
- Added `data/measurements/solar-readings-2026-09-14.csv` and updated Flask to load the newest dated measurement CSV automatically.
- Added the clear project goal to the dashboard, README, and notebook.

### Software verification

- Started the Flask development server locally.
- Confirmed the dashboard loads successfully with HTTP 200.
- Confirmed the dashboard displays data loaded from the dated CSV file.

### Still pending

- Perform the first open-circuit solar-panel voltage measurement during daylight.
- Build and test the low-voltage LED/resistor circuit.
- Replace the simulated CSV readings with real hardware measurements.

### Evidence saved

- GitHub repository: https://github.com/Arus588/suniq
- Flask dashboard source code and local HTTP 200 test result
- Project README and initial dashboard templates

### Next week's goal

Complete the first solar-panel voltage measurement, then build a dashboard with simulated solar data and test the panel under several conditions.
