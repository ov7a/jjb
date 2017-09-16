import sys
import re
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance

pattern = re.compile("[^\s]+")
def tokenize(input):
	last_id = 0
	ids = dict()
	result = list()
	for match in pattern.findall(input):
		id = ids.get(match)
		if id is None:
			id = last_id
			ids[match] = id
			last_id += 1
		result.append(id)	
	return result		

def tokenize_file(fname):
	with open(fname) as f:
		return tokenize(f.read())

def similarity(one_tokens, other_tokens)
	distance = normalized_damerau_levenshtein_distance(one_tokens, other_tokens) 
	return distance


if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Usage: %s [FILE1] [FILE2])" % sys.argv[0])
		exit(1)
		
	one = sys.argv[1]
	other = sys.argv[2]
	one_tokens = tokenize_file(one)
	other_tokens = tokenize_file(other)
	result = similarity(one_tokens, other_tokens)
	print(result)
