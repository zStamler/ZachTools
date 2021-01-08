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



with open(path.join(basePath,'movDirs.txt'), 'r') as f:
    foundPaths = f.readlines()
foundPaths = [pth.split('\n')[0] for pth in foundPaths]
prevNames = []
for pth in foundPaths:
    for root,_,files in walk(pth):
        for f in files:
            if f[-4:] == ".mp4":
                prevNames.append((f,root))
                print("Appended", f, "                              ", end='\r')
prefs = [r[1].split('/')[-2] for r in prevNames]
sufs = [r[0].split('_') for r in prevNames]
sufs = [s[-2] + '_' + s[-1] for s in sufs]
newNames = [p + '_' + s for p,s in zip(prefs,sufs)]
newPaths = [path.join(basePath,"Previews",nm) for nm in newNames]
oldPaths = [path.join(nm[1],nm[0]) for nm in prevNames]
system("mkdir " + path.join(basePath,"Previews"))
[system("mv " + op + " " + np) for op,np in zip(oldPaths,newPaths)]
