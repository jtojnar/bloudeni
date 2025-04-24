#!/usr/bin/env python3

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
from typing import Optional, Sequence, TypedDict, Union
from utils import format_time, optionals, parse_time, parse_timedelta
from xml.etree import ElementTree as ET

TeamId = str
SportIdent = str


class TeamStageResult(TypedDict):
    time: timedelta
    total: int


class Team(TypedDict):
    ignore: bool
    skip: bool
    team: str
    id: TeamId
    si: SportIdent
    stages: dict[str, TeamStageResult]
    gender: str
    age: str
    member1lst: str
    member1fst: str
    member2lst: str
    member2fst: str
    friday2h: bool
    saturday5h: bool
    sunday4h: bool


class Stage(TypedDict):
    name: str
    short: str
    start: str
    csv_column: str
    duration: str
    penalty: int
    cps: dict[str, int]
    maxOvertime: int  # NotRequired[int]


class Event(TypedDict):
    name: str
    maxOvertime: int
    stages: OrderedDict[str, Stage]


Punches = dict[TeamId, list[int]]


ArrivalTimes = dict[SportIdent, str]


@dataclass
class ResultTeam:
    id: str
    team: str
    gender: str
    age: str
    si: SportIdent
    members: list[str]
    stages: set[str]
    time: timedelta
    penalty_min: int
    penalty: int
    punches_points: int
    total: int
    punches: list[str]
    ignore: bool


def add_cells(
    tr: ET.Element,
    vals: Sequence[
        Union[
            list[str],
            str,
            int,
            timedelta,
            tuple[Union[str, int, timedelta], bool],
        ]
    ],
) -> None:
    for val in vals:
        attrib = {}
        match val:
            case tuple((val, bool(dim))):
                if dim:
                    attrib["class"] = "not-participating"

        td = ET.Element("td", attrib=attrib)
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

SCROLLER_SCRIPT = """
function pageScroll(jumpToTop) {
    let wait = false;

    if (jumpToTop) {
        window.scrollTo(0, 0);
    } else {
        window.scrollBy(0, 1);

        wait = Math.abs((window.innerHeight + window.scrollY) - document.documentElement.offsetHeight) < 1;
    }

    if (wait) {
        setTimeout(() => pageScroll(true), 5000);
    } else {
        setTimeout(() => pageScroll(false), 30);
    }
}
if (document.location.search === '?scroll') {
    pageScroll(false);
}
"""

event_teams: dict[TeamId, Team] = {}


def print_stage(
    stage_name: str,
    event: Event,
    stage: Stage,
    punches: Punches,
    times: ArrivalTimes,
) -> None:
    html = ET.Element("html")
    head = ET.Element("head")
    html.append(head)
    style = ET.Element("link", attrib={"rel": "stylesheet", "href": "style.css"})
    head.append(style)
    meta = ET.Element("meta", attrib={"charset": "utf-8"})
    head.append(meta)
    meta = ET.Element("meta", attrib={"http-equiv": "refresh", "content": "60"})
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

    scroller = ET.Element("script")
    scroller.text = SCROLLER_SCRIPT
    body.append(scroller)

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

        stages = set(
            [
                *optionals(team["friday2h"], ["N2H"]),
                *optionals(team["saturday5h"], ["D5H"]),
                *optionals(team["sunday4h"], ["H4H"]),
            ]
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
                stages=stages,
                time=(
                    time if has_time and stage_name in stages else timedelta(seconds=0)
                ),
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
        not_participating = (
            " not-participating"
            if not event_teams[result_team.id].get(stage["csv_column"])
            else ""
        )
        tr = ET.Element(
            "tr",
            attrib={"class": "gender-" + result_team.gender + not_participating},
        )
        tbody.append(tr)
        vals: list[Union[list[str], str, int, timedelta]] = [
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
    with open(dst / f"Vysledky_{stage_name}.html", "w") as file:
        file.write("<!doctype html>\n")
        tree.write(file, encoding="unicode", method="html")

    with open(dst / f"pm_{stage_name}.csv", "w", newline="") as csvfile:
        cps = list(stage["cps"].keys())
        fieldnames = [
            "Start Time",
            "Team",
            "Category",
            "Member1",
            "Member2",
            "Time",
            "Total points",
        ] + cps

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for result_team in result_data:
            members = result_team.members
            if result_team.time != timedelta(seconds=0):
                row = {
                    "Start Time": stage["start"],
                    "Team": result_team.team,
                    "Category": result_team.gender + result_team.age,
                    "Member1": members[0],
                    "Member2": members[1] if len(members) >= 2 else "",
                    "Time": result_team.time,
                    "Total points": result_team.total,
                } | {
                    cp: points if points != "0" else ""
                    for cp, points in zip(cps, result_team.punches)
                }
                writer.writerow(row)


headers_tot = [
    "Rank",
    "Rank",
    "ID",
    "Team",
    "Category",
    "Members",
]


def dim(
    text: Union[str, int, timedelta],
    dim: bool,
) -> tuple[Union[str, int, timedelta], bool]:
    return (text, dim)


def print_total() -> None:
    html = ET.Element("html")
    head = ET.Element("head")
    html.append(head)
    style = ET.Element("link", attrib={"rel": "stylesheet", "href": "style.css"})
    head.append(style)
    meta = ET.Element("meta", attrib={"charset": "utf-8"})
    head.append(meta)
    meta = ET.Element("meta", attrib={"http-equiv": "refresh", "content": "60"})
    head.append(meta)
    title = ET.Element("title")
    title.text = "Výsledky STB 2025"
    head.append(title)
    body = ET.Element("body")
    html.append(body)
    h1 = ET.Element("h1")
    h1.text = "Výsledky STB 2025"
    body.append(h1)
    table = ET.Element("table", attrib={"class": "foo"})
    body.append(table)

    scroller = ET.Element("script")
    scroller.text = SCROLLER_SCRIPT
    body.append(scroller)

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

    teams = [row for row in teams if not event_teams[row["id"]]["skip"]]

    for row in teams:
        tr = ET.Element("tr", attrib={"class": "gender-" + row["gender"]})
        tbody.append(tr)
        vals: list[
            Union[
                list[str],
                str,
                int,
                timedelta,
                tuple[Union[str, int, timedelta], bool],
            ]
        ] = [
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
                        dim(
                            row["stages"].get(stage, {"total": ""})["total"],
                            not_participating := (
                                stage != "total"
                                and not row.get(event["stages"][stage]["csv_column"])
                            ),
                        ),
                        dim(
                            row["stages"].get(stage, {"time": ""})["time"],
                            not_participating,
                        ),
                    ]
                    for stage in list(event["stages"].keys()) + ["total"]
                ]
            ),
        ]
        add_cells(tr, vals)

    tree = ET.ElementTree(html)
    ET.indent(tree)
    with open(dst / "total.html", "w") as file:
        file.write("<!doctype html>\n")
        tree.write(file, encoding="unicode", method="html")


class pos:
    def __init__(self) -> None:
        self.positions = {
            (gender + age): 0 for (gender, age) in itertools.product(genders, ages)
        }

    def get(self, team: Union[ResultTeam, Team]) -> tuple[str, str]:
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


def write_style() -> None:
    style = """
    html, body {
        background: white;
        color: black;
    }

    table {
        border-collapse: collapse;
        border: 3px solid black;
    }

    thead {
        border: 3px solid black;
        position: sticky;
        top: 0;
        background: white;
    }

    td, th {
        border: 1px solid black;
        padding: 0.2em;
        text-align: left;
    }

    .not-participating {
        color: #555;
    }

    tbody tr:nth-child(odd) {
        background: #ddd;
    }

    tbody tr:hover {
        background: #ffc100;
    }

    tr.gender-M + tr.gender-W, tr.gender-W + tr.gender-X {
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


def main() -> None:
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
                    "friday2h": row["friday2h"] == "yes",
                    "saturday5h": row["saturday5h"] == "yes",
                    "sunday4h": row["sunday4h"] == "yes",
                }

    dst.mkdir(parents=True, exist_ok=True)

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
