# -*- coding: utf-8 -*-
import os
import sys
import subprocess


def getFileExplorer():
    import java.lang.System
    OSis=java.lang.System.getProperty('os.name')
    import os.path
#    MSG(OSis)
    if 'Windows' in OSis:
        return 'C:\WINDOWS\explorer.exe'
    elif 'Darwin' in OSis or 'Mac OS X' in OSis:
        return '/usr/bin/open'
    elif  OSis=='Linux' :
        if os.path.exists('/usr/bin/xdg-open'):
            return '/usr/bin/xdg-open'
        elif os.path.exists('/usr/bin/gnome-open'):
            return '/usr/bin/gnome-open'
    else : raise
#MSG(getFileExplorer())    
dtset=CURDATA()
# special treatment for topspin<3
d1d=dtset[:]
if len(d1d)==5: # for topspin 2-
    d1d[3]="%s/data/%s/nmr" % (d1d[3],d1d[4])

datfile="%s/%s/%s/pdata/%s/" % (d1d[3],d1d[0],d1d[1],d1d[2])
print datfile
try : 
    explor=getFileExplorer()
#    print " ".join((explor,datfile))
    # os.system(" ".join((explor,datfile)))
    subprocess.call([explor]+[datfile])
    
except : 
    MSG("can't open file manager")
    EXIT()

