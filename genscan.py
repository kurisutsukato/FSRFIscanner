import numpy as np

def gen(output):
    '''
    generates an antenna control file
    :param output: output filename
    '''

    azinit = 0
    elinit = 2

    el = np.linspace(0,np.pi/2,88)[2::2]
    az = 1/np.cos(el)
    azspeed = az*0.5
    azspeed[azspeed>3] = 3

    coords = [[('az', 360, f'{q:.2f}'), ('el', 1, .1),('az',-360, f'{q:.2f}'), ('el', 1, .1)] for q in azspeed.tolist()]
    coords = np.asarray([q for sublist in coords for q in sublist])

    with open(output, 'w') as f:
        print(f'{azinit},{elinit}', file=f)
        np.savetxt(f, coords, fmt="%s", delimiter=',')

if __name__ == '__main__':
    gen('fullsky.cnf')
