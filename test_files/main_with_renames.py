import sys
import re
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance

shablon = re.compile("[^\s]+")
def parcing(input):
	poslednii = 0
	nomera = dict()
	otvet = list()
	for s in shablon.findall(input):
		nomer = nomera.get(s)
		if nomer is None:
			nomer = poslednii
			nomera[s] = nomer
			poslednii += 1
		otvet.append(nomer)	
	return otvet		

def parcing_fail(imya):
	with open(imya) as f:
		return parcing(f.read())

def pohozhest(first_chasti, second_chasti)
	rasstoyanie = normalized_damerau_levenshtein_distance(first_chasti, second_chasti) 
	return rasstoyanie


if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Usage: %s [FILE1] [FILE2])" % sys.argv[0])
		exit(1)
		
	first = sys.argv[1]
	second = sys.argv[2]
	first_chasti = parcing_fail(first)
	second_chasti = parcing_fail(second)
	otvet = pohozhest(first_chasti, second_chasti)
	print(otvet)
