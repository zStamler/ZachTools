import datetime
from os import listdir

def namer():
    # create YYYYMMDD substring
    dateString = ''.join(str(datetime.date.today()).split('-'))

    # scan directory for existing files
    fileType = 'dat' # not sure this is the right extension
    ext = listdir('.')
    # restrict the list to only the correct file type
    ext = [f.split('.')[0] for f in ext if fileType in f[-4:]]
    # get the last file in the sequence and make the name one more than that
    if len(ext) > 0:
        ext = ext[-1].split('_')[-1]
        ext = '_' + "{:03d}".format(int(ext)+1)
    # else just start with 001
    else: 
        ext = '_001'
    # format the string and return it
    fName =  dateString + '_acq' + ext + '.' + fileType
    return fName

