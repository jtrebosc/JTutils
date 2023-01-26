# -*- coding: utf-8 -*-
import re, os
import JTutils

if GETPROCDIM() < 3:
    MSG('Change F2 nucleus in nD with n>=3 datasets only !')
    EXIT()
dataset = CURDATA()
dtst = JTutils.brukerPARIO.dataset(dataset)

# definir la dimensionalité :
maxdim=GETACQUDIM()
dimlist=range(1,maxdim+1)
m=[0,0,0,0]
NUCx=[0,0,0,0]
SFOx=[0,0,0,0]
Ox=[0,0,0,0]
BFx=[0,0,0,0]
boutons=[]
mnemonique=[]
channelmap=[]
# Find channels used in pp
for pp_name in ['pulseprogram', 'pulseprogram.precomp']:
    pp_full_name = os.path.join(dtst.returnacqpath(), pp_name)
    if os.path.isfile(pp_full_name):
        break
    else:
        pp_full_name = None
if pp_full_name is None:
    pp = ":f1 :f2 :f3 :f4"  # assume all 4 channels can be selected
else:
    with open(pp_full_name,'r') as f:
        pp = f.read()

for chan in range(0,4,1):
	NUCx[chan]="not active"
	SFOx[chan]="not active"
	Ox[chan]="not active"
	BFx[chan]="not active"
	matchpattern="^.*:f"+str(chan+1)
	m[chan]=re.search(matchpattern,pp,flags=re.M)
	if m[chan] : 
		NUCx[chan]=GETPAR("status NUC"+str(chan+1))
		if NUCx[chan]=="off":
			NUCx[chan]="not active"
			continue
		SFOx[chan]=GETPAR("status SFO"+str(chan+1))
		BFx[chan]=GETPAR("status BF"+str(chan+1))
		Ox[chan]=GETPAR("status O"+str(chan+1))
		mnemonique.append(str(chan+1))
		boutons.append("channel "+str(chan+1) +": "+NUCx[chan])
		channelmap.append(chan)
# 		MSG("channel f"+str(chan)+" is active")
# 	else : 
# 		MSG("channel f"+str(chan)+" is not active|"+str(m[chan])+"|")

channel=SELECT(title="available channels",message="what channel do you want to use for F2 (click button) ?",buttons=boutons,mnemonics=mnemonique)
if channel <0:
    EXIT()
chosenChan=channelmap[channel]
# master parameters are BF,O,SW,SF and SW signification depend on
# SFO : SW_h=SW*SFO
# so writing the parameters in the right order is important ;
# 1st : BF then O or SFO (then SFO or O is recalculated by 
# PUTPAR) finally SW_h (that must be stored before hand) to 
# recalculate SW according to new new SFO

# since only SW is reliable one has to calculate SW_h
sw=float(GETPAR("2s SW"))
SFOold=float(GETPAR("2s SFO1"))
swh=sw*SFOold

PUTPAR("2s NUC1",NUCx[chosenChan])
PUTPAR("2 NUC1",NUCx[chosenChan])
PUTPAR("2s BF1",BFx[chosenChan])
PUTPAR("2 BF1",BFx[chosenChan])
# Apparently one cannot set O parameter only SFO is allowed
# PUTPAR("2s 01",Ox[chosenChan])
# PUTPAR("2 01",Ox[chosenChan])
PUTPAR("2s SFO1",SFOx[chosenChan])
PUTPAR("2 SFO1",SFOx[chosenChan])

# recalculate SW
sw=swh/float(SFOx[chosenChan])
#MSG("SWh="+str(swh))
#MSG("SW="+str(sw))
#PUTPAR("2s SW_h",str(swh))
PUTPAR("2s SW",str(sw))
#PUTPAR("2s INF",str(1e6/swh))
RE(dataset)
