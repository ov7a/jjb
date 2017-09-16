import inspect
import types
import sys
import jjb

def straight(config, old_run_source, new_run_source):
	old_tokens = jjb.tokenize(old_run_source)
	new_tokens = jjb.tokenize(new_run_source)
	result = jjb.similarity(old_tokens, new_tokens)
	return result
	
def goldfish(config, old_run_source, new_run_source):
	memory = config["memory"]
	old_tokens = jjb.tokenize(old_run_source, memory)
	new_tokens = jjb.tokenize(new_run_source, memory)
	result = jjb.similarity(old_tokens, new_tokens)
	return result	

all_handlers = dict(inspect.getmembers(sys.modules[__name__], predicate=lambda x: isinstance(x, types.FunctionType)))

def get(handler_name):
	return all_handlers[handler_name]
