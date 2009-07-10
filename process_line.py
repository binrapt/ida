import sys

def extract_data(original_line):
	line = original_line.replace('\t', ' ')
	offset = line.find(' ')
	if offset == -1:
		offset = len(line)
	description = line[0 : offset]
	line = line[offset + 1: ]
	tokens = description.split(':')
	if len(tokens) != 2:
		print 'Unable to parse description in line "%s"' % original_line
		sys.exit(1)
	section = tokens[0]
	address = tokens[1]
	return section, address, line
	
def get_code(line):
	section, address, line = extract_data(line)
	return line