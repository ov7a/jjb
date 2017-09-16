import sys
import jjb

def simple_tests(token_mem):
	tests_dir = "test_files"
	
	test_data = [
		{"file": "main_with_spaces.py"},
		{"file": "main_with_extra_spaces.py"},
		{"file": "main_with_renames.py"},
		{"file": "main_with_lineswap.py"},
		{"file": "main_with comments.py"},
	]
	
	genuine = jjb.tokenize_file(tests_dir + "/main.py", token_mem)
	for test in test_data:
		file_name = test["file"]
		sample = jjb.tokenize_file("%s/%s" % (tests_dir, file_name), token_mem)
		similarity = jjb.similarity(genuine, sample)
		print(file_name, similarity, sep='\t')
		assert similarity > 0.7, "test for %s failed, got %f" % (file_name, similarity)
	print("simple tests passed")	

if __name__ == "__main__":
	token_mem = None
	if len(sys.argv) > 1:
		token_mem = int(sys.argv[1])
	simple_tests(token_mem)
