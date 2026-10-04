"""Save INA219 Arduino serial readings to a dated CSV session."""

import argparse
import csv
import math
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data" / "measurements"
FIELDS = (
    "captured_at", "timestamp_ms", "bus_voltage_v", "shunt_voltage_mv",
    "current_ma", "power_mw", "scenario", "panel_orientation",
)


def parse_reading(line):
    """Return a valid five-column sensor row, or None for headers/noise."""
    parts = line.strip().split(",")
    if len(parts) != 5:
        return None
    try:
        timestamp = int(parts[0])
        values = [float(part) for part in parts[1:]]
    except ValueError:
        return None
    if timestamp < 0 or not all(math.isfinite(value) for value in values):
        return None
    return [timestamp, *values]


def capture(port, scenario, orientation, max_readings=None):
    import serial

    with serial.Serial(port, 115200, timeout=2) as connection:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        started = datetime.now().astimezone()
        path = DATA_DIR / f"ina219-capture-{started:%Y%m%d-%H%M%S-%f}.csv"
        with path.open("x", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(FIELDS)
            csv_file.flush()
            print(f"Saving {scenario} readings to {path}")
            count = 0
            while max_readings is None or count < max_readings:
                line = connection.readline().decode("utf-8", errors="replace")
                reading = parse_reading(line)
                if reading is None:
                    continue
                writer.writerow([datetime.now().astimezone().isoformat(timespec="seconds"),
                                 *reading, scenario, orientation])
                csv_file.flush()
                count += 1
                print(f"{count}: {reading[1]:.3f} V, {reading[3]:.3f} mA, {reading[4]:.3f} mW")
    return path


def main():
    parser = argparse.ArgumentParser(description="Log INA219 readings from the Uno to CSV")
    parser.add_argument("--port", required=True, help="Arduino USB port, for example COM3")
    parser.add_argument("--scenario", required=True, help="Condition label, for example sun or hand shade")
    parser.add_argument("--orientation", default="not recorded", help="Panel position description")
    parser.add_argument("--max-readings", type=int, help="Stop after this many valid readings")
    args = parser.parse_args()
    if args.max_readings is not None and args.max_readings < 1:
        parser.error("--max-readings must be at least 1")
    try:
        capture(args.port, args.scenario, args.orientation, args.max_readings)
    except KeyboardInterrupt:
        print("Capture stopped. Saved readings remain in the CSV.")
    except Exception as error:
        parser.exit(1, f"Capture failed: {error}\n")


if __name__ == "__main__":
    main()
