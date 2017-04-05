# -*- coding: utf-8 -*-
import re

dataset = CURDATA()
if len(dataset) == 5: # for topspin 2-
	MSG("this is topspin 2")
	datasetdir = "%s/data/%s/nmr" % (dataset[3], dataset[4])
else: datasetdir = dataset[3]

#fenetre=NEWWIN(-1,-1)
# definir la dimensionalité :
maxdim = GETACQUDIM()
dimlist = range(1, maxdim+1)
m = [0,0,0,0]
NUCx = [0,0,0,0]
SFOx = [0,0,0,0]
Ox = [0,0,0,0]
BFx = [0,0,0,0]
boutons = []
mnemonique = []
channelmap = []
# trouver les channels utilisés dans le pp
ppname = datasetdir + '/' + dataset[0] + '/' + dataset[1] + '/pulseprogram'
#ppname="/home/trebosc/toto"
ppfile = open(ppname, 'r')
pp = ppfile.read()
ppfile.close()

for chan in range(0, 4, 1):
	NUCx[chan] = "not active"
	SFOx[chan] = "not active"
	Ox[chan] = "not active"
	BFx[chan] = "not active"
	matchpattern = "^.*:f" + str(chan+1)
	m[chan] = re.search(matchpattern, pp, flags=re.M)
	if m[chan]: 
		NUCx[chan] = GETPAR("status NUC" + str(chan+1))
		if NUCx[chan] == "off":
			NUCx[chan] = "not active"
			continue
		SFOx[chan] = GETPAR("status SFO" + str(chan+1))
		BFx[chan] = GETPAR("status BF" + str(chan+1))
		Ox[chan] = GETPAR("status O" + str(chan+1))
		mnemonique.append(str(chan+1))
		boutons.append("channel " + str(chan+1) + ": " + NUCx[chan])
		channelmap.append(chan)
# 		MSG("channel f"+str(chan)+" is active")
# 	else : 
# 		MSG("channel f"+str(chan)+" is not active|"+str(m[chan])+"|")

channel = SELECT(title="available channels",
                 message="what channel do you want to use for F1 (click button) ?",
                 buttons=boutons, mnemonics=mnemonique)
chosenChan = channelmap[channel]

# master parameters are BF,O,SW,SF and SW signification depends on
# SFO : SW_h = SW*SFO
# so writing the parameters in the right order is important
# also the initial SWh must be saved before changing SFO1
# 1st: BF 
# 2nd: then SFO (then O is recalculated by PUTPAR) 
# 3rd: SW recalculated according to saved SWh new SFO1


# let's use topspin logic: read sw and calculate swh
sw = float(GETPAR("1s SW"))
SFOold = float(GETPAR("1s SFO1"))
swh = sw*SFOold

# write parameters in right order
PUTPAR("1s NUC1", NUCx[chosenChan])
PUTPAR("1 NUC1", NUCx[chosenChan])
PUTPAR("1s BF1", BFx[chosenChan])
PUTPAR("1 BF1", BFx[chosenChan])
# Apparently one cannot set O parameter only SFO is allowed
# PUTPAR("1 01",Ox[chosenChan])
PUTPAR("1s SFO1", SFOx[chosenChan])  # recalculates Ox based on BF1 and SFO1
PUTPAR("1 SFO1", SFOx[chosenChan])

# Only now recalculate and store SW 
sw = swh/float(SFOx[chosenChan])
PUTPAR("1s SW", str(sw))  # this also sets SWh = sw*SFOx and INF = 1/SWh

RE(dataset)
