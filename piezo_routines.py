#%%


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os
import sys
equip_control_path = 'C:/Users/lpd/Documents/Leticia/DFS/EquipmentControl'
sys.path.insert(1, equip_control_path)
import leticia_lib as llb




def set_polarization(att_in, att_out, att_r, sigen, tunics, scope,
    sigen_freq = 5, sigen_amplitude=5, lbd_piezo=1550,
    ch_reflection = 0, ch_transmission = 1, ch_mzi = 2, ch_hcn=3,
    val_att_in = None, val_att_r = None, val_att_out=None, power = None):

    if val_att_in is not None: att_in.set_att(val_att_in)
    if val_att_out is not None: att_out.set_att(val_att_out)
    if val_att_r is not None:att_r.set_att(val_att_r)
    
    if power is None: power = tunics.power_default

    tunics.power.on(pow_val=power, lbd=lbd_piezo)

    #sigen ramp
    sigen.waveforms.ramp(symmetry=90, frequency=sigen_freq, amplitude=sigen_amplitude, offset=0)
    time.sleep(1)
    sigen.output.on()

    #oscilloscope trigger on aux port
    scope._write(":ACQuire:POINts 1000000")
    scope._write(":RUN")
    scope._write(':TRIGger:EDGE:SOURce AUX')
    scope._write(":TRIGger:LEVel AUX, 1")
    scope._write(":TIMebase:ROLL:ENABLE OFF")
    scope.acquisition.time_per_record =2.5/sigen_freq

    # 
    print("Is polarization set? y/n ")
    pol = input("Is polarization set? y/n ")
    print(pol)

    if pol!='y' and pol!='Y':
        sigen.output.off()
        raise Exception("Polarization not successful")

    print("Polarization set successfully.")
    transmission = np.array(scope.channels[ch_transmission].measurement.fetch_waveform())
    reflection = np.array(scope.channels[ch_reflection].measurement.fetch_waveform())
    mzi = np.array(scope.channels[ch_mzi].measurement.fetch_waveform())
    hcn = np.array(scope.channels[ch_hcn].measurement.fetch_waveform())
    
    plt.plot(mzi[0, ::100], mzi[1, ::100])
    plt.plot(hcn[0, ::100], hcn[1, ::100])
    plt.plot(transmission[0, ::100], transmission[1, ::100])
    plt.show()
    
    df_pol = pd.DataFrame()
    df_pol['time'] = transmission[0]
    df_pol['cav'] = transmission[1]
    df_pol['reflec'] = reflection[1]
    df_pol['mzi'] = mzi[1]
    df_pol['hcn'] = hcn[1]

    sigen.output.off()
    tunics.power.off()
    
    return df_pol

def start_scan( sigen, tunics, scope,
    att_in= None, att_out= None, att_r= None,
    val_att_in = None, val_att_r = None, val_att_out=None):

    if val_att_in is not None and att_in is not None:
        att_in.set_att(val_att_in)
    if val_att_out is not None and att_out is not None:
        att_out.set_att(val_att_out)
    if val_att_r is not None and att_r is not None:
        att_r.set_att(val_att_r)

    #tunics.power.on()
    sigen.output.on()

    #oscilloscope trigger on aux port
    scope._write(":ACQuire:POINts 1000000")
    scope._write(":RUN")
    scope._write(':TRIGger:EDGE:SOURce AUX')
    scope._write(":TRIGger:LEVel AUX, 1")
    scope._write(":TIMebase:ROLL:ENABLE OFF")
    scope.acquisition.time_per_record =2.5/sigen.frequency

def end_scan(sigen, tunics, scope,
    ch_reflection = 0, ch_transmission = 1, ch_mzi = 2, ch_hcn=3,
    plot_bool = True, sigen_onoff = True):

    transmission = np.array(scope.channels[ch_transmission].measurement.fetch_waveform())
    reflec = np.array(scope.channels[ch_reflection].measurement.fetch_waveform())
    mzi = np.array(scope.channels[ch_mzi].measurement.fetch_waveform())
    hcn = np.array(scope.channels[ch_hcn].measurement.fetch_waveform())
    
    if plot_bool:
        plt.plot(mzi[0, ::100], mzi[1, ::100])
        plt.plot(hcn[0, ::100], hcn[1, ::100])
        plt.plot(transmission[0, ::100], transmission[1, ::100])
        plt.plot(reflec[0, ::100], reflec[1, ::100])
        plt.show()
    
    df_pol = pd.DataFrame()
    df_pol['time'] = transmission[0]
    df_pol['cav'] = transmission[1]
    df_pol['reflec'] = reflec[1]
    df_pol['mzi'] = mzi[1]
    df_pol['hcn'] = hcn[1]

    if sigen_onoff: sigen.output.off()
    #tunics.power_off()
    
    return df_pol


def wavelength_search(sigen, tunics, scope):

    start_scan(sigen, tunics, scope)
    
    lbd = tunics.wavelength.search()

    end_scan(sigen, tunics, scope)

    return lbd

def _flatten(a):
    return np.array([item for sublist in a for item in sublist])

def pxa_stitching(sigen, tunics, scope, pxa, freq_lst,
                nwait = 5, acqtime = 0.03, sigen_onoff = True):
    #pxa.rt.config()
    #pxa.continuous()
    #pxa.write(":TRAC:TYPE MAXH")

    #xlist=[]
    #ylist=[]
    if sigen_onoff: start_scan(sigen, tunics, scope)
    #for freq in freqlst:
    #    pxa.rt.fcenter(freq)
    #    time.sleep(nwait/sigen.frequency+acqtime)
    #    x,y = pxa.trace()
    #    xlist.append(x)
    #    ylist.append(y)
    x, y = pxa.rt.stitching(freq_lst, nwait/sigen.frequency+acqtime)
    df = end_scan(sigen, tunics, scope, 
            plot_bool = False, sigen_onoff = sigen_onoff)

    #xflat =_flatten(xlist)
    #yflat =  _flatten(ylist)
    #idx = np.argsort(xflat)

    return x, y, df

def save_data(equip, save_path, sigen_freq, sigen_amp, sigen_sym):
    df_pxa = pd.DataFrame()
    df_osa1 = pd.DataFrame()
    df_osa2 = pd.DataFrame()

    df_pxa['x'], df_pxa['y']  = equip['pxa'].trace()
    df_osa1['x'], df_osa1['y'] = equip['osa1'].GetData()
    df_osa2['x'], df_osa2['y'] = equip['osa2'].GetData()
    df = end_scan(equip['sigen'], equip['tunics'], equip['scope'], 
                        plot_bool = False, sigen_onoff = False)

    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(7,3))
    ax1.plot(df_pxa['x'], df_pxa['y'])
    ax2.plot(df.cav/np.max(df.cav.values))
    ax2.plot(df.reflec)
    ax2.plot(df.hcn/np.max(df.hcn.values))
    
    temp = equip['ted'].read_temp()
    lbd_real = equip['tunics'].wavelength.lbd_real(1e9*float(equip['tunics'].wavelength.sense()))
    power = equip['pm'].pow_dBm(delta_input=True)

    fname = os.path.join(save_path, 
                llb.time_stamp()+"Temp{:.2f}C_Lbd{:.3f}nm_Pow_in{:.1f}dBm_Sigen_freq{}amp{}sym{}".format(
                                    temp, lbd_real, power, sigen_freq, sigen_amp, sigen_sym))
    df_pxa.to_csv(fname+"_PXA.csv")
    df_osa1.to_csv(fname+"_OSA1.csv")
    df_osa2.to_csv(fname+"_OSA2.csv")
    df.to_parquet(fname+"_ScopeData.parq")
    plt.savefig(fname+".png")
    plt.show()
    
    peak_f =df_pxa['x'][ np.argmax(df_pxa['y'])]
    return fname, peak_f

    
if __name__=='__main__':
    import  tunics_lib, sigen_lib
    import attenuators as atts
    import ivi

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
    att_out = atts.MN9625A(gpib=21)
    att_in = atts.DA100(resource_str = att_in_id)
    att_r = atts.VOA(daq_port,'U00306')
    tunics = tunics_lib.T100R(ip=tunics_ip)
    scope = ivi.agilent.agilentDSOX92504A(scope_id, prefer_pyvisa = True)
    sigen = sigen_lib.Sigen(sigen_visa = sigen_id)
# %%
