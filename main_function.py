import string, utility, sys
from process_offset import process_offset
from process_arguments import process_arguments

def is_number(input):
	try:
		int(input)
	except:
		return False
	return True

def process_main_function(module_name, image_base, new_name, procedure_lines, offsets):
	replacements = [
		('\t', ' '),
		(' short ', ' '),
		(' far ', ' ')
	]
	
	operators = ['+', '-', '*']
	
	declaration_signature = 'void %s()' % new_name
	signature = 'void __declspec(naked) %s()' % new_name
	
	is_first_line = True
	
	initialisation_function_name = 'initialise_%s' % new_name
	interrupt_function_name = '%s_interrupt' % new_name
	
	main_function = """%s
{
	__asm
	{
		//Initialisation code:
		
		cmp module_base, 0
		jnz is_already_initialised
		
		call %s
		
	is_already_initialised:
	
		//Actual code starts here:
		
""" % (signature, initialisation_function_name)
	
	intra_module_procedures = set()
	
	linking_counter = 0
	
	for original_line in procedure_lines:
		line = original_line
		
		line = utility.shrink(line)
			
		for target, replacement in replacements:
			line = line.replace(target, replacement)
			
		comment_offset = line.find(';')
		if comment_offset != -1:
			line = line[0 : comment_offset]
			
		line = line.strip()
		
		if len(line) == 0:
			continue
	
		tokens = line.split(' ')
		
		if len(tokens) == 5 and tokens[1] == '=':
			if tokens[2] != 'dword' or tokens[3] != 'ptr':
				print 'Unknown definition type: %s' % original_line
				return None
			
			macro = tokens[0]
			replacement = tokens[-1]
			if replacement[0] == '-':
				replacement = '-%s' % replacement[1 : ]
			replacements.append(('+%s' % macro, replacement))
				
			continue
			
		elif len(tokens) == 2 and tokens[0] == 'call':
			target = tokens[1]
			
			error = False
			
			try:
				offset = offsets[target]
				intra_module_procedures.add((target, offset))
				
			except KeyError:				
				error = True
					
			if error:
				print 'Warning: Was unable to retrieve the offset of the procedure in "%s"' % line

		requires_linking, new_line = process_arguments(line, offsets)
		if new_line != line:
			print 'Warning: Translated "%s" to "%s"' % (line, new_line)
		line = new_line
			
		uses_offset, offset_output = process_offset(original_line, tokens, offsets)
		if uses_offset:
			print 'Warning: "offset" keyword used in line "%s", translated to "%s"' % (line, offset_output)
			line = offset_output
			
		for operator in operators:
			line = line.replace(operator, ' %s ' % operator)
			
		indentation = 1
		if line[-1] != ':':
			indentation = 2
		else:
			if is_first_line:
				continue
			
		if uses_offset:
			requires_linking = True
			
		main_function += '%s%s\n' % (indentation * '\t', line)
		if requires_linking:
			print 'Added linker reference %d for line "%s"' % (linking_counter, line)
			main_function += '\tlinker_address_%d:\n' % linking_counter
			linking_counter += 1
			
		is_first_line = False
			
	main_function += '\n\t\t//Instruction address table hack:\n\n'
	
	ud2_count = 4
	marker = '\\x0f\\x0b' * ud2_count
			
	for i in range(0, ud2_count):
		main_function += '\t\tud2\n'
		
	main_function += '\n'
		
	for i in range(0, linking_counter):
		main_function += '\t\tpush linker_address_%d\n' % i
			
	main_function += '\t}\n}\n\n'
	
	variables = 'namespace\n{\n'
	variables += '\t//Initialisation variables\n\n'
	variables += '\tchar const * module_name = "%s";\n' % module_name
	variables += '\tunsigned image_base = %s;\n' % image_base
	variables += '\tunsigned module_base = 0;\n\n'
	
	call_addresses = ''
	first = True
	for name, offset in intra_module_procedures:
		if first:
			first = False
		else:
			call_addresses += ',\n'
		call_addresses += '\t\t&%s' % name
		variables += '\tunsigned %s = 0x%s;\n' % (name, offset)
		
	if len(intra_module_procedures) > 0:
		variables += '\n'
	
	variables += '}\n\n'
	
	headers = [
		'string',
		'windows.h'
	]
	
	includes = ''
	for header in headers:
		includes += '#include <%s>\n' % header
	includes += '\n'
	
	initialisation_function = """void %s()
{
	__asm
	{
		int 3
	}
}

%s;

void __stdcall %s()
{
	module_base = reinterpret_cast<unsigned>(GetModuleHandle(module_name));
	if(module_base == 0)
		%s();
	
	unsigned * call_addresses[] =
	{
%s
	};
	
	unsigned linking_offset = module_base - image_base;
	
	for(std::size_t i = 0; i < %d; i++)
	{
		unsigned & address = *call_addresses[i];
		address += linking_offset;
	}
	
	bool success = false;
	
	std::string const marker = "%s";
	
	char * data_pointer = reinterpret_cast<char *>(&%s);
	while(true)
	{
		std::string current_string(data_pointer, marker.size());
		if(current_string == marker)
		{
			success = true;
			break;
		}
		data_pointer++;
	}
	
	if(!success)
		%s();
	
	data_pointer += marker.size();
	
	for(unsigned i = 0; i < %d; i++)
	{
		char * label_pointer = *reinterpret_cast<char **>(data_pointer + 1);
		unsigned * immediate_pointer = reinterpret_cast<unsigned *>(label_pointer - 4);
		DWORD old_protection;
		SIZE_T const patch_size = 4;
		if(!VirtualProtect(immediate_pointer, patch_size, PAGE_EXECUTE_READWRITE, &old_protection))
			%s();
		unsigned & address = *immediate_pointer;
		address += linking_offset;
		DWORD unused;
		if(!VirtualProtect(immediate_pointer, patch_size, old_protection, &unused))
			%s();
		data_pointer += 5;
	}
}
""" % (interrupt_function_name, declaration_signature, initialisation_function_name, interrupt_function_name, call_addresses, len(intra_module_procedures), marker, new_name, interrupt_function_name, linking_counter, interrupt_function_name, interrupt_function_name)
	
	return (includes, variables, main_function, initialisation_function)