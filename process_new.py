import sys
import jjb
import logging
from logging.handlers import RotatingFileHandler
import argparse
import yaml
from ejudge_client import EjudgeClient
import handlers
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from subprocess import Popen, PIPE
from collections import namedtuple

Alert = namedtuple("Alert", "original_run checker similarity")

def format_similarity(x):
	return "%0.2f" % x if x else "None"

def format_floats(floats):
	return ", ".join(map(format_similarity, floats))

def create_attachment(prefix, run):
	name = "%s_%d_%s" % (prefix, run.id, run.user_login)
	attachment = MIMEApplication(run.source, Name=name)
	attachment['Content-Disposition'] = 'attachment; filename="%s"' % name
	return attachment

def sendmail(new_run, alerts_by_run, mail):
	text = "%s\n" % str(new_run)
	for (_, alerts) in alerts_by_run.items():
		text += "\nProbably a copy of\n%s\nSimilarities:\n" % (str(alerts[0].original_run))
		text += "\n".join(map(lambda x: "%s\t%s" % (x.checker, format_similarity(x.similarity)), alerts))
		text += '\n'
	
	top_alert = next(iter(alerts_by_run.values()))[0]
	for (_, alerts) in alerts_by_run.items():
		for alert in alerts:
			if not(alert.similarity is None) and ((top_alert.similarity is None) or (alert.similarity > top_alert.similarity)):
				top_alert = alert
	
	message = MIMEMultipart()
	message["To"] = mail
	message["Subject"] = "[%d] Suspicious run: %d, %s, %s, %s. %s: %s" % (new_run.contest_id, new_run.id, new_run.problem, new_run.lang, new_run.user_login, top_alert.checker, format_similarity(top_alert.similarity))
	
	message.attach(MIMEText(text))
	message.attach(create_attachment("suspisious_run", new_run))
	for (old_run_id, alerts) in alerts_by_run.items():
		message.attach(create_attachment("original_%d" % old_run_id, alerts[0].original_run))
	
	p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
	p.communicate(message.as_bytes())

def log_alerts(old_run, new_run, alerts):
	names = list(map(lambda x: x.checker, alerts))
	similarities = list(map(lambda x: x.similarity, alerts))
	logging.info("%s is a copy of %s, according to %s. Similarities: (%s)", str(new_run), str(old_run), ", ".join(names), format_floats(similarities))

def get_similar_runs_filter(run):
	return '(status == OK or status == PR or status == DQ) and login !="%s" and prob == "%s"' % (run.user_login, run.problem)

def compare_runs(old_run, new_run, checkers):
	logging.info("Comparing runs %s and %s", old_run, new_run)
	all_results = []
	alerts = []
	for checker in checkers:
		handler = handlers.get(checker['type'])
		similarity = handler(checker, old_run, new_run)
		if ((similarity is not None) and (similarity > checker['threshold'])) or ((similarity is None) and checker.get('alert_if_none', True)):
			alerts.append(Alert(old_run, checker['name'], similarity))			
		all_results.append(similarity)
	logging.info("Similarity between %d and %d is (%s)", old_run.id, new_run.id, format_floats(all_results))
	if len(alerts) > 0:
		log_alerts(old_run, new_run, alerts)
	return alerts

def check_run(client, run, checkers, alert_mail):
	runs_filter = get_similar_runs_filter(run)
	previous_runs = client.get_runs(0, run.id - 1, runs_filter)
	if not len(previous_runs):
		logging.info("Skipping check of run %d - no similar runs found.", run.id)
		return
	run.source = client.get_run_source(run.id)
	all_alerts = dict()
	for old_run in previous_runs:
		old_run.source = client.get_run_source(old_run.id)
		alerts = compare_runs(old_run, run, checkers)
		if len(alerts) > 0:
			all_alerts[old_run.id] = alerts
	if (len(all_alerts) > 0) and not (alert_mail is None):
		sendmail(run, all_alerts, alert_mail)	

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
		config = yaml.load(cf, Loader=yaml.FullLoader)
		
	log_file = config['logging']['file'] % args.contest_id
	log_max_bytes = config['logging'].get('max_bytes', 10*1024*1024)
	log_backups = config['logging'].get('backups', 10)
	
	logging.basicConfig(
		format='%(asctime)s %(levelname)5s: %(message)s', 
		datefmt='%Y-%m-%d %H:%M:%S', 
		level=getattr(logging, args.log_level.upper()),
		handlers = [
			logging.StreamHandler(stream=sys.stdout),
			RotatingFileHandler(log_file, maxBytes=log_max_bytes, backupCount=log_backups)
		]
	)
	
	checkers = config['checkers']
	last_run_file = config['last_run_file'] % args.contest_id
	alert_mail = config.get('alert_mail')

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
		check_run(client, run, checkers, alert_mail)

	if len(runs):
		max_run = max(runs, key=lambda x: x.id).id
		with open(last_run_file, "w") as f:
			f.write(str(max_run))
	else:
		max_run = last_run		
	logging.info("Checked %d runs. Latest run: %d", len(runs), max_run)
	client.logout()
