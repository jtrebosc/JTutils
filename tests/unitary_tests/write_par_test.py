import brukerIO
from shutil import copyfile

sample = "../data/qcpmg/4/pdata/1/"
fresh = "../data/qcpmg/4/" + 'acqu'
backup = "../data/qcpmg/4/" + 'acqu.bak'
copyfile(backup, fresh)

dat = brukerIO.dataset(brukerIO.splitprocpath(sample))

P = [
"P 1", 
"L 31", 
"SPNAM 8",
"BF1", 
"NS", 
"AUNM", 
"LOCKED", 
"L 64",
"TOTO",
]
values = [
1.5,
5,
"test_shape",
180.2,
23,
"toto",
True,
7,
'bidule',
]
for par_name, value in zip(P, values) :
    try:
        dat.writeacqpar(par_name, value, status=False, dimension=1)
        par = dat.readacqpar(par_name, status=False, dimension=1)
        if par == value: 
            print(f"SUCCESS: {par_name} -> {par}={value}")
        else:
            print(f"FAILURE: {par_name} -> {par} != {value}")
    except Exception as e:
        print(f"for parameter {par_name}:")
        print(e)
