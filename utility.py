def shrink(line):
	target = '  '
	while line.find(target) != -1:
		line = line.replace(target, ' ')
	return line.strip()