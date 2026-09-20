# SunIQ INA219 serial test

## Wiring

With the Arduino powered by USB and the battery disconnected:

| INA219 | Arduino Uno |
|---|---|
| VCC | 5V |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

The measured power path is:

```text
Panel positive -> INA219 VIN+
INA219 VIN- -> safe resistor/LED load positive
Panel negative -> load negative
```

Do not connect the panel directly to the Arduino 5V pin. Confirm polarity before powering the circuit.

## Upload and test

1. Install the **Adafruit INA219** library in Arduino IDE Library Manager.
2. Open `ina219_serial_test.ino`.
3. Select the Arduino board and USB port.
4. Upload the sketch.
5. Open Serial Monitor at **115200 baud**.
6. Confirm that CSV rows appear every five seconds.
7. Compare bus voltage with the multimeter under the same lighting and load.
