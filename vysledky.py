import csv
import itertools
import json
import operator
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from functools import reduce
from itertools import chain
from math import ceil
from pathlib import Path
from typing import Union
from utils import optionals, parse_time, parse_timedelta
from xml.etree import ElementTree as ET


@dataclass
class ResultTeam:
    id: str
    team: str
    gender: str
    age: str
    si: SportIdent
    members: list[str]
    time: timedelta
    penalty_min: int
    penalty: int
    punches_points: int
    total: int
    punches: list[str]
    ignore: bool


def add_cells(tr: ET.Element, vals: list):
    for val in list(vals):
        td = ET.Element("td")
        tr.append(td)
        if isinstance(val, list):
            head, tail = val[0], val[1:]
            td.text = head
            for item in tail:
                br = ET.Element("br")
                br.tail = item
                td.append(br)
        else:
            td.text = str(val)


dst = Path("out")
src = Path("data")

with open("event.json") as event_file:
    event = json.load(event_file)
    event["stages"] = OrderedDict(event["stages"])

genders = ["X", "M", "W"]
ages = ["J", "O", "V"]

headers = [
    "Rank",
    "Rank",
    "ID",
    "Team",
    "Category",
    "SI Card",
    "Members",
    "Time",
    "Penalty minutes",
    "Penalty points",
    "Found points",
    "Total points",
]

event_teams = {}


def print_stage(stage_name, event, stage, punches, times):
    html = ET.Element("html")
    head = ET.Element("head")
    html.append(head)
    style = ET.Element("link", attrib={"rel": "stylesheet", "href": "style.css"})
    head.append(style)
    meta = ET.Element("meta", attrib={"charset": "utf-8"})
    head.append(meta)
    title = ET.Element("title")
    title.text = event["name"] + " – " + stage["name"]
    head.append(title)
    body = ET.Element("body")
    html.append(body)
    h1 = ET.Element("h1")
    h1.text = event["name"] + " – " + stage["name"]
    body.append(h1)
    table = ET.Element("table")
    body.append(table)
    thead = ET.Element("thead")
    table.append(thead)
    tr = ET.Element("tr")
    thead.append(tr)

    cps = list("{}\n{}".format(k, stage["cps"][k]) for k in stage["cps"])

    for header in headers + cps:
        th = ET.Element("th")
        tr.append(th)
        th.text = header

    tbody = ET.Element("tbody")
    table.append(tbody)

    result_data: list[ResultTeam] = []
    for team_id in punches.keys():
        if team_id == "0":
            continue

        team = event_teams[team_id]

        stage_start = parse_time(stage["start"])
        stage_duration = parse_timedelta(stage["duration"])
        arrival = parse_time(times.get(team["si"], "00:00:00"), strip_milliseconds=True)
        has_time = team["si"] in times
        time = arrival - stage_start
        time_pre = time
        if has_time and time < timedelta(seconds=0):
            time = time + timedelta(hours=24)
        penalty_min = ceil(max((time - stage_duration) / timedelta(minutes=1), 0))
        penalty = penalty_min * stage["penalty"]
        punches_points = list(
            map(
                lambda cp: (
                    int(int(cp) in punches.get(str(team_id), [])) * stage["cps"][cp]
                ),
                stage["cps"].keys(),
            )
        )
        total_points = (
            0
            if penalty_min > (stage.get("maxOvertime", event["maxOvertime"]))
            else max(sum(punches_points) - penalty, 0)
        )

        result_data.append(
            ResultTeam(
                id=team_id,
                team=team["team"],
                gender=team["gender"],
                age=team["age"],
                si=team["si"],
                members=[
                    team["member1lst"] + " " + team["member1fst"],
                    *optionals(
                        "member2lst" in team,
                        [
                            team["member2lst"] + " " + team["member2fst"],
                        ],
                    ),
                ],
                time=time if has_time else timedelta(seconds=0),
                penalty_min=penalty_min,
                penalty=penalty,
                punches_points=sum(punches_points),
                total=total_points,
                punches=list(map(str, punches_points)),
                ignore=team.get("ignore", False),
            )
        )

    result_data = [team for team in result_data if not event_teams[team.id]["skip"]]
    result_data = sorted(result_data, key=sort_order_teams)

    positions = pos()
    for result_team in result_data:
        tr = ET.Element("tr", attrib={"class": "gender-" + result_team.gender})
        tbody.append(tr)
        vals = [
            *positions.get(result_team),
            result_team.id,
            result_team.team,
            result_team.gender + result_team.age,
            result_team.si,
            result_team.members,
            (
                "00:00:00"
                if result_team.time == timedelta(seconds=0)
                else result_team.time
            ),
            result_team.penalty_min,
            result_team.penalty,
            result_team.punches_points,
            result_team.total,
            *result_team.punches,
        ]

        add_cells(tr, vals)

        event_teams[result_team.id]["stages"][stage_name] = {
            "time": result_team.time,
            "total": result_team.total,
        }

    tree = ET.ElementTree(html)
    ET.indent(tree)
    tree.write(dst / f"Vysledky_{stage_name}.html", encoding="utf8", method="html")


headers_tot = [
    "Rank",
    "Rank",
    "ID",
    "Team",
    "Category",
    "Members",
]


def print_total():
    html = ET.Element("html")
    head = ET.Element("head")
    html.append(head)
    style = ET.Element("link", attrib={"rel": "stylesheet", "href": "style.css"})
    head.append(style)
    meta = ET.Element("meta", attrib={"charset": "utf-8"})
    head.append(meta)
    title = ET.Element("title")
    title.text = "Výsledky STB 2023"
    head.append(title)
    body = ET.Element("body")
    html.append(body)
    h1 = ET.Element("h1")
    h1.text = "Výsledky STB 2023"
    body.append(h1)
    table = ET.Element("table", attrib={"class": "foo"})
    body.append(table)
    thead = ET.Element("thead")
    table.append(thead)
    tr = ET.Element("tr")
    thead.append(tr)

    for header in headers_tot:
        th = ET.Element("th", attrib={"rowspan": "2"})
        tr.append(th)
        th.text = header

    short_stages = [event["stages"][stage]["short"] for stage in event["stages"]]
    for header in short_stages + ["Total"]:
        th = ET.Element("th", attrib={"colspan": "2"})
        tr.append(th)
        th.text = header

    tr2 = ET.Element("tr")
    thead.append(tr2)
    for header in ["Points", "Time"] * (len(event["stages"]) + 1):
        th = ET.Element("th")
        tr2.append(th)
        th.text = header

    tbody = ET.Element("tbody")
    table.append(tbody)

    positions = pos()
    for team in event_teams:
        event_teams[team]["stages"]["total"] = {
            "time": reduce(
                operator.add,
                map(lambda stage: stage["time"], event_teams[team]["stages"].values()),
                timedelta(),
            ),
            "total": sum(
                map(lambda stage: stage["total"], event_teams[team]["stages"].values())
            ),
        }
    teams = sorted(
        event_teams.values(),
        key=lambda row: (
            row["gender"],
            -int(row["stages"]["total"]["total"]),
            row["stages"]["total"]["time"],
        ),
    )

    teams = filter(lambda row: not event_teams[row["id"]]["skip"], teams)

    for row in teams:
        tr = ET.Element("tr", attrib={"class": "gender-" + row["gender"]})
        tbody.append(tr)
        vals = [
            *positions.get(row),
            row["id"],
            row["team"],
            row["gender"] + row["age"],
            [
                row["member1lst"] + " " + row["member1fst"],
                *optionals(
                    "member2lst" in row,
                    [
                        row["member2lst"] + " " + row["member2fst"],
                    ],
                ),
            ],
            *itertools.chain.from_iterable(
                [
                    [
                        row["stages"].get(stage, {"total": ""})["total"],
                        row["stages"].get(stage, {"time": ""})["time"],
                    ]
                    for stage in list(event["stages"].keys()) + ["total"]
                ]
            ),
        ]
        add_cells(tr, vals)

    tree = ET.ElementTree(html)
    ET.indent(tree)
    tree.write(dst / "total.html", encoding="utf8", method="html")


class pos:
    def __init__(self):
        self.positions = {
            (gender + age): 0 for (gender, age) in itertools.product(genders, ages)
        }

    def get(self, team: Union[ResultTeam, dict]) -> tuple[int, int]:
        prank = ""
        srank = ""
        if type(team) == ResultTeam:
            team_id, age, gender = team.id, team.age, team.gender
        elif type(team) == dict:
            team_id, age, gender = team["id"], team["age"], team["gender"]

        if team_id != "0" and not event_teams[team_id]["ignore"]:
            primary = gender + "O"
            secondary = gender + age
            self.positions[primary] += 1
            prank = primary + str(self.positions[primary])

            if secondary != primary:
                self.positions[secondary] += 1
                srank = secondary + str(self.positions[secondary])

        return (prank, srank)


def write_style():
    style = """
    table {
        border-collapse: collapse;
        border: 3px solid black;
    }

    thead {
        border: 3px solid black;
    }

    td, th {
        border: 1px solid black;
        padding: 0.2em;
        text-align: left;
    }

    tbody tr:nth-child(odd) {
        background: #ddd;
    }

    tbody tr:hover {
        background: #ffc100;
    }

    tr.gender-m + tr.gender-w, tr.gender-w + tr.gender-x {
        border-top: 3px solid black;
    }
    body {
        font-family: sans-serif;
    }
    """

    with open(dst / "style.css", "w") as style_file:
        style_file.write(style)


def sort_order_teams(result_team: ResultTeam) -> tuple[str, int, timedelta, int]:
    """Generate a value, whose comparisons will determine the order of teams in stage results."""

    return (
        # Results are clustered into gender categories.
        result_team.gender,
        # Within them, the highest number of points wins.
        -result_team.total,
        # When there is a tie, shortest time goes first.
        # People not running would have time=0 but we are already putting to the bottom
        # because they also have total=0.
        result_team.time,
        # People running out of competition will be listed in the place
        # they would be if they competed but below of those who competed in case of a tie.
        # They will just not be assigned ranking by `pos` class.
        int(event_teams.get(result_team.id, {"ignore": True})["ignore"]),
    )


def main():
    with open(src / "entries.csv") as entries_file:
        reader = csv.DictReader(entries_file)
        for row in reader:
            if row["category"]:
                event_teams[row["#"]] = {
                    "ignore": row.get("ignore", None) == "ms",
                    "skip": row.get("ignore", None) == "del",
                    "team": row["name"],
                    "id": row["#"],
                    "si": row["sportident"],
                    "stages": {},
                    "gender": row["category"][0],
                    "age": row["category"][1],
                    "member1lst": row["m1lastname"],
                    "member1fst": row["m1firstname"],
                    "member2lst": row["m2lastname"],
                    "member2fst": row["m2firstname"],
                }

    for stage_name, stage in event["stages"].items():
        punches_cm = open(src / f"punches-{stage_name}.json")
        times_cm = open(src / f"times-{stage_name}.json")
        with punches_cm as punches_file, times_cm as times_file:
            punches = json.load(punches_file)
            times = json.load(times_file)
            print_stage(stage_name, event, event["stages"][stage_name], punches, times)
    print_total()

    write_style()


if __name__ == "__main__":
    main()
