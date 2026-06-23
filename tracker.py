import time
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from datetime import datetime, timedelta

import logging

from analyzer import Analyzer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__file__)


class Tracker:
    def __init__(self, antenna, analyzer):
        self.antenna = antenna
        self.analyzer = analyzer

    def measure_until(self, delta, data=[]):
        tmp = data
        start = datetime.now()

        while datetime.now() < start+timedelta(seconds=delta):
            tmp.append([datetime.now(), self.analyzer.maxval()])
            time.sleep(0.2)
        if data != []:
            self.maxval = pd.DataFrame(tmp, columns=['time','maxval'])
            self.maxval['time'] = pd.to_datetime(self.maxval['time'], utc=True)
        return tmp


    def linescan(self, rate=.1, amp=2):
        az,el = self.antenna.get_azel()
        self.antenna.move_to(az-amp, el)

        start = datetime.now()
        self.antenna.slew(rate,0)

        tmp = self.measure_until(amp*2 / rate)

        self.antnena.move_to(az, el-amp)

        self.antenna.slew(0,rate)
        self.measure_until(amp*2 / rate, tmp)

        self.antenna.stan()

        return data

    def fit(self, data):

        merged = pd.merge_asof(
            data,
            self.gain,
            on="time",  # timestamp column
            direction="nearest",  # or 'backward', 'forward'
            tolerance=pd.Timedelta("200ms")
        )

        merged = merged.set_index("time")
        data = merged.reset_index().dropna(axis='rows').drop(columns='time').to_numpy()

        azdata = data.take(np.argwhere(np.diff(data[:, 0]) > 0.05).flat, axis=0)
        eldata = data.take(np.argwhere(np.diff(data[:, 1]) > 0.05).flat, axis=0)

        print(azdata)
        print(eldata)

        az, _, azpow = azdata.T
        _, el, elpow = eldata.T

        azmax = az[np.argmax(azpow)]
        elmax = el[np.argmax(elpow)]

        print(azmax, elmax)

        azpars, _ = curve_fit(norm, az, azpow, (azmax, azpow.max(), 1, 0))
        elpars, _ = curve_fit(norm, el, elpow, (elmax, elpow.max(), 1, 0))
        return round(azpars[0],1), round(elpars[0],1)

def doscan():
    parser = argparse.ArgumentParser()

    parser.add_argument("az", type=float, help="az initial ")
    parser.add_argument("el", type=float, help="el initial")
    parser.add_argument("output_file", help="Path to output file")
    args = parser.parse_args()

    if len(sys.argv) == 3:
        az = float(sys.argv[1])
        el = float(sys.argv[2])
    else:
        az = 53.9
        el = 38.9

    az = args.az
    el = args.el
    out = args.output_file

    log.info(f'start position: {az:.1f}/{el:.1f}')

    p = Tracker()
    p.activate()

    log.info('moving to start')
    p.center(az, el)
    while True:
        log.info(f'running linescan')
        data = p.linescan(.2)
        aznew, elnew = p.fit(data)
        if abs(aznew-az) > 3 or abs(elnew-el) > 3:
            log.info(f'warning: new position too far away ({aznew}/{az}, {elnew}/{el}) ')
            break
        az = aznew
        el = elnew
        log.info(f'new maximum at {az:.1f}/{el:.1f}')
        p.center(az, el)
        with open(out, 'a+') as f:
            d = dt.now().strftime('%Y%m%d %H%M%S')
            f.write(f'{d}\t{az}\t{el}\n')
        log.info(f'waiting for 300 seconds')
        time.sleep(300)