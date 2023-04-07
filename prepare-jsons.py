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
    "PRINT E1": "N2H",
    "PRINT E2": "D5H",
    "PRINT E3": "H4H",
}


def csv_from_excel(file: Path, sheets: dict[str, str]) -> None:
    for sheet, target in sheets.items():
        file_name = target if target == "entries" else "Vysledky_" + target
        with open(src / f"{file_name}.csv", "wb") as out:
            subprocess.run(
                ["in2csv", "--no-inference", "--sheet", sheet, file],
                stdout=out,
            )


def main() -> None:
    csv_from_excel(Path("Vysledky_Bloudeni_2023.xlsx"), sheets)

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
                            row["SIID"].strip(),
                        )
                        for row in readouts
                    },
                    times_file,
                )


if __name__ == "__main__":
    main()
