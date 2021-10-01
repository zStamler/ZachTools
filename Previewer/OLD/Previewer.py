from sys import argv
from os import system, path, walk
from math import ceil
from multiprocessing import Pool, cpu_count
from distutils.util import strtobool
import pickle

# default vals
targetFrameRate=30
basePath=''
symlinks=False
# this is all if we're running this straight from the command line.
# Should be pretty easily adaptable if we're using this as a module inside another program.
# possible arguments -- input_path, startframe, stopframe, targetrate
# input with format "{arg}=val"
if len(argv) > 1:
    argsList = ['input_path', 'output_path', 'startframe', 'stopframe', 'targetrate', 'symlinks']
    for arg in argv[1:]:
        arg = arg.split('=')
        if arg[0] in argsList:
            if arg[0] == 'input_path':
                basePath=arg[1]
            elif arg[0] == 'output_path':
                basePath_OP=arg[1]
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
    previewer(input_path=args[0], output_path=args[1], targetrate=args[2])

# by default this will just crank out a preview for every found folder of images in the given folder, so we're only gonna want to do this once!
foundPaths = []
try:
    print('Generating previews from base folder ' + basePath + ' to reside in output folder ' + basePath_OP)
except:
    print('Must specify input and output paths')
    exit()
tiffExt = ['tif','tiff','TIF','TIFF']
if True: # should usually be True, False for debugging only
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
    OPpaths = [pth.split('/')[-3:] for pth in foundPaths]
    OPpaths = [path.join(basePath_OP,pth[1],pth[0] + '_' + pth[1] + '_' + pth[2] + '.mp4') for pth in OPpaths]
    [system("mkdir " + path.join(basePath_OP,"CAM" + str(ii))) for ii in range(1,4)]
    #exit()
    foundPaths = [pth.split('\n')[0] for pth in foundPaths]
else:
    if False:
        pickle.dump((OPpaths,foundPaths),open('dev.p', 'wb'))
        exit()
    else:
        (OPpaths,foundPaths) = pickle.load(open('dev.p','rb'))
#

def previewer(input_path='', output_path='', **kwargs):
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
    
    # relies on file extension
    validNames, validNumbers, _ = findTiffs(basePath)
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
    OPname = output_path.split('/')[-1]
    OPdir = '/' + path.join(*output_path.split('/')[:-1])
    lndir = path.join(OPdir,OPname.split('.')[0])
    system('mkdir ' + lndir)

    def imgStr(prefix,num,suffix):
        return prefix + "{:06d}".format(num) + suffix

    skipFrames = ceil(155/targetFrameRate)
    fRate = 155/skipFrames
    print('Starting frame:', start, '\nStopping frame:', end, '\nSkip frames:', skipFrames)
    print('Actual target frame rate: ' + str(fRate))

    frameList = [num for num in range(start,end,skipFrames)]
    imgStrs = [imgStr(prefix,num,suffix) for num in frameList]
    # create symlinks for all the images in series
    [system("ln -s " + path.join(basePath,pth) + " " + path.join(lndir,pth)) for pth in imgStrs]
    # write the list of files to be encoded
    
    with open(path.join(lndir,'frameList.txt'), 'w') as f:
        for pth in imgStrs:
            f.write('file %s\n' % pth)
            f.write('duration ' + str(1/fRate) + '\n')
        f.write('file %s\n' % imgStrs[-1]) # this has to be here for some reason, per the ffmpeg documentation
    system("ffmpeg -f concat -probesize 200M -i " + path.join(lndir,"frameList.txt") + " -vsync vfr " + path.join(OPdir,OPname))
    system('rm -r ' + lndir)


args = [(IPpath,OPpath,targetFrameRate) for IPpath,OPpath in zip(foundPaths,OPpaths)]

# this should be a comfortable enough paralellism since ffmpeg multithreads anyway
numProcs = ceil(cpu_count()/2)
if __name__ == '__main__':
    with Pool(numProcs) as p:
        p.map(prevMPwrapper, args)

