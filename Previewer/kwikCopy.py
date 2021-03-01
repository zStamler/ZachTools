from os import walk,path,system

for root,dirs,files in walk("."):
    tt_one = [path.join(root,d) for d in dirs if d[:4] == "2021"]
    if len(tt_one) > 0:
        break
allFiles = []
for root,dirs,files in walk("../PREVIEWS/"):
    allFiles = allFiles + [path.join(root,f) for f in files if f[-4:] == ".mp4"]
dates = [(f.split('/')[-1]).split('_')[0] for f in allFiles]
files_with_dates = [(f,d) for f,d in zip(allFiles,dates)]

for d in tt_one:
    date = (d.split('/')[-1]).split('_')
    date = date[0]
    dateFiles = [f[0] for f in files_with_dates if f[1] == date]
    system("mkdir " + path.join(d,"REAL_TIME"))
    for df in dateFiles:
        system("cp " + df + " " + path.join(d,"REAL_TIME"))
