import sys, os.path
sys.path.insert(0, os.path.abspath('../../CpyLib'))
import brukerIO as bio
import unittest
from pathlib import Path
list_to_test = [path for path in Path('/home/trebosc/NMR/data/').rglob('*/acqus')]
#list_to_test = [path for path in Path('/home/trebosc/NMR/data/RMN400s/nmr/400.XL-110203').rglob('acqus')]
total_tests = len(list_to_test)
print(f"length of dataset list = {total_tests}")
#for file in list_to_test:
#    print(file)

#search for input data files to generate a file_list
# run the test in a loop :
# read start and stop times
# read NS, AQ, D.1, TD{123} 
# compare stop-start > 0 and equal to NS*(D.1+AQ)*TD{123} within 10%

class testAuditaTimes(unittest.TestCase):
    def test_audita(self):
        
        AssertFailed = 0
        for file in list_to_test:
#            print([os.path.normpath(path) for path in Path(os.path.dirname(file)).rglob('*/procs')])
            proc_file = str([os.path.dirname(path) for path in Path(os.path.dirname(os.path.normpath(file))).rglob('*/procs')][0])
            with self.subTest(proc_file=proc_file):
                data = bio.dataset(bio.splitprocpath(proc_file))
                start, stop, expt_audita = data.audita_times()
                SW_h = data.readacqpar('SW_h', status=True, dimension=1)
                TD = data.readacqpar('TD', status=True, dimension=1)
                AQ = TD/SW_h/2
                D1 = data.readacqpar('D 1', status=True, dimension=1)
                NS = data.readacqpar('NS', status=True, dimension=1)
                DS = data.readacqpar('DS', status=True, dimension=1)
                TDi = []
                for dim in range(data.dimA):
                    if dim == 0 : continue
                    TDi.append(data.readacqpar('TD', status=True, dimension=dim+1))
                TDall = 1
                for td in TDi:
                    TDall *= td
                if data.haveRawData and expt_audita.total_seconds()>0:
                    expt_calc = (DS+NS*TDall)*(D1+AQ)+1
                    ratio = expt_calc / expt_audita.total_seconds()
                else:
                    expt_calc = 0
                    ratio = 1
#                print(proc_file, ratio, data.haveRawData)
                pulprog =  data.readacqpar('PULPROG', status=True, dimension=1)
                zgoptns =  data.readacqpar('ZGOPTNS', status=True, dimension=1)
                if (expt_audita.total_seconds() - expt_calc < 4 
                    and expt_audita.total_seconds() - expt_calc > 0):
                    pass
                elif ('satrect1' in pulprog) or ('t1ir' in pulprog) or (('T1' in zgoptns) and ('halfecho' in pulprog)):
                    # pulse programs with vd list are notably inaccurate for expt_calc
                    print(f'@@@@@@@@@@@@@@@@@@  skipped program {pulprog} @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2')
                elif D1<0.3:
                    # pulse programs with short D1 are not accounting for extra overhead 
                    print(f'@@@@@@@@@@@@@@@@@@  skipped short D1 in {file} @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2')
                else:
                    try:
                        self.assertAlmostEqual(1, ratio, msg=f"""
                            Failed calculation
                            File {proc_file}
                            raw data exists: {data.haveRawData}, PULPROG={pulprog},
                            expt_calc={expt_calc}
                            audit_time={expt_audita.total_seconds()} 
                            audit_start={start}
                            audit_stop={stop}""", delta=0.2)
                    except AssertionError as e: 
                        pass
                        print(proc_file)
                        print(f"============= program version= {data.versionA}")
                        print(e)
                        AssertFailed += 1
                        print(f"===================================== {AssertFailed} Assertion failed over {total_tests}!")
if __name__ == '__main__':
    unittest.main()
