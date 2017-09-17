import inspect
import types
import sys
import jjb
import tempfile
import subprocess
import os

def straight(config, old_run, new_run):
	old_tokens = jjb.tokenize(old_run.source)
	new_tokens = jjb.tokenize(new_run.source)
	result = jjb.similarity(old_tokens, new_tokens)
	return result
	
def goldfish(config, old_run, new_run):
	memory = config["memory"]
	old_tokens = jjb.tokenize(old_run.source, memory)
	new_tokens = jjb.tokenize(new_run.source, memory)
	result = jjb.similarity(old_tokens, new_tokens)
	return result	

def external(config, old_run, new_run):
	args = config['args']
	old_file = tempfile.NamedTemporaryFile(delete=False)
	new_file = tempfile.NamedTemporaryFile(delete=False)
	with old_file as old, new_file as new:
		old.write(bytes(old_run.source, 'UTF-8'))
		new.write(bytes(new_run.source, 'UTF-8'))
	all_args = list(map(str, args)) + [new_run.lang, old.name, new.name]
	try:
		output = subprocess.check_output(all_args).decode('utf-8')
		result = float(output)
	except subprocess.CalledProcessError:	
		if (old_run.lang != new_run.lang):
			result = 0.0
		else:	
			result = None					
	os.remove(old_file.name)
	os.remove(new_file.name)
	return result

all_handlers = dict(inspect.getmembers(sys.modules[__name__], predicate=lambda x: isinstance(x, types.FunctionType)))

def get(handler_name):
	return all_handlers[handler_name]
