# -*- coding: utf-8 -*-
# for datasets acquired with topspin > 2.1 (requires INF)
# scale F1 dimension to get unified scale for MQMAS/STMAS experiments
# the program rewrites BF1/SFO1/O1/SW/SF/OFFSET according to 
# the apparent Larmor frequency of isotropic dimension
# Select the nucleus to use for indirect dimension
# Select the MQMAS/STMAS type of experiment that gives the isotropic dimension
# option F2toF1 will read SF from F2 dimension (usefull for MQMAS/STMAS 2D)
# if F2 does not contain the same nucleus as F1 (MQ-INEPT experiment for example)
# then F1 must contain the original SFO1/SF data

from __future__ import division

import re
import os


def scalef1sheared(F2toF1=False, exptype='3QMAS', dataset=None):
    """
    Calculate the universal scale for MQMAS/STMAS experiments
    input args : 
    F2toF1: (bool) if True uses SF from F2 dimension for calculating SF in F1
    exptype: (string) None (default), '3QMAS', 5QMAS' or 'STMAS': calculate new scale for exptype
           if None ask user for exptype
    dataset: the dataset as returned by CURDATA()
    """ 
    # if this function is called from imported module then 
    # one needs to import TOPSPIN functions
    # so that they are available in the current namespace
    from TopCmds import CURDATA, RE, MSG, SELECT

    from JTutils.CpyLib import brukerPARIO
    if dataset == None: 
        dataset = CURDATA()
    dtst = brukerPARIO.dataset(dataset)

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
                         message="what channel do you want to use for F1 (click button) or ESCAPE to cancel ?",
                         buttons=boutons, mnemonics=mnemonique)
        if channel < 0 :
            EXIT()
        chosenChan = channelmap[channel]

    sfo = float(SFOx[chosenChan])
    bf = float(BFx[chosenChan])
    o = float(Ox[chosenChan])

    # get the spectral window / dwell time in F1
    swh = float(dtst.readacqpar("SW_h",dimension=2,status=True),)
    inf1 = 1e6/swh

    #MSG(str(swh)+"\n"+str(inf1))
    if F2toF1:
        # status of not status that is the question....
        sf = float(dtst.readprocpar("SF", dimension=1, status=True))
    else:
        sf = float(dtst.readprocpar("SF", dimension=2, status=True))
    #MSG("sf=" + str(sf))
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

    theTypes = ['3QMAS', '5QMAS', 'STMAS']
    if exptype == None:
        typeIndex = SELECT(title="Kind of experiment",
                     message="What is the experiment that need universal scaling in F1?",
                     buttons=["3QMAS","5QMAS","STMAS"])
        if typeIndex < 0 :
            EXIT()
        exptype = theTypes[typeIndex]

    folding_times = "0"
    result = INPUT_DIALOG("number of times the spectrum is folded (-1, 0, +1,...)", 
          """ Adjust the scale of a folded spectrum. Input how many times the spectrum is folded
          a positive number shift the scale to higher ppm value
          """, 
             ["fold times="],
             [folding_times])
    folding_times = int(result[0])

    # calculate scaling factor based on experiment type and spin
    # 3QMAS correlates 3Q coherence with CT coherence
    if exptype == '3QMAS':
        ni = 3./2.
        mi = -3./2.
        nf = -1./2.
        mf = 1./2.
    # 5QMAS correlates 3Q coherence with CT coherence
    if exptype == '5QMAS':
        ni = 5./2.
        mi = -5./2.
        nf = -1./2.
        mf = 1./2.
    # STMAS correlates ST2 coherence with CT coherence
    if exptype == 'STMAS':
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
# change the apparent carrier frequency if spectrum is folded
    sfo += folding_times*swh/1e6 
    o += folding_times*swh
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



if __name__ == '__main__':
    description = """
    Adjust the F1 scale for isotropic dimension in MQMAS/STMAS of MQHETCOR type experiments.
    """
    class dummy():
        def __init__(self):
            self.F2toF1 = False
            self.Q3 = False
            self.Q5 = False
            self.ST = False
    try : 
        import argparse
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument('--F2toF1', action='store_true', 
                    help='use parameters from F2 dimension to calculate scale in F1 (ex.: for MQMAS)')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--3qmas', action='store_true', dest='Q3',
                    help='Calculate the scale for a 3QMAS experiment')
        group.add_argument('--5qmas', action='store_true', dest='Q5',
                    help='Calculate the scale for a 5QMAS experiment')
        group.add_argument('--stmas', action='store_true', dest='ST',
                    help='Calculate the scale for a STMAS experiment')
        args  =  parser.parse_args(sys.argv[1:])
    except ImportError:
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        args = dummy()
    except SystemExit:
        MSG(""" Script is exiting : either you asked for help or there is an argument error.
        Check console for additional information
        """  + parser.format_help() )
        EXIT()
    if args.Q3 : exptype = '3QMAS'
    elif args.Q5 : exptype = '5QMAS'
    elif args.ST : exptype = 'STMAS'
    else : exptype = None
    dataset = CURDATA()
    scalef1sheared(F2toF1=args.F2toF1, exptype = exptype, dataset=dataset)
