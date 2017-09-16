import sys
import jjb
import logging
from logging.handlers import RotatingFileHandler
import argparse
import yaml
from ejudge_client import EjudgeClient
import handlers

def format_floats(floats):
	return ", ".join(map(lambda x: "%0.2f" % x, floats))

def alert(old_run, new_run, alerts):
	(names, similarities) = zip(*alerts)
	logging.info("%s is a copy of %s, according to %s. Similarities: (%s)", str(new_run), str(old_run), ", ".join(names), format_floats(similarities))

def get_similar_runs_filter(run):
	return '(status == OK or status == DQ) and login !="%s" and prob == "%s"' % (run.user_login, run.problem)

def compare_runs(old_run, old_run_source, new_run, new_run_source, checkers):
	logging.debug("Comparing runs %s and %s", old_run, new_run)
	all_results = []
	alerts = []
	for checker in checkers:
		handler = handlers.get(checker['type'])
		similarity = handler(checker, old_run_source, new_run_source)
		if similarity > checker['threshold']:
			alerts.append((checker['name'], similarity))
		all_results.append(similarity)
	if len(alerts):
		alert(old_run, new_run, alerts)
	logging.info("Similarity between %d and %d is (%s)", old_run.id, new_run.id, format_floats(all_results))

def check_run(client, run, checkers):
	runs_filter = get_similar_runs_filter(run)
	previous_runs = client.get_runs(0, run.id - 1, runs_filter)
	if not len(previous_runs):
		logging.info("Skipping check of run %d - no similar runs found.", run.id)
		return
	run_source = client.get_run_source(run.id)
	for old_run in previous_runs:
		old_run_source = client.get_run_source(old_run.id)
		compare_runs(old_run, old_run_source, run, run_source, checkers)


def get_args():
	parser = argparse.ArgumentParser(description='Process new runs from ejudge')
	parser.add_argument('--config-file', '-c', metavar='FILE', type=str, default="./config.yaml", help='path to config file')
	parser.add_argument('--log-level', '-ll',  metavar='LEVEL', type=str, default="INFO", choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'], help='log level (DEBUG, INFO, WARN, ERROR or CRITICAL)')
	parser.add_argument('--contest-id', '-i',  metavar='ID', type=int, required=True)
	args = parser.parse_args()
	return args

if __name__=="__main__":
	args = get_args()

	with open(args.config_file) as cf:
		config = yaml.load(cf)
		
	log_file = config['logging']['file'] % args.contest_id
	log_max_bytes = config['logging'].get('max_bytes', 10*1024*1024)
	log_backups = config['logging'].get('backups', 10)
	
	logging.basicConfig(
		format='%(asctime)s %(levelname)5s: %(message)s', 
		datefmt='%Y-%m-%d %H:%M:%S', 
		level=getattr(logging, args.log_level.upper()),
		handlers = [
			logging.StreamHandler(),
			RotatingFileHandler(log_file, maxBytes=log_max_bytes, backupCount=log_backups)
		]
	)
	
	checkers = config['checkers']
	last_run_file = config['last_run_file'] % args.contest_id

	try:
		with open(last_run_file) as f:
			last_run = int(f.read().strip('\n'))
	except:		
		last_run = 0
		
	login = config['credentials']['login']
	password = config['credentials']['password']	
	client = EjudgeClient(args.contest_id)
	client.login(login, password)
	del login
	del password
	
	logging.info("Checking runs... Latest run: %d", last_run)
	runs = client.get_runs(last_run + 1)
	for run in runs:
		logging.info("Checking run %s", str(run))
		check_run(client, run, checkers)

	if len(runs):
		max_run = max(runs, key=lambda x: x.id).id
		with open(last_run_file, "w") as f:
			f.write(str(max_run))
	else:
		max_run = last_run		
	logging.info("Checked %d runs. Latest run: %d", len(runs), max_run)
	client.logout()
