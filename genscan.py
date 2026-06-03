import numpy as np
import sys

el = np.linspace(0,np.pi/2,88)[2::2]
az = 1/np.cos(el)
azspeed = az*0.5
azspeed[azspeed>3] = 3

coords = [[('az', 360, f'{q:.2f}'), ('el', 1, .1),('az',-360, f'{q:.2f}'), ('el', 1, .1)] for q in azspeed.tolist()]
#for n,x in enumerate(coords):
#    print(f'{n:02d} {x}')
coords = np.asarray([q for sublist in coords for q in sublist])
#coords = [('el', 1, 1),('az', 10, .2), ('el', 1, 1),('az',-10, .2)]*10

tot = 2
for a,b,c in coords:
    if a == 'el':
        tot += float(b)
print(tot)

with open(sys.argv[1], 'w') as f:
    print('0,2', file=f)
    np.savetxt(f, coords, fmt="%s", delimiter=',')

