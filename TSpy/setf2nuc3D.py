# -*- coding: utf-8 -*-
import re

dataset=CURDATA()
if len(dataset)==5: # for topspin 2-
	MSG("this is topspin 2")
	datasetdir="%s/data/%s/nmr" % (dataset[3],dataset[4])
else: datasetdir=dataset[3]
#check that expt is 3D :
dim=GETPAR("PARMODE")
if dim not in "2" : 
  MSG("expt is not 3D")
  EXIT()
#fenetre=NEWWIN(-1,-1)
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
# trouver les channels utilisés dans le pp
ppname=datasetdir+'/'+dataset[0]+'/'+dataset[1]+'/pulseprogram'
#ppname="/home/trebosc/toto"
ppfile=open(ppname,'r')
pp=ppfile.read()
ppfile.close()

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
