import nil.file, utility
from process_procedure import process_procedure
from process_line import get_code, extract_data
from process_offset import extract_offsets

def find_target(lines, target, offset, address_mode):
	end = len(lines)
	for i in range(offset, end):
		line = utility.shrink(lines[i])
		if len(line) == 0:
			continue
		if address_mode:
			section, address, line = extract_data(line)
			if address == target:
				return i
		else:
			line = get_code(line)
			if line[0 : len(target)] == target:
				return i
			
	return None
	
def get_image_base(lines):
	for line in lines:
		if line.find('Imagebase') == -1:
			continue
		return '0x%s' % line.split(' ')[-1]
	return None

def get_line(offset):
	return offset + 1

def process_file(module_name, input, target, name, output):
	print 'Loading the file'
	lines = nil.file.read_lines(input)
	if lines == None:
		print 'Failed to open %s' % input
		return False
		
	print 'Loaded %d lines' % len(lines)
	
	image_base = get_image_base(lines)
	if image_base == None:
		print 'Failed to retrieve the image base of %s' % input
		return False
	
	print 'Creating an offset dictionary for the entire listing'
	offsets = extract_offsets(lines)
	
	if type(target) == tuple:
		offset = find_target(lines, target[0], 0, True)
	else:
		offset = find_target(lines, '%s proc near' % target, 0, False)
	if offset == None:
		print 'Unable to locate the target in %s' % input
		return False
		
	print 'Discovered the procedure at line %d' % get_line(offset)
	
	if type(target) == tuple:
		end = find_target(lines, target[1], offset, True)
	else:
		end = find_target(lines, '%s endp' % target, offset, False)
	if end == None:
		print 'Unable to locate the end of the target in %s' % input
		return False
		
	print 'Discovered the end of the target at line %d' % get_line(end)

	procedure_lines = lines[offset + 1: end]
	i = 0
	for i in range(0, len(procedure_lines)):
		procedure_lines[i] = get_code(procedure_lines[i])
	
	print 'Creating the output'
	data = process_procedure(module_name, image_base, name, procedure_lines, lines, offsets)
	
	print 'Writing data to %s' % output
	
	file = open(output, 'w+b')
	file.write(data)
	file.close()
	
	return True