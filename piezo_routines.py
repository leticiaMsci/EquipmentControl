#%%
import  att_lib, tunics_lib, aq63XX, sigen_lib
import VOA.VOA_lib as VOA_lib
import ivi
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time




def set_polarization(att_in, att_out, att_r, sigen, tunics, scope,
    sigen_freq = 5, sigen_amplitude=5, lbd_piezo=1550,
    ch_reflection = 0, ch_transmission = 1, ch_mzi = 2, ch_hcn=3,
    val_att_in = None, val_att_r = None, val_att_out=None):

    if val_att_in is not None: att_in.set_att(val_att_in)
    if val_att_out is not None: att_out.set_att(val_att_out)
    if val_att_r is not None:att_r.set_att(val_att_r)

    tunics.power.on(pow_val=3, lbd=lbd_piezo)

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
    mzi = np.array(scope.channels[ch_mzi].measurement.fetch_waveform())
    hcn = np.array(scope.channels[ch_hcn].measurement.fetch_waveform())
    
    plt.plot(mzi[0, ::100], mzi[1, ::100])
    plt.plot(hcn[0, ::100], hcn[1, ::100])
    plt.plot(transmission[0, ::100], transmission[1, ::100])
    plt.show()
    
    df_pol = pd.DataFrame()
    df_pol['time'] = transmission[0]
    df_pol['cav'] = transmission[1]
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
    plot_bool = True):

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

    sigen.output.off()
    #tunics.power_off()
    
    return df_pol


def wavelength_search(sigen, tunics, scope):

    start_scan(sigen, tunics, scope)
    
    lbd = tunics.wavelength.search()

    end_scan(sigen, tunics, scope)

    return lbd

def _flatten(a):
    return np.array([item for sublist in a for item in sublist])

def pxa_stitching(sigen, tunics, scope, pxa, freqlst, nwait = 5, acqtime = 0.03):
    pxa.rt.config()
    pxa.continuous()
    pxa.write(":TRAC:TYPE MAXH")

    xlist=[]
    ylist=[]
    start_scan(sigen, tunics, scope)
    for freq in freqlst:
        pxa.rt.fcenter(freq)
        time.sleep(nwait/sigen.frequency+acqtime)
        x,y = pxa.trace()
        xlist.append(x)
        ylist.append(y)
    df = end_scan(sigen, tunics, scope, plot_bool = False)

    xflat =_flatten(xlist)
    yflat =  _flatten(ylist)
    idx = np.argsort(xflat)

    return xflat[idx], yflat[idx], df

    
if __name__=='__main__':
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
    att_out = VOA_lib.VOA(daq_port,'VOA\calib_U00306.json')
    att_in = att_lib.Att(resource_str = att_in_id)
    att_r = att_lib.Att(resource_str = att_r_id)
    tunics = tunics_lib.T100R(ip=tunics_ip)
    scope = ivi.agilent.agilentDSOX92504A(scope_id, prefer_pyvisa = True)
    sigen = sigen_lib.Sigen(sigen_visa = sigen_id)