# -*- coding: utf-8 -*-
# get information on current setup
# print information in MSG box, in console and it should propose to save
# the report in a file
# this Script will serve as setup to detect/define CPYTHON in a config file
# There should be different tests functions, a report function and a setup


import sys
import os
from os.path import abspath, dirname, normpath, join, isdir, isfile


# This script should be called from within topspin so these should be defined
XWINNMRHOME = os.getenv('XWINNMRHOME', "undefined")
USERHOME_DOT_TOPSPIN = os.getenv('USERHOME_DOT_TOPSPIN', "undefined")

# these env variables will become obsolete
# one should get the values from JTutils module
#CPYTHON = os.getenv('CPYTHON', "not defined")
#PYTHONPATH = os.getenv('PYTHONPATH', "not defined")
#
#if (abspath(CpyLibDir) != abspath(PYTHONPATH)):
#   WarningLibDir = """Warning : JTutils folder structure and PYTHONPATH are not consistent. 
#You should make sure that PYTHON points to %s""" % (abspath(CpyLibDir),)
#else :  WarningLibDir =  ""


def is_conda_python(CPYTHON):
    """ check if CPYTHON exe is related to a conda distribution
        return True if conda-meta file is found in same directory as CPYTHON interpreter
   """
    return os.path.isdir(os.path.join(dirname(CPYTHON), "conda-meta"))

def get_os_version():
    """ returns the underlying OS as string: either win, linux or mac """ 
    version = sys.platform.lower()
    if version.startswith('java'):
        import java.lang
        version = java.lang.System.getProperty("os.name").lower()
    return version

def test_jmodule_import(module_name):
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
    import JTutils
    CMD = """
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
    import JTutils
    import subprocess
    CMD = """import sys
print(sys.version) """
    try:
        version = JTutils._run_string_ext_script(CMD)
        return (True, version)
    except subprocess.CalledProcessError, exc:
        return (False, exc.output)
    except OSError, exc:
        return (False, "OSError, unspecified")

def check_module_link():
    """
    Check if XWINNMRHOME/jython/Lib/JTutils exists, 
    and is a link to current installation
    returns strings :
        "missing" if no file exist
        "wrong link" if link exists but points to wrong location
        "wrong file" if regular file exists but is not a link
        "wrong dir" if file exists and is a directory
        "OK" if file is a link to the right location
    """
    link_name = join(XWINNMRHOME, "jython", "Lib", "JTutils")
    link_target = normpath(abspath(join(dirname(sys.argv[0]),".."))) 
    if not os.path.lexists(link_name):
        return "missing"
    OS = get_os_version()
    if 'win' in OS:
        import subprocess
        dir_list = subprocess.check_output(['dir',  join(XWINNMRHOME, "jython", "Lib")], shell=True)
        os_encoding = 'cp850' 
        for line in dir_list.decode(os_encoding).splitlines():
            if 'JTutils' in line:
                break
        if '<JUNCTION>' in line:
            link = line[line.index('[')+1 : line.index(']')]
            if os.path.normpath(link) == link_target:
                return "OK"
            else:
                return "wrong link"
        elif '<SYMLINK>' in line:
            return "wrong link"
        elif '<SYMLINKD>' in line:
            # it should be a JUNCTION but if SYMLINKD was created manually 
            # and points to correct location then it's OK
            link = line[line.index('[')+1, line.index(']')]
            if os.path.normpath(link) == link_target:
                return "OK"
            else:
                return "wrong link"
        elif os.path.isfile(link_name):
            return "wrong file"
        elif os.path.isdir(link_name):
            return "wrong dir"
    else:
        if os.path.islink(link_name):
            if os.path.realpath(link_name) == link_target:
                return "OK"
            else :
                return "wrong link"
        elif os.path.isfile(link_name):
            return "wrong file"
        elif os.path.isdir(link_name):
            return "wrong dir"

def make_module_link():
    """
    create a symbolic link in XWINNMRHOME/jython/Lib to JTutils location
    """
    link_name = join(XWINNMRHOME, "jython", "Lib", "JTutils")
    link_target = normpath(abspath(join(dirname(sys.argv[0]),".."))) 
    OS = get_os_version()
    import subprocess
    if 'win' in OS:
        link = "mklink"
        link_opt = "/j"
        try:
            subprocess.call([link, link_opt, link_name, link_target], shell=True)
        except subprocess.CalledProcessError, exc:
            MSG(exc.output)
            EXIT()
    else:
        link = "ln"
        link_opt = "-s"
        subprocess.call([which(link), link_opt, link_target, link_name])

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    path_env = os.environ["PATH"].split(os.pathsep)
    # On windows, I need to add a search in conda standard location:
    # os.environ['USERPROFILE']/*conda*
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in path_env:
            exe_file = join(path, program)
            if is_exe(exe_file):
                return exe_file
    return ""

    
def check_config_file():
    """ 
    Test if JTutils folder exists in USERHOME_DOT_TOPSPIN
    Try to read JTutils/config.json file
    Test if CPYTHON key exists and if is usable
    returns a tuple (bool, message) where bool is True if config is valid, 
    if bool is False, message contains the error
    """ 
    import JTutils
    conf_path_dir = join(USERHOME_DOT_TOPSPIN,"JTutils")
    if not isdir(conf_path_dir):
        return (False, "DIR_NOT_FOUND: JTutils configuration folder not found in " + conf_path_dir)
    conf_path_file = join(conf_path_dir,"config.json")
    if not os.path.isfile(conf_path_file):
        MSG((conf_path,"config.json"))
        return (False, "FILE_NOT_FOUND: JTutils configuration file not found at " + conf_path)
    try:
        config = JTutils._read_config()
    except:
        return (False, "JSON_READ_FAILED: failed reading config json file")
    CPYTHON = config['CPYTHON']
    test_success, message = test_CPYTHON(CPYTHON)
    if not test_success:
        return (False, "CPYTHON_FAILED: Interpreter %s failed to run" % (CPYTHON,))
    return (True, "Configuration OK : %s is a valid python interpreter." % (CPYTHON,))

def create_report():
    """
    Run tests and dispay or save a report on current configuration
    1) read a few parameters (jython version, cwd, os, etc.
    2) check for modules within TOPSPIN
    3) check for external PYTHON
    4) check for required modules in external python
    5) display report
    6) write report in a file
    """
    # report basic information :
    version = sys.version
    var_env = os.environ
    curdir = os.getcwd()
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


    """ % (version,  curdir, scriptFile, CpyLibDir, CpyBinDir, XWINNMRHOME) 
    
    import_report = "JTutils jython module requirement:\n"
    # test if modules can be imported in topspin
    jmodule_imported = {}
    for module in ['JTutils', 'JTutils.CpyLib.brukerPAR', 'argparse']:
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
    success, message = check_config_file()
    WarningCpython += message + '\n'
    if success:
        cmodule_imported = {}
        for module in ["numpy", "argparse", "multiprocessing", "bruker"]:
            cmodule_imported[module], version_message = test_cmodule_import(module)
            if cmodule_imported[module]:
                WarningCpython += "%s %s module imported successfully\n" % (module, version_message)
            else:
                WarningCpython += "ERROR: %s module import FAILED.\n %s\n" % (module, version_message)

    report_message += import_report
    report_message += WarningCpython
    MSG(report_message)

    env_list = "\nList of defined environment variables\n"
    env_list += "\n".join(["%s: %s" % (key,var_env[key]) for key in var_env.keys()])
    #print(env_list)

    save_report = CONFIRM(title="Save report", message="Do you want to save the report in a file ?")
    if save_report :
        # add a file dialog to choose the directory and filename where to store report
        f = open("report.txt",'w')
        f.write(report_message)
        f.write(env_list)
        f.close()
        MSG("""report written in %s.""" % (curdir+"/report.txt",))


from java.io import File
from java.awt import BorderLayout
from javax.swing import JFileChooser, JFrame, JPanel
class FileSelector(JFrame):
    """ Opens a file selector dialog """

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
            EXIT()

    def get_file_name(self):
        return self.file_name


def setup():
    """ Configure JTutils :
    Create link to jython/Lib TOPSPIN sub-folder so that JTutils can be imported as a module.
    Ask for an external python interpreter (CPYTHON), and extra path requirement (mainly conda related distribution)
    write USERHOME_DOT_TOPSPIN/JTutils/config.json file
    launch a report
    """

    link_status = check_module_link()
    #    "missing" if no file exist
    #    "wrong link" if link exists but points to wrong location
    #    "wrong file" if regular file exists but is not a link
    #    "wrong dir" if file exists and is a directory
    #    "OK" if file is a link to the right location
    link_name = join(XWINNMRHOME, "jython", "Lib", "JTutils")
    if link_status == "OK":
        pass
    elif link_status == "missing":
        make_module_link()
    elif link_status == "wrong link":
        if os.path.isdir(link_name):
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

    import JTutils
    success, message = check_config_file()
    if not success:
        if 'DIR_NOT_FOUND' in message:
            os.mkdir(join(USERHOME_DOT_TOPSPIN,"JTutils"))
            success, message = check_config_file()
        config = {}
        if os == 'win':
            CPYTHON_name = 'python.exe' 
        else :
            CPYTHON_name = 'python' 
        foundCPYTHON = which(CPYTHON_name)
    else :
        config = JTutils._read_config()
        foundCPYTHON = config['CPYTHON']
    chooseUI = FileSelector(title="Choose a python interpreter", 
                                    defaultFile=foundCPYTHON)
    CPYTHON = chooseUI.get_file_name()
    config['CPYTHON'] = CPYTHON
    if is_conda_python(CPYTHON):
        config['PATH_EXTRA'] = [dirname(CPYTHON), 
                                join(dirname(CPYTHON), "Scripts"),
                                join(dirname(CPYTHON), "Library"),
                                join(dirname(CPYTHON), "Library", 'bin'),
                                join(dirname(CPYTHON), "DLLs"),
                                ]
    JTutils._write_config(config)
    create_report()
    
        
if __name__ == '__main__':
#    MSG(str(check_config_file()))
    setup()
