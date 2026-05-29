from struct import unpack
from sysv_ipc import SharedMemory, ftok

st = SharedMemory(ftok("/usr2/st", 2))

def read_shm(offset, num=1, tp='f'):
    dtsize = {'f':4, 'd':8, 'i':4, 'l':4, 'h':2}
    return unpack('{:d}{:s}'.format(num, tp), st.read(num*dtsize[tp.lower()], offset=offset))

