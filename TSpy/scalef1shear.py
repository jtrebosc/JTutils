# for datasets acquired with topspin > 2.1 (requires INF)
# scale F1 dimension to get unified scale for MQMAS/STMAS experiments
# the program rewrites BF1/SFO1/O1/SW/SF/OFFSET according to 
# the apparent Larmor frequency of isotropic dimension
# Select the nucleus to use for indirect dimension
# Select the MQMAS/STMAS type of experiment that gives the isotropic dimension
# option F2toF1 will read SF from F2 dimension (usefull for MQMAS/STMAS 2D)
# if F2 does not contain the same nucleus as F1 (MQ-INEPT experiment for example)
# then F1 must contain the original SFO1/SF data

from __future__ import division, print_function

import re
import os
import argparse

description = """
Adjust the F1 scale for isotropic dimension in MQMAS/STMAS of MQHETCOR type experiments.
"""

parser = argparse.ArgumentParser(description=description)
# F2toF1
parser.add_argument('--F2toF1', action='store_true', 
            help='use parameters from F2 dimension to calculate scale in F1 (ex.: for MQMAS)')
group = parser.add_mutually_exclusive_group()
group.add_argument('--3qmas', action='store_true', dest='Q3',
            help='Calculate the scale for a 3QMAS experiment')
group.add_argument('--5qmas', action='store_true', dest='Q5',
            help='Calculate the scale for a 5QMAS experiment')
group.add_argument('--stmas', action='store_true', dest='ST',
            help='Calculate the scale for a STMAS experiment')
try :
    args = parser.parse_args()
    F2toF1 = args.F2toF1
    Q3 = args.Q3
    Q5 = args.Q5
    ST = args.ST
except argparse.ArgumentError as E:
    MSG(str(E))
    EXIT()
except SystemExit:
    MSG(""" Script is exiting : either you asked for help or there is an argument error.
    Check console for additional information
    """  + parser.format_help() )
    EXIT()
       
    

DIRINST = os.path.dirname(sys.argv[0]) 
LIBPATH = DIRINST+ "/../CpyLib"
if LIBPATH not in sys.path:
    sys.path.append(LIBPATH)
import brukerPAR


dataset = CURDATA()
dtst = brukerPAR.dataset(dataset)

# topspin 3.0 and higher dataset only have 4 parameters : DIR, NAME, EXPNO and PROCNO
if len(dataset) > 4 : 
    DIR = dataset[3] + "/data/" + dataset[4] + "/nmr/"
else : 
    DIR = dataset[3] + "/"

# check the dimensionality of dataset 
#maxdim = GETACQUDIM()
#dimlist = range(1, maxdim+1)

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
# channelmap lists the active channels
for chan in range(0,4,1):
    NUCx[chan] = "not active"
    SFOx[chan] = "not active"
    Ox[chan] = "not active"
    BFx[chan] = "not active"
    matchpattern = "^[^;]*:f" + str(chan+1)
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

if F2toF1 :
    # F1 parameters are calculated from F2 (chan=0)
    chosenChan = 0
else:
    # user selects the channel to set in F1 among the active channels
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
if F2toF1:
    sf = float(dtst.readprocpar("SF", dimension=1, status=False))
else:
    sf = float(dtst.readprocpar("SF", dimension=2, status=False))

# select spin number based on nucleus name from bruker table
TOPSPIN_HOME = os.path.normpath(os.getenv("XWINNMRHOME"))
nuclei = TOPSPIN_HOME + os.path.normpath("/exp/stan/nmr/lists/nuclei.all")
spin = ''
with open(nuclei,'r') as F:
    for line in F:
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

if Q3:
    exptype = 0
elif Q5:
    exptype = 1
elif ST: 
    exptype = 2
else:
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
#MSG("ratio R=" + str(ratio))


#apply scaling factor to frequencies
nuciso = "%s" % (NUCx[chosenChan])
sf *= factor
sfo *= factor
bf *= factor
o *= factor
# recalculate SW: note that topspin uses SFO instead of SF for calculating SW in ppm. 
# This make the SW parameter not accurately meaningful
# 
newSW = swh/sfo


# master parameters are BF,O,SW,SF and SW signification depend on
# SFO : SW_h=SW*SFO
# I'm not using Bruker function as relations make it difficult to predict
# 1st : BF 
# then :O or SFO 
# finally: SW_h (that must be stored before hand) to recalculate SW 
# according to new new SFO
# SF: seems to be fully independant

# for scale to be OK after reprocessing: store modified acq parameters
dtst.writeacqpar("NUC1", nuciso, dimension=2, status=True)
dtst.writeacqpar("BF1", str(bf), dimension=2, status=True)
dtst.writeacqpar("SFO1", str(sfo), dimension=2, status=True)
dtst.writeacqpar("O1", str(o), dimension=2, status=True)
dtst.writeacqpar("SW", str(newSW), dimension=2, status=True)
# for current spectrum to look OK : stores modified proc parameters
# from acqu and proc parameters
si =  int(dtst.readprocpar("FTSIZE", dimension=2, status=True))
stsi = int(dtst.readprocpar("STSI", dimension=2, status=True))
stsr =  int(dtst.readprocpar("STSR", dimension=2, status=True))
hzppt = swh/si
swp = stsi*hzppt
offset = ((sfo*1e6+swh/2)-stsr*hzppt -sf*1e6)/sf
dtst.writeprocpar("SW_p", str(swp), dimension=2, status=True)
dtst.writeprocpar("SF", str(sf), dimension=2, status=False)
dtst.writeprocpar("SF", str(sf), dimension=2, status=True)
dtst.writeprocpar("OFFSET",str(offset),dimension=2,status=True)

RE(dataset)
