#%%optical c band 1530-1564 nm

import numpy as np
import matplotlib.pyplot as plt
import sys
import  att_lib, tunics_lib, aq63XX, sigen_lib
import VOA.VOA_lib as VOA_lib
import ivi
import visa
import time
import sys

#%%
daq_port = 'Dev1/ao1'
att_in_visa = 'ASRL5::INSTR'
att_r_visa = 'ASRL13::INSTR'
sigen_visa = 'USB0::0x0957::0x2B07::MY52701124::INSTR'

#%%
att_out = VOA_lib.VOA(daq_port,'VOA\calib_U00306.json')
att_in = att_lib.Att(resource_str = att_in_visa)
att_r = att_lib.Att(resource_str = att_r_visa)

att_in.set_att(29)
att_out.att_dB(0.1)


# %% set polarization 
tunics = tunics_lib.T100R()
#tunics.sweep_config(lbd_nm_ini=1530, lbd_nm_end=1565, lbd_nms_speed=2)
tunics.power_on(power=5, lbd=1550)
# %%
#%%
scope = ivi.agilent.agilentDSOX92504A('TCPIP0::nano-osc-ag9254a::hislip0::INSTR', prefer_pyvisa = True)
ch_reflection = 0
ch_transmission = 1
ch_mzi = 2

timebase=2e-3
scope.acquisition.time_per_record =timebase
def scope_avg(scope, channel):    
    scope.measurement.initiate()    
    time.sleep(timebase)
    vmean = scope.channels[channel].measurement.fetch_waveform_measurement("voltage_average")
    return vmean
# %%
sigen = sigen_lib.Sigen(sigen_visa = sigen_visa)
sigen.ramp_config(symmetry=90, frequency=5, amplitude=5, offset=0)
sigen.output_on()
# %%
sigen.output_off()
# %%
scope.utility.reset_with_defaults()
with open('Solitons-Silica-Piezo.dat', 'rb') as f:
    setup = f.read()
scope.system.load_setup(setup)
# %%
