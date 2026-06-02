import pyvisa
import numpy as np
import h5py
import time
from datetime import datetime, timezone
import warnings
import re

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
                self[k.lower()] = int(v)


class VISADummy(object):
    def __init__(self, pts):
        self.pts = pts

    def query(self, query):
        if query == '*IDN?':
            return 'visadummy device'

    def write(self, data):
        log.debug(f'visadummy write {data}')

    def close(self):
        log.debug(f'visadummy close')

    def query_binary_values(self, cmd, datatype='f', container=np.array):
        log.debug(f'visadummy query binary')
        return np.sin(np.linspace(0,100,self.pts)+time.time())

class Measurement:
    def __init__(self, filename, start_freq=70, stop_freq=670, points=101, rbw=10, maxhold=10):
        '''
        :param filename: filename
        :param start_freq: start frequency (MHz)
        :param stop_freq: stop frequency (MHz)
        :param pts: number of points
        :param rbw: resolution  bandwidth (Mhz), default is 10
        :param maxhold: maxhold time (s), default is 10s
        '''
        if filename.split('.')[-1] != 'h5':
            filename = filename + '.h5'

        self.filename = filename
        self.start_freq = start_freq*1e6
        self.stop_freq = stop_freq*1e6
        self.pts = points
        self.rbw = rbw*1e6
        self.maxhold = maxhold

        log.debug(f'created file: {filename}')

    def open_hdf5(self):
        self.h5 = h5py.File(self.filename, "a")

        grp_spec = self.h5.require_group("spectra")

        h5_spec = grp_spec.require_dataset(
            "spectrum",
            shape=(0,self.pts),
            maxshape=(None,self.pts),
            dtype="float32",
            chunks=(1024,self.pts)
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

        frequencies = np.linspace(self.start_freq, self.stop_freq, self.pts)
        if not 'frequencies' in self.h5.attrs:
            self.h5.attrs['frequencies'] = frequencies
            self.h5.attrs['rbw'] = self.rbw
            self.h5.attrs['maxhold'] = self.maxhold
            self.h5.attrs['pts'] = self.pts

        return h5_spec, h5_ts

    def close_hdf5(self):
        self.h5.close()

    def run(self, device="TCPIP0::10.10.10.152::INSTR"):
        '''
        :param device: VISA address string
        :return:
        '''

        try:
            rm = pyvisa.ResourceManager()
            sa = rm.open_resource(device)
        except Exception as e:
            print(e)
            sa = VISADummy(self.pts)

        sa.timeout = 20000

        log.info(f'connected to {sa.query("*IDN?")}')

        sa.write("*RST")

        sa.write(f"SWE:POIN {self.pts}")
        sa.write(f"BAND {self.rbw}")
        sa.write("INIT:CONT ON")

        sa.write("DET SAMPLE")
        #sa.write("DET POS")
        sa.write("DISP:TRAC1:MODE MAXH")
        sa.write("DISP:TRAC:Y:RLEV -10")
        sa.write("DISP:TRAC:Y:SCAL 100")

        sa.write("FORM REAL,32")

        sa.write(f"FREQ:STAR {self.start_freq}")
        sa.write(f"FREQ:STOP {self.stop_freq}")

        try:
            while True:
                sa.write("INIT:CONT ON")

                time.sleep(self.maxhold)
                sa.write("INIT:CONT OFF")
                sa.write("TRAC:CLE")

                trace = sa.query_binary_values(
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

        finally:
            sa.close()
            self.close_hdf5()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("config_file", type=str)
    parser.add_argument("output_file", type=str)

    args = parser.parse_args()

    config = Config(args.config_file)

    m = Measurement(args.output_file, **config)
    m.run("TCPIP0::10.10.10.152::INSTR")
