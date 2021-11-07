import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyLPD.MLtools as mlt

def cband_scan(sigen, tunics, scope, config = True,
    lbd_ini = 1529, lbd_end = 1565, lbd_speed = 5,
    ch_reflec = 0, ch_cav = 1, ch_mzi=2, ch_hcn=3,
    power = None,
    wait_tfs =0.99):
    """Controls equipment and performs a wavelength sweep over the C-band
    or whatever interval defined by lbd_ini and lbd_end.

    Args:
        sigen (Sigen): initialized Sigen class (signal generator)
        tunics (TR100): laser
        scope (ivi.agilent.agilentDSOX92504A.agilentDSOX92504A): oscilloscope
        config (bool, optional): If true will set tunics and scope configuration. If false will skip setting parameters. Defaults to True.
        lbd_ini (int, optional): Initial sweep wavelength [nm]. Defaults to 1530.
        lbd_end (int, optional): Final sweep wavelength [nm]. Defaults to 1565.
        lbd_speed (int, optional): sweep speed [nm/s]. Defaults to 5.
        ch_reflec (int, optional): scope channel correspondinf to reflection output. Defaults to 0.
        ch_cav (int, optional): scope cavity transmission channel. Defaults to 1.
        ch_mzi (int, optional): scope MZI channel. Defaults to 2.
        ch_hcn (int, optional): scope HCN channel. Defaults to 3.

    Returns:
        dataframe: dataframe containing acquired scope waveforms
    """

    print("Starting C-band scan. Please wait a few seconds.")

    time_frame = (lbd_end-lbd_ini)/lbd_speed

    sigen.output.off()
    time.sleep(.2)

    if config:
        scope._write(":ACQuire:POINts 10000000")
        scope._write(":TIMebase:ROLL:ENABLE ON")
        scope.acquisition.time_per_record = 1.6*time_frame
        scope._write(":STOP")

        if power is None:
            power = tunics.power_default

        tunics.power.on(pow_val=power, lbd = lbd_ini)
        tunics.sweep.config(lbd_ini, lbd_end, lbd_speed, sweep_max_cycles=1)
    
    print("waiting for acquisition...")
      
    
    tunics.sweep.start()
    scope._write(":RUN")
    tunics.sweep.wait(max_time = wait_tfs*time_frame)
    scope._write(":STOP")
    print("stopped")
    time.sleep((1.1-wait_tfs)*time_frame)
    #time.sleep(0.5)
    print("timeout = fetching waveforms")

    waveform1 = np.array(scope.channels[ch_reflec].measurement.fetch_waveform())
    waveform2 = np.array(scope.channels[ch_cav].measurement.fetch_waveform())
    waveform3 = np.array(scope.channels[ch_mzi].measurement.fetch_waveform())
    waveform4 = np.array(scope.channels[ch_hcn].measurement.fetch_waveform())

    df = pd.DataFrame()

    df['time'] = waveform1[0]
    df['reflec'] = waveform1[1]
    df['cav'] = waveform2[1]
    df['mzi'] = waveform3[1]
    df['hcn'] = waveform4[1]


    tunics.sweep.stop()
    #if config: tunics.power_off()

    return df

def plot_diff_freq(data, fname, pkdet_delta=0.25):
    ind_max, maxtab, ind_min, mintab = mlt.peakdet(data.cav.values, delta=pkdet_delta)
    fΩ = data.freq.values[ind_min][:-1]
    Ω =  np.diff(data.freq.values[ind_min])*1e3
    mask = Ω<15
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))
    ax1.plot(data.freq.values[::10], data.cav.values[::10]/max(data.cav.values))
    ax1.plot(data.freq.values[::10], data.reflec.values[::10]/max(1, max(data.reflec.values)))
    ax1.set_xlabel("Frequency [THz]")
    ax1.set_ylabel("T [a.u.]")
    ax1.set_title("Transmission")

    ax2.hist(Ω[mask], bins = np.linspace(0, 12, 50))
    ax2.set_xlabel(r"f$_{n+1}$ - f$_n$ [GHz]")
    ax2.set_ylabel("Occurence")
    ax2.set_title("Delta Frequency Histogram")
    ax2.set_yscale('log')
    plt.savefig(fname[:-5]+"DeltaFrequencyHistogram.pdf")
    plt.show()

    return data.freq.values[ind_min], mintab