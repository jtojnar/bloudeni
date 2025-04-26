#!/usr/bin/env python3

import agate
import agateexcel
import csv
import json
import subprocess
import unittest
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from utils import format_time, parse_time


def correct_time(finish_string: str, start_string: str, si5: bool) -> str:
    """
    Adjusts time of SI 5 card, which only supports 12-hour format.
    """
    finish = parse_time(finish_string, strip_milliseconds=True)
    start = parse_time(start_string)
    noon = parse_time("12:00:00")

    if si5:
        if finish < start:
            finish += timedelta(hours=12)
        if finish < start:
            finish += timedelta(hours=12)
    else:
        if finish < start:
            finish += timedelta(hours=24)

    return format_time(finish)


def is_sportident_5(si: str) -> bool:
    return 1 <= int(si) <= 499999


src = Path("data")
src.mkdir(exist_ok=True)

sheets = {
    "CSV Import": "entries",
    "PRINT E1": "N2H",
    "PRINT E2": "D5H",
    "PRINT E3": "H4H",
}


def csv_from_excel(file: Path, sheets: dict[str, str]) -> None:
    for sheet, target in sheets.items():
        file_name = target if target == "entries" else "Vysledky_" + target
        table = agate.Table.from_xlsx(
            file,
            sheet=sheet,
            column_types=agate.TypeTester(
                types=[
                    agate.Text(),
                ],
            ),
        )
        with open(src / f"{file_name}.csv", "w") as out:
            table.to_csv(out)


def main() -> None:
    csv_from_excel(Path("Vysledky_Bloudeni_2025.xlsx"), sheets)

    with open("event.json") as event_file:
        event = json.load(event_file)

    stages = OrderedDict(event["stages"])

    for stage_name, stage in stages.items():
        with open(src / f"Vysledky_{stage_name}.csv") as stage_file:
            reader = csv.DictReader(stage_file)
            with open(src / f"punches-{stage_name}.json", "w") as punches_file:
                punches = {}
                for row in reader:
                    punches[row["id"]] = list(
                        filter(
                            lambda cp: cp is not None,
                            map(
                                lambda cp: int(cp) if int(row[str(cp)]) != 0 else None,
                                stage["cps"].keys(),
                            ),
                        )
                    )
                json.dump(punches, punches_file)

        readouts_path = src / f"readouts-{stage_name}.csv"
        if Path(readouts_path).exists():
            readouts_cm = open(readouts_path, errors="ignore", encoding="utf-8")
            times_cm = open(src / f"times-{stage_name}.json", "w")
            with readouts_cm as readouts_file, times_cm as times_file:
                readouts = csv.DictReader(readouts_file, delimiter=";")

                json.dump(
                    {
                        row["SIID"].strip(): correct_time(
                            row["Finish time"].strip() or "00:00:00",
                            stage["start"],
                            si5=is_sportident_5(row["SIID"].strip()),
                        )
                        for row in readouts
                    },
                    times_file,
                )


if __name__ == "__main__":
    main()


class CorrectTimeTests(unittest.TestCase):
    def test_night_before_midnight_si7(self):
        self.assertEqual(
            "23:07:21",
            correct_time(
                finish_string="23:07:21",
                start_string="21:00:00",
                si5=False,
            ),
        )

    def test_night_before_midnight_si5(self):
        self.assertEqual(
            "23:05:10",
            correct_time(
                finish_string="11:05:10",
                start_string="21:00:00",
                si5=True,
            ),
        )

    def test_night_over_midnight_si7(self):
        self.assertEqual(
            "24:01:05",
            correct_time(
                finish_string="00:01:05",
                start_string="21:00:00",
                si5=False,
            ),
        )

    def test_night_over_midnight_si5(self):
        self.assertEqual(
            "24:15:44",
            correct_time(
                finish_string="00:15:44",
                start_string="21:00:00",
                si5=True,
            ),
        )

    def test_exactly_midnight_si7(self):
        self.assertEqual(
            "24:00:00",
            correct_time(
                finish_string="00:00:00",
                start_string="23:00:00",
                si5=False,
            ),
        )

    def test_exactly_midnight_si5(self):
        self.assertEqual(
            "24:00:00",
            correct_time(
                finish_string="00:00:00",
                start_string="23:00:00",
                si5=True,
            ),
        )

    def test_no_adjustment_needed(self):
        self.assertEqual(
            "22:30:30",
            correct_time(
                finish_string="22:30:30",
                start_string="21:00:00",
                si5=False,
            ),
        )

    def test_almost_wraparound_si5(self):
        self.assertEqual(
            "23:59:59",
            correct_time(
                finish_string="11:59:59",
                start_string="21:00:00",
                si5=True,
            ),
        )

    def test_small_time_si5(self):
        self.assertEqual(
            "21:05:10",
            correct_time(
                finish_string="09:05:10",
                start_string="21:00:00",
                si5=True,
            ),
        )

    def test_exact_noon_si5(self):
        self.assertEqual(
            "12:00:00",
            correct_time(
                finish_string="12:00:00",
                start_string="09:00:00",
                si5=True,
            ),
        )

    def test_after_noon_si5(self):
        self.assertEqual(
            "13:00:00",
            correct_time(
                finish_string="01:00:00",
                start_string="11:00:00",
                si5=True,
            ),
        )

    def test_exact_noon_si7(self):
        self.assertEqual(
            "12:00:00",
            correct_time(
                finish_string="12:00:00",
                start_string="09:00:00",
                si5=False,
            ),
        )

    def test_before_noon_si5(self):
        self.assertEqual(
            "11:30:00",
            correct_time(
                finish_string="11:30:00",
                start_string="09:00:00",
                si5=True,
            ),
        )
