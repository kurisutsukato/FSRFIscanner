
import subprocess
from datetime import datetime, timezone
import re
import numpy as np

import threading
import time
import signal
import os

import h5py

import sys
from pathlib import Path

import dotenv
dotenv.load_dotenv()

import logging
log = logging.getLogger('track')
fmt = '%(asctime)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)

try:
    from st_shm import read_shm
except ImportError:
    pass
finally:
    try:
        AZOFFSET = int(os.environ['AZOFFSET'])
        ELOFFSET = int(os.environ['ELOFFSET'])
        AZRATEOFFSET = int(os.environ.get('AZRATEOFFSET', -1))
        ELRATEOFFSET = int(os.environ.get('ELRATEOFFSET', -1))
    except KeyError:
        raise Exception('run stcom.py first')

stop_event = threading.Event()
write_lock = threading.Lock()

def load_cnf(filename):
    with open(filename) as f:
        a,b = f.readline().strip().split(',')
        return (int(a),int(b)),[(k, float(l), float(m)) for row in f for k, l, m in [row.strip().split(',')]]

def acquisition_loop(get_azel, h5file, ts_dset,
                     az_dset, el_dset, azr_dset, elr_dset):
    period = 0.1  # seconds

    while not stop_event.is_set():
        t0 = time.monotonic()

        az, el, azrate, elrate = get_azel()
        dt = datetime.now(timezone.utc)
        timestamp = int(dt.timestamp()*1000)

        with write_lock:
            n = ts_dset.shape[0]

            # extend dataset by one row
            ts_dset.resize(n + 1, axis=0)
            az_dset.resize(n + 1, axis=0)
            el_dset.resize(n + 1, axis=0)
            azr_dset.resize(n + 1, axis=0)
            elr_dset.resize(n + 1, axis=0)

            # store structured entry
            ts_dset[n] = timestamp
            az_dset[n] = az
            el_dset[n] = el
            azr_dset[n] = azrate
            elr_dset[n] = elrate

            # optional:
            h5file.flush()

        dt = time.monotonic() - t0
        sleep_time = max(0, period - dt)
        time.sleep(sleep_time)

    with write_lock:
        h5file.flush()


class Antenna:
    def __init__(self, simulation=True):
        self.simulation = simulation
        self.az_target = 0
        self.el_target = 0

        # those are only used for simulation mode
        self.az = 0
        self.el = 0
        self.az_speed = 0
        self.el_speed = 0

        self.t0 = time.monotonic()

        if simulation:
            log.info('using dummy ACU')
        else:
            log.info('taking control over the ACU')

        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, signum, frame):
        self.stop()
        sys.exit()

    def acquire(self, filename, append=False):
        if filename.split('.')[-1] != 'h5':
            filename = filename + '.h5'

        if not append:
            try:
                os.unlink(filename)
            except OSError:
                pass

        self.h5 = h5py.File(filename, "a")

        ts_dset = self.h5.require_dataset("timestamp", shape=(0,), maxshape=(None,), chunks=(1024,), dtype=np.int64)
        ts_dset.attrs["unit"] = "miliseconds since Unix epoch"
        ts_dset.attrs["timezone"] = "UTC"

        az_dset = self.h5.require_dataset("az", shape=(0,), maxshape=(None,), chunks=(1024,), dtype=np.float64)
        el_dset = self.h5.require_dataset("el", shape=(0,), maxshape=(None,), chunks=(1024,), dtype=np.float64)
        azr_dset = self.h5.require_dataset("azrate", shape=(0,), maxshape=(None,), chunks=(1024,), dtype=np.float64)
        elr_dset = self.h5.require_dataset("elrate", shape=(0,), maxshape=(None,), chunks=(1024,), dtype=np.float64)

        self.thread = threading.Thread(
            target=acquisition_loop,
            args=(self.get_azel, self.h5, ts_dset, az_dset, el_dset, azr_dset, elr_dset),
            daemon=True,
        )
        log.info('starting acquisition loop')
        self.thread.start()

    def stop(self):
        stop_event.set()
        self.deactivate()
        try:
            self.thread.join()
        except AttributeError:
            pass

    def move_rel(self, axis, delta, speed):
        speed = speed if delta > 0 else -speed

        t0 = time.monotonic()
        delta_t = delta / speed
        tfinal = t0 + delta_t

        log.info(f'slewing in {axis} direction with speed {speed}')
        azspeed = speed if axis == 'az' else 0
        elspeed = speed if axis == 'el' else 0
        self.slew(azspeed, elspeed)

        log.info(f'waiting for {delta_t} seconds')

        while True:
            now = time.monotonic()
            if now - tfinal > 0:
                self.slew(0, 0)
                break
            time.sleep(0.01)

        if axis == 'az':
            self.move_to(self.az_target + delta, self.el_target)
        else:
            self.move_to(self.az_target, self.el_target + delta)

    def move_to(self, azcmd, elcmd):
        log.info(f'moving to {azcmd}/{elcmd}')
        self.pres(azcmd, elcmd)

        while True:
            az, el = self.get_azel()[:2]
            if abs(az - azcmd) < 0.1 and abs(el - elcmd) < 0.1:
                break
            time.sleep(0.2)
        az, el = self.get_azel()[:2]
        log.info(f'reached {az}/{el}')

        self.az_target, self.el_target = azcmd, elcmd

    def pres(self, az, el):
        log.info(f'positioning {az}/{el}')
        self.execute(f'antenna=PRES,{az},{el}')

    def slew(self, az=0, el=0):
        log.info(f'slewing {az}/{el}')
        self.execute(f'antenna=SLEW,{az},{el}')

    def activate(self):
        log.info('activating')
        self.execute('antenna=ACTI')
        self.az_target, self.el_target = self.get_azel()[:2]
        time.sleep(0.5)

    def deactivate(self):
        log.info('deactivating')
        time.sleep(0.5)
        self.execute('antenna=STAN')

    def execute(self, cmd):
        if self.simulation:
            mat = re.match(r'antenna=(\w+),([-\d\.]+),([-\d\.]+)', cmd)
            log.info(f'dummy ACU received {cmd}')
            if mat is not None:
                cmd, a, e = mat.groups()
                if cmd == 'PRES':
                    self.az = float(a)
                    self.el = float(e)
                elif cmd == 'SLEW':
                    self.az_speed = float(a)
                    self.el_speed = float(e)
                    self.t0 = time.monotonic()
                else:
                    log.error(f'unknown dummy ACU command {cmd}')
            else:
                log.error(f'dummy ACU: command not implemented: {cmd}')
        else:
            subprocess.call(['inject_snap', cmd])

    def get_azel(self):
        if self.simulation:
            now = time.monotonic()
            self.az += self.az_speed * (now - self.t0)
            self.el += self.el_speed * (now - self.t0)
            self.t0 = now
            return self.az, self.el, 0, 0
        else:
            offsets = [read_shm(AZOFFSET, 1, 'd')[0], read_shm(ELOFFSET, 1, 'd')[0]]
            if AZRATEOFFSET and ELRATEOFFSET:
                offsets.extend([read_shm(AZRATEOFFSET, 1, 'd')[0], read_shm(ELRATEOFFSET, 1, 'd')[0]])
            else:
                offsets.extend([0,0])
            return offsets

    def scan(self, conf_file):
        tstr = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        if conf_file is None:
            output = f'{tstr}.h5'
            self.acquire(output)
            while True:
                time.sleep(1000)
        else:
            start, coords = load_cnf(conf_file)

            output = f'{tstr}_{Path(conf_file).stem}.h5'

            self.activate()
            self.move_to(*start)
            time.sleep(2)
            self.acquire(output)
            for pos in coords:
                self.move_rel(*pos)
                log.info(f'{self.get_azel()}')
            self.stop()

if __name__ == '__main__':
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument('configfile', help='The antenna control config file contains the scanning pattern. '
                                           'If no config file is provided, only the acquisition loop will run. This can be used '
                                           'to record the antenna position in parallel to a running observation program.', nargs='?')
    parser.add_argument('--nosim', action='store_true', default=False, help='disable simulation mode')
    args = parser.parse_args()

    a = Antenna(simulation=args.nosim is False and args.configfile is not None)
    a.scan(args.configfile)






