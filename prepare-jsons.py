import agate
import agateexcel
import csv
import json
import subprocess
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from utils import format_time, parse_time


def correct_time(finish_string: str, start_string: str, si: str) -> str:
    """
    Adjusts time of SI 5 card, which only supports 12-hour format.
    """
    finish = parse_time(finish_string, strip_milliseconds=True)
    start = parse_time(start_string)
    noon = parse_time("12:00:00")

    if is_sportident_5(si) and finish < noon and not (start <= finish < noon):
        finish += timedelta(hours=12)

    return format_time(finish)


def is_sportident_5(si: str) -> bool:
    return 1 <= int(si) <= 499999


src = Path("data")
src.mkdir(exist_ok=True)

sheets = {
    "CSV Import": "entries",
    "PRINT E1": "E1",
    "PRINT E2": "E2",
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
    csv_from_excel(Path("Web_Vysledky_Kockogaining_2024.xlsx"), sheets)

    with open("event.json") as event_file:
        event = json.load(event_file)

    stages = OrderedDict(event["stages"])

    for stage_name, stage in stages.items():
        with open(src / f"Vysledky_{stage_name}.csv") as stage_file:
            reader = csv.DictReader(stage_file)
            times_cm = open(src / f"times-{stage_name}.json", "w")
            punches_cm = open(src / f"punches-{stage_name}.json", "w")
            with punches_cm as punches_file, times_cm as times_file:
                punches = {}
                times = {}
                for row in reader:
                    if row["id"] == "":
                        continue
                    times[row["id"]] = row["time"]
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
                json.dump(times, times_file)


if __name__ == "__main__":
    main()
