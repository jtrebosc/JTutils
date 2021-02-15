# -*- coding: utf-8 -*-
import os
import subprocess
import sys

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

def get_os_version():
    """ returns the underlying OS as string: either win, linux or mac """ 
    ver = sys.platform.lower()
    if ver.startswith('java'):
        import java.lang
        ver = java.lang.System.getProperty("os.name").lower()
    return ver

_OS = get_os_version()
# _OS should be in [ 'win', 'linux', 'mac os x']

default_wine_path = which('wine')
prop_dir = os.getenv('USERHOME_DOT_TOPSPIN', "not defined")
environment_var = os.environ.copy()

def read_config_file():
    """ read config file and returns a dictionnary
If no default declared, first entry is default
"""
    config = dict()
    config_file = os.path.join(prop_dir,'JTutils','dmfit.path')
    if not os.path.exists(config_file):
        return config
    with open(config_file, 'r') as f:
        key = None
        for line in f:
            line = line.strip()
            if line.startswith('['):
                key = line.lstrip('[')
                key = key.rstrip(']')
                config[key] = dict()
                continue
            if key is not None:
                for keyword in ['DMFITPATH', 'WINEPATH', 'WINEPREFIX', 'DEFAULT']:
                    if line.startswith(keyword):
                        _, config[key][keyword] = line.split('=')
                        config[key][keyword] = config[key][keyword].strip()
        for key in config.keys():
            if 'DEFAULT' not in config[key].keys():
                config[key]['DEFAULT'] = False
            else:
                print 
                config[key]['DEFAULT'] = (config[key]['DEFAULT'] == '1')
    return config 

def write_config_file(config):
    """ Write a configuration file for dmfit given a dictionnary """

    config_dir = os.path.join(prop_dir,'JTutils')
    # test if JTutils folder exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    config_file = os.path.join(prop_dir,'JTutils','dmfit.path')
    
    with open(config_file, 'w') as f:
        for key in config.keys():
            f.write('['+key+']')
            f.write('\n')
            for keyword in config[key].keys():
                if keyword == 'DEFAULT':
                    if  config[key][keyword]:
                        f.write("=".join([keyword, '1']))
                    else:
                        f.write("=".join([keyword, '0']))
                else:
                    f.write("=".join([keyword, config[key][keyword]]))
                f.write('\n')
                
                
def check_config(config):
    pass

def run_setup():
    config = read_config_file()
    setup_panel = ConfigPanel(config)
#    dmfitpath = select_dmfitpath()
#    MSG(dmfitpath)
#    winepath = select_winepath()
#    MSG(winepath)
# check if file already exists
# parse the file
# check for validity of each entry
# return info on validity
# ask for update (edit/add/delete)
# dmfit location
# wine exe
# wine prefix
# check for validity
# add entry
# ask for update (loop)
# write file

from java.io import File
from java.awt import BorderLayout, Dimension
from javax.swing import JFileChooser, JFrame, JPanel, JLabel, JButton, JRadioButton, ButtonGroup, BoxLayout, Box, JTextField, JDialog

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
        chosenFile.setSelectedFile(File(defaultFile))
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

    def get_file_name(self):
        return self.file_name


class ConfigPanel(JFrame):

    class SetKey(JDialog):
        def __init__(self, button=None):
            super(ConfigPanel.SetKey, self).__init__()
            self.setTitle('Enter version label')
            self.setModal(True)
            if button is None:
                self.button = JButton()
            else:
                self.button = button
            self.initUI()
            
        def initUI(self):
            self.JP = JPanel()
            self.JL = JLabel('Set version label: enter to validate')
            self.JP.add(self.JL)
            self.JTF = JTextField(self.button.getText(), 10)
            self.JTF.actionPerformed = self.doit
            self.JP.add(self.JTF)
            self.add(self.JP)
            self.pack()
            self.setLocation(150,150)
            self.setVisible(True)
            
        def doit(self,event):
            key = self.JTF.getText()
            self.button.setText(self.JTF.getText())
            self.dispose()
        

    def __init__(self, config=dict()):
        super(ConfigPanel, self).__init__()
        self.setTitle('DMFIT setup')
        self.config = config.copy()
        self.param_list = ['DMFITPATH', 'WINEPATH', 'WINEPREFIX', 'DEFAULT']
        self.actions_list = {'DMFITPATH': self.set_dmfitpath, 'WINEPATH': self.set_winepath, 'WINEPREFIX': self.set_wineprefix}
        self.initUI(self.config)

    def update_config_from_UI(self):
        config = dict()
        for keyUI in self.config_item_dict.keys():
            key =  self.config_item_dict[keyUI]['JB'].getText()
            config[key] = dict()
            for param in self.config_item_dict[keyUI].keys():
                if param not in self.param_list:
                    continue
                if param == 'DEFAULT':
                    config[key][param] = self.config_item_dict[keyUI][param]['JRB'].isSelected()
                else:
                    print(type(self.config_item_dict[keyUI][param]))
                    config[key][param] = self.config_item_dict[keyUI][param]['JB'].getText()
        self.config = config
        print self.config

    def add_entry(self, event):
        # get key, 
        new_version = dict()
        dummyJB = JButton()
        ConfigPanel.SetKey(dummyJB)
        key = dummyJB.getText()
        del dummyJB
        if key == '':
            return

        winepath=None
        wineprefix=None
        dmfitpath = select_dmfitpath()
        if dmfitpath is None:
            return
        new_version['DMFITPATH'] = dmfitpath
        if  'win' not in _OS : # then one must use WINE
            winepath = select_winepath()
            if winepath is None:
                return
            new_version['WINEPATH'] = winepath
            wineprefix = self.guess_wineprefix(dmfitpath)
            if wineprefix is None:
                return    
            new_version['WINEPREFIX'] = wineprefix
        new_version['DEFAULT'] = False
        self.add_UI_entry(key, new_version)
        self.revalidate()
        
    def remove_entry(self,event):
        selectedRB = None
        for i in  self.select_key_rb_group.getElements():
            if i.isSelected():
                selectedRB = i
                break
        if selectedRB is None:
            return
        self.select_key_rb_group.remove(selectedRB)
        key = self.hash4keys[selectedRB]
        self.select_default_rb_group.remove(self.config_item_dict[key]['DEFAULT']['JRB'])
        self.panelEntries.remove(self.config_item_dict[key]['JP'])
        self.revalidate()
        del self.config_item_dict[key]
        self.pack()

    def save_config(self,event):
        self.update_config_from_UI()
        write_config_file(self.config)
        self.dispose()

    def guess_wineprefix(self, path):
        head, tail = os.path.split(path)
        while tail != 'drive_c' and tail != '':
            head, tail = os.path.split(head)
        if tail == '':
            "ask for explicit wine prefix"
            chooseUI = FileSelector(hidden=True, dir_only=True, title='Select WINEPREFIX')
            wineprefix = chooseUI.get_file_name()
        else :
            wineprefix = head
        return wineprefix

    def set_dmfitpath(self, event):
        button = event.getSource()
        old_path = button.getText()
        path = select_dmfitpath(defaultFile=old_path)
        if path is None:
            return
        button.setText(path)
        if 'win' not in _OS : # let's guess wineprefix
            wineprefix = self.guess_wineprefix()
            key = self.hash4keys[button]
            self.config_item_dict[key]['WINEPREFIX']['JB'].setText(wineprefix)

    def set_wineprefix(self, event):
        button = event.getSource()
        old_path = button.getText()
        chooseUI = FileSelector(hidden=False, dir_only=True, title='Select WINEPREFIX')
        path = chooseUI.get_file_name()
        if path is None:
            return
        button.setText(path)

    def set_winepath(self, event):
        button = event.getSource()
        old_path = button.getText()
        path = select_winepath(defaultFile=old_path)
        if path is None:
            return
        button.setText(path)
        
    def set_key(self, event):
        button = event.getSource()
        SK = ConfigPanel.SetKey(event.getSource())

    def add_UI_entry(self,key, dico=dict()):
        UI_key_dict = dict()
        UI_key_dict['JP'] = JPanel()
        UI_key_dict['JP'].setLayout(BoxLayout(UI_key_dict['JP'], BoxLayout.X_AXIS))
        UI_key_dict['JRB'] = JRadioButton()
        self.select_key_rb_group.add(UI_key_dict['JRB'])
        self.hash4keys[UI_key_dict['JRB']] = key
        UI_key_dict['JB'] = JButton(key, actionPerformed=self.set_key)
        UI_key_dict['JB'].setPreferredSize(Dimension(100,25))
        UI_key_dict['JPP'] = JPanel()

        UI_key_dict['JP'].add(UI_key_dict['JRB'])
        UI_key_dict['JP'].add(UI_key_dict['JB'])
        UI_key_dict['JP'].add(Box.createRigidArea(Dimension(15, 0)))
        UI_key_dict['JP'].add(UI_key_dict['JPP'])
        UI_key_dict['JPP'].setLayout(BoxLayout(UI_key_dict['JPP'], BoxLayout.Y_AXIS))
        self.panelEntries.add(UI_key_dict['JP'])
        for param in self.param_list:
            if param not in dico.keys(): continue
            if param == 'DEFAULT':
                UI_key_dict[param] = {'JP':JPanel(), 'JRB': JRadioButton('is Default')}
                UI_key_dict[param]['JP'].setLayout(BoxLayout(
                                    UI_key_dict[param]['JP'], BoxLayout.X_AXIS))
                UI_key_dict[param]['JP'].add(UI_key_dict[param]['JRB'])
                UI_key_dict[param]['JP'].add(Box.createHorizontalGlue())
                self.select_default_rb_group.add(UI_key_dict[param]['JRB'])
                UI_key_dict['JPP'].add(UI_key_dict[param]['JP'])
                UI_key_dict[param]['JRB'].setSelected(dico[param])
                self.hash4keys[UI_key_dict[param]['JRB']] = key
                continue
            UI_key_dict[param] = { 'JP':JPanel(), 'JL': JLabel(param+": "), 
                                 'JB': JButton(dico[param]) }
            self.hash4keys[UI_key_dict[param]['JB']] = key
            UI_key_dict[param]['JL'].setPreferredSize(Dimension(100,25)) 
            UI_key_dict[param]['JB'].actionPerformed = self.actions_list[param] 
            UI_key_dict[param]['JP'].setLayout(BoxLayout(UI_key_dict[param]['JP'], BoxLayout.X_AXIS))
            UI_key_dict[param]['JP'].add(UI_key_dict[param]['JL'])
            UI_key_dict[param]['JP'].add(UI_key_dict[param]['JB'])
            UI_key_dict[param]['JP'].add(Box.createHorizontalGlue())
            UI_key_dict['JPP'].add(UI_key_dict[param]['JP'])
        UI_key_dict['JPP'].add(Box.createRigidArea(Dimension(0, 20)))
        self.config_item_dict[key]=UI_key_dict
        self.pack()
        pass

    def initUI(self, config):
        self.setLayout(BoxLayout(self.getContentPane(), BoxLayout.Y_AXIS))
        self.entries = config.keys()
        self.hash4keys = dict()

        self.panelEntries = JPanel()
        self.panelEntries.setLayout(BoxLayout(self.panelEntries,BoxLayout.Y_AXIS))
        self.add(self.panelEntries)

        #buttons
        self.panelButtons = JPanel()
        self.panelButtons.setLayout(BoxLayout(self.panelButtons,BoxLayout.X_AXIS))
        #'Configuration list:')
        self.addB = JButton('Add')
        self.addB.actionPerformed = self.add_entry
        self.removeB = JButton('Remove')
        self.removeB.actionPerformed = self.remove_entry
        self.saveB = JButton('Save')
        self.saveB.actionPerformed = self.save_config
        # pack buttons
        self.add(self.panelButtons)
        self.panelButtons.add(self.addB)
        self.panelButtons.add(self.removeB)
        self.panelButtons.add(self.saveB)

        self.config_item_dict = {}
        self.select_key_rb_group = ButtonGroup()
        self.select_default_rb_group = ButtonGroup()
        for key in self.entries:
            if key == 'default':
                continue
            self.add_UI_entry(key, config[key])
        self.pack()
        self.setLocation(150,150)

        self.setVisible(True)

def select_winepath(hidden=False, dir_only=False, title="Select wine executable", defaultFile=which('wine')): 
    chooseUI = FileSelector(hidden, dir_only, title, defaultFile)
    return chooseUI.get_file_name()
def select_dmfitpath(hidden=(_OS == 'win'), dir_only=False, title='Select DMFIT executable', defaultFile=''):
    chooseUI = FileSelector(hidden, dir_only, title, defaultFile)
    # note : WINEPREFIX should be set from dmfitpath
    return chooseUI.get_file_name()

if __name__ == "__main__" :
    run_setup()
