import pyvisa
import warnings

warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__file__)

logging.getLogger("pyvisa").disabled = True

def run(device="TCPIP0::10.10.10.152::INSTR", **kw):
    '''
    :param device: VISA address string
    :return:
    '''

    rm = pyvisa.ResourceManager()
    sa = rm.open_resource(device)

    sa.timeout = 20000

    log.info(f'connected to {sa.query("*IDN?")}')

    #sa.write("*RST")

    if 'pts' in kw:
        sa.write(f"SWE:POIN {kw['pts']}")
    if 'rbw' in kw:
        sa.write(f"BAND {kw['rbw']}")

    if 'start_freq' in kw:
        print(kw['start_freq'])
        sa.write(f"FREQ:STAR {kw['start_freq']}")
    if 'stop_freq' in kw:
        sa.write(f"FREQ:STOP {kw['stop_freq']}")
    if 'center' in kw:
        sa.write(f"FREQ:CENT {kw['center']}")
    if 'span' in kw:
        sa.write(f"FREQ:SPAN {kw['span']}")

    sa.write("INIT:CONT ON")

    sa.write("DET SAMPLE")
    #sa.write("DET POS")
    if kw['m']:
        sa.write("DISP:TRAC1:MODE WRIT")
        sa.write("DISP:TRAC1:MODE MAXH")
    else:
        sa.write("DISP:TRAC1:MODE WRIT")
    sa.write("DISP:TRAC:Y:RLEV -10")
    sa.write("DISP:TRAC:Y:SCAL 100")

    sa.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--start_freq", type=float)
    parser.add_argument("--stop_freq", type=float)
    parser.add_argument("--center", type=float)
    parser.add_argument("--span", type=float)
    parser.add_argument("--rbw", type=float)
    parser.add_argument("--pts", type=int)
    parser.add_argument("-m", action="store_true")

    args = parser.parse_args()

    run("TCPIP0::10.10.10.152::INSTR", **vars(args))
