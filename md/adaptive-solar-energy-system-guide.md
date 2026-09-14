# Adaptive Solar Energy System

## A beginner project guide for an 11th-grade student

### The project in one sentence

Build a small solar-powered system that measures available energy, learns how much energy is likely to be available, and decides when to charge a battery or run a useful load.

The final system may power an LED, fan, or small pump. It will measure solar-panel voltage, current, power, light level, temperature, and battery voltage.

## What makes this project interesting?

A simple solar charger only charges a battery. This project asks a better engineering question:

> Can a low-cost solar system use measurements and predictions to collect energy efficiently and use it intelligently?

The project combines electrical engineering, solar energy, programming, sensors, data analysis, and optimization.

## Important safety rules

- Work only with low-voltage DC systems.
- Do not connect anything to household AC power.
- Do not use rooftop panels or large batteries.
- Do not build a lithium-ion charger from individual unprotected cells.
- Use a small sealed lead-acid battery or a protected commercial battery pack.
- Add a fuse near the battery positive terminal.
- Check polarity and voltage with a multimeter before connecting anything.
- Never leave a battery charging unattended.
- Ask an adult, teacher, or electrical engineer to review the wiring before battery testing.

## The learning path

Do not begin by building the complete system. Complete these stages in order:

1. Learn electricity and solar basics.
2. Measure a solar panel manually.
3. Read sensors with an Arduino.
4. Record and graph data.
5. Add a safe battery and load.
6. Add simple automatic energy-management rules.
7. Add MPPT and compare it with a simpler method.
8. Test, analyze, and document the results.

## Stage 0: Learn the basics

Spend the first 1–2 weeks learning these ideas:

### Electricity

- Voltage: electrical pressure
- Current: flow of electric charge
- Resistance: opposition to current
- Power: how quickly energy is being used
- Energy: power used over time

Important equations:

```text
Power (watts) = Voltage (volts) × Current (amps)
Energy (watt-hours) = Power (watts) × Time (hours)
Ohm's law: Voltage = Current × Resistance
```

### Solar panels

A solar panel does not always produce the same power. Its output changes with:

- Sunlight intensity
- Panel angle
- Temperature
- Shade
- Electrical load

### Programming

Learn how to:

- Write and upload a simple Arduino program
- Read an analog sensor
- Print values to the Serial Monitor
- Use variables, loops, and `if` statements
- Save data to a CSV file
- Plot a graph in Excel or Python

Good search topics:

- Arduino beginner tutorial
- Voltage, current, and power for beginners
- Solar panel IV curve
- Arduino INA219 tutorial
- Python plot CSV data

Keep a notebook. Record what was learned, questions, wiring changes, code versions, and mistakes.

## Shopping list

### Buy first: measurement kit

| Item | Specification | Estimated cost |
|---|---|---:|
| Arduino Uno-compatible board | USB programmable | $15–$30 |
| Small solar panel | 6 V, 2–6 W | $15–$30 |
| INA219 sensor | Voltage/current/power measurement | $10–$20 |
| Breadboard and jumper wires | Beginner electronics kit | $10–$20 |
| Digital multimeter | Basic DC voltage/current measurement | $15–$30 |
| Resistors, LEDs, switches | Basic experiments | $10–$20 |
| USB cable and 5 V supply | For Arduino | $10–$15 |
| **Initial total** |  | **About $75–$135** |

An Arduino Uno and INA219 are beginner-friendly choices. The INA219 can measure voltage, current, and power. See the [Arduino Uno documentation](https://store.arduino.cc/products/arduino-uno-rev3) and [Arduino INA219 documentation](https://docs.arduino.cc/libraries/arduinoina219/).

### Buy later: system upgrades

| Item | Specification | Estimated cost |
|---|---|---:|
| ESP32 board | Optional Wi-Fi/data features | $8–$20 |
| Light sensor | LDR or BH1750 | $3–$15 |
| Temperature sensor | DS18B20 or similar | $3–$10 |
| Small OLED display | Optional live display | $5–$15 |
| SD-card module | Optional data logging | $5–$12 |
| Small sealed battery | 6 V or 12 V, 1–4 Ah | $20–$40 |
| Fuse holder and fuses | 0.5–1 A for small prototype | $5–$10 |
| Small DC load | LED, fan, or pump | $10–$25 |
| Commercial low-voltage solar controller | Safe comparison baseline | $15–$40 |
| Adjustable buck converter | Low-power, current-limited | $10–$25 |
| **Later total** |  | **About $80–$175** |

### Expected complete-project budget

Approximately **$155–$310**, depending on what is already available and whether optional parts are purchased.

## Stage 1: Measure the solar panel

Do this before connecting a battery.

1. Put the panel in sunlight.
2. Measure its open-circuit voltage with the multimeter.
3. Connect a small resistor or LED load.
4. Measure voltage and current.
5. Calculate power using `Power = Voltage × Current`.
6. Repeat at different angles and in partial shade.
7. Record every result in a table.

Example data table:

| Date/time | Condition | Voltage | Current | Power | Temperature |
|---|---|---:|---:|---:|---:|
|  | Full sun |  |  |  |  |
|  | Shade |  |  |  |  |
|  | 45° angle |  |  |  |  |

## Stage 2: Connect the Arduino and sensors

The first goal is simply to display measurements:

```text
Solar panel → INA219 → small safe load
                  ↓
               Arduino
```

Start with the Arduino Serial Monitor. Display:

- Voltage
- Current
- Power
- Temperature
- Light level

Do not add the battery yet. First prove that the measurements are believable by comparing them with the multimeter.

## Stage 3: Build a data logger

Record one measurement every 5–10 seconds. Save the data as CSV and make graphs of:

- Power versus time
- Voltage versus time
- Current versus time
- Power versus light level
- Power versus panel angle

At this point, the student has completed a meaningful mini-project: **Measuring and modeling small solar-panel performance under changing conditions.**

## Stage 4: Add the battery and useful load

Only after the previous stages work:

1. Use a small sealed battery.
2. Add a fuse near the battery positive terminal.
3. Use a commercial low-voltage solar charge controller as the safety baseline.
4. Connect a small LED, fan, or pump as the load.
5. Measure battery voltage, charging current, and load operation.

The commercial controller is useful because the student can compare his measurements and control strategy with a known working device.

## Stage 5: Add adaptive energy management

Begin with simple rules—not artificial intelligence.

Example rules:

```text
If battery level is low:
    turn the load off

If sunlight is strong and battery level is acceptable:
    allow the load to run

If sunlight is falling quickly:
    reduce or stop the load

If battery temperature is too high:
    stop charging and raise an alert
```

Test whether these rules keep the load operating longer than a system that simply runs the load continuously.

## Stage 6: Add energy prediction

Use the collected data to estimate how much solar energy may be available during the next few hours.

Start with a simple approach:

1. Record solar power for several days.
2. Calculate the average power for each hour.
3. Compare today’s measurements with previous days.
4. Predict whether enough energy will be available later.
5. Use the prediction to decide whether to run or conserve energy.

Later, he can try a simple Python model using sunlight, temperature, time of day, and recent power.

## Stage 7: Add MPPT

MPPT stands for Maximum Power Point Tracking. The controller changes the panel’s operating point and searches for the voltage that produces the most power.

Use the Perturb and Observe method:

1. Slightly change the converter setting.
2. Measure panel power.
3. If power increases, continue in the same direction.
4. If power decreases, reverse direction.
5. Repeat periodically.

Compare three methods:

- Fixed-voltage operation
- PWM-style operation
- MPPT operation

Use the same panel, battery, and test conditions for each method.

## Final research question

> Can a low-cost adaptive solar system use real-time measurements and simple predictions to increase useful load operation while protecting the battery?

## Measurements for the final report

Collect:

- Solar-panel voltage
- Solar-panel current
- Solar-panel power
- Battery voltage
- Charging current
- Temperature
- Light level
- Load operating time
- Energy collected
- Energy delivered to the load
- MPPT and overall system efficiency
- Prediction error

Test under:

- Direct sunlight
- Morning and afternoon sunlight
- Partial shade
- Different panel angles
- Cloudy conditions, if available

Repeat each test several times and report averages. Explain unusual results instead of deleting them.

## Suggested 12-week schedule

| Weeks | Goal |
|---|---|
| 1–2 | Learn electricity, solar, Arduino, and multimeter basics |
| 3 | Measure the panel manually |
| 4 | Read INA219 and other sensors |
| 5 | Record and graph solar data |
| 6 | Add temperature/light measurements |
| 7 | Add a safe battery and commercial controller |
| 8 | Control an LED, fan, or pump with simple rules |
| 9 | Build a basic energy-prediction method |
| 10 | Add and test MPPT |
| 11 | Repeat controlled experiments |
| 12 | Analyze results and prepare the report/presentation |

## Project notebook template

For every work session, write:

```text
Date:

Today's goal:

What I changed:

Measurements:

What worked:

What failed:

What I learned:

Next step:
```

## What would make the project stand out?

The project should not claim only that “MPPT is more efficient.” Instead, answer a specific practical question with original measurements. Strong additions include:

- Net energy: subtract the energy used by motors, sensors, and electronics.
- Prediction accuracy: compare predicted and actual solar output.
- Battery protection: show that the system avoids excessive discharge or overheating.
- Cost analysis: estimate the cost per watt-hour delivered.
- Reproducibility: repeat tests and publish the data and code.
- Real use case: optimize the system for emergency lighting, irrigation, or an off-grid sensor.

## First task today

Do not buy the complete system yet. Start by doing these five things:

1. Learn voltage, current, power, and energy.
2. Watch or read one Arduino beginner lesson.
3. Obtain a multimeter and small solar panel.
4. Measure the panel in sunlight and shade.
5. Start the project notebook.

The first milestone is simple: **produce a graph showing how solar-panel power changes with sunlight or panel angle.**
