from sys import argv
from os import system, path, walk
from math import ceil
from multiprocessing import Pool, cpu_count
from distutils.util import strtobool

# default vals
targetFrameRate=30
basePath=''
symlinks=False
# this is all if we're running this straight from the command line.
# Should be pretty easily adaptable if we're using this as a module inside another program.
# possible arguments -- input_path, startframe, stopframe, targetrate
# input with format "{arg}=val"
if len(argv) > 1:
    argsList = ['input_path', 'startframe', 'stopframe', 'targetrate', 'symlinks']
    for arg in argv[1:]:
        arg = arg.split('=')
        if arg[0] in argsList:
            if arg[0] == 'input_path':
                basePath=arg[1]
            elif arg[0] == 'startframe':
                start=int(arg[1])
            elif arg[0] == 'stopframe':
                stop=int(arg[1])
            elif arg[0] == 'targetrate':
                targetFrameRate=int(arg[1])
            elif arg[0] == 'symlinks':
                symlinks=bool(strtobool(arg[1]))
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
        break # I think we can get away with this, as long as the walk() method iterates in a a consistent order
    return validNames,validNumbers,root

def prevMPwrapper(args):
    previewer(input_path=args[0], targetrate=args[1])

# by default this will just crank out a preview for every found folder of images in the given folder, so we're only gonna want to do this once!
foundPaths = []
tiffExt = ['tif','tiff','TIF','TIFF']
for root, dirs, files in walk(basePath, followlinks=symlinks):
    print("scanning", root, "for tifs..                                                       ", end='\r')
    if len(files) == 0:
        continue
    done = False
    for ext in tiffExt:
        for f in files:
#            print(f)
            if ext in f:
                done = True
#                print("                                                                         ", end='\r')
                break
        if done:
            break
    if done:
        foundPaths.append(root)
        continue
#with open(path.join(basePath,'imgDirs.txt'), 'w') as f:
#    for pth in foundPaths:
#        f.write('%s\n' % pth)
#with open(path.join(basePath,'imgDirs.txt'), 'r') as f:
#    foundPaths = f.readlines()
foundPaths = [pth.split('\n')[0] for pth in foundPaths]

def previewer(input_path='', **kwargs):
    basePath = input_path
    start = None
    end = None
    targetFrameRate = 30
    for key,value in kwargs.items():
        if key == 'startframe':
            start = value
        elif key == 'stopframe':
            end = value
        elif key == 'targetrate':
            targetFrameRate = value
        else:
            print('previewer: Incorrect argument found! Possible keywords are "input_path", "start", "end", and "targetrate".  Exiting..')
            return None
    
    # create the output directory if it doesn't yet exist (eventually this should probably raise a warning if it's already there)
    # NOTE: if we want this to work on Windows we need to create this folder through OS instead of using a system call
    OPdir = path.join(basePath,"PREVIEW")
    OPname = ''
    while True:
        OPname = path.split(path.split(basePath)[0])
        if OPname[-1] != '':
            OPname = OPname[-1]
            break
    try:
        system("mkdir " + OPdir)
    except FileError:
        nop=True

    # get the list of filenames
    # relies on file extension
    validNames, validNumbers, _ = findTiffs(basePath)
#    tiffExt = ['tif','tiff','TIF','TIFF']
#    for root, dirs, files in walk(basePath):
#        fileNameModules = [name.split('.') for name in files]
#        validNames = [name for name,mod in zip(files,fileNameModules) if mod[-1] in tiffExt]
#        validNumbers = [int(mod.split('_')[-1].split('.')[0]) for mod in validNames]
#        break # I think we can get away with this, as long as the walk() method iterates in a a consistent order
    prefix = validNames[0].split('_')[0] + '_'
    suffix = '.' + validNames[0].split('.')[-1]
    try:
        start = max(min(validNumbers),start)
    except (TypeError,NameError) as NoStartError:
        start = min(validNumbers)
    try:
        end = min(max(validNumbers),end)
    except (TypeError,NameError) as NoEndError:
        end = max(validNumbers)
    OPname = OPname + '_fr_' + str(start) + '-' + str(end) + '.mp4'

    def imgStr(prefix,num,suffix):
        return prefix + "{:06d}".format(num) + suffix

    skipFrames = ceil(155/targetFrameRate)
    fRate = 155/skipFrames
    print('Starting frame:', start, '\nStopping frame:', end, '\nSkip frames:', skipFrames)
    print('Actual target frame rate: ' + str(fRate))

    frameList = [num for num in range(start,end,skipFrames)]
    imgStrs = [imgStr(prefix,num,suffix) for num in frameList]
    # create symlinks for all the images in series
    [system("ln -s " + path.join(basePath,pth) + " " + path.join(OPdir,pth)) for pth in imgStrs]
    # write the list of files to be encoded
    with open(path.join(OPdir,'frameList.txt'), 'w') as f:
        for pth in imgStrs:
            f.write('file %s\n' % pth)
            f.write('duration ' + str(1/fRate) + '\n')
        f.write('file %s\n' % imgStrs[-1]) # this has to be here for some reason, per the ffmpeg documentation

    system("ffmpeg -f concat -probesize 200M -i " + path.join(OPdir,"frameList.txt") + " -vsync vfr " + path.join(OPdir,OPname))
    [system("rm " + path.join(OPdir,pth)) for pth in imgStrs]


args = [(path,targetFrameRate) for path in foundPaths]
# this should be a comfortable enough paralellism since ffmpeg multithreads anyway
numProcs = ceil(cpu_count()/2)
if __name__ == '__main__':
    with Pool(numProcs) as p:
        p.map(prevMPwrapper, args)

