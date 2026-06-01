
import subprocess
from datetime import datetime, timezone

import threading
import time
import signal
import os

import numpy as np
import h5py

import logging
import sys

import dotenv
dotenv.load_dotenv()

log = logging.getLogger('track')
fmt = '%(asctime)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)

try:
    from st_shm import read_shm
except ImportError:
    pass
else:
    AZOFFSET = int(os.environ['AZOFFSET'])
    ELOFFSET = int(os.environ['ELOFFSET'])

import re

class Antenna:
    def __init__(self, az, el):
        self.az = 0
        self.el = 0
        self.azspeed = 0
        self.elspeed = 0
        self.t0 = time.monotonic()

        log.info('using dummy ACU')

    def execute(self, cmd):
        mat = re.match(r'antenna=(\w+),([-\d\.]+),([-\d\.]+)', cmd)
        log.info(f'antenna received {cmd}')
        if mat is not None:
            cmd, a, e = mat.groups()
            if cmd == 'PRES':
                self.az = float(a)
                self.el = float(e)
            elif cmd == 'SLEW':
                self.azspeed = float(a)
                self.elspeed = float(e)
                self.t0 = time.monotonic()
            else:
                log.error(f'unknown antenna command {cmd}')
        else:
            log.error(f'not understood')

    def get_azel(self):
        now = time.monotonic()
        self.az += self.azspeed * (now - self.t0)
        self.el += self.elspeed * (now - self.t0)
        self.t0 = now
        return self.az, self.el

ant = Antenna(0,0)

def inject(cmd):
    try:
        subprocess.call(['inject_snap', cmd])
    except OSError:
        ant.execute(cmd)

def get_azel():
    try:
        return read_shm(AZOFFSET, 1, 'd')[0], read_shm(ELOFFSET, 1, 'd')[0]
    except NameError:
        return ant.get_azel()


stop_event = threading.Event()
write_lock = threading.Lock()

def acquisition_loop(h5file, ts_dset, az_dset, el_dset):
    period = 0.1  # seconds

    while not stop_event.is_set():
        t0 = time.monotonic()

        az, el = get_azel()
        #timestamp = datetime.utcnow().isoformat()
        dt = datetime.now(timezone.utc)
        timestamp = int(dt.timestamp()*1000)

        with write_lock:
            n = ts_dset.shape[0]

            # extend dataset by one row
            ts_dset.resize(n + 1, axis=0)
            az_dset.resize(n + 1, axis=0)
            el_dset.resize(n + 1, axis=0)

            # store structured entry
            ts_dset[n] = timestamp
            az_dset[n] = az
            el_dset[n] = el

            # optional:
            h5file.flush()

        dt = time.monotonic() - t0
        sleep_time = max(0, period - dt)
        time.sleep(sleep_time)

    with write_lock:
        h5file.flush()

class RFIScanner:
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)
        self.running = True

        self.az_real = 0
        self.el_real = 0

    def exit(self, signum, frame):
        self.stop()
        sys.exit()

    def aquire(self, filename, append=False):
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

        self.thread = threading.Thread(
            target=acquisition_loop,
            args=(self.h5, ts_dset, az_dset, el_dset),
            daemon=True,
        )

        self.thread.start()

    def stop(self):
        stop_event.set()
        self.deactivate()
        self.thread.join()

    def move(self, azcmd, elcmd):
        log.info(f'moving to {azcmd}/{elcmd}')
        inject(f'antenna=PRES,{azcmd},{elcmd}')

        while True:
            az, el = get_azel()
            if abs(az - azcmd) < 0.2 and abs(el - elcmd) < 0.2:
                break
            time.sleep(0.5)
        az, el = get_azel()
        self.az_real, self.el_real = az, el

    def move_rel(self, dir, delta, speed=0.1):
        speed = speed if delta > 0 else -speed
        tmp = np.asarray(get_azel()) - np.array([self.az_real, self.el_real])
        corr = tmp[0] if dir == 'az' else tmp[1]
        delta_corr = delta-corr

        log.info(f'slewing in {dir} direction with speed {speed}')
        t0 = time.monotonic()
        tfinal = delta_corr / speed + t0

        azspeed = speed if dir == 'az' else 0
        elspeed = speed if dir == 'el' else 0
        self.slew(azspeed, elspeed)

        log.info(f'waiting for {delta_corr/speed} seconds')

        while True:
            now = time.monotonic()
            if now - tfinal > 0:
                self.slew(0, 0)
                break
            time.sleep(0.01)

        if dir == 'az':
            self.az_real += delta
        else:
            self.el_real += delta

    def slew(self, az=0, el=0):
        log.info(f'slewing {az}/{el}')
        inject(f'antenna=SLEW,{az},{el}')

    def activate(self):
        log.info('activating')
        inject('antenna=ACTI')
        time.sleep(1)

    def deactivate(self):
        log.info('deactivating')
        time.sleep(0.5)
        inject('antenna=STAN')


def scan(start, coords, filename):
    rs = RFIScanner()
    rs.activate()
    rs.move(*start)
    time.sleep(2)
    rs.aquire(filename)
    for pos in coords:
        rs.move_rel(*pos)
        log.info(f'{get_azel()}')
    rs.stop()

el = np.linspace(0,np.pi/2,89)[::2]
az = 1/np.cos(el)
azspeed = az*0.1
azspeed[azspeed>3] = 2

coords = [[('el', 1, 1),('az', 2, q), ('el', 1, 1),('az',-2, q)] for q in azspeed.tolist()]
#for n,x in enumerate(coords):
#    print(f'{n:02d} {x}')
coords = [q for sublist in coords for q in sublist]

coords = [('el', 1, 1),('az', 10, .2), ('el', 1, 1),('az',-10, .2)]*10

if __name__ == '__main__':
    #scan((0,60),coords[120:], 'neu.h5')
    scan((0,20),coords, 'neu.h5')




