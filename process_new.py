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

def format_floats(floats):
	return ", ".join(map(lambda x: "%0.2f" % x if x else "None", floats))

def create_attachment(prefix, run, run_source):
	name = "%s_%d_%s" % (prefix, run.id, run.user_login)
	attachment = MIMEApplication(run_source, Name=name)
	attachment['Content-Disposition'] = 'attachment; filename="%s"' % name
	return attachment

def sendmail(old_run, old_run_source, new_run, new_run_source, alerts, mail, contest_id):
	text = "%s\nis probably a copy of\n%s\nSimilarities:\n" % (str(new_run), str(old_run))
	text += "\n".join(map(lambda x: "%s\t%0.2f" % x if x[1] is not None else "%s\t%s" % x, alerts))
	
	message = MIMEMultipart()
	message["To"] = mail
	message["Subject"] = "[%d] Suspicious run: %d, %s, %s, %s" % (contest_id, run.id, run.problem, run.lang, run.user_login)
	
	message.attach(MIMEText(text))
	message.attach(create_attachment("original", old_run, old_run_source))
	message.attach(create_attachment("copy", new_run, new_run_source))
	
	p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
	p.communicate(message.as_bytes())

def alert(old_run, old_run_source, new_run, new_run_source, alerts, alert_mail, contest_id):
	(names, similarities) = zip(*alerts)
	logging.info("%s is a copy of %s, according to %s. Similarities: (%s)", str(new_run), str(old_run), ", ".join(names), format_floats(similarities))
	if alert_mail is not None:
		sendmail(old_run, old_run_source, new_run, new_run_source, alerts, alert_mail, contest_id)

def get_similar_runs_filter(run):
	return '(status == OK or status == DQ) and login !="%s" and prob == "%s"' % (run.user_login, run.problem)

def compare_runs(old_run, old_run_source, new_run, new_run_source, checkers, alert_mail, contest_id):
	logging.info("Comparing runs %s and %s", old_run, new_run)
	all_results = []
	alerts = []
	for checker in checkers:
		handler = handlers.get(checker['type'])
		similarity = handler(checker, old_run_source, new_run_source, new_run.lang)
		if ((similarity is not None) and (similarity > checker['threshold'])) or ((similarity is None) and checker.get('alert_if_none', True)):
			alerts.append((checker['name'], similarity))
		all_results.append(similarity)
	if len(alerts):
		alert(old_run, old_run_source, new_run, new_run_source, alerts, alert_mail, contest_id)
	logging.info("Similarity between %d and %d is (%s)", old_run.id, new_run.id, format_floats(all_results))

def check_run(client, run, checkers, alert_mail):
	runs_filter = get_similar_runs_filter(run)
	previous_runs = client.get_runs(0, run.id - 1, runs_filter)
	if not len(previous_runs):
		logging.info("Skipping check of run %d - no similar runs found.", run.id)
		return
	run_source = client.get_run_source(run.id)
	for old_run in previous_runs:
		old_run_source = client.get_run_source(old_run.id)
		compare_runs(old_run, old_run_source, run, run_source, checkers, alert_mail, client.contest_id)


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
