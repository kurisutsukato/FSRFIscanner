import pyvisa
import numpy as np
import h5py
import time
from datetime import datetime, timezone
import warnings
import re
import os

warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__file__)

logging.getLogger("pyvisa").disabled = True

class Config(dict):
    def __init__(self, filename):
        for row in open(filename):
            mat = re.match(r'(\S+)\s*=\s*(\S+)', row.strip())
            if mat:
                k,v = mat.groups()
                self[k.lower()] = float(v)

class Analyzer:
    def __init__(self, device="TCPIP0::10.10.10.152::INSTR"):
        self.sa = None
        self.device = device
        self.maxhold = 2.0

        self.connect()

    def __del__(self):
        if self.sa is not None:
            self.sa.close()
            log.info('disconnected')

    def connect(self):
        if self.sa is None:
            rm = pyvisa.ResourceManager()
            self.sa = rm.open_resource(self.device)
            log.info('connected')

    def maxval(self, wait=0.1):
        self.sa.write("INIT:CONT ON")
        self.sa.write("FORM REAL,32")
        self.hold()
        time.sleep(wait)

        #self.sa.write("INIT:CONT OFF")
        #self.sa.write("TRAC:CLE")
        self.clearwrite()

        trace = self.sa.query_binary_values(
            "TRAC:DATA? TRACE1",
            datatype='f',
            container=np.array
        )
        return trace.max()

    def init_hdf5(self, filename, start_freq, stop_freq, num_points, rbw):
        if os.path.exists(filename):
            print(f'file {filename} exists')
            return

        self.filename = filename
        h5 = h5py.File(filename, "a")

        grp_spec = h5.require_group("spectra")

        h5_spec = grp_spec.require_dataset(
            "spectrum",
            shape=(0,num_points),
            maxshape=(None,num_points),
            dtype="float32",
            chunks=(1024,num_points)
        )

        h5_ts = grp_spec.require_dataset(
            "timestamp",
            shape=(0,),
            maxshape=(None,),
            chunks=(1024,),
            dtype=np.int64
        )
        h5_ts.attrs["unit"] = "miliseconds since Unix epoch"
        h5_ts.attrs["timezone"] = "UTC"

        frequencies = np.linspace(start_freq, stop_freq, num_points)
        if not 'frequencies' in h5.attrs:
            h5.attrs['frequencies'] = frequencies
            h5.attrs['rbw'] = rbw
            h5.attrs['maxhold'] = self.maxhold
            h5.attrs['pts'] = num_points

        h5.close()

    def open_hdf5(self):
        self.h5 = h5py.File(self.filename, "a")

        grp_spec = self.h5.require_group("spectra")
        return grp_spec['spectrum'], grp_spec['timestamp']

    def close_hdf5(self):
        self.h5.close()

    def hold(self):
        self.sa.write("DISP:TRAC1:MODE MAXH")

    def clearwrite(self):
        self.sa.write("DISP:TRAC1:MODE WRIT")

    def reset(self):
        self.sa.write('*RST')


    def config(self, kw):
        if 'pts' in kw:
            self.sa.write(f"SWE:POIN {kw['pts']}")
        if 'rbw' in kw:
            self.sa.write(f"BAND {kw['rbw']}")

        if 'start_freq' in kw:
            print(kw['start_freq'])
            self.sa.write(f"FREQ:STAR {kw['start_freq']}")
        if 'stop_freq' in kw:
            self.sa.write(f"FREQ:STOP {kw['stop_freq']}")
        if 'center' in kw:
            self.sa.write(f"FREQ:CENT {kw['center']}")
        if 'span' in kw:
            self.sa.write(f"FREQ:SPAN {kw['span']}")

        if 'maxhold' in kw:
            self.maxhold = kw['maxhold']


    def run(self, filename, device="TCPIP0::10.10.10.152::INSTR"):
        if filename.split('.')[-1] != 'h5':
            filename = filename + '.h5'

        start_freq = float(self.sa.query("FREQ:STAR?"))
        stop_freq = float(self.sa.query("FREQ:STOP?"))
        num_points = int(self.sa.query("SWE:POIN?"))
        rbw = float(self.sa.query("BAND?"))

        self.init_hdf5(filename, start_freq, stop_freq, num_points, rbw)

        self.sa.write("INIT:CONT ON")

        self.sa.write("DET SAMPLE")
        #self.sa.write("DET POS")
        self.sa.write("DISP:TRAC1:MODE MAXH")
        self.sa.write("DISP:TRAC:Y:RLEV -10")
        self.sa.write("DISP:TRAC:Y:SCAL 100")

        self.sa.write("FORM REAL,32")

        try:
            while True:
                self.sa.write("INIT:CONT ON")

                time.sleep(self.maxhold)
                self.sa.write("INIT:CONT OFF")
                self.sa.write("TRAC:CLE")

                trace = self.sa.query_binary_values(
                    "TRAC:DATA? TRACE1",
                    datatype='f',
                    container=np.array
                )

                dt = datetime.now(timezone.utc)
                timestamp = int(dt.timestamp() * 1000)

                spec, ts = self.open_hdf5()

                n = spec.shape[0]
                spec.resize(n+1,axis=0)
                spec[n] = trace
                ts.resize(n+1,axis=0)
                ts[n] = timestamp

                self.close_hdf5()

                log.info(f"cycle {n} saved")

        except KeyboardInterrupt:
            log.info("Stopping")
            self.close_hdf5()


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()

    parser.add_argument("config_file", type=str)
    parser.add_argument("output_file", nargs="?")
    args = parser.parse_args()

    config = Config(args.config_file)

    tstr = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    if args.output_file:
        outfile = args.output_file
    else:
        outfile = f'{tstr}_{Path(args.config_file).stem}'
    m = Analyzer()
    m.config(config)
    m.run(outfile)
