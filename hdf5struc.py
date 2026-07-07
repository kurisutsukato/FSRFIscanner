import h5py

hfile = 'data/session/pos.h5'
#hfile = 'data/session/20260629-225115_sband.h5'

import h5py
import numpy as np

def print_attrs(obj, indent):
    for name, value in obj.attrs.items():
        arr = np.asarray(value)
        print(f"{indent}@{name}: dtype={arr.dtype}, shape={arr.shape}")

def print_group(group, indent=0):
    prefix = "  " * indent

    for key, item in group.items():
        if isinstance(item, h5py.Group):
            print(f"{prefix}{key}/")
            print_attrs(item, prefix + "  ")
            print_group(item, indent + 1)
        else:
            print(f"{prefix}{key}  shape={item.shape}, dtype={item.dtype}")
            print_attrs(item, prefix + "  ")

with h5py.File(hfile, "r") as f:
    print("attributes:")
    print_attrs(f, "  ")
    print_group(f)
