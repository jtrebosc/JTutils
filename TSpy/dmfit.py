import os
import subprocess
import sys

# test if exists prop_dir/JTutils/dmfit
# read dmfit_location line
# assign the location to dmfit_path var
# if does not exists : launch setup dialog
# option to launch several versions
# use of wine prefix
# what structure for file dmfit ?
# FILEPATH=version:/path/to/exec;version:path/to/exec
# WINEPREFIX=
# WINEPATH=
# what else ?
# setup option if no working dmfit :
# is setup file present ?
# are intialised variables valid ?
# if not : 
# search for wine, search for dmfit
# ask for prefix...
# need add all kind of check 


def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def get_os_version():
    ver = sys.platform.lower()
    if ver.startswith('java'):
        import java.lang
        ver = java.lang.System.getProperty("os.name").lower()
    return ver

prop_dir = os.getenv('USERHOME_DOT_TOPSPIN', "not defined")
environment_var = os.environ.copy()
dmfit_path = dict()
with open(os.path.join(prop_dir,'JTutils','dmfit.path'), 'r') as f:
    for line in f:
        line = line.strip()
        if line.lstrip()[0] == '#': continue
        var, path = line.split('=')
        if var == 'DMFIT_PATH':
            versions = path.split(';')
            for ver in versions:
                key, path = ver.split(':')
                dmfit_path[key] = path
                default_key = key
        if var == 'WINEPREFIX':
            environment_var[var] = path
            

WIN_dmfit_path = r'C:/Program Files (x86)/dmfit/dm2011.exe'
LIN_dmfit_path = r'/home/trebosc/.wine32/drive_c/Program Files/dmfit2015/dm2015.exe'
MAC_dmfit_path = r'.wine/drive_c/Program Files/dmfit2015/dm2015.exe'
        
#setup the following path to dmfit executable and to wine executablefor linux and mac os x

MAC_wine = r'/usr/local/bin/wine'
LIN_wine = r'/usr/bin/wine'
wine_path = which('wine')
# check if wine is exe
print wine_path


OS = get_os_version()


if OS.startswith('mac'):
    # for Linux with wine
    wine = os.path.normpath(MAC_wine)
    home = os.getenv("HOME")
    dmfit_location = os.path.join(os.path.normpath(home),os.path.normpath(MAC_dmfit_path))
    if not os.path.exists(wine):
        MSG("""wine executable not not found at 
               %s
               Please update MAC_wine variable in this script
              """ % (wine,))
        EXIT()
    if not os.path.exists(dmfit_location):
        MSG("""dmfit not not found at 
               %s
               Please update MAC_dmfit_path variable in this script
              """ % (dmfit_location,))
        EXIT()
        
elif OS.startswith('linux'):
    # for Linux with wine
    wine = os.path.normpath(LIN_wine)
    home = os.getenv("HOME")
    dmfit_location = os.path.join(os.path.normpath(home),os.path.normpath(LIN_dmfit_path))
    if not os.path.exists(wine):
        MSG("""wine executable not not found at 
               %s
               Please update LIN_wine variable in this script
              """ % (wine,))
        EXIT()
    if not os.path.exists(dmfit_location):
        MSG("""dmfit not not found at 
               %s
               Please update LIN_dmfit_path variable in this script
              """ % (dmfit_location,))
        EXIT()
else: 
    # that's windows
    dmfit_location = os.path.normpath(WIN_dmfit_path)
    if not os.path.exists(dmfit_location):
        MSG("""dmfit not not found at 
               %s
               Please update WIN_dmfit_path variable in this script
              """ % (dmfit_location,))
        EXIT()


#TS 2 :  [EXPNAME, EXPNO, PROCNO, DIR, USER]
#TS >3 : [EXPNAME, EXPNO,PROC, DIR]
# topspin 2- or 3+
dtset = CURDATA()
if len(dtset) == 5: # for topspin 2-
	dtset[3] = os.path.join(dtset[3], "data", dtset[4], "nmr")

dim = GETPROCDIM()
if dim == 1 :
    spectname = "1r"
elif dim == 2 :
    spectname = "2rr"
else :
    MSG("dmfit can only open 1D or 2D datasets")
    EXIT()
 
datfile = os.path.join(dtset[3], dtset[0], dtset[1], "pdata", dtset[2], spectname)

if len(sys.argv)>1:
    key = sys.argv[1]
    if key not in dmfit_path.keys():
        key = default_key
else: 
    key = default_key
    

if OS.startswith('linux') or OS.startswith('mac'):
    #check for wine is exec
    subprocess.call([wine_path, dmfit_path[key], datfile], env=environment_var)
else:
    # check for dmfit is exec
    subprocess.call([dmfit_path[key], datfile])
