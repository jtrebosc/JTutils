import os
import subprocess
import sys

#setup the following path to dmfit executable and to wine executablefor linux and mac os x
WIN_dmfit_path=r'C:/Program Files (x86)/dmfit/dm2011.exe'

LIN_dmfit_path=r'.wine/drive_c/Program Files/dmfit2015/dm2015.exe'
MAC_dmfit_path=r'.wine/drive_c/Program Files/dmfit2015/dm2015.exe'

MAC_wine=r'/usr/local/bin/wine'
LIN_wine=r'/usr/bin/wine'

def get_os_version():
    ver = sys.platform.lower()
    if ver.startswith('java'):
        import java.lang
        ver = java.lang.System.getProperty("os.name").lower()
    return ver

OS=get_os_version()


if OS.startswith('mac'):
    # for Linux with wine
    wine=os.path.normpath(MAC_wine)
    home=os.getenv("HOME")
    dmfit_location=os.path.join(os.path.normpath(home),os.path.normpath(MAC_dmfit_path))
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
    wine=os.path.normpath(LIN_wine)
    home=os.getenv("HOME")
    dmfit_location=os.path.join(os.path.normpath(home),os.path.normpath(LIN_dmfit_path))
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
    dmfit_location=os.path.normpath(WIN_dmfit_path)
    if not os.path.exists(dmfit_location):
        MSG("""dmfit not not found at 
               %s
               Please update WIN_dmfit_path variable in this script
              """ % (dmfit_location,))
        EXIT()


#TS 2 :  [EXPNAME, EXPNO, PROCNO, DIR, USER]
#TS >3 : [EXPNAME, EXPNO,PROC, DIR]
# topspin 2- or 3+
dtset=CURDATA()
if len(dtset)==5: # for topspin 2-
	dtset[3]=os.path.join(dtset[3],"data",dtset[4],"nmr")

dim=GETPROCDIM()
if dim == 1 :
    spectname="1r"
elif dim == 2 :
    spectname="2rr"
else :
    MSG("dmfit can only open 1D or 2D datasets")
    EXIT()
 
datfile=os.path.join(dtset[3],dtset[0],dtset[1],"pdata",dtset[2],spectname)

if OS.startswith('linux') or OS.startswith('mac'):
    subprocess.call([wine,dmfit_location,datfile])
else:
    subprocess.call([dmfit_location,datfile])
