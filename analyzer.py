from abc import abstractmethod, ABC

import pyvisa
import numpy as np
import h5py
import time
from datetime import datetime, timezone
import warnings
import re
import os
import sys

warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__file__)

logging.getLogger("pyvisa").disabled = True

class Config(dict):
    def __init__(self, filename):
        super().__init__()
        for row in open(filename):
            mat = re.match(r'(\S+)\s*=\s*(\S+)', row.strip())
            if mat:
                k,v = mat.groups()
                self[k.lower()] = float(v)

class Analyzer(ABC):
    def __init__(self, device):
        '''

        :param device: VISA address string, e.g. TCPIP0::10.10.10.152::INSTR
        '''
        self.conn = None
        self.device = device
        self.maxhold = 2.0

        self.connect()

    def __del__(self):
        self.disconnect()

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    def init_hdf5(self, filename, start_freq, stop_freq, num_points, rbw):
        '''

        :param filename: hdf5 filename
        :param start_freq: start frequency in Hz (metadata stored in t the hdf5 file)
        :param stop_freq: stop frequency in Hz (metadata stored in t the hdf5 file)
        :param num_points: number of points of the traces (metadata stored in t the hdf5 file)
        :param rbw: resolution bandwidth in Hz (metadata stored in t the hdf5 file)
        :return:
        '''

        if os.path.exists(filename):
            log.error(f'file {filename} exists, aborting')
            sys.exit()

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

    @abstractmethod
    def hold(self):
        pass

    @abstractmethod
    def clearwrite(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def config(self, kw):
        pass

    def write_hdf5(self, trace):
        dt = datetime.now(timezone.utc)
        timestamp = int(dt.timestamp() * 1000)

        spec, ts = self.open_hdf5()

        n = spec.shape[0]
        spec.resize(n + 1, axis=0)
        spec[n] = trace
        ts.resize(n + 1, axis=0)
        ts[n] = timestamp

        self.close_hdf5()

        log.info(f"cycle {n} saved")

    @abstractmethod
    def run(self, filename):
        pass


class FSL18(Analyzer):
    def connect(self):
        if self.conn is None:
            rm = pyvisa.ResourceManager()
            self.conn = rm.open_resource(self.device)
            log.info('connected')

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
            log.info('disconnected')

    def hold(self):
        self.conn.write("DISP:TRAC1:MODE MAXH")

    def clearwrite(self):
        self.conn.write("DISP:TRAC1:MODE WRIT")

    def reset(self):
        self.conn.write('*RST')

    def config(self, kw):
        if 'pts' in kw:
            self.conn.write(f"SWE:POIN {kw['pts']}")
        if 'rbw' in kw:
            self.conn.write(f"BAND {kw['rbw']}")
        if 'start_freq' in kw:
            self.conn.write(f"FREQ:STAR {kw['start_freq']}")
        if 'stop_freq' in kw:
            self.conn.write(f"FREQ:STOP {kw['stop_freq']}")
        if 'center' in kw:
            self.conn.write(f"FREQ:CENT {kw['center']}")
        if 'span' in kw:
            self.conn.write(f"FREQ:SPAN {kw['span']}")
        if 'level' in kw:
            self.conn.write(f"DISP:TRAC:Y:RLEV {kw['level']}")
        if 'maxhold' in kw:
            self.maxhold = kw['maxhold']

    def run(self, filename):
        if filename.split('.')[-1] != 'h5':
            filename = filename + '.h5'

        start_freq = float(self.conn.query("FREQ:STAR?"))
        stop_freq = float(self.conn.query("FREQ:STOP?"))
        num_points = int(self.conn.query("SWE:POIN?"))
        rbw = float(self.conn.query("BAND?"))

        self.init_hdf5(filename, start_freq, stop_freq, num_points, rbw)

        self.conn.write("INIT:CONT ON")

        self.conn.write("DET SAMPLE")
        self.conn.write("DISP:TRAC1:MODE MAXH")
        self.conn.write("DISP:TRAC:Y:SCAL 100")

        self.conn.write("FORM REAL,32")

        try:
            while True:
                self.conn.write("INIT:CONT ON")

                time.sleep(self.maxhold)
                self.conn.write("INIT:CONT OFF")
                self.conn.write("TRAC:CLE")

                trace = self.conn.query_binary_values(
                    "TRAC:DATA? TRACE1",
                    datatype='f',
                    container=np.array
                )

                self.write_hdf5(trace)

        except KeyboardInterrupt:
            log.info("Stopping")
            self.close_hdf5()

if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()

    parser.add_argument("config_file", type=str, help="defines the scanning pattern")
    parser.add_argument("visa_address", type=str, help="VISA address, e.g. TCPIP0::10.10.10.152::INSTR")
    parser.add_argument("output_file", nargs="?", help="hdf5 output file, if not given, the output file will be named"
                                                       "according to the pattern \"<datetime>_<config file>.h5\"")
    args = parser.parse_args()

    config = Config(args.config_file)

    tstr = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    if args.output_file:
        outfile = args.output_file
    else:
        outfile = f'{tstr}_{Path(args.config_file).stem}'

    m = FSL18(args.visa_address)
    m.config(config)
    m.run(outfile)
