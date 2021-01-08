from sys import argv
from os import system, path, walk
from math import ceil
from multiprocessing import Pool, cpu_count

# this is all if we're running this straight from the command line.
# Should be pretty easily adaptable if we're using this as a module inside another program.
# possible arguments -- filepath, startframe, stopframe, targetrate
# input with format "{arg}=val"
if len(argv) > 1:
    argsList = ['filepath']
    for arg in argv[1:]:
        arg = arg.split('=')
        if arg[0] in argsList:
            if arg[0] == 'filepath':
                basePath=arg[1]
        else:
            print('Error: only permitted keywords are', end='')
            [print('"' + st + '"', end=', ') for st in argsList[:-1]]
            print('"' + argsList[-1] + '".', end=' ')
            print("Exiting..")
            exit()

def findTiffs(path):
    tiffExt = ['tif','tiff','TIF','TIFF']
    for root, dirs, files in walk(path):
        fileNameModules = [name.split('.') for name in files]
        validNames = [name for name,mod in zip(files,fileNameModules) if mod[-1] in tiffExt]
        validNumbers = [int(mod.split('_')[-1].split('.')[0]) for mod in validNames]
        break # I think we can get away with this, as long as the walk() method iterates in a consistent order
    return validNames,validNumbers,root

def prevMPwrapper(args):
    previewer(filepath=args[0], targetrate=args[1])

## by default this will just crank out a preview for every found folder of images in the given folder, so we're only gonna want to do this once!
#foundPaths = []
##tiffExt = ['tif','tiff','TIF','TIFF']
#for root, dirs, files in walk(basePath):
#    print("scanning", root, "for mp4..                                                       ", end='\r')
#    if len(files) == 0:
#        continue
#    for f in files:
#        if f[-4:] == '.mp4':
#            foundPaths.append(root)
#            continue
#
#with open(path.join(basePath,'movDirs.txt'), 'w') as f:
#    for pth in foundPaths:
#        f.write('%s\n' % pth)
#exit()
for root,_,files in walk(basePath):
    allFiles = files
allFiles = [(f.split('_')[:-2],f) for f in allFiles]
for f in allFiles:
    f[0].pop(2)
allFiles = [('_'.join(f[0]),f[1]) for f in allFiles]
newFolders = list(dict.fromkeys([f[0] for f in allFiles]))
newPaths = [path.join(basePath,nf) for nf in newFolders]
[system("mkdir " + np) for np in newPaths]
for nf in newFolders:
    for f in allFiles:
        if f[0] == nf:
            print(path.join(basePath,nf,f[1]))
            system("sudo mv " + path.join(basePath,f[1]) + " " + path.join(basePath,nf,f[1]))
