import string

def process_arguments(line, offsets):
	requires_linking = False
	if line[-1] == ':':
		return requires_linking, line
	tokens = line.split(' ')
	instruction = tokens[0]
	input = line[len(instruction) + 1 : ]
	arguments = input.split(',')
	if len(arguments) == 1:
		return requires_linking, line
	arguments = map(lambda x: x.strip(), arguments)
	for i in range(0, len(arguments)):
		argument = arguments[i]
		
		tokens = argument.split(' ')
		if tokens[0] in ['byte', 'word', 'dword'] and len(tokens) >= 3:
			tokens[2] = 'ds:%s' % tokens[2]
			argument = string.join(tokens, ' ')
		else:
			target = 'ds:'
			if len(argument) >= len(target) and argument[0 : len(target)] == target:
				argument = argument[len(target) : ]
			offset = argument.find('[')
			if offset == -1:
				name = argument
				try:
					address = offsets[name]
					argument = 'ds:[0%sh]' % address
					requires_linking = True
				except KeyError:
					pass
			else:
				name = argument[0 : offset]
				if len(name) > 0:
					try:
						address = offsets[name]
						arithmetic_term = argument[offset + 1 : - 1]
						argument = 'ds:[%s+0%sh]' % (arithmetic_term, address)
						requires_linking = True
					except KeyError:
						print 'Error: Unable to resolve address in "%s"' % line
						sys.exit(1)
				else:
					argument = 'ds:%s' % argument
		arguments[i] = argument
	return requires_linking, '%s %s' % (instruction, string.join(arguments, ', '))