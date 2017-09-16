import sys
import re
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance

pattern = re.compile("[^\s]+") #lets heavily comment code
def tokenize(input): # every
	last_id = 0 # line
	ids = dict() #should 
	result = list() # be
	for match in pattern.findall(input): # commented
		id = ids.get(match) # or
		if id is None: # no 
			id = last_id # one 
			ids[match] = id # will 
			last_id += 1 # understand
		result.append(id) # what
	return result # is 

def tokenize_file(fname): # going
	with open(fname) as f: # on
		return tokenize(f.read()) # here

def similarity(one_tokens, other_tokens) # right?
	distance = normalized_damerau_levenshtein_distance(one_tokens, other_tokens) # i
	return distance # was


if __name__ == "__main__": # told
	if len(sys.argv) != 3: # that
		print("Usage: %s [FILE1] [FILE2])" % sys.argv[0]) # comments
		exit(1) # are
		
	one = sys.argv[1] # a
	other = sys.argv[2] # good
	one_tokens = tokenize_file(one) # thing
	other_tokens = tokenize_file(other) # for
	result = similarity(one_tokens, other_tokens) # senior
	print(result) # programmers
