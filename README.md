FSRFIscanner
------------

FSRFIscanner is a collection of Python scripts that enables a Field
System–controlled radio telescope to be used as an RFI (Radio Frequency Interference)
scanner.

`antenna_control.py`, running on the Field System computer, continuously
records the antenna pointing position along with a UTC timestamp and
stores the data in an HDF5 file.

`analyzer.py` can be run on any computer with TCP/IP access to a
VISA-compatible spectrum analyzer. It continuously acquires the current
spectrum trace, timestamps it in UTC, and stores the data in an HDF5
file.

`vis.py` combines the antenna pointing and spectrum datasets by matching
their timestamps, reduces the data through binning, and
generates spectral intensity maps. It provides interactive tools for
exploring the data, allowing the user to filter by frequency range,
azimuth/elevation coordinates, or both.

The latter two scripts run on linux and windows, the former naturally on the
Field System linux computer.

Technical prerequisites
-----------------------

The antenna control code relies on the following snap commands:

    antenna=PRES,az,el
    antenna=SLEW,azspeed,elspeed
    antenna=ACTI
    antenna=STAN

if your antenna control uses other commands, you will need to modify `antenna_control.py`
or implement a subclass of `antenna_control.Antenna` that
provides the required command mappings.

Communication with the spectrum analyzer is performed using SCPI commands sent
via VISA. Most modern spectrum analyzers support this interface. If your
instrument uses a different communication protocol, you will need to adapt the
implementation or create a subclass of `analyzer.Analyzer` that implements the
appropriate communication methods.

Installation
------------

The software has been tested with python3 (>3.7) but it should be possible to
run at least `antenna_control.py` with python2. Please ask me if you need help. 
The required python packages can easily be installed via `pip`. 

Create a virtual python environment

    python -m venv .venv
    . .venv/bin/activate

then install the dependencies with:

    python -m pip install -r requirements.txt

To read the antenna position from the Field System shared memory, the software must
know which station-code variables contain the azimuth and elevation values and where
these variables are located within the shared memory structure.

The script `stcom.py` assists with this task. Under the hood it calls a C compiler
which is usually installed by default on a field system computer. It looks for `stcom.h` either in its
standard location (`/usr2/st/include`) or in the current working directory. When
executed successfully, it generates a `.env` file containing the shared-memory
offsets of the relevant azimuth and elevation variables. You need to provide the variable
names as command line argument, e.g.

    python stcom.py Azactpos Elactpos

Adapt the variable names according to your `stcom.h`.
 
These offsets are subsequently used by antenna_control.py to access the antenna
position data directly from shared memory.


Using the antenna control
-------------------------

`antenna_control.py` is executed from the command line. Before running it,
a configuration file describing the desired scan pattern must be created.

The configuration file uses the following format.

The first line specifies the initial antenna position as a comma-separated
azimuth/elevation pair:

    az_init,el_init

Each subsequent line defines a relative antenna movement and the
corresponding slew rate:

    axis,offset,speed

where:

- `axis` is either `az` (azimuth) or `el` (elevation),
- `offset` is the relative movement in degrees (positive or negative),
- `speed` is the absolute slew rate in degrees per second.

For example,

    az,-40,0.4

moves the antenna by −40° in azimuth at a slew rate of 0.4°/s.

Similarly,

    el,1,0.1

moves the antenna by +1° in elevation at a slew rate of 0.1°/s.

The commands are executed sequentially in the order in which they appear
in the configuration file, thereby defining the complete scanning
pattern. The `gensky.py` script generates a full sky scan (saved as `fullsky.cnf`)
starting at 0,2 az/el position.

Start the scan in simulation mode (no commands are sent to the anntena) by executing

    python antenna_control.py fullsky.cnf

Once you are sure everything is alright, start the real scan with

    python antenna_control.py fullsky.cnf --nosim

Using the analyzer interface
----------------------------

The `analyzer.py` scripts takes a configuration file as first parameter and a  VISA device address as 
second mandatory parameter, e.g.:

    python analyzer.py sband.cnf TCPIP0::10.10.10.152::INSTR

with `sband.cnf`:

    START_FREQ=20e6
    STOP_FREQ=500e6
    POINTS=1001
    RBW=1e6
    MAXHOLD=2

The configuration consists of `parameter=value` pairs. The following parameters are supported:

- PTS - number of points of the trace
- RBW - resolution bandwidth (Hz)
- START_FREQ - start frequency (Hz)
- STOP_FREQ - stop frequency (Hz)
- CENTER - center frequency (Hz)
- SPAN - frequency span (Hz)
- LEVEL - reference level (dB)
- MAXHOLD - maxhold time (s)

Any subset of these parameters may be specified, and the configuration file may even be empty.
Parameters that are omitted will retain their current values on the instrument, allowing the
existing analyzer configuration to be used unchanged.

Run a scan
----------

Start both scripts at roughly the same time to generate the position and spectra datasets. When the scan
finishes, stop the analyzer script with CTRL-C.

Visualization
-------------

