# suniq: Congressional App Challenge Plan

## Project goal

Build a web app connected to a small solar-energy experiment. The app will measure or accept solar data, display it clearly, predict available energy, and recommend when a small off-grid load should run or conserve energy.

## Final app statement

> suniq helps small off-grid systems predict available solar energy and decide when to charge a battery or operate a useful load.

## Deadline strategy

The 2026 Congressional App Challenge deadline is **October 26, 2026 at 12:00 p.m. EDT**. The goal is to finish a working minimum version early, then improve it.

The app does not need to be a commercial solar controller. It needs to be functional, understandable, original, and built primarily by the student.

## Minimum successful version

The project is ready to submit if it can:

- Display solar data on a web page.
- Calculate voltage, current, power, and energy.
- Show charts over time.
- Predict available solar energy using simple previous data.
- Recommend “Run load,” “Conserve energy,” or “Charge battery.”
- Show real measurements from a small solar panel, or clearly labeled test data if hardware is delayed.
- Explain the difference between MPPT and PWM.
- Include a short demonstration video and accessible source code.

## Recommended technology

Start simply:

- Frontend: HTML, CSS, JavaScript
- Charts: Chart.js
- Backend: Python Flask, if a backend is needed
- Data: CSV files first; SQLite later
- Hardware: Arduino Uno or ESP32
- Sensors: INA219, light sensor, and temperature sensor
- Repository: GitHub

Do not begin with a complicated cloud system, mobile app, or machine-learning model.

## Seven-week schedule

### Week 1 — Learn and plan

Learn:

- Voltage, current, resistance, power, and energy
- Ohm’s law
- How a solar panel produces electricity
- Basic HTML, CSS, JavaScript, and Python
- How to use a multimeter
- How to create and use a GitHub repository

Deliverables:

- Project notebook started
- One-page project description
- System diagram
- List of parts
- GitHub repository created

### Week 2 — Build the web-app prototype

Create a web page with:

- App name and purpose
- Current voltage, current, power, and battery level
- A line chart
- Sunny, cloudy, and shaded test buttons

Use simulated data first. The app should work before connecting hardware.

Deliverable: a working local web dashboard using sample data.

### Week 3 — Add calculations and recommendations

Add:

```text
Power = Voltage × Current
Energy = Power × Time
```

Add simple rules:

```text
If battery level is low:
    recommend conserving energy

If solar power is strong and battery level is acceptable:
    recommend running the load

If solar power is falling quickly:
    recommend conserving energy
```

Deliverable: the app changes its recommendation when the input conditions change.

### Week 4 — Measure real solar data

Use the Arduino and INA219 sensor to measure:

- Solar-panel voltage
- Current
- Power
- Light level
- Temperature

Compare the sensor readings with a multimeter. Record data every 5–10 seconds and save it as CSV.

Deliverable: at least one real data file and one graph showing solar power over time.

### Week 5 — Connect real data to the web app

Add:

- CSV upload or data import
- Historical charts
- Daily energy total
- Battery-level display
- Real versus simulated data labels

If live Wi-Fi data is difficult, use CSV upload. A reliable CSV-based application is better than an unfinished live system.

Deliverable: the app displays real measurements from the solar experiment.

### Week 6 — Add prediction and MPPT comparison

Start with a simple prediction method:

1. Group previous measurements by time of day.
2. Calculate average solar power for each time period.
3. Estimate the next few hours.
4. Compare predicted and actual power.
5. Calculate prediction error.

Add a comparison page for:

- Fixed-voltage operation
- PWM-style operation
- MPPT operation

Show energy collected and efficiency under different sunlight conditions.

Deliverable: a chart comparing the approaches and a written explanation of the results.

### Week 7 — Test, polish, and submit

Complete:

- Multiple tests in sunlight and shade
- Bug fixes
- Clear labels and units
- Mobile-friendly layout if possible
- Source-code cleanup
- README file
- Demonstration video
- Submission answers
- AI-use disclosure

Submit several days before the deadline.

## Hardware plan

### Buy first

- Arduino Uno-compatible board or ESP32
- 6 V, 2–6 W solar panel
- INA219 voltage/current sensor
- Breadboard and jumper wires
- Digital multimeter
- Resistors and LEDs
- USB cable and 5 V power supply

Expected initial cost: approximately **$75–$135**.

### Buy later, only if needed

- Light sensor
- Temperature sensor
- OLED display
- SD-card module
- Small sealed 6 V or 12 V battery
- Fuse holder and small fuse
- Small LED, fan, or pump
- Commercial low-voltage solar charge controller
- Adjustable low-power buck converter

Expected additional cost: approximately **$80–$175**.

Estimated total project cost: **$155–$310**.

## Safety limits

- Use low-voltage DC only.
- Never connect to household AC power.
- Do not use rooftop panels.
- Do not use large batteries.
- Do not charge unprotected lithium-ion cells.
- Add a fuse near the battery positive terminal.
- Verify polarity and voltage before every connection.
- Have an adult, teacher, or electrical engineer review the battery wiring.

## Testing plan

Test the system under:

- Direct sunlight
- Morning sunlight
- Afternoon sunlight
- Partial shade
- Different panel angles
- Cloudy conditions, if available

Record:

- Voltage
- Current
- Power
- Battery voltage
- Temperature
- Light level
- Load operating time
- Energy collected
- Prediction error

Repeat important tests at least three times and report averages.

## Final research question

> Can a low-cost adaptive solar system use real-time measurements and simple predictions to increase useful load operating time while protecting the battery?

## What makes the app original?

The project should not only say that MPPT is better than PWM. It should demonstrate a practical decision and measure the result.

Possible final finding:

> suniq used solar measurements and battery status to reduce unnecessary load operation and extend the useful operating time of a small off-grid system.

Only include performance numbers supported by the student’s own tests.

## Submission preparation

The demonstration video should show:

1. The student’s name and app name.
2. The problem being addressed.
3. The physical solar setup.
4. The web dashboard.
5. A change in the app recommendation.
6. The technology and programming languages used.
7. One result from testing.

The student should be able to explain every important part of the code. AI tools may support development, but their use must be disclosed and the student must make significant technical contributions.

## If the project falls behind

Keep these features:

- Working web dashboard
- Solar data upload
- Power and energy calculations
- Charts
- Simple prediction
- Adaptive recommendation
- Documented testing

Drop these features first:

- Live cloud database
- Mobile app
- Advanced machine learning
- Automatic high-power battery control
- Complex custom MPPT hardware

## First three tasks

1. Create the GitHub repository and project notebook.
2. Build a simple web page that displays simulated solar voltage, current, and power.
3. Learn to measure a small solar panel safely with a multimeter.

The first milestone is complete when the app displays a graph and recommendation using sample data.
