# -*- coding: utf-8 -*-
dat=CURDATA()
SFO1=float(GETPAR("2s SFO1"))
SF=float(GETPAR("2s SF"))
PUTPAR("1 SF",str(2*SF-SFO1))
PUTPAR("1s SF",str(2*SF-SFO1))
RE(dat)
