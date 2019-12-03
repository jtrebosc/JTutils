# Simple GUI example
from javax.swing import *
from java.awt import *
import optparse

import sys

## does summation of echoes using external python script
import sys
import os
import os.path
import subprocess

"""
import argparse

parser = argparse.ArgumentParser(description='Add echoes in a qcpmg bruker experiment')
parser.add_argument('-l','--lb',type=float, help='Lorentzian broadening applied to the decaying echo',default=0)
parser.add_argument('-g','--gb',type=float, help='Gaussian broadening applied to each echo',default=0)
parser.add_argument('-n',type=int, help='Number of echo to sum')
parser.add_argument('-c',type=float, help='qcpmg cycle in us')
parser.add_argument('infile',help='Full path of the dataset to process')
"""

import JTutils

dataset = CURDATA()
N = str(1+int(GETPARSTAT("L 22")))
LB = GETPAR("LB")
GB = GETPAR("USERP1")
slope = GETPAR("USERP2")
cycle = float(GETPARSTAT("P 60"))
if cycle < 1: # P60 is not likely to have stored the cycle time then uses historic calculation
    # historic qcpmg.jt cycle calculation
    D3 = float(GETPARSTAT("D 3"))*1e6
    D6 = float(GETPARSTAT("D 6"))*1e6
    P4 = float(GETPARSTAT("P 4"))
    cycle = 2*(D3+D6)+P4
cycle = str(cycle)


print cycle
fulldataPATH = JTutils.fullpath(dataset)

def canceled(event):
	frame0.dispose()

def validated(event):
	(GB, LB, slope, N, cycle) = [JTFgb.getText(), JTFlb.getText(), JTFslope.getText(), JTFn.getText(), JTFcycle.getText()]
	
	opt_args = " -g %s -l %s -n %s -c %s -s %s" % (GB, LB, N, cycle, slope)
	if echoB.isSelected():
			opt_args += " -o "
	if aechoB.isSelected():
			opt_args += " -e "
	script = JTutils.CpyBin_script("qcpmgadd2D_.py")
    #  os.system(" ".join((JTutils.CPYTHON,script,opt_args,fulldataPATH)))
    subprocess.call([JTutils.CPYTHON] + [script] + opt_args.split() + [fulldataPATH])    
	frame0.dispose()
	EXEC_PYSCRIPT("RE_PATH('%s')" % (fulldataPATH, ))
	#PUTPAR("LB",LB)
  #PUTPAR("USERP1",GB)



"""
JLabel("GB:")  
LB:
slope:
cycle:
buttonGroup : odd/even/both

button_OK
button_CANCEL
button_HELP
"""



# defined a frame with 2 buttons
Lgb = JLabel("GB", SwingConstants.RIGHT)
JTFgb = JTextField(GB)

Llb = JLabel("LB", SwingConstants.RIGHT)
JTFlb = JTextField(LB)

Ln = JLabel("N", SwingConstants.RIGHT)
JTFn = JTextField(N)

Lslope = JLabel("Slope", SwingConstants.RIGHT)
JTFslope = JTextField(slope)

Lcycle = JLabel("Cycle", SwingConstants.RIGHT)
JTFcycle = JTextField(cycle)

echoB = JRadioButton("sum odd echoes")
aechoB = JRadioButton("sum even echoes")
bechoB = JRadioButton("sum all echoes")

button1 = JButton('OK', actionPerformed=validated) 
button2 = JButton('Cancel', actionPerformed=canceled)

# create window with title
frame0 = JFrame('TopSPin / Python GUI Example') 
# set window size x, y
frame0.setSize(500, 300) 
frame0.setLayout(GridLayout(0,1)) 

frame1 = JPanel(GridLayout(0,2))
frame0.add(frame1)
frame2 = JPanel()
frame0.add(frame2)
frame3 = JPanel()
frame0.add(frame3)

grpB = ButtonGroup()
grpB.add(echoB)
grpB.add(aechoB)
grpB.add(bechoB)



# layout manager for horizontal alignment
frame1.add(Lgb)
frame1.add(JTFgb)
frame1.add(Llb)
frame1.add(JTFlb)
frame1.add(Lcycle)
frame1.add(JTFcycle)
frame1.add(Ln)
frame1.add(JTFn)
frame1.add(Lslope)
frame1.add(JTFslope)
frame2.add(echoB)
frame2.add(aechoB)
frame2.add(bechoB)
frame3.add(button1)
frame3.add(button2)
frame0.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
frame0.setVisible(True)

