# to convert to 8-bit TIFF files that have been accidentally saved as 12-bit
# usage: python bitCut.py /path/or/paths/to/images

import numpy as np
from PIL import Image
from os import path, walk, mkdir
import sys

basePath = sys.argv[1:]
for bp in basePath:
    for root, dirs, files in walk(bp):
        files = [f for f in files if f.split(".")[-1] == "tif"]
        OPdir = path.join(root,"bit_fix")
        try:
            mkdir(OPdir)
        except OSError:
            nop=True
        for f in files:
            IPpath = path.join(root,f)
            OPpath = path.join(OPdir,f)
            im = Image.open(IPpath)
            img = np.array(im).astype(np.uint16)
            img = np.floor(np.divide(img,2**4)).astype(np.uint8)
            im = Image.fromarray(img)
            im.save(OPpath)

