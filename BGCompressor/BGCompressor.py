# REQUIRES VALID LIBTIFF INSTALLATION ON HOST MACHINE
# tested with Pillow 7.2.0, Python 3.7.6
# Usage:
#   Input arguments:
#       basePath thresholdSize(in kB, optional, default 6000) deleteRaw(bool, optional, default=False) compressionScheme(optional)
#   example: python BGCompressor.py "/Volumes/NASMountPath" 8000 False 'LZW'
# App will scan the specified drive for any TIFFs that are larger than the threshold size, then compress them using specified scheme (packbits default).
# If deleteRaw=True, will delete the original images after verifying validity of output files (probably best to run false until we can test this extensively).
# compressionScheme options:
#   'packbits'
#   'deflate'
#   'lzw'
# for PIL support, refer to LIBTIFF interface source code at:
# https://pillow.readthedocs.io/en/stable/_modules/PIL/TiffTags.html

import numpy as np
import os
from sys import argv
from PIL import Image, TiffImagePlugin
from multiprocessing import Pool, cpu_count, set_start_method
from time import sleep, time
from shutil import copyfile, rmtree

startTime = time()
thrDefault = 6000
thresholdSize = thrDefault
headless = False
deleteRaw = False
cScheme = 'packbits'
args = tuple(argv[1:])
validSchemes = ['packbits', 'deflate', 'LZW']
validOptions = ['headless']
# verify args and throw error if no good. Replace defaults if appropriate.

if len(args) < 1:
    print("Error: not enough arguments! Need at least root-level filepath (str) and threshold size in kB (int).")
    exit()
# verify valid filepath
if type(args[0]) is not str:
    raise ValueError('Argument 1 must be a string pointing to a valid filepath.')
with open(os.path.join(args[0], ".pathTest.py"), 'wb') as f:
    basePath = args[0]
    print('Using path ' + basePath)
os.remove(os.path.join(args[0], ".pathTest.py"))
# verify our optional arguments. Lucky for us they're all different types
if len(args) > 1:
    for arg in args[1:]:
        try:
            # verify threshold val, use 500kB and 20000kB as lower/upper limits respectively
            # our files tend to be ~9100kB uncompressed, but can't hurt to have a little flex
            arg = int(arg)
            thresholdSize = min(max(500,arg),20000)
        except ValueError:
            if arg == 'True':
                deleteRaw = True
            elif arg == 'False':
                deleteRaw = False
            elif arg in validSchemes:
                cScheme = arg
            elif arg in validOptions:
                if arg == 'headless':
                    headless = True
            else:
                raise TypeError('Compression scheme must be one of the following: ' + str(validSchemes))

print("Using threshold val " + str(thresholdSize) + "kB.")
print("Delete originals:", deleteRaw)
print("Using", cScheme, "compression scheme.")
if not headless:
    while True:
        print("Proceed? [y/n]:")
        doit = input()
        if doit == 'y' or doit == 'Y':
            break
        elif doit == 'n' or doit == 'N':
            print('Process cancelled by user.                 ')
            exit()

if cScheme == 'packbits':
    cStr = 'packbits'
elif cScheme == 'deflate':
    cStr = 'tiff_deflate'
elif cScheme == 'LZW':
    cStr = 'tiff_lzw'


def emptyListBuster(l):
    if type(l) == list:
        if len(l) == 0:
            return ''
        elif len(l) == 1 and l[0][0] == '@':
            return ''
    return l

# build a list of all TIF files and their paths in base dir
tiffExt = ['tif', 'TIF', 'tiff', 'TIFF']
allIPPaths = []
for (dirpath, dirnames, filenames) in os.walk(basePath):
    print('Gathering files in dir', dirpath, end='\r', flush=True)
    for f in filenames:
        # also weed out files that start with "._ due to some stupid bug we're getting :/"
        if f[:2] == "._":
            continue
        # weed out any files with wrong extension
        checkTiff = f.split('.')
        if checkTiff[-1] in tiffExt:
            dirpath = emptyListBuster(dirpath)
            dirnames = emptyListBuster(dirnames)
            try:
#                print(dirpath,dirnames,f)
                allIPPaths.append(os.path.join(dirpath, dirnames, f))
            except TypeError:
                # there was a list in the path somewhere
                typeList = tuple([type(obj)==list for obj in (dirpath,dirnames)]) 
                if True in typeList:
                    if typeList[0] and typeList[1]:
                        fullpaths = [[os.path.join(dp,dn,f) for dp in dirpath] for dn in dirnames]
                    elif typeList[0]:
                        fullpaths = [os.path.join(dp, dirnames, f) for dp in dirpath]
                    elif typeList[1]:
                        fullpaths = [os.path.join(dirpath, dn, f) for dn in dirnames]
                else:
                    fullpaths = os.path.join(dirpath,dirnames,f)
                fullpaths = [path for path in fullpaths if os.path.getsize(path)/1000 >= thresholdSize]
                allIPPaths.append(fullpaths)
        else:
            continue

#allIPPaths = [path for path in allIPPaths if os.path.getsize(path)/1000 >= thresholdSize]
if len(allIPPaths) == 0:
    print("\nNo uncompressed files found in target directory!")
    exit()
with open(os.path.join(basePath,"compressedFiles.log"),'w') as f:
    for fpath in allIPPaths:
        f.write("%s\n" % fpath)

# build a list of destinations for all those TIFFs
# if we're not deleting the originals they'll all go in a dir called COMP in whatever folder they were in
# if we are they'll still go there, but we'll later delete the originals, move the comps into the vacated folder, then delete the COMP folder
ps = [os.path.split(p) for p in allIPPaths]
allOPPaths = [os.path.join(p[0],'COMP',p[1]) for p in ps]
sepr = [p.split(os.path.sep)[:-1] for p in allOPPaths]
if allOPPaths[0][0] == os.path.sep:
    uniquePaths = np.unique([os.path.join(os.path.sep + s[0],*s[1:]) for s in sepr])
else:
    uniquePaths = np.unique([os.path.join(s[0],*s[1:]) for s in sepr])
print('')
for up in uniquePaths:
    try:
        os.mkdir(up)
        print('Created COMP folder in ', up)
    except FileExistsError:
        continue


def ProcessFileFromPath(args):
    (src,dest,comp,thresh) = args
    src = os.path.abspath(src)
    dest = os.path.abspath(dest)
    # get file size, compare to threshold
    srcSize = os.path.getsize(src)/1000
    if srcSize >= thresh:
        TiffImagePlugin.WRITE_LIBTIFF = True
        f = Image.open(src)
        if srcSize > 15e3:
            fl = np.asarray(f).flatten()
            # note that though the images are technically 16-bit, they are actually encoded as 12, hence the shift of 4
            fl = np.right_shift(fl,4).astype(np.uint8) 
            f = f.convert('L')
            f.putdata(fl)
        f.save(dest, compression=comp)
        print('Saved: ', dest, '                                        ', end='\r', flush=True)
        f.close()
        destSize = os.path.getsize(dest)/1000
        f = Image.open(dest)
        f.verify()
        f.close()
    else:
        copyfile(src,dest)
        destSize = os.path.getsize(dest)
    return (srcSize,destSize)

def PFFPChunks(chunk):
    return [ProcessFileFromPath(f) for f in chunk]


print('')
paths = [(ip,op,cStr,thresholdSize) for ip,op in zip(allIPPaths,allOPPaths)]
numProcs = cpu_count() - 2
chunkSize = min(64,np.ceil(len(paths)/numProcs).astype(int))
paths = [paths[x:x+min(chunkSize,(len(paths)-x))] for x in range(0,len(paths),chunkSize)]
if __name__ == '__main__':
    with Pool(numProcs) as p:
#        OP = p.map(ProcessFileFromPath,paths)
        OP = p.map(PFFPChunks,paths)

OPFlat = [tup for sub in OP for tup in sub]
#totalSrc = [tup[0] for tup in OP]
totalSrc = [tup[0] for tup in OPFlat]
totalSrc = sum(totalSrc)
#totalDest = [tup[1] for tup in OP]
totalDest = [tup[1] for tup in OPFlat]
totalDest = sum(totalDest)
print("\nTotal size of src files: " + str(totalSrc) + "kB")
print("Total size of dest files: " + str(totalDest) + "kB")
print("Time:", time()-startTime)

if deleteRaw:
    
    def CopyFile(args):
        (src,dest) = args
        os.remove(src)
        copyfile(dest,src)
        print('Copied: ', dest, '                                                   ', end='\r', flush=True)

#    def BatchCopy(args):
#        [CopyFile(a) for a in args]

    paths = [(ip,op) for ip,op in zip(allIPPaths,allOPPaths)]
#    paths = [paths[x:x+min(chunkSize,(len(paths)-x))] for x in range(0,len(paths),chunkSize)]
    if __name__ == '__main__':
        with Pool(numProcs) as p:
            OP = p.map(CopyFile,paths)
    [rmtree(up) for up in uniquePaths]
    print("\nDeleted temporary COMP folder(s) and replaced uncompressed files!")

print("Finished!")
print("Total time:", time()-startTime)














