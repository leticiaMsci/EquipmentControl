#%%
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


#%%
tunics = tunics_lib.T100R()
tunics.wavelength(1550)
tunics.power_on(power=5)

#%%
osa = aq63XX.AQ63XX()
osa.ConnectOSA(isgpib = True, address = 13)
osa.InitOSA()
osa.osa.write('AUTO OFFSET OFF')
osa.SetSpanWavelength(.5)
osa.SetCenterWavelength(1550)
osa.SingleSweep()
x_osa = 1e9*osa.trace_data(axis = "X")
y_osa = osa.trace_data(axis = "Y")

plt.plot(x_osa,y_osa)



#%%
scope = ivi.agilent.agilentDSOX92504A('TCPIP0::nano-osc-ag9254a::hislip0::INSTR', prefer_pyvisa = True)
ch_reflection = 0
ch_transmission = 1
ch_mzi = 3

timebase=2e-3
scope.acquisition.time_per_record =timebase
def scope_avg(scope, channel):    
    scope.measurement.initiate()    
    time.sleep(timebase)
    vmean = scope.channels[channel].measurement.fetch_waveform_measurement("voltage_average")
    return vmean

#%%
sigen = sigen_lib.Sigen(sigen_visa = sigen_visa)
sigen.output_off()
# %%
total_att = 29
att_in_0 = 10
#att_in_f = 25

lbd_0 = 1551
lbd_f = 1551.5#1565
lbd_step = 0.001
osa_w = 2

att_in.set_att(att_in_0)
att_out.att_dB(total_att-att_in_0)
att_r.set_att(total_att-att_in_0)

lbd_list = np.arange(lbd_0, lbd_f, lbd_step)
nsteps = len(lbd_list)
transm_vec=np.zeros(nsteps)
reflec_vec=np.zeros(nsteps)
mzi_vec=np.zeros(nsteps)
osa_table=np.zeros((len(x_osa), nsteps))
λ_table=np.zeros((len(x_osa), nsteps))

toolbar_width = len(lbd_list)


for i, lbd in enumerate(lbd_list):
    tunics.wavelength(lbd)
    osa.SetSpanWavelength(.5)
    osa.SetCenterWavelength(lbd)
    osa.SingleSweep()
    time.sleep(.5)

    x = osa.trace_data(axis = "X")
    y = osa.trace_data(axis = "Y")
    
    osa_table[:, i]=y[:]
    λ_table[:, i]=x[:]
    transm_vec[i]=scope_avg(scope, ch_transmission)
    reflec_vec[i]=scope_avg(scope, ch_reflection)
    mzi_vec[i]=scope_avg(scope, ch_mzi)

    #plt.plot(1e9*x,y)
    #plt.title(str(lbd)+"nm")
    #plt.show()


# %%
np.savetxt("./2021-08-27_osa_table.csv", osa_table, delimiter=",")
np.savetxt("./2021-08-27_lbd_table.csv", λ_table, delimiter=",")
np.savetxt("./2021-08-27_transm_vec.csv", transm_vec, delimiter=",")
np.savetxt("./2021-08-27_reflec_vec.csv", reflec_vec, delimiter=",")
np.savetxt("./2021-08-27_mzi_vec.csv", mzi_vec, delimiter=",")
# %%
