import brukerIO
from shutil import copyfile

sample = "../data/qcpmg/4/pdata/1/"
fresh = "../data/qcpmg/4/" + 'acqu'
backup = "../data/qcpmg/4/" + 'acqu.bak'

copyfile(backup, fresh)

dat = brukerIO.dataset(brukerIO.splitprocpath(sample))

PA = ["P 1", 
"L 31", 
"SPNAM 8",
"BF1", 
"NS", 
"AUNM", 
"LOCKED", 
"L 64",
"DTYPA",
"TOTO",
]
PP = ["USERP1", 
"TOTO",
]
print("reading acquisition non status parameter")
for par_name in PA :
    try:
        par = dat.readacqpar(par_name, status=False, dimension=1)
        print(par_name, type(par), par)
    except Exception as e:
        print(f"{par_name} triggered an exception")
        print(e)
print("reading acquisition status parameter")
for par_name in PA :
    try:
        par = dat.readacqpar(par_name, status=True, dimension=1)
        print(par_name, type(par), par)
    except Exception as e:
        print(f"{par_name} triggered an exception")
        print(e)
print("reading processing non status parameter")
for par_name in PP :
    try:
        par = dat.readprocpar(par_name, status=False, dimension=1)
        print(par_name, type(par), par)
    except Exception as e:
        print(f"{par_name} triggered an exception")
        print(e)
print("reading processing status parameter")
for par_name in PP :
    try:
        par = dat.readprocpar(par_name, status=True, dimension=1)
        print(par_name, type(par), par)
    except Exception as e:
        print(f"{par_name} triggered an exception")
        print(e)
