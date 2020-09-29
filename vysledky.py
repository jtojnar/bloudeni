import csv
import itertools
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

stages = OrderedDict([
	('Vysledky_N2H', {
		'name': '6. STB 2020 – výsledková listina páteční noční dvouhodinovky',
		'short': 'Stage 1 – Friday night 2hrs',
		'start': '21:00:00',
		'penalty': 10,
		'cps': {1: 50, 2: 90, 3: 60, 4: 70, 5: 40, 6: 60, 7: 50, 8: 50, 9: 30, 10: 40, 11: 40, 12: 60, 13: 30, 14: 40, 15: 90},
	}),
	('Vysledky_D5H', {
		'name': '6. STB 2020 – výsledková listina sobotní pětihodinovky',
		'short': 'Stage 2 – Saturday 5hrs',
		'start': '10:30:00',
		'penalty': 20,
		'cps': {1: 90, 2: 90, 3: 30, 4: 50, 5: 60, 6: 50, 7: 30, 8: 90, 9: 50, 10: 30, 11: 50, 12: 80, 13: 50, 14: 70, 15: 40, 16: 50, 17: 50, 18: 40, 19: 50, 20: 90, 21: 40, 22: 40, 23: 80, 24: 90, 25: 70, 26: 70},
	}),
	('Vysledky_H4H', {
		'name': '6. STB 2020 – výsledková listina nedělní čtyřhodinovky',
		'short': 'Stage 3 – Sunday 4hrs',
		'start': '09:00:00',
		'penalty': 20,
		'cps': {1: 90, 2: 90, 3: 40, 4: 40, 5: 30, 6: 50, 7: 80, 8: 70, 9: 90},
	})
])

sheets = {
	'CSV Import': 'entries',
	'PRINT E1': 'Vysledky_N2H',
	'PRINT E2': 'Vysledky_D5H',
	'PRINT E3': 'Vysledky_H4H',
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

def print_stage(stage_name, stage, teams):
	html = ET.Element('html')
	head = ET.Element('head')
	html.append(head)
	style = ET.Element('link', attrib={'rel': 'stylesheet', 'href': 'style.css'})
	head.append(style)
	meta = ET.Element('meta', attrib={'charset': 'utf-8'})
	head.append(meta)
	title = ET.Element('title')
	title.text = stage['name']
	head.append(title)
	body = ET.Element('body')
	html.append(body)
	h1 = ET.Element('h1')
	h1.text = stage['name']
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
		vals = list(positions.get(row)) + [row['id'], row['team'], row['gender'] + row['age'], row['si'], row['member1lst'] + ' ' + row['member1fst'], row['member2lst'] + ' ' + row['member2fst'], row['time'], row['penaltymin'], row['penaltypts'], row['pts'], row['total']] + list(map(lambda cp: row[str(cp)], stage['cps'].keys()))
		for val in vals:
			td = ET.Element('td')
			tr.append(td)
			td.text = val

		event_teams[row['id']]['stages'][stage_name] = {
			'time': delta,
			'total': int(row['total']),
		}

	ET.ElementTree(html).write(dst + stage_name + '.html', encoding='utf8', method='html')


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
	title.text = 'Výsledky STB 2020'
	head.append(title)
	body = ET.Element('body')
	html.append(body)
	h1 = ET.Element('h1')
	h1.text = 'Výsledky STB 2020'
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
		with open(src + target + '.csv','wb') as out:
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
	csv_from_excel('Vysledky_Bloudeni_2020.xlsx', sheets)

	with open(src + 'entries.csv') as entries_file:
		reader = csv.DictReader(entries_file)
		for row in reader:
			if row['category']:
				event_teams[row['#']] = {
					'ignore': row['ignore'] == 'ms',
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
		with open(src + stage_name + '.csv') as stage_file:
			teams = csv.DictReader(stage_file)
			teams = map(clean_overtimes, teams)
			teams = sorted(teams, key=sort_order_teams)
			print_stage(stage_name, stage, teams)
	print_total()

	write_style()

if __name__ == '__main__':
	main()
