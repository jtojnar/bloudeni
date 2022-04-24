import csv
import itertools
import json
import operator
import sys
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from functools import reduce
from math import ceil
from utils import parse_time, parse_timedelta
from xml.etree import ElementTree as ET


def optionals(condition: bool, value: list) -> list:
    if condition:
        return value
    else:
        return []


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


dst = "out/"
src = "data/"

with open("event.json") as event_file:
    event = json.load(event_file)

stages = OrderedDict(event["stages"])

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

    result_data = []
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
            OrderedDict(
                [
                    ("id", team_id),
                    ("team", team["team"]),
                    ("gender", team["gender"]),
                    ("age", team["age"]),
                    ("si", team["si"]),
                    (
                        "members",
                        [
                            team["member1lst"] + " " + team["member1fst"],
                        ]
                        + optionals(
                            "member2lst" in team,
                            [
                                team["member2lst"] + " " + team["member2fst"],
                            ],
                        ),
                    ),
                    ("time", time if has_time else timedelta(seconds=0)),
                    ("penalty_min", penalty_min),
                    ("penalty", penalty),
                    ("punches_points", sum(punches_points)),
                    ("total", total_points),
                    ("punches", list(map(str, punches_points))),
                    ("ignore", team.get("ignore", False)),
                ]
            )
        )

    result_data = filter(lambda row: not event_teams[row["id"]]["skip"], result_data)
    result_data = sorted(result_data, key=sort_order_teams)

    positions = pos()
    for result_row in result_data:
        tr = ET.Element("tr", attrib={"class": "gender-" + result_row["gender"]})
        tbody.append(tr)
        vals = (
            list(positions.get(result_row))
            + [
                result_row["id"],
                result_row["team"],
                result_row["gender"] + result_row["age"],
                result_row["si"],
                result_row["members"],
                (
                    "00:00:00"
                    if result_row["time"] == timedelta(seconds=0)
                    else result_row["time"]
                ),
                result_row["penalty_min"],
                result_row["penalty"],
                result_row["punches_points"],
                result_row["total"],
            ]
            + result_row["punches"]
        )

        add_cells(tr, vals)

        event_teams[result_row["id"]]["stages"][stage_name] = {
            "time": result_row["time"],
            "total": result_row["total"],
        }

    ET.ElementTree(html).write(
        dst + "Vysledky_" + stage_name + ".html", encoding="utf8", method="html"
    )


headers_tot = [
    "Rank",
    "Rank",
    "ID",
    "Team",
    "Category",
    "Members",
]

flatten = lambda l: reduce(operator.iconcat, l, [])


def print_total():
    html = ET.Element("html")
    head = ET.Element("head")
    html.append(head)
    style = ET.Element("link", attrib={"rel": "stylesheet", "href": "style.css"})
    head.append(style)
    meta = ET.Element("meta", attrib={"charset": "utf-8"})
    head.append(meta)
    title = ET.Element("title")
    title.text = "Výsledky STB 2022"
    head.append(title)
    body = ET.Element("body")
    html.append(body)
    h1 = ET.Element("h1")
    h1.text = "Výsledky STB 2022"
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

    for header in [stages[stage]["short"] for stage in stages] + ["Total"]:
        th = ET.Element("th", attrib={"colspan": "2"})
        tr.append(th)
        th.text = header

    tr2 = ET.Element("tr")
    thead.append(tr2)
    for header in ["Points", "Time"] * (len(stages) + 1):
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
        table.append(tr)
        vals = (
            list(positions.get(row))
            + [
                row["id"],
                row["team"],
                row["gender"] + row["age"],
                (
                    [
                        row["member1lst"] + " " + row["member1fst"],
                    ]
                    + optionals(
                        "member2lst" in row,
                        [
                            row["member2lst"] + " " + row["member2fst"],
                        ],
                    )
                ),
            ]
            + flatten(
                [
                    [
                        row["stages"].get(stage, {"total": ""})["total"],
                        row["stages"].get(stage, {"time": ""})["time"],
                    ]
                    for stage in list(stages.keys()) + ["total"]
                ]
            )
        )
        add_cells(tr, vals)

    ET.ElementTree(html).write(dst + "total.html", encoding="utf8", method="html")


class pos:
    def __init__(self):
        self.positions = {
            (gender + age): 0 for (gender, age) in itertools.product(genders, ages)
        }

    def get(self, row):
        prank = ""
        srank = ""

        if row["id"] != "0" and not event_teams[row["id"]]["ignore"]:
            primary = row["gender"] + "O"
            secondary = row["gender"] + row["age"]
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
        background: #eee;
    }

    tr.gender-m + tr.gender-w, tr.gender-w + tr.gender-x {
        border-top: 3px solid black;
    }
    body {
        font-family: sans-serif;
    }
    """

    with open(dst + "style.css", "w") as style_file:
        style_file.write(style)


def sort_order_teams(row):
    """Generate a value, whose comparisons will determine the order of teams in stage results."""

    return (
        # Results are clustered into gender categories.
        row["gender"],
        # Within them, the highest number of points wins.
        -int(row["total"]),
        # When there is a tie, shortest time goes first.
        # People not running would have time=0 but we are already putting to the bottom
        # because they also have total=0.
        row["time"],
        # People running out of competition will be listed in the place
        # they would be if they competed but below of those who competed in case of a tie.
        # They will just not be assigned ranking by `pos` class.
        int(event_teams.get(row["id"], {"ignore": True})["ignore"]),
    )


def main():
    with open(src + "entries.csv") as entries_file:
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

    for stage_name, stage in stages.items():
        punches_cm = open(src + "punches-" + stage_name + ".json")
        times_cm = open(src + "times-" + stage_name + ".json")
        with punches_cm as punches_file, times_cm as times_file:
            punches = json.load(punches_file)
            times = json.load(times_file)
            print_stage(stage_name, event, event["stages"][stage_name], punches, times)
    print_total()

    write_style()


if __name__ == "__main__":
    main()
