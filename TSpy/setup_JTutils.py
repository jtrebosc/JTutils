#!/usr/bin/env python 
# coding: utf8 
# get information on current setup
# print information in MSG box, in console and it should propose to save
# the report in a file
# this Script will serve as setup to detect/define CPYTHON in a config file
# There should be different tests functions, a report function and a setup

#from __future__ import unicode_literals
import sys
import os
from os.path import abspath, dirname, normpath, realpath, isdir, isfile, islink
from os.path import join as join_path
from os.path import split as split_path

sys_enc = sys.getfilesystemencoding()
# This script should be called from within topspin so these should be defined
XWINNMRHOME = normpath(os.getenv('XWINNMRHOME', "undefined").decode(sys_enc))
USERHOME_DOT_TOPSPIN = normpath(os.getenv('USERHOME_DOT_TOPSPIN', "undefined").decode(sys_enc))

# these env variables will become obsolete
# one should get the values from JTutils module
#CPYTHON = os.getenv('CPYTHON', "not defined")
#PYTHONPATH = os.getenv('PYTHONPATH', "not defined")
#
#if (abspath(CpyLibDir) != abspath(PYTHONPATH)):
#   WarningLibDir = """Warning : JTutils folder structure and PYTHONPATH are not consistent. 
#You should make sure that PYTHON points to %s""" % (abspath(CpyLibDir), )
#else :  WarningLibDir =  ""

JTutils_modules = ["numpy", "argparse", "multiprocessing", "brukerIO"]
ssnake_extra_modules = ["matplotlib", "scipy", "PyQt5", "h5py", "numba", "numba_scipy"]
ssnake_conda_pack = "numpy matplotlib pyqt=5 h5py scipy numba numba::numba-scipy"

def is_conda_python(CPYTHON):
    """ check if CPYTHON exe is related to a conda distribution
        return True if conda-meta directory is found in same directory as CPYTHON interpreter
        This may not be the most elegant way but it should work
   """
    return isdir(join_path(dirname(CPYTHON), "conda-meta"))


def is_exe(fpath):
    return isfile(fpath) and os.access(fpath, os.X_OK)

def which(program):
    import os
    path_env = os.getenv("PATH").decode(sys_enc).split(os.pathsep)
    # On windows, I need to add a search in conda standard location:
    # os.environ['USERPROFILE']/*conda*
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in path_env:
            exe_file = join_path(path, program)
            if is_exe(exe_file):
                return exe_file
    return ""

def get_os_version():
    """ returns the underlying OS as lowercase string: 
        string contains either windows, linux or mac """ 
    version = sys.platform.lower()
    if version.startswith('java'):
        import java.lang
        version = java.lang.System.getProperty("os.name").lower()
    return version

def test_jmodule_import(module_name):
    """ test if module_name module can import successfuly
        from topspin JYTHON interpreter
        input module_name
        output : tuple with 2 elements:
            bool : test success (True= success, False=Failure)
            message :  exception message if test fail, module version if test is successful
    """
    from importlib import import_module
    try :
        module = import_module(module_name)
        if hasattr(module, '__version__'):
            message = module.__version__
        else:
            message = ""
        return (True, message)
    except ImportError, exc:
        return (False, exc)

def test_cmodule_import(module_name):
    """ test if module_name module can import successfuly
        from CPYTHON interpreter
        input module_name
        output : tuple with 2 elements:
            bool : test success (True= success, False=Failure)
            message :  exception message if test fail, module version if test is successful
    """
    import JTutils
    reload(JTutils) # in case an old JTutils was already installed and loaded
    CMD = """
# coding: utf8
#from __future__ import unicode_literals
import %s
if hasattr(%s, '__version__'):
    print(%s.__version__)
""" % (module_name, module_name, module_name)
    import subprocess
    try:
        version = JTutils._run_string_ext_script(CMD)
        return (True, version)
    except subprocess.CalledProcessError, exc:
        return (False, exc.output)
    except Exception, exc:
        return (False, exc)

def test_CPYTHON(CPYTHON):
    """ tries to execute a python script to get python version
        returns a tuple (True/False, message)
        True: CPYTHON is valid, message contains version 
        False: CPYTHON triggered an exception, message contains Exception message
    """
    import JTutils
    reload(JTutils) # in case an old JTutils was already installed and loaded
    import subprocess
    CMD = """
# coding: utf8
#from __future__ import unicode_literals
import sys
print(sys.version) """
    try:
        version = JTutils._run_string_ext_script(CMD)
        return (True, version)
    except subprocess.CalledProcessError, exc:
        return (False, exc.output)
    except OSError, exc:
        return (False, "OSError, unspecified")

def test_module_link():
    """
    test if XWINNMRHOME/jython/Lib/JTutils exists, 
    and is a link to current installation
    returns tuple (Bool, "message strings") :
    if True: message is "link is valid"
    if False: message is
        "missing" if no file exist
        "wrong link" if link exists but points to wrong location
        "wrong file" if regular file exists but is not a link
        "wrong dir" if file exists and is a directory
    """
    link_name = join_path(XWINNMRHOME, "jython", "Lib", "JTutils")
    link_target = normpath(abspath(join_path(dirname(sys.argv[0]), ".."))) 
    if not os.path.lexists(link_name):
        return (False, "missing")
    OS = get_os_version()
    if 'win' in OS:
        import subprocess
        dir_list = subprocess.check_output(['dir',  join_path(XWINNMRHOME, "jython", "Lib")], shell=True)
        os_encoding = 'cp850' 
        for line in dir_list.decode(os_encoding).splitlines():
            if 'JTutils' in line:
                break
        if '<JUNCTION>' in line:
            link = line[line.index('[')+1 : line.index(']')]
            if normpath(link) == link_target:
                return (True, "link is valid")
            else:
                return (False, "wrong link")
        elif '<SYMLINK>' in line:
            return (False, "wrong link")
        elif '<SYMLINKD>' in line:
            # it should be a JUNCTION but if SYMLINKD was created manually 
            # and points to correct location then it's OK
            link = line[line.index('[')+1 : line.index(']')]
            if normpath(link) == link_target:
                return (True, "link is valid")
            else:
                return (False, "wrong link")
        elif isfile(link_name):
            return (False, "wrong file")
        elif isdir(link_name):
            return (False, "wrong dir")
    else:
        if islink(link_name):
            if realpath(link_name) == link_target:
                return (True, "link is valid")
            else :
                return (False, "wrong link")
        elif isfile(link_name):
            return (False, "wrong file")
        elif isdir(link_name):
            return (False, "wrong dir")

def make_module_link():
    """
    create a symbolic link in XWINNMRHOME/jython/Lib to JTutils location
    """
    link_name = join_path(XWINNMRHOME, "jython", "Lib", "JTutils")
    link_target = normpath(abspath(join_path(dirname(sys.argv[0]), ".."))) 
    OS = get_os_version()
    import subprocess
    if 'win' in OS:
        link = "mklink"
        link_opt = "/j"
        try:
            subprocess.call([link, link_opt, link_name, link_target], shell=True)
        except subprocess.CalledProcessError, exc:
            MSG(exc.output)
            MSG("About to exit setup... Sorry")
            EXIT()
    else:
        link = "ln"
        link_opt = "-s"
        subprocess.call([which(link), link_opt, link_target, link_name])
    
def test_config_file():
    """ 
    Test if JTutils folder exists in USERHOME_DOT_TOPSPIN
    Try to read JTutils/config.json file
    Test if CPYTHON key exists and if is usable (returns a version number)
    returns a tuple (bool, message) where bool is True if config is valid, 
    if bool is False, message contains the error:
        DIR_NOT_FOUND: $USERHOME_DOT_TOPSPIN/JTtutils folder does not exist or cannot be read
        FILE_NOT_FOUND:  $USERHOME_DOT_TOPSPIN/JTtutils/config.json file does not exist or cannot be opened
        JSON_READ_FAILED:  $USERHOME_DOT_TOPSPIN/JTtutils/config.json is not a valid JSON
        CPYTHON_FAILED: CPYTHON entry found in $USERHOME_DOT_TOPSPIN/JTtutils/config.json is missing or does 
                        not point to a valid cpython interpreter
    """ 
    conf_path_dir = join_path(USERHOME_DOT_TOPSPIN, "JTutils")
    if not isdir(conf_path_dir):
        return (False, "DIR_NOT_FOUND: JTutils configuration folder not found in " + conf_path_dir)
    conf_path_file = join_path(conf_path_dir, "config.json")
    if not isfile(conf_path_file):
#        MSG(conf_path_file + " not found")
        return (False, "FILE_NOT_FOUND: JTutils configuration file not found at " + conf_path_file)
    try:
        import JTutils
        reload(JTutils) # in case an old JTutils was already installed and loaded
        config = JTutils._read_config()
    except:
        return (False, "JSON_READ_FAILED: failed reading config json file")
    CPYTHON = config.get('CPYTHON') # use dict.get to avoid exception if key doesn't exists
    test_success, message = test_CPYTHON(CPYTHON)
    if not test_success:
        return (False, "CPYTHON_FAILED: Interpreter %s failed to run with message \n %s" % (CPYTHON, message))
    return (True, "Configuration OK : %s version %s is a valid python interpreter." % (CPYTHON, message))

def select_external_python(*preselected):
    """ returns full_path_to_python_exe 
1) Search for python executable
2) The user choose among the preselected path, found path, or other
2a) If other the user selects the exe in filechooser 
3) If nothing found or returned, issue a message to install miniconda and exit program


Search for conda python in standard locations:
On windows: looks for python executable in 
%USERPROFILE%/Miniconda[23]/envs/JTutils_env
%USERPROFILE%/Miniconda[23]/
%USERPROFILE%/AppData/Local/Continuum/Anaconda[23]
"""

    # search default system path as returned by which function
    OS = get_os_version()
    if 'win' in OS:
        searched_python_exe = "python.exe"
    else:
        searched_python_exe = "python"
    found_default = which(searched_python_exe)
    if found_default != "":
        found_python_exe = [found_default]
    else:
        found_python_exe = []
    # search conda distribution
    # on windows
    if 'win' in OS:
        userpath = os.getenv("USERPROFILE").decode(sys_enc)
        path_list = [
            [ userpath, "Miniconda3", "envs", "JTutils","python.exe"],
            [ userpath, "Miniconda2", "envs", "JTutils","python.exe"],
            [ userpath, "Miniconda2","python.exe"],
            [ userpath, "Miniconda3","python.exe"],
            [ userpath, "APPDATA", "Local", "Continuum", "Anaconda2", "envs", "JTutils","python.exe"],
            [ userpath, "APPDATA", "Local", "Continuum", "Anaconda3","python.exe"],
            [ userpath, "APPDATA", "Local", "Continuum", "Anaconda2","python.exe"],
            [ userpath, "APPDATA", "Local", "Continuum", "Anaconda3","python.exe"],
        ]
    elif ('linux' in OS) or ('mac' in OS):
        userpath = os.getenv("HOME").decode(sys_enc)
        path_list = [
            [ userpath, "miniconda2", "envs", "JTutils", "bin", "python"],
            [ userpath, "miniconda3", "envs", "JTutils", "bin", "python"],
            [ userpath, "miniconda2", "bin", "python"],
            [ userpath, "miniconda3", "bin", "python"],
            [ userpath, "anaconda2", "envs", "JTutils", "bin", "python"],
            [ userpath, "anaconda3", "envs", "JTutils", "bin", "python"],
            [ userpath, "anaconda2", "bin", "python"],
            [ userpath, "anaconda3", "bin", "python"],
        ]

    for cur_path_test in path_list:
        test_path = join_path(*cur_path_test)
        if os.path.exists(test_path):
            found_python_exe.append(test_path)

    for pre in preselected:
        if pre not in found_python_exe:
            found_python_exe.insert(0,pre)
    found_python_exe.append("Other")
    found_python_exe_indexes = [str(i+1) for i,j in enumerate(found_python_exe)]
    select_message = '\n'.join(["Select the python you want to use"] + ["%d: %s"% (i+1, path) for i, path in enumerate(found_python_exe)])
    selected_python = SELECT(title="CPYTHON selection", message=select_message, buttons=found_python_exe_indexes)
    if found_python_exe[selected_python] == "Other":
        chooseUI = FileSelector(title="Choose a python interpreter", 
                                    defaultFile=found_python_exe[0])
        CPYTHON = chooseUI.get_file_name()
        if is_exe(CPYTHON):
            return CPYTHON
    else:
        CPYTHON = found_python_exe[selected_python]
        if is_exe(CPYTHON):
            return CPYTHON

    # no executable python found
    # message to inform failing to find an adequate python exe
    # propose to install miniconda
    quit_message =""" CPYTHON=%s is not an executable file:
Try another proposition or click Exit to install Miniconda following 
the instructions in Miniconda_Installation.odt found in JTutils 
main folder. Once done relaunch setup_JTutils
"Choose a New python executable or Quit ?"
""" % (CPYTHON,)
    select_val = SELECT(title="Exit?", 
                            message=quit_message,
                            buttons=["New", "Quit"],
                            mnemonics=["N", "Q"] )
    if select_val == 0:
        return select_external_python(*preselected)
    else:
        EXIT()

def guess_config(python_exe_full_path):
    """
    Then gets the path like how conda activate defines path
    If not found : MSG about downloading and installing miniconda
        if installed still ask for manual file chooser
    if found return CPYTHON and EXTRA_PATH fields
    """

#    to open a new window with cmd prompt with activated miniconda environment:
#        start %windir%\System32\cmd.exe "/K"  %USERPROFILE%\Miniconda2\Scripts\activate.bat  JTutils

    CPYTHON = python_exe_full_path
    import subprocess

    OS = get_os_version()
    if 'win' in OS:
        CONDA_EXE = ['condabin', 'conda.bat']
    else: #unix (linux or mac)
        CONDA_EXE = ['condabin', 'conda']

    #split path into folder list
    splited_path_to_python = []
    head = python_exe_full_path
    i = 0
    tail = "start"
    while tail != "":  
        head, tail = split_path(head)
        if tail != "":
            splited_path_to_python.append(tail)
    splited_path_to_python.append(head)
    splited_path_to_python.reverse()
    
    # test if provided file is from conda distribution and initialize conda_base and conda_exe
    conda_exe = False
    for neg_index_base in range(1,len(splited_path_to_python)):
        tmp = splited_path_to_python[:-neg_index_base]+CONDA_EXE
        tested_file = join_path(*tmp)
        if is_exe(tested_file):
            conda_exe = tested_file
            conda_base = join_path(*splited_path_to_python[:-neg_index_base])
            break
    if conda_exe == False:
        MSG("This doesn't seem to be a conda (miniconda/anaconda) distribution. Can be fine: check the report.")
        return { 'CPYTHON': python_exe_full_path}
        
    # now I have the base and conda_exe and we are in conda distribution
    # which environement is the python_exe_full_path from ?
    # check if JTutils environement exists
    if 'win' in OS:
        if neg_index_base < 2 :
            conda_env = 'base'
        else:
            if splited_path_to_python[-3].lower() == 'envs' :
                conda_env = splited_path_to_python[-2]
            else: 
                raise ValueError("Conda distribution seems inconsistent !")
    else: # macosx or linux
        if neg_index_base < 3 :
            conda_env = 'base'
        else:
            if splited_path_to_python[-4].lower() == 'envs' :
                conda_env = splited_path_to_python[-3]
            else: 
                raise ValueError("Conda distribution seems inconsistent !")
    # yes we are in JTutils environment
    # if JTutils does not exist ask of automatic installation    
    if conda_env != 'JTutils':
        if 'win' in OS:
            new_python_exe = join_path(conda_base, 'envs', 'JTutils', 'python.exe')
        else:
            new_python_exe = join_path(conda_base, 'envs', 'JTutils', 'bin', 'python')  
            
        select_val = SELECT(title="Create JTutils environnent (recommended)", 
                            message="""JTutils conda environment not found. %s is found. 
Do you want to create JTutils python environment (recommended)?
If Yes, new python exe file will be selected : %s
Please CLICK on one button (enter on keyboard does not work)""" % (conda_env, new_python_exe) ,
                            buttons=["Yes", "No"],
                            mnemonics=["y", "n"] )
        if select_val == 0 :
            # first check JTutils does not exists already:
            if is_exe(new_python_exe):
                pass
            else: # run install script
                if 'win' in OS:
                    cmd = " ".join([conda_exe, "activate &",
                                   conda_exe, "create -y -n JTutils numpy matplotlib pyqt h5py scipy&",
                                   conda_exe, "env list"])
                else: # unix
                    # default jython shell is /bin/sh : source command is "."
                    # first source the conda initialisation script
                    # once done conda is available as a shell internal command
                    shell_init_file = join_path(conda_base,'etc', 'profile.d', 'conda.sh')
                    cmd = " ".join([".", shell_init_file, ";",
                                  "conda create -y -n JTutils " + ssnake_conda_pack + ";", 
                                  "conda env list"])
                MSG(subprocess.check_output(cmd, shell=True))
                MSG("JTutils environment created")
            CPYTHON = new_python_exe
            conda_env = 'JTutils'

    if 'win' in OS:
#        batfile = join_path(dirname(abspath(sys.argv[0])), "..", "condat_env_setup.bat")
#        cmd = ["start", "%windir%\system32\cmd.exe", "/k",  batfile + " " + found_path + " JTutils"]
        cmd = " ".join([
                      join_path(conda_base,'condabin', 'activate.bat'), conda_env,
                        '& set CONDA',
                        '& set PATH'])
                        
    elif ('linux' in OS) or ('mac' in OS):
        # default shell is /bin/sh : source command is "."
        # first source the conda initialisation script
        # once done conda is available as a shell internal command
        shell_init_file = join_path(conda_base,'etc', 'profile.d', 'conda.sh')
        cmd = " ".join([
                        ".", shell_init_file, ";",
                        "conda activate", conda_env, ";"
                        "env |grep -i CONDA ; echo PATH=$PATH" ])
    try:
#        MSG(cmd)
        res = subprocess.check_output(cmd, shell=True)
        res = res.decode(sys_enc)
    except subprocess.CalledProcessError as grepexc:
        grepexc = grepexc.decode(sys_enc)
        print("error code", grepexc.returncode, grepexc.output)
        MSG("Error during retrieval of conda environment.")
        raise

    # now Parse the returned string to extract conda env vars 
    conf_dict = dict()
    for line in res.split('\n'):
        line = line.strip()
        if '=' in line:
            key, val = line.split('=', 1)
            if 'PATH' == key.upper():
                path_list = val.split(';')
                extra_path = []
                # windows is not case sensitive : required for valid string comparison
                if 'win' in OS : cb = conda_base.lower() 
                else : cb = conda_base
                for one_path in path_list:
                    if 'win' in OS : op = one_path.lower() 
                    else: op = one_path
                    if cb in op:
                        extra_path.append(one_path)
                conf_dict['EXTRA_PATH'] = extra_path
            else:
                if 'CONDA' in key.upper():
                    conf_dict[key] = val
    conf_dict['CPYTHON'] = CPYTHON
        
    return conf_dict

def create_report():
    """
    Run tests and dispay or save a report on current configuration
    1) read a few parameters (jython version, cwd, os, etc.
    2) report link consistency
    3) check for modules within TOPSPIN
    4) check for external PYTHON
    5) check for required modules in external python
    6) display report
    7) write report in a file
    """
    # report basic information :
    version = sys.version
    var_env = os.environ
    curdir = os.getcwd().decode(sys_enc)
    scriptFile = sys.argv[0]
    scriptDir = dirname(sys.argv[0])
    CpyLibDir = scriptDir + '/../CpyLib'
    CpyBinDir = scriptDir + '/../CpyBin'

    report_message = """Current python version is: %s
    Current working directory is : %s
    Current python script is : %s
    CpyLib is : %s
    CpyBin is : %s
    XWINNMRHOME is : %s
    Preferences directory is : %s

    """ % (version,  curdir, scriptFile, CpyLibDir, CpyBinDir, XWINNMRHOME, USERHOME_DOT_TOPSPIN) 
    
    import_report = "JTutils jython module requirement:\n"
    # test if modules can be imported in topspin
    jmodule_imported = {}
    for module in ['JTutils', 'JTutils.CpyLib.brukerPARIO', 'argparse']:
        jmodule_imported[module], version_message = test_jmodule_import(module)
        if jmodule_imported[module]:
            import_report += "%s %s module imported successfully\n" % (module, version_message)
        else:
            import_report += "ERROR: %s module import FAILED.\n %s\n" % (module, version_message)
            if module == 'argparse':
                import_report += """
                    You should consider installing argparse.py  in %s  
                    argparse.py module file can be downloaded from https://pypi.org/project/argparse/ website
                    """ % (XWINNMRHOME + "/jython/Lib/")
    # how to run tests for external python configuration ?
    # need to test that python can run, can import argparse, numpy and processing and return respective versions

    WarningCpython = "Checking CPYTHON configuration\n"
    success, message = test_config_file()
    WarningCpython += message + '\n'
    if success:
        cmodule_imported = {}
        for module in ["numpy", "argparse", "multiprocessing", "brukerIO"] + ssnake_modules:
            cmodule_imported[module], version_message = test_cmodule_import(module)
            if cmodule_imported[module]:
                WarningCpython += "%s %s module imported successfully\n" % (module, version_message)
            else:
                WarningCpython += "ERROR: %s module import FAILED.\n %s\n" % (module, version_message)
                if module in ssnake_modules:
                    WarningCpython += "You will not be able to call ssNake from JTutils tools!\n"
                    

    report_message += import_report
    report_message += WarningCpython
    MSG(report_message)

    env_list = "\nList of defined environment variables\n"
    env_list += "\n".join(["%s: %s" % (key, var_env[key]) for key in var_env.keys()])
    report_message += env_list

    save_report = CONFIRM(title="Save report", message="Do you want to save the report in a file ?")
    if save_report :
        # add a file dialog to choose the directory and filename where to store report
        f = open("report.txt", 'w')
        f.write(report_message)
        f.write(env_list)
        f.close()
        MSG("""report written in %s.""" % (curdir + "/report.txt", ))


from java.io import File
from java.awt import BorderLayout
from javax.swing import JFileChooser, JFrame, JPanel
class FileSelector(JFrame):
    """ 
    Opens a file selector dialog 
    The class object launch the UI and stores the result in a class instance variable
    The selected filename is returned by get_file_name class function
    False is returned if cancel button is pressed
    The filename is returned if OK button is pressed
    """

    def __init__(self, hidden=False, dir_only=False, title='', defaultFile=''):
        super(FileSelector, self).__init__()
        self.file_name = None
        self.initUI(hidden, dir_only,  title, defaultFile)

    def initUI(self, hidden, dir_only, title, defaultFile):
        self.panel = JPanel()
        self.panel.setLayout(BorderLayout())
        chosenFile = JFileChooser()
        sel_file = File(defaultFile)
        chosenFile.setSelectedFile(sel_file)
        chosenFile.setDialogTitle(title)
        if dir_only:
            chosenFile.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        chosenFile.setFileHidingEnabled(hidden)

        ret = chosenFile.showOpenDialog(self.panel)

        if ret == JFileChooser.APPROVE_OPTION:
            if dir_only:
                if chosenFile.getSelectedFile().isDirectory():
                    self.file_name = str(chosenFile.getSelectedFile())
            else:
                self.file_name = str(chosenFile.getSelectedFile())
        else:
            self.file_name = False
            # MSG("setup canceled")
            # EXIT()

    def get_file_name(self):
        return self.file_name

def write_config(config): # cannot rely on JTutils write config if config is not set properly as module cannot loaf in that case
    """ write json config file in user topspin preference folder 
        (.topspin1 for example)
        argument config is a dictionnary with configuration parameters
    """
    import json
    prop_dir = os.getenv('USERHOME_DOT_TOPSPIN', "not defined").decode(sys_enc)
    if prop_dir == "not defined":
        print("USERHOME_DOT_TOPSPIN not defined")
        raise
    config_file = os.path.join(normpath(prop_dir),'JTutils','config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f)



def update_config():
    """ Configure JTutils :
    Create link to jython/Lib TOPSPIN sub-folder so that JTutils can be imported as a module.
    Ask for an external python interpreter (CPYTHON), and extra path requirement (mainly conda related distribution)
    write USERHOME_DOT_TOPSPIN/JTutils/config.json file
    launch a report
    """

    (is_valid_link, link_status) = test_module_link()
    #    "missing" if no file exist
    #    "wrong link" if link exists but points to wrong location
    #    "wrong file" if regular file exists but is not a link
    #    "wrong dir" if file exists and is a directory
    #    "OK" if file is a link to the right location
    link_name = join_path(XWINNMRHOME, "jython", "Lib", "JTutils")
    if is_valid_link:
        pass
    elif link_status == "missing":
        make_module_link()
    elif link_status == "wrong link":
        if isdir(link_name):
            os.rmdir(link_name)
        else:
            os.remove(link_name)
        make_module_link()
    elif link_status == "wrong file":
        os.remove(link_name)
        make_module_link()
    elif link_status == "wrong dir":
        from shutil import rmtree
        rmtree(link_name)
        make_module_link()

    # but some functions that require 
    # external cpython through run_CpyBin_script may still fail if setup is not correct
    # check configuration file
    success, message = test_config_file()
    if not success:
        if 'DIR_NOT_FOUND' in message:
            os.mkdir(join_path(USERHOME_DOT_TOPSPIN, "JTutils"))
            success, message = test_config_file()
        config = {}
        cpython = select_external_python()
    else :
        import JTutils
        reload(JTutils)
        config = JTutils._read_config()
        foundCPYTHON = config['CPYTHON']
        cpython = select_external_python(foundCPYTHON)
    config = guess_config(cpython)
    write_config(config)

    #now we can try to import JTutils
    import JTutils
    reload(JTutils)
#    MSG(str(config))
    create_report()
    
        
if __name__ == '__main__':
#    Menu : report/test, new config, update config
#    MSG(str(test_config_file()))
#    MSG(get_os_version())
#    EXIT()
#    cpython = select_external_python()
#    MSG('\n'.join( ['%s=%s' % (key,value) for key, value in guess_config(cpython).items()]))
#    cpython, dir_list = search_conda_python()
#    MSG("\n".join(dir_list['PATH']))
#    EXIT()
    #setup()

    # argparse prints help messages to stdout and error to stderr so we need to redirect these
    from StringIO import StringIO
    import sys
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    my_stdout = StringIO()
    sys.stdout = my_stdout
    sys.stderr = my_stdout
    try : 
        import argparse
        parser  =  argparse.ArgumentParser(
            description='Setup JTutils, making required links and selecting external python')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-r', '--report', 
            help='Report on current installation', action='store_true')
        group.add_argument('-s', '--setup', action='store_true', 
            help='Setup the configuration file and required links')
        args  =  parser.parse_args(sys.argv[1:])
    except ImportError:
        if len(sys.argv) > 1:
            MSG("Argparse module not found!\n Arguments won't be processed")
        class dummy():
            def __init__(self):
                self.setup = True
                self.report = False
        args = dummy()
    except SystemExit:
        # argparse has triggered an exception : print the error in a MSG box
        # and restore the stdout and err
        err_msg = my_stdout.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        MSG(err_msg)
        print(err_msg)
        EXIT()

    err_msg = my_stdout.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    print(err_msg)
    if args.report:
        create_report()
    else:
        update_config()
        


