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

At the initial Week 1 entry, testing was pending. The first open-circuit voltage test was completed on September 19, 2026; see the work log below.

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

- At the initial entry, hardware testing was pending. The voltage-measurement task was completed on September 19; load testing remains pending.

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


## Position convention: September 19, 2026

For the seven morning open-circuit readings in `data/measurements/solar-readings-2026-09-19.csv`, the user reported sun position as 135 degrees. Panel positions use user-assigned descriptive labels: facing up/horizontal = 180 degrees, facing down = -180 degrees, facing sun = 135 degrees. These are not measured geometric angles and should not be used for angle-based calculations. The user corrected all panel angles previously labeled 45 degrees to 135 degrees, including facing opposite the sun. The panel-position description column was removed at the user's request; both directions now share the same angle label. This correction supersedes the initial estimated angles; original voltage readings and timestamps are unchanged.


## Work log: September 19, 2026

### What I completed today

- Completed the Week 1 task of setting up the multimeter for DC voltage and recording the panel's open-circuit voltage in sunlight.
- Used the panel labeled DC 6 V, with no LED, battery, Arduino, or other load attached. Black probe was connected to COM and panel negative; red probe to the V/ohm/mA socket and panel positive, with the meter set to the 20 V DC range.
- Recorded seven real voltage readings while changing panel orientation, from 11:37:27 to 11:43:12 PDT. Conditions were sunny; subsequent readings carried forward that condition. Timestamps were recorded when readings were logged.
- Saved readings in `data/measurements/solar-readings-2026-09-19.csv`. Current and battery fields remain blank because they were not measured.
- Updated the dashboard to show the seven recorded readings, timestamps, voltage chart, sun position, and panel angle. Current, power, and battery are shown as not measured rather than zero.
- Corrected the position labels using the convention above and removed the panel-position description column as requested.

### What I learned

- The solar panel produces voltage; the multimeter measures it.
- DC maintains polarity; AC reverses polarity. A changing DC voltage is still DC if polarity does not reverse.
- Voltage is measured in volts, current in amperes, and power in watts. Power equals voltage times current.
- Open-circuit voltage is measured without a load and does not establish the panel's available power.
- The panel's 6 V rating differs from its measured open-circuit voltage; the highest recorded value today was 6.94 V.

### Measurements

Date: September 19, 2026. Times below are PDT (UTC-07:00). Sun-position label: 135 for all readings. Panel-angle numbers are user-assigned position labels, not measured geometric angles.

| Time | Open-circuit voltage (V) | Panel-angle label |
| --- | --- | --- |
| 11:37:27 | 6.84 | 135 |
| 11:40:06 | 6.80 | 180 |
| 11:41:11 | 6.90 | 135 |
| 11:41:35 | 2.74 | -180 |
| 11:41:59 | 6.00 | 135 |
| 11:42:50 | 6.87 | 180 |
| 11:43:12 | 6.94 | 135 |

### What worked and what needs improvement

- The meter initially showed zero; after reviewing the setup and changing to the 20 V DC setting, readable voltage values were obtained.
- Recorded voltage ranged from 2.74 V to 6.94 V. These measurements alone do not compare power output across positions.
- Exact panel angles were difficult to determine. Position labels were corrected during the session and must not be used as measured angles for calculations.
- Test location was not recorded.
- Software checks confirmed all seven rows load, the latest voltage is 6.94 V, the page returns HTTP 200, and missing measurements are labeled correctly. Browser visual verification was unavailable.

### Initial Week 2 hardware plan (before the afternoon test)

- Identify the LED and the available resistor values/power ratings before choosing the series resistor.
- With the panel covered, build the series loop: panel positive -> resistor -> LED anode; LED cathode -> panel negative.
- Uncover the panel and check the LED. Measure voltage across the connected panel/load with the meter still in DC voltage mode.
- Learn the meter-specific series connection and fused input requirements before measuring current. Do not switch to current mode while the meter remains across the panel.
- Record loaded voltage and current under the same conditions, then calculate power. Complete at least three load-test observations.
- Arduino, INA219, and battery connections are not part of this first LED test.

### Evidence saved

- `data/measurements/solar-readings-2026-09-19.csv`
- Updated Flask dashboard and this notebook

The Week 1 open-circuit voltage task is complete. By the end of the afternoon session, the Week 2 LED/resistor circuit was operating and five loaded-voltage readings were recorded. Current determination and power calculation remain pending.


### Measurement-type labels for logging

Removed the duplicate `setup` column. Keep `measurement_type` as the single field identifying the test: `open_circuit_voltage` for the seven existing readings and `loaded_voltage` for the five afternoon LED/resistor load-test readings. The file now contains twelve readings in total.


## Afternoon hardware test: September 19, 2026

### Setup and completion

- Assembled a solar-panel, resistor, and LED series circuit on the breadboard using jumper wires. The user confirmed that the LED lit up.
- The selected design uses a standard red LED and a nominal 1 kOhm series resistor; verify the installed resistor value before calculating current. The panel label is DC 6 V.
- Breadboard wiring provided: LED long leg E10, short leg E11; resistor C10 to C15; panel-positive jumper A15; panel-negative jumper A11. No UNO, INA219, or battery is required for this circuit.
- Measured voltage across the panel with the LED/resistor circuit connected, using the 20 V DC meter setting. These are loaded-voltage readings, not current readings.
- Recorded five observations under sunny conditions, with sun-position label 160 throughout. Times are logging times in PDT (UTC-07:00).

### Loaded-voltage measurements

| Time (PDT) | Sun-position label | Panel-angle label | Loaded voltage (V) |
| --- | --- | --- | --- |
| 14:53:13 | 160 | 180 | 6.66 |
| 14:55:05 | 160 | 135 | 6.86 |
| 14:55:47 | 160 | 45 | 3.47 |
| 14:56:28 | 160 | -180 | 1.57 |
| 14:57:45 | 160 | 90 | 6.76 |

### Findings and limits

- Highest loaded voltage in this session: 6.86 V at panel label 135. Lowest: 1.57 V at panel label -180 (facing down).
- Changing panel orientation coincided with changes in loaded voltage. This does not establish the best angle for power generation: current has not yet been determined, and sunlight was not independently measured.
- The LED lighting confirms that the panel supplied current to the load. LED brightness/on-off status was not recorded for each individual reading, so it cannot be inferred for every position.
- Do not directly attribute morning-versus-afternoon voltage differences to the load alone: measurement times and sun-position labels differed, and no matched open-circuit/loaded pair was taken under identical conditions.
- Angles remain user-assigned position labels, not instrument-measured geometry. The morning correction from 45 to 135 applies only to those earlier readings; the afternoon panel label 45 is retained exactly as reported.
- Current and battery fields remain blank. Power has not been calculated. Twelve readings are saved: seven open-circuit and five loaded-voltage observations.

### Next experiment: determine current and power

1. Confirm the resistor is 1 kOhm (1,000 ohms); record its actual value or tolerance if available.
2. Keep the existing LED/resistor circuit connected and the meter on DC voltage, with black lead in COM and red lead in the voltage socket.
3. Measure across the resistor: red probe at its C15 end and black probe at its C10 end. Keep probe tips from bridging the two ends.
4. Calculate estimated circuit current using I = V_resistor / R. For a 1,000-ohm resistor, the numerical resistor voltage in volts equals the estimated current in milliamperes. This is current inferred from voltage and resistance, not a direct ammeter measurement.
5. Without changing panel position, measure loaded panel voltage again promptly under steady sunlight. Calculate P = V_panel * I, using amperes for watts. Do not divide panel voltage by the resistor value: the LED also has a voltage drop.
6. Record resistor voltage, resistance, loaded panel voltage, calculated current/power, conditions, and LED status. No resistor-voltage reading has been supplied yet.

Keep the meter in voltage mode for this method. Any later direct current measurement needs a separate series-wiring procedure and confirmation of the meter's appropriate input and range.

### Evidence and remaining Week 2 work

Evidence: `data/measurements/solar-readings-2026-09-19.csv` contains all twelve observations. The LED circuit and the session's loaded-voltage tests are complete. Current determination, power calculations, and documenting those results remain before the Week 2 voltage/current/power work is complete.
