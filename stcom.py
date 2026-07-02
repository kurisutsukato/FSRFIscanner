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

    ffi.set_source(f"_{symbol}", header+source)
    ffi.cdef("""long offset();""")
    ffi.compile()

    _stcom = importlib.import_module(f"_{symbol}")
    return _stcom.lib.offset()

if __name__ == '__main__':
    import argparse
    import os

    env_var_mapping = {'azvar':'AZOFFSET','elvar':'ELOFFSET','azratevar':'AZRATEOFFSET','elratevar':'ELRATEOFFSET'}

    parser = argparse.ArgumentParser()
    parser.add_argument('azvar', help='name of the station SHM variable for the actual azimuth position, e.g. Azactpos')
    parser.add_argument('elvar', help='name of the station SHM variable for the actual elevation position, e.g. Elactpos')
    parser.add_argument('azratevar', help='name of the station SHM variable for the actual azimuth rate, e.g. Azactrate', nargs='?')
    parser.add_argument('elratevar', help='name of the station SHM variable for the actual elevation rate, e.g. Elactrate', nargs='?')

    out = {}

    args = parser.parse_args()
    for k,v in vars(args).items():
        if v:
            cleanup()
            out[env_var_mapping[k]] = offset(v)
    cleanup()

    out = '\n'.join(f'{k}={v}' for k,v in out.items())
    with open('.env', 'w') as f:
        f.write(out)
    print('done')

    
    
