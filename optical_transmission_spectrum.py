#%%optical c band 1530-1564 nm
import numpy as np
import matplotlib.pyplot as plt
import sys
import  att_lib, tunics_lib, aq63XX, sigen_lib
import VOA.VOA_lib as VOA_lib
import ivi
import visa
import time
import os
import pandas as pd
import hvplot.pandas
import leticia_lib as llb


experiment = 'OpticalTransmission'
sample = 'BareSphere-238umDiameter'
observation = 'Tunics-Laser-5nms-1_C-Band'
path = "C:/Users/lpd/Documents/Leticia/DFS/2021-09-02_OpticalTransmission/"
base_name = experiment + '_' + sample + '_' + observation


daq_port = 'Dev1/ao1'
att_in_id = 'ASRL5::INSTR'
att_r_id = 'ASRL13::INSTR'
tunics_ip = 'yetula.ifi.unicamp.br'
sigen_id = 'USB0::0x0957::0x2B07::MY52701124::INSTR'
scope_id = 'TCPIP0::nano-osc-ag9254a::hislip0::INSTR'
#scope channels
ch_reflection = 0
ch_transmission = 1
ch_mzi = 2
ch_hcn=3

#sigen params
sigen_freq = 5 #Hz

#%%
att_out = VOA_lib.VOA(daq_port,'VOA\calib_U00306.json')
att_in = att_lib.Att(resource_str = att_in_id)
att_r = att_lib.Att(resource_str = att_r_id)
att_in.set_att(32)
att_out.set_att(0.1)
att_r.set_att(0.1)


tunics = tunics_lib.T100R(ip=tunics_ip)

scope = ivi.agilent.agilentDSOX92504A(scope_id, prefer_pyvisa = True)
#hcn channel should have impedance 1MOhm


sigen = sigen_lib.Sigen(sigen_visa = sigen_id)
sigen.ramp_config(symmetry=90, frequency=sigen_freq, amplitude=5, offset=0)

#%%
#laser on
lbd_piezo = 1550
tunics.power_on(power=5, lbd=lbd_piezo)

#sigen ramp
sigen.output_on()

#oscilloscope trigger on aux port
scope._write(":RUN")
scope._write(':TRIGger:EDGE:SOURce AUX')
scope._write(":TRIGger:LEVel AUX, 1")
scope._write(":TIMebase:ROLL:ENABLE OFF")
scope.acquisition.time_per_record =2.5/sigen_freq

#%% For safety, ask user if polarization was set correctly
pol = input()
print("Is polarization set? y/n "+pol)

#%% Retrieve and Plot Piezo Polarization data
if pol != 'y' and pol != 'Y':
    raise Exception("Please try again setting the polarization.")

print("Polarization Set Correctly")
transmission = np.array(scope.channels[ch_transmission].measurement.fetch_waveform())
mzi = np.array(scope.channels[ch_mzi].measurement.fetch_waveform())
hcn = np.array(scope.channels[ch_hcn].measurement.fetch_waveform())
plt.plot(transmission[0, ::100], transmission[1, ::100])
plt.plot(mzi[0, ::100], mzi[1, ::100])
plt.plot(hcn[0, ::100], hcn[1, ::100])
plt.show()

df_pol = pd.DataFrame()
df_pol['time'] = transmission[0]
df_pol['transmission'] = transmission[1]
df_pol['mzi'] = mzi[1]
df_pol['hcn'] = hcn[1]


#%% optical c band 1530-1565 nm
# C-Band sweep
lbd_ini = 1530
lbd_end = 1565
lbd_speed = 5
time_frame = (lbd_end-lbd_ini)/lbd_speed

sigen.output_off()
time.sleep(2)

scope._write(":TIMebase:ROLL:ENABLE ON")
scope.acquisition.time_per_record = 2.5*time_frame

tunics.sweep_config(lbd_ini, lbd_end, lbd_speed, sweep_max_cycles=5)
tunics.sweep_start()
print("waiting for acquisition...")
scope._write(":RUN")
time.sleep(3.2*time_frame)
print("time is up")
scope._write(":STOP")

waveform1 = np.array(scope.channels[0].measurement.fetch_waveform())
waveform2 = np.array(scope.channels[1].measurement.fetch_waveform())
waveform3 = np.array(scope.channels[2].measurement.fetch_waveform())
waveform4 = np.array(scope.channels[3].measurement.fetch_waveform())

df = pd.DataFrame()

df['time'] = waveform1[0]
df['reflec'] = waveform1[1]
df['transm'] = waveform2[1]
df['mzi'] = waveform3[1]
df['hcn'] = waveform4[1]

#%% Save Piezo and C-Band span data
time_stamp =llb.time_stamp()
step = "/Pol1_C-Band_Sweep"
save_path = os.path.join(path+time_stamp+"_"+base_name)
llb.folder(save_path)

df.to_parquet(save_path+step+"C-BandSweep.parq")
df_pol.to_parquet(save_path+step+"Piezo_PolSetting.parq")


# %% OSA Sweep
total_att = 20
att_in_0 = 10
#%%
lbd_0 = 1551
lbd_f = 1551.5#1565
lbd_step = 0.001
osa_w = 2

osa = aq63XX.AQ63XX()
osa.ConnectOSA(isgpib = True, address = 13)
osa.InitOSA()
#osa.osa.write('AUTO OFFSET OFF')
osa.SweepRange(lbd_ini-osa_w/2, lbd_ini+osa_w/2, 2)
osa.SingleSweep()
x_osa = 1e9*osa.trace_data(axis = "X")
y_osa = osa.trace_data(axis = "Y")

plt.plot(x_osa,y_osa)
# %%
att_in.set_att(att_in_0)
att_out.set_att(total_att-att_in_0+9)
att_r.set_att(total_att-att_in_0)

lbd_list = np.arange(lbd_0, lbd_f, lbd_step)
nsteps = len(lbd_list)
transm_vec=np.zeros(nsteps)
reflec_vec=np.zeros(nsteps)
mzi_vec=np.zeros(nsteps)
osa_table=np.zeros((len(x_osa), nsteps))
lbd_table=np.zeros((len(x_osa), nsteps))

toolbar_width = len(lbd_list)


for i, lbd in enumerate(lbd_list):
    tunics.wavelength(lbd)
    osa.SweepRange(lbd - osa_w/2, lbd+osa_w/2, 2)
    osa.SingleSweep()
    time.sleep(.5)

    x = osa.trace_data(axis = "X")
    y = osa.trace_data(axis = "Y")
    
    osa_table[:, i]=y[:]
    lbd_table[:, i]=x[:]
    transm_vec[i]=scope.channels[ch_transmission].measurement.fetch_waveform_measurement("voltage_average")
    reflec_vec[i]=scope.channels[ch_reflection].measurement.fetch_waveform_measurement("voltage_average")
    mzi_vec[i]=scope.channels[ch_mzi].measurement.fetch_waveform_measurement("voltage_average")

    plt.plot(1e9*x,y)
    plt.title(str(lbd)+"nm")
    plt.show()


# %%
