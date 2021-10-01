from os import walk, path, system
from sys import argv

p = argv[1]
for root, dirs, files in walk(p):
    fi = [f for f in files if f[-4:] == '.mp4']
    IPpaths = [path.join(root,f) for f in fi]
    fi = [f.split('_') for f in fi]
    print(fi[0])
    fi = [f[0] + '_' + f[1] + '_' + f[3] + '_' + f[4][:-4] + '_' + f[2] + '.mp4' for f in fi]
    OPpaths = [path.join(root,f) for f in fi]
for i,o in zip(IPpaths, OPpaths):
    print('renamed\t' + i,'as \t' + o, '', sep='\n')
    system('mv ' + i + ' ' + o)
    
