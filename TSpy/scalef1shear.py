# for datasets acquired with topspin > 2.1 (requires INF)
# scale F1 dimension to get unified scale for MQMAS/STMAS experiments
# the program rewrites BF1/SFO1/O1/SW/SF/OFFSET according to 
# the apparent Larmor frequency of isotropic dimension
# Select the nucleus to use for indirect dimension
# Select the MQMAS/STMAS type of experiment that gives the isotropic dimension
# option SFF2 will read SF from F2 dimension (usefull for MQMAS/STMAS 2D)
# if F2 does not contain the same nucleus as F1 (MQ-INEPT experiment for example)
# then F1 must contain the original SFO1/SF data

from __future__ import division

import re
import os
DIRINST = os.path.dirname(sys.argv[0]) + "/../"
sys.path.append(DIRINST+"CpyLib")
import brukerPAR

dataset = CURDATA()
TOPSPIN_HOME = os.getenv("XWINNMRHOME")
dtst = brukerPAR.dataset(dataset)

# topspin 3.0 and higher dataset only have 4 parameters : DIR, NAME, EXPNO and PROCNO
if len(dataset) > 4 : DIR = dataset[3] + "/data/" + dataset[4] + "/nmr/"
else : DIR = dataset[3] + "/"

# check the dimensionality of dataset 
maxdim = GETACQUDIM()
dimlist = range(1, maxdim+1)

# initialize up to 4 channels
m = [0, 0, 0, 0]
NUCx = [0, 0, 0, 0]
SFOx = [0, 0, 0, 0]
Ox = [0, 0, 0, 0]
BFx = [0, 0, 0, 0]
boutons=[]
mnemonique=[]
channelmap=[]

# find channels used in pp
ppname = dtst.returnacqpath()+'/pulseprogram'
ppfile = open(ppname,'r')
pp = ppfile.read()
ppfile.close()

# check if channels f1,..,f4 are present in pp
for chan in range(0,4,1):
    NUCx[chan] = "not active"
    SFOx[chan] = "not active"
    Ox[chan] = "not active"
    BFx[chan] = "not active"
    matchpattern = "^.*:f" + str(chan+1)
    m[chan] = re.search(matchpattern, pp, flags=re.M)
    if m[chan] : 
        NUCx[chan] = dtst.readacqpar("NUC" + str(chan+1))
        if NUCx[chan] == "off":
            NUCx[chan] = "not active"
            continue
        SFOx[chan] = dtst.readacqpar("SFO" + str(chan+1))
        BFx[chan] = dtst.readacqpar("BF" + str(chan+1))
        Ox[chan] = dtst.readacqpar("O" + str(chan+1))
        mnemonique.append(str(chan+1))
        boutons.append("channel " + str(chan+1) + ": " + NUCx[chan])
        channelmap.append(chan)        
# user selects the channel to set in F1
channel = SELECT(title="available channels",
                 message="what channel do you want to use for F1 (click button) ?",
                 buttons=boutons, mnemonics=mnemonique)
chosenChan = channelmap[channel]

sfo = float(SFOx[chosenChan])
bf = float(BFx[chosenChan])
o = float(Ox[chosenChan])

# get the spectral window / dwell time in F1
swh = float(dtst.readacqpar("SW_h",dimension=2,status=True),)
inf1 = 1e6/swh

#MSG(str(swh)+"\n"+str(inf1))
# check for command line argument : only SFF2 is checked manually
if len(sys.argv) > 1:
    if sys.argv[1] == 'SFF2':
        sf = float(dtst.readprocpar("SF",dimension=1,status=False))
        print "read SF from F2"
    else:
        sf = float(dtst.readprocpar("SF",dimension=2,status=False))
else:
    sf = float(dtst.readprocpar("SF",dimension=2,status=False))


# select spin number based on nucleus name from bruker table
nuclei = TOPSPIN_HOME + "/exp/stan/nmr/lists/nuclei.all"
f = open(nuclei,'r')
spin = ''
while (1):
    line = f.readline()
    if (line == ''):
        break
    line.strip()
    if (line.find('#') == 0):
        continue
    if (line.find(NUCx[chosenChan]) > 0):
        tmp=line.split()
        spinstr = tmp[4]
        break
if spinstr[1] == '/' :
    spin = float(spinstr[0])/2
else :
    spin = float(spinstr[0])
f.close()

exptype = SELECT(title="Kind of experiment",
                 message="What is the experiment that need universal scaling in F1?",
                 buttons=["3QMAS","5QMAS","STMAS"])

# calculate scaling factor based on experiment type and spin
# 3QMAS correlates 3Q coherence with CT coherence
if exptype == 0:
    ni = 3./2.
    mi = -3./2.
    nf = -1./2.
    mf = 1./2.
# 5QMAS correlates 3Q coherence with CT coherence
if exptype==1:
    ni = 5./2.
    mi = -5./2.
    nf = -1./2.
    mf = 1./2.
# STMAS correlates ST2 coherence with CT coherence
if exptype == 2:
    ni = 3./2.
    mi = 1./2.
    nf = -1./2.
    mf = 1./2.

mq = ni-mi
I2 = spin*(spin + 1.)
C4ni = ni*(18.*I2 - 34.*ni*ni - 5.)
C4mi = mi*(18.*I2 - 34.*mi*mi - 5.)
C4nf = nf*(18.*I2 - 34.*nf*nf - 5.)
C4mf = mf*(18.*I2 - 34.*mf*mf - 5.)
ratio = -(C4mi-C4ni)/(C4mf-C4nf)
factor = abs(ratio - mq)
MSG("ratio R=" + str(ratio))


#apply scaling factor to frequencies
nuciso = "%s" % (NUCx[chosenChan])
sf *= factor
sfo *= factor
bf *= factor
o *= factor
# recalculate SW
newSW = swh/sfo


# master parameters are BF,O,SW,SF and SW signification depend on
# SFO : SW_h=SW*SFO
# I'm not using Bruker function as relations make it difficult to predict
# 1st : BF 
# then :O or SFO 
# finally: SW_h (that must be stored before hand) to recalculate SW 
# according to new new SFO
# SF: seems to be fully independant

dtst.writeacqpar("NUC1", nuciso, dimension=2, status=True)
dtst.writeacqpar("BF1", str(bf), dimension=2, status=True)
dtst.writeacqpar("SFO1", str(sfo), dimension=2, status=True)
dtst.writeacqpar("O1", str(o), dimension=2, status=True)
dtst.writeacqpar("SW", str(newSW), dimension=2, status=True)

dtst.writeprocpar("SW_p", str(swh), dimension=2, status=True)
offset=str((sfo*1e6 + swh/2 - sf*1e6)/sf)
dtst.writeprocpar("OFFSET",offset,dimension=2,status=True)
dtst.writeprocpar("SF", str(sf), dimension=2, status=False)
dtst.writeprocpar("SF", str(sf), dimension=2, status=True)

# maybe one need to calculate/set OFFSET parameter to actually 
# change the reference frequency in topspin display
#MSG(offset + "\n" + str(swh))
RE(dataset)
