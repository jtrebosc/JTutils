# Simple GUI example
from javax.swing import *
from java.awt import *

import sys

## does summation of echoes using external python script
#import sys
import os
import os.path
import subprocess

import JTutils
from JTutils.TSpy import qcpmgadd

dataset = CURDATA()
N = str(1+int(GETPARSTAT("L 22")))
LB = GETPAR("LB")
GB = GETPAR("USERP1")
cycle = float(GETPARSTAT("P 60"))
if cycle < 1: # P60 is not likely to have stored the cycle time then uses historic calculation
    # historic qcpmg.jt cycle calculation
    D3 = float(GETPARSTAT("D 3"))*1e6
    D6 = float(GETPARSTAT("D 6"))*1e6
    P4 = float(GETPARSTAT("P 4"))
    cycle = 2*(D3+D6)+P4
cycle = str(cycle)
PUTPAR("LB", LB)
PUTPAR("USERP1", GB)

print cycle

def canceled(event):
	frame0.dispose()

def validated(event):
    (GB, LB, N, cycle) = [JTF_gb.getText(), JTF_lb.getText(),
                      JTF_slope.getText(), JTF_cycle.getText()]
    opt_args = " -g %s -l %s -n %s -c %s" % (GB, LB, N, cycle)
    if JRB_oddecho.isSelected():
        opt_args += " -o "
    if JRB_evenecho.isSelected():
        opt_args += " -e "
    script = JTutils.CpyBin_script("qcpmgadd_.py")
    #	os.system(" ".join((JTutils.CPYTHON, script, opt_args, fulldataPATH)))
    subprocess.call([JTutils.CPYTHON] + [script] + opt_args.split() + [fulldataPATH])
    frame0.dispose()
    EXEC_PYSCRIPT("RE_PATH('%s')"%(fulldataPATH,))

fulldataPATH = JTutils.fullpath(dataset)

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
JL_gb = JLabel("GB", SwingConstants.RIGHT)
JTF_gb = JTextField(GB)
JL_lb = JLabel("LB", SwingConstants.RIGHT)
JTF_lb = JTextField(LB)
JL_slope = JLabel("N", SwingConstants.RIGHT)
JTF_slope = JTextField(N)
JL_cycle = JLabel("Cycle", SwingConstants.RIGHT)
JTF_cycle = JTextField(cycle)

JRB_oddecho = JRadioButton("sum odd echoes")
JRB_evenecho = JRadioButton("sum even echoes")
JRB_bothecho = JRadioButton("sum all echoes")

button1 = JButton('OK', actionPerformed=validated) 
button2 = JButton('Cancel', actionPerformed=canceled)

# create window with title
frame0 = JFrame('TopSPin / Python GUI Example') 
# set window size x, y
frame0.setSize(500, 300) 
frame0.setLayout(GridLayout(0, 1)) 

frame1 = JPanel(GridLayout(0, 2))
frame0.add(frame1)
frame2 = JPanel()
frame0.add(frame2)
frame3 = JPanel()
frame0.add(frame3)

grpB = ButtonGroup()
grpB.add(JRB_oddecho)
grpB.add(JRB_evenecho)
grpB.add(JRB_bothecho)



# layout manager for horizontal alignment
frame1.add(JL_gb)
frame1.add(JTF_gb)
frame1.add(JL_lb)
frame1.add(JTF_lb)
frame1.add(JL_slope)
frame1.add(JTF_slope)
frame1.add(JL_cycle)
frame1.add(JTF_cycle)
frame2.add(JRB_oddecho)
frame2.add(JRB_evenecho)
frame2.add(JRB_bothecho)
frame3.add(button1)
frame3.add(button2)
frame0.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
frame0.setVisible(True)

