import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import serial

import app
import capture_ina219


class FakeSerial:
    def __init__(self, lines):
        self.lines = iter(lines)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def readline(self):
        return next(self.lines)


class CaptureTests(unittest.TestCase):
    def test_plot_time_ranges_use_captured_clock_time(self):
        sessions = [
            {"label": "Earlier", "filename": "old.csv", "prediction": None,
             "rows": [{"power_mw": "30", "timestamp_ms": "10"}]},
            {"label": "New", "filename": "new.csv",
             "prediction": {"history_mw": [None, 2, 4]},
             "rows": [
                 {"power_mw": "2", "captured_at": "2026-10-04T15:00:00-07:00"},
                 {"power_mw": "4", "captured_at": "2026-10-04T15:06:00-07:00"},
                 {"power_mw": "6", "captured_at": "2026-10-04T16:00:00-07:00"},
             ]},
        ]
        all_sessions, latest = app.plot_data_for_range(sessions)
        self.assertEqual(sum(len(s["rows"]) for s in all_sessions), 4)
        self.assertEqual(latest.hour, 16)
        recent, _ = app.plot_data_for_range(sessions, "5m")
        self.assertEqual(len(recent), 1)
        self.assertEqual([r["power_mw"] for r in recent[0]["rows"]], ["6"])
        custom, _ = app.plot_data_for_range(sessions, "custom", "2026-10-04T15:05", "2026-10-04T15:10")
        self.assertEqual([r["power_mw"] for r in custom[0]["rows"]], ["4"])
        self.assertEqual(custom[0]["rows"][0]["predicted_mw"], 2)

    def test_capture_is_discovered_and_predicted(self):
        lines = [
            b"timestamp_ms,bus_voltage_v,shunt_voltage_mv,current_ma,power_mw\n",
            b"startup noise\n",
            b"1000,6.0,0.4,4.0,30.0\n",
            b"6000,6.1,0.4,4.1,32.0\n",
            b"11000,6.2,0.4,4.2,34.0\n",
            b"16000,6.3,0.4,4.3,36.0\n",
        ]
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            with patch.object(capture_ina219, "DATA_DIR", data_dir), \
                 patch.object(app, "DATA_DIR", data_dir), \
                 patch.object(serial, "Serial", return_value=FakeSerial(lines)):
                path = capture_ina219.capture("COM3", "sun", "fixed", max_readings=4)
                with path.open(newline="", encoding="utf-8") as csv_file:
                    self.assertEqual(len(list(csv.DictReader(csv_file))), 4)
                sessions = app.load_ina219_sessions()
                self.assertEqual(len(sessions), 1)
                self.assertEqual(sessions[0]["label"], "Sun")
                self.assertEqual(sessions[0]["prediction"]["next_mw"], 34)
                self.assertEqual(sessions[0]["prediction"]["mae_mw"], 4)
                page = app.app.test_client().get("/?live=1").get_data(as_text=True)
                self.assertIn("34.0 mW", page)
                self.assertIn("Stop auto-refresh", page)


if __name__ == "__main__":
    unittest.main()
