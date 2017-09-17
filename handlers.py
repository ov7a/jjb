import inspect
import types
import sys
import jjb
import tempfile
import subprocess
import os

def straight(config, old_run_source, new_run_source, lang):
	old_tokens = jjb.tokenize(old_run_source)
	new_tokens = jjb.tokenize(new_run_source)
	result = jjb.similarity(old_tokens, new_tokens)
	return result
	
def goldfish(config, old_run_source, new_run_source, lang):
	memory = config["memory"]
	old_tokens = jjb.tokenize(old_run_source, memory)
	new_tokens = jjb.tokenize(new_run_source, memory)
	result = jjb.similarity(old_tokens, new_tokens)
	return result	

def external(config, old_run_source, new_run_source, lang):
	args = config['args']
	try:
		old_file = tempfile.NamedTemporaryFile(delete=False)
		new_file = tempfile.NamedTemporaryFile(delete=False)
		with old_file as old, new_file as new:
			old.write(bytes(old_run_source, 'UTF-8'))
			new.write(bytes(new_run_source, 'UTF-8'))
		all_args = list(map(str, args)) + [lang, old.name, new.name]
		output = subprocess.check_output(all_args).decode('utf-8')
		result = float(output)
		os.remove(old_file)
		os.remove(new_file)
	except: 
		return None					
	return result

all_handlers = dict(inspect.getmembers(sys.modules[__name__], predicate=lambda x: isinstance(x, types.FunctionType)))

def get(handler_name):
	return all_handlers[handler_name]
