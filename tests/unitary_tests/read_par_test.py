import brukerIO
from shutil import copyfile

sample = "../data/qcpmg/4/pdata/1/"
fresh = "../data/qcpmg/4/" + 'acqu'
backup = "../data/qcpmg/4/" + 'acqu.bak'

copyfile(backup, fresh)

dat = brukerIO.dataset(brukerIO.splitprocpath(sample))

P = ["P 1", 
"L 31", 
"SPNAM 8",
"BF1", 
"NS", 
"AUNM", 
"LOCKED", 
"L 64",
"TOTO",
]
for par_name in P :
    try:
        par = dat.readacqpar(par_name, status=False, dimension=1)
        print(par_name, type(par), par)
    except Exception as e:
        print(e)
