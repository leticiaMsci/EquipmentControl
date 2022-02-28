#%%
import sys
import os
import time
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
equip_control_path = 'C:/Users/lpd/Documents/Leticia/DFS/EquipmentControl'
sys.path.insert(1, equip_control_path)

from equipment_init import init_equip
import leticia_lib as llb
import piezo_routines as piezo
import cband_sweep as cbs
import WavelengthCalibration.wavelength_calibration as wc
import pyLPD.MLtools as mlt
import WavelengthCalibration.piezo_fsc as pz


class MainWindow(QMainWindow):
    def __init__(self,pm):
        super(MainWindow, self).__init__()

        scriptDir = os.path.dirname(os.path.realpath("control_app.py"))
        #self.setWindowIcon(QIcon(scriptDir + os.path.sep + 'extras/icons/LOGO.png'))


        self.OuterLayout = QGridLayout() # Parent layout

        self.Visor = QLineEdit("0.0")                                      # It starts with 0.0
        self.Visor.setFixedWidth(80)
        self.Visor.setAlignment(Qt.AlignCenter)
        self.Visor.setReadOnly(True)


        self.timer =  QTimer()
        self.timer.timeout.connect(self.ShowPower)

        self.StartBtn = QPushButton('Start')
        self.StartBtn.clicked.connect(self.Start)
        self.StopBtn = QPushButton('Stop')
        self.StopBtn.clicked.connect(self.Stop)



        self.OuterLayout.addWidget(self.Visor, 0, 0)
        self.OuterLayout.addWidget(self.StartBtn, 0, 1)
        self.OuterLayout.addWidget(self.StopBtn, 0, 2)

        self.widget = QWidget(self)
        self.widget.setLayout(self.OuterLayout)
        self.setCentralWidget(self.widget)
    
    def ShowPower(self):
        try:
            self.p_dBm = np.round(pm.pow_dBm(delta_input =False),3)
        except:
            self.p_dBm = pm.pow_dBm(delta_input =False)
        self.Visor.setText(str(self.p_dBm))
    def Start(self):
        self.t0 = time.time()
        self.timer.start(1000)
        self.StartBtn.setEnabled(False)
        self.StopBtn.setEnabled(True)
    def Stop(self):
        self.timer.stop()
        self.StopBtn.setEnabled(False)
        self.StartBtn.setEnabled(True)
        
        
def Open(pm):
    app = QApplication(sys.argv)
    window = MainWindow(pm)
    window.setWindowTitle("Powermeter Display v0.01 (updated: Fev/2022)")
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    equip = init_equip(att_in = False, att_r = False, att_out = False,
                    pxa = False, scope = False, sigen = False, tunics = False,
                    pm=True, ted=False, edfa=False,
                    osa1=False, osa2=False)
    pm = equip['pm']

    Open(pm)
    #app = QApplication(sys.argv)
    #window = MainWindow(pm)
    #window.setWindowTitle("Powermeter visualizer v0.01 (updated: Fev/2022)")
    #window.show()
    #sys.exit(app.exec())
# %%
