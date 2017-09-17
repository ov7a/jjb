import sys
import subprocess
from collections import namedtuple

EJUDGE_PATH="/opt/ejudge/bin/"
CONTESTS_CMD = "ejudge-contests-cmd"
SESSION_PARAM = "--session"

class Run(namedtuple("Run", "contest_id id user_id user_login problem_id problem lang status")):
	pass # to allow injecting source

def run_cmd(*args):
	#out = subprocess.run(args, stdout=subprocess.PIPE).stdout.decode('utf-8') #python3.5+
	out = subprocess.check_output(list(map(str,args))).decode('utf-8')
	return out


class EjudgeClient():
	def __init__(self, contest_id):
		self.contest_id = contest_id
		self.session = None
		
	def run_ejudge_cmd(self, command, *args):
		return run_cmd(EJUDGE_PATH+command, *args)

	def run_contests_cmd(self, command, *args):
		return self.run_ejudge_cmd(CONTESTS_CMD, self.contest_id, command, SESSION_PARAM, self.session, *args)

	def login(self, login, password):
		self.session = self.run_ejudge_cmd(CONTESTS_CMD, self.contest_id, "judge-login", "STDOUT", login, password).strip('\n')	
		del login
		del password

	def logout(self):
		response = self.run_contests_cmd("logout")
		self.session = None
		return response

	@staticmethod
	def get_filter():
		return 'status == OK or status == DQ'

	@staticmethod
	def wrap_filter(run_filter, first_run, last_run):
		f = '(%s) and run_id >= %d' % (run_filter, first_run)
		if (last_run != None):
			f += ' and run_id <= %d' % last_run
		return f

	def parse_run(self, raw_run):
		parts = raw_run.split(';')
		return Run(self.contest_id, int(parts[0]), int(parts[10]), parts[11], int(parts[17]), parts[18], parts[22], parts[25])

	def get_runs(self, first_run, last_run = None, runs_filter = None):
		if runs_filter is None:
			runs_filter = self.get_filter()
		prepared_filter = self.wrap_filter(runs_filter, first_run, last_run)	
		
		raw_runs = self.run_contests_cmd("dump-filtered-runs", prepared_filter, 0, -1)
		lines = filter(None, raw_runs.split("\n"))
		runs = sorted(map(self.parse_run, lines), key=lambda x: x.id)
		return runs

	def get_run_source(self, run_id):
		return self.run_contests_cmd("dump-source", run_id)
