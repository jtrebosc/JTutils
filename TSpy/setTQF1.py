# -*- coding: utf-8 -*-
dat=CURDATA()
SFO1=float(GETPAR("2s SFO1"))
SF=float(GETPAR("2s SF"))
PUTPAR("1 SF",str(3*SF-2*SFO1))
PUTPAR("1s SF",str(3*SF-2*SFO1))
RE(dat)
