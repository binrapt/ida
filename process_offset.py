import sys, string, utility
from process_line import extract_data

def process_offset(original_line, tokens, offsets):
	uses_offset = False
	
	i = 0
	while i < len(tokens):
		token = tokens[i]
		if token == 'offset':
			uses_offset = True
			tokens = tokens[0 : i] + tokens[i + 1 : ]
			offset_target = tokens[i]
			try:
				address = offsets[offset_target]
			except KeyError:
				print 'Error: Unable to process offset in "%s"' % original_line
				sys.exit(1)
			tokens[i] = '0%sh' % address
		i += 1
		
	return uses_offset, string.join(tokens)
	
def extract_offsets(lines):
	keywords = ['proc', 'db', 'dw', 'dd']
	offsets = {}
	for line in lines:
		if len(line) < 15:
			continue
		section, address, line = extract_data(line)
		line = utility.shrink(line)
		tokens = line.split(' ')
		if len(tokens) >= 2 and tokens[1] in keywords:
			name = tokens[0]
			offsets[name] = address
	print 'Parsed %d offsets' % len(offsets)
	return offsets