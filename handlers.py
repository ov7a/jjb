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

def __try_external(config, old_run, new_run, force_temp=False):
	args = config['args']
	
	(old_is_temp, old_path) = get_source_path(old_run, force_temp)
	(new_is_temp, new_path) = get_source_path(new_run, force_temp)
		
	all_args = list(map(str, args)) + [new_run.lang, old_path, new_path]
	try:
		output = subprocess.check_output(all_args).decode('utf-8')
		result = float(output)
	except subprocess.CalledProcessError:	
		result = None					
	if old_is_temp:
		os.remove(old_path)
	if new_is_temp:
		os.remove(new_path)
	return result

def external(config, old_run, new_run):
	result = __try_external(config, old_run, new_run)
	if result is None:
		result = __try_external(config, old_run, new_run, force_temp=True)
	if (result is None) and (old_run.lang != new_run.lang):
		result = 0.0
	return result	

all_handlers = dict(inspect.getmembers(sys.modules[__name__], predicate=lambda x: isinstance(x, types.FunctionType) and (not x.__name__.startswith("__"))))

def get(handler_name):
	return all_handlers[handler_name]		
	
def get_source_path(run, force_temp):
	if (not force_temp):
		path = run.source_path()
		if (os.path.isfile(path)):
			return (False, path)
		
	temp_file = tempfile.NamedTemporaryFile(delete=False)
	with temp_file as temp:
		temp.write(bytes(run.source.encode('ascii', 'replace').decode(), 'UTF-8'))
	return (True, temp_file.name)
