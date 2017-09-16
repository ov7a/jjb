import sys
import re
import difflib
from tokens_buffer import TokensBuffer

tokens_pattern = re.compile('("[^"]*")|(\'[^\']*\')|([a-zA-Z0-9_]*)')
comments_patterns = [
	re.compile("/\*.*?\*/", re.DOTALL), # /*COMMENT */
	re.compile("//.*?\n"), # //COMMENT
	re.compile("#.*?\n") # #COMMENT
]

def strip_comments(input):
	for comment_pattern in comments_patterns:
		input = re.sub(comment_pattern, "", input)
	return input

def tokenize(raw_input, token_memory=None):
	input = strip_comments(raw_input)
	tokens = TokensBuffer(token_memory)
	result = list()
	for matches in tokens_pattern.findall(input):
		match = next(filter(None, matches), None)
		if match is None:
			continue
		id = tokens.get_id(match)
		result.append(id)	
	#for (token, id)	in sorted(tokens.ids.items(), key = lambda x: x[1]):
	#	print("%s\t%s" % (token, id))
	return result		

def tokenize_file(fname, token_memory):
	with open(fname) as f:
		return tokenize(f.read(), token_memory)


def similarity(one_tokens, other_tokens):
	comparer = difflib.SequenceMatcher()
	comparer.set_seqs(one_tokens, other_tokens)
	distance = comparer.ratio()
	return distance


if __name__ == "__main__":
	if len(sys.argv) != 3 and len(sys.argv) != 4:
		print("Usage: %s [FILE1] [FILE2] [TOKEN_MEM])" % sys.argv[0])
		exit(1)
		
	one = sys.argv[1]
	other = sys.argv[2]
	mem = int(sys.argv[3]) if len(sys.argv) > 3 else None
	one_tokens = tokenize_file(one, mem)
	other_tokens = tokenize_file(other, mem)
	result = similarity(one_tokens, other_tokens)
	print(result)
