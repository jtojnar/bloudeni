import csv
import json
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from utils import format_time, parse_time

def correct_time(finish_string, start_string, si):
	'''
	Adjusts time of SI 5 card, which only supports 12-hour format.
	'''
	finish = parse_time(finish_string, strip_milliseconds=True)
	start = parse_time(start_string)

	if start.hour >= 12 and start > finish and is_sportident_5(si):
		finish += timedelta(hours=12)

	return format_time(finish)

def is_sportident_5(si):
	return 1 <= int(si) <= 499999

def main():
	src = 'data/'

	with open('event.json') as event_file:
		event = json.load(event_file)

	stages = OrderedDict(event['stages'])

	for stage_name, stage in stages.items():
		readouts_path = src + 'readouts-' + stage_name + '.csv'
		if Path(readouts_path).exists():
			with open(readouts_path, errors='ignore') as readouts_file, \
				open(src + 'times-' + stage_name + '.json', 'w') as times_file:
				readouts = csv.DictReader(readouts_file, delimiter=';')

				punches = json.dump({
					row['SIID'].strip(): correct_time(row['Finish time'].strip(), stage['start'], row['SIID'].strip())
					for row in readouts
				}, times_file)

if __name__ == '__main__':
	main()
