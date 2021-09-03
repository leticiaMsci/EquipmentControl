import time
import numpy as np
import pandas as pd

def cband_scan(sigen, tunics, scope):
    print("Starting C-band scan. Please wait a few seconds.")
    lbd_ini = 1530
    lbd_end = 1565
    lbd_speed = 5
    time_frame = (lbd_end-lbd_ini)/lbd_speed

    sigen.output_off()
    time.sleep(1)

    scope._write(":TIMebase:ROLL:ENABLE ON")
    scope.acquisition.time_per_record = 2.5*time_frame

    tunics.sweep_config(lbd_ini, lbd_end, lbd_speed, sweep_max_cycles=5)
    tunics.sweep_start()
    print("waiting for acquisition...")
    scope._write(":RUN")
    time.sleep(3.2*time_frame)
    print("acquisition time is up")
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

    return df