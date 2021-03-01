from os import path,system,walk
from sys import argv

IPpath = argv[1]
if len(argv) > 2:
    cornerFileName = argv[2]
else:
    cornerFileName = "corners.dat"

for root, dirs, files in walk(IPpath):
    cornerFile = [f for f in files if f == cornerFileName]
    try:
        cornerFile = cornerFile[0]
    except IndexError:
        continue
    nameTokens = root.split('/')
    while nameTokens[0][:3] != 'CAM' or len(nameTokens) > 2:
        nameTokens.pop(0)
    cornerFile = nameTokens[0] + '_' + nameTokens[1] + '_' + cornerFile
    print("Copied: " + path.join(root,cornerFileName) + " to: " + path.join(IPpath,cornerFile))
    system("cp " + path.join(root,cornerFileName) + ' ' + path.join(IPpath,cornerFile))

