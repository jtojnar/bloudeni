import csv
import itertools
import json
import operator
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from functools import reduce
from xml.etree import ElementTree as ET

dst = 'out/'
src = 'data/'

with open('event.json') as event_file:
	event = json.load(event_file)

stages = OrderedDict(event['stages'])

sheets = {
	'CSV Import': 'entries',
	'PRINT E1': 'N2H',
	'PRINT E2': 'D5H',
	'PRINT E3': 'H4H',
}

genders = ['X', 'M', 'W']
ages = ['J', 'O', 'V']

headers = [
	'Rank',
	'Rank',
	'ID',
	'Team',
	'Category',
	'SI Card',
	'Member1',
	'Member2',
	'Time',
	'Penalty minutes',
	'Penalty points',
	'Found points',
	'Total points',
]

event_teams = {}

NO_DURATION = timedelta(hours=0)

def parse_time(time_cell):
	try:
		t = datetime.strptime(time_cell, '%H:%M:%S')
		delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
	except:
		delta = NO_DURATION

	# delta = timedelta(seconds=float(row['time'])*60*60*24)

	return delta

def print_stage(stage_name, stage, teams, punches):
	html = ET.Element('html')
	head = ET.Element('head')
	html.append(head)
	style = ET.Element('link', attrib={'rel': 'stylesheet', 'href': 'style.css'})
	head.append(style)
	meta = ET.Element('meta', attrib={'charset': 'utf-8'})
	head.append(meta)
	title = ET.Element('title')
	title.text = event['name'] + ' – ' + stage['name']
	head.append(title)
	body = ET.Element('body')
	html.append(body)
	h1 = ET.Element('h1')
	h1.text = event['name'] + ' – ' + stage['name']
	body.append(h1)
	table = ET.Element('table')
	body.append(table)
	thead = ET.Element('thead')
	table.append(thead)
	tr = ET.Element('tr')
	thead.append(tr)

	cps = list('{}\n{}'.format(k, stage['cps'][k]) for k in stage['cps'])

	for header in headers + cps:
		th = ET.Element('th')
		tr.append(th)
		th.text = header

	tbody = ET.Element('tbody')
	table.append(tbody)

	positions = pos()
	for row in teams:
		if row['id'] == '0':
			continue

		delta = parse_time(row['time'])
		if delta == NO_DURATION:
			row['time'] = '00:00:00'

		tr = ET.Element('tr', attrib={'class': 'gender-' + row['gender']})
		tbody.append(tr)
		punches_points = list(map(lambda cp: int(int(cp) in punches.get(str(row['id']), [])) * stage['cps'][cp], stage['cps'].keys()))
		vals = list(positions.get(row)) + [row['id'], row['team'], row['gender'] + row['age'], row['si'], row['member1lst'] + ' ' + row['member1fst'], row['member2lst'] + ' ' + row['member2fst'], row['time'], row['penaltymin'], row['penaltypts'], str(sum(punches_points)), row['total']] + list(map(str, punches_points))
		for val in vals:
			td = ET.Element('td')
			tr.append(td)
			td.text = val

		event_teams[row['id']]['stages'][stage_name] = {
			'time': delta,
			'total': int(row['total']),
		}

	ET.ElementTree(html).write(dst + 'Vysledky_' + stage_name + '.html', encoding='utf8', method='html')


headers_tot = [
	'Rank',
	'Rank',
	'ID',
	'Team',
	'Category',
	'Member1',
	'Member2',
]

flatten = lambda l: reduce(operator.iconcat, l, [])

def print_total():
	html = ET.Element('html')
	head = ET.Element('head')
	html.append(head)
	style = ET.Element('link', attrib={'rel': 'stylesheet', 'href': 'style.css'})
	head.append(style)
	meta = ET.Element('meta', attrib={'charset': 'utf-8'})
	head.append(meta)
	title = ET.Element('title')
	title.text = 'Výsledky STB 2021'
	head.append(title)
	body = ET.Element('body')
	html.append(body)
	h1 = ET.Element('h1')
	h1.text = 'Výsledky STB 2021'
	body.append(h1)
	table = ET.Element('table', attrib={'class': 'foo'})
	body.append(table)
	thead = ET.Element('thead')
	table.append(thead)
	tr = ET.Element('tr')
	thead.append(tr)

	for header in headers_tot:
		th = ET.Element('th', attrib={'rowspan': '2'})
		tr.append(th)
		th.text = header

	for header in [stages[stage]['short'] for stage in stages] + ['Total']:
		th = ET.Element('th', attrib={'colspan': '2'})
		tr.append(th)
		th.text = header

	tr2 = ET.Element('tr')
	thead.append(tr2)
	for header in ['Points', 'Time'] * (len(stages) + 1):
		th = ET.Element('th')
		tr2.append(th)
		th.text = header

	tbody = ET.Element('tbody')
	table.append(tbody)

	positions = pos()
	for team in event_teams:
		event_teams[team]['stages']['total'] = {
			'time': reduce(operator.add, map(lambda stage: stage['time'], event_teams[team]['stages'].values()), timedelta()),
			'total': sum(map(lambda stage: stage['total'], event_teams[team]['stages'].values())),
		}
	teams = sorted(event_teams.values(), key=lambda row: (row['gender'], -int(row['stages']['total']['total']), row['stages']['total']['time']))

	for row in teams:
		tr = ET.Element('tr', attrib={'class': 'gender-' + row['gender']})
		table.append(tr)
		vals = list(positions.get(row)) + [row['id'], row['team'], row['gender'] + row['age'], row['member1lst'] + ' ' + row['member1fst'], row['member2lst'] + ' ' + row['member2fst']] + flatten([[row['stages'][stage]['total'], row['stages'][stage]['time']] for stage in list(stages.keys()) + ['total']])
		for val in vals:
			td = ET.Element('td')
			tr.append(td)
			td.text = str(val)

	ET.ElementTree(html).write(dst + 'total.html', encoding='utf8', method='html')

class pos:
	def __init__(self):
		self.positions = {gender + age: 0 for (gender, age) in itertools.product(genders, ages)}

	def get(self, row):
		prank = ''
		srank = ''

		if row['id'] != '0' and not event_teams[row['id']]['ignore']:
			primary = row['gender'] + 'O'
			secondary = row['gender'] + row['age']
			self.positions[primary] += 1
			prank = primary + str(self.positions[primary])

			if secondary != primary:
				self.positions[secondary] += 1
				srank = secondary + str(self.positions[secondary])

		return (prank, srank)

def csv_from_excel(file, sheets):
	for sheet, target in sheets.items():
		with open(src + 'Vysledky_' + target + '.csv','wb') as out:
			subprocess.run(['in2csv', '--no-inference', '--sheet', sheet, file], stdout=out)


def write_style():
	style = '''
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
	'''

	with open(dst + 'style.css', 'w') as style_file:
		style_file.write(style)


def clean_overtimes(row):
	if parse_time(row['time']) == NO_DURATION:
		row['pts'] = '0'
		row['total'] = '0'
	return row

def sort_order_teams(row):
	'''Generate a value, whose comparisons will determine the order of teams in stage results.'''

	return (
		# Results are clustered into gender categories.
		row['gender'],
		# Within them, the highest number of points wins.
		-int(row['total']),
		# When there is a tie, shortest time goes first.
		# People not running would have time=0 but we are already putting to the bottom
		# because they also have total=0.
		parse_time(row['time']),
		# People running out of competition will be listed in the place
		# they would be if they competed but below of those who competed in case of a tie.
		# They will just not be assigned ranking by `pos` class.
		int(event_teams.get(row['id'], {'ignore': True})['ignore']),
	)

def main():
	csv_from_excel('Vysledky_Bloudeni_2021.xlsx', sheets)

	with open(src + 'entries.csv') as entries_file:
		reader = csv.DictReader(entries_file)
		for row in reader:
			if row['category']:
				event_teams[row['#']] = {
					'ignore': row.get('ignore', None) == 'ms',
					'team': row['name'],
					'id': row['#'],
					'stages': {},
					'gender': row['category'][0],
					'age': row['category'][1],
					'member1lst': row['m1lastname'],
					'member1fst': row['m1firstname'],
					'member2lst': row['m2lastname'],
					'member2fst': row['m2firstname'],
				}

	for stage_name, stage in stages.items():
		with open(src + 'Vysledky_' + stage_name + '.csv') as stage_file, \
			open(src + 'punches-' + stage_name + '.json') as punches_file:
			teams = csv.DictReader(stage_file)
			punches = json.load(punches_file)
			teams = map(clean_overtimes, teams)
			teams = sorted(teams, key=sort_order_teams)
			print_stage(stage_name, stage, teams, punches)
	print_total()

	write_style()

if __name__ == '__main__':
	main()
