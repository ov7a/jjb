from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance
import re
import sys

pattern = re.compile("[^\s]+")
def tokenize(input):
	result = list()
	ids = dict()
	last_id = 0
	for match in pattern.findall(input):
		id = ids.get(match)
		if id is None:
			ids[match] = last_id
			last_id += 1
			id = last_id - 1
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
		
	other = sys.argv[2]
	one = sys.argv[1]
	other_tokens = tokenize_file(other)
	one_tokens = tokenize_file(one)
	result = similarity(one_tokens, other_tokens)
	print(result)
