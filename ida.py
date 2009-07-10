import sys, nil.file
from process_file import process_file

if len(sys.argv) < 6:
	print 'python %s <name of the DLL> <path to input assembly .lst> <procedure to extract> <new name of the procedure> <output C++ file>' % sys.argv[0]
	print 'python %s <name of the DLL> <path to input assembly .lst> <start address> <end address> <new name of the procedure> <output C++ file>' % sys.argv[0]
	sys.exit(1)

if len(sys.argv) == 6:
	process_file(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
else:
	process_file(sys.argv[1], sys.argv[2], (sys.argv[3], sys.argv[4]), sys.argv[5], sys.argv[6])