# -*- coding: utf-8 -*-
import re, os
import JTutils

if GETPROCDIM() < 2:
    MSG('Change F1 nucleus in nD with n>=2 datasets only !')
    EXIT()
dataset = CURDATA()
dtst = JTutils.brukerPARIO.dataset(dataset)

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
if channel <0:
    EXIT()
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
