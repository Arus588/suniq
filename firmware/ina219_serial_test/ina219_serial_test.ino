// SunIQ Week 3: INA219 serial test
// Hardware: Arduino Uno-compatible board + INA219 breakout.
// Keep the battery disconnected during this first test.

#include <Wire.h>
#include <Adafruit_INA219.h>

Adafruit_INA219 ina219;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  if (!ina219.begin()) {
    Serial.println("ERROR: INA219 not found. Check power, ground, SDA, and SCL.");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("timestamp_ms,bus_voltage_v,shunt_voltage_mv,current_ma,power_mw");
}

void loop() {
  const float busVoltage = ina219.getBusVoltage_V();
  const float shuntVoltage = ina219.getShuntVoltage_mV();
  const float current = ina219.getCurrent_mA();
  const float power = ina219.getPower_mW();

  Serial.print(millis());
  Serial.print(',');
  Serial.print(busVoltage, 3);
  Serial.print(',');
  Serial.print(shuntVoltage, 3);
  Serial.print(',');
  Serial.print(current, 3);
  Serial.print(',');
  Serial.println(power, 3);

  delay(5000);
}
