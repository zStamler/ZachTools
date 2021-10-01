from os import path, walk
from sys import argv
from time import sleep

# run script with path to Cam3 download folder as first arg and total number of acqs as second

pth = argv[1]
numAcqs = int(argv[2])

def readConfig(pth):
    with open(pth, 'r') as f:
        lines = f.readlines()
    stopIdxLine = lines[15].split("=")
    if stopIdxLine[0] != "StopIdx":
        for line in lines:
            if line.split("=")[0] == "StopIdx":
                return line.split("=")[1]
    else:
        return stopIdxLine[1]

lastAcqFound=False
lastAcqPath=""
while not lastAcqFound: 
    for root,dirs,files in walk(pth):
        for d in dirs:
            if "acq_" in d:
                acqNum = int(d.split("_")[-1])
                if acqNum == numAcqs:
                    lastAcqFound=True
                    lastAcqPath = path.join(root,d)
                    lastAcqConf = path.join(root,d,"_config.xsv")

# stopIdx is a string, not an int!
stopIdx = None
while stopIdx is None:
    try:
        stopIdx = readConfig(lastAcqConf)
    except FileNotFoundError:
        nop = True
    except IndexError:
        nop=True
lastFilePresent=False
while not lastFilePresent:
    for root,dirs,files in walk(lastAcqPath):
        fileNums = [int(f.split('.')[0].split('_')[-1]) for f in files if ".tif" in f]
        try:
            if fileNums[-1] == int(stopIdx):
                lastFilePresent=True
                break
            else:
                sleep(10)
        except IndexError:
            nop=True
print("done!")





