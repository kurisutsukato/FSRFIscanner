from cffi import FFI
import importlib
import sys

from glob import glob

def cleanup():
    try:
        for f in glob('_stcom.*'):
            os.unlink(f)
    except IOError:
        pass

def offset(symbol):
    ffi = FFI()
    try:
        header = open('/usr2/st/include/stcom.h', 'r').read()
    except IOError:
        try:
            header = open('stcom.h', 'r').read()
        except IOError:
            print('unable to find stcom.h')
            sys.exit()

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
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument('azvar', help='name of the station SHM variable for the actual azimuth position, e.g. Azactpos')
    parser.add_argument('elvar', help='name of the station SHM variable for the actual elevation position, e.g. Elactpos')

    cleanup()
    args = parser.parse_args()
    azoff = offset(args.azvar)
    cleanup()
    eloff = offset(args.elvar)
    cleanup()

    print(f'AZOFFSET={azoff}\nELOFFSET={eloff}', file=open('.env', 'w'))
    print('done')

    
    
