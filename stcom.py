from cffi import FFI
import importlib

import os
from glob import glob

def cleanup():
    try:
        for f in glob('_stcom.*'):
            os.unlink(f)
    except IOError:
        pass

def offset(symbol):
    ffi = FFI()
    header = open('stcom.h', 'r').read()
    source = """
long offset() {{
	return (long)(&((struct stcom *)NULL)->{});
}}
    """.format(symbol)

    ffi.set_source("_stcom", header+source)
    ffi.cdef("""long offset();""")
    ffi.compile()
    _stcom = importlib.import_module('_stcom')
    return _stcom.lib.offset()

if __name__ == '__main__':
    import sys
    name = sys.argv[1]
    cleanup()
    print('{}: offset {}'.format(name, offset(name)))  
    cleanup()
    
    
    
