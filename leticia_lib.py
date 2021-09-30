#%%
import time
import os
import numpy as np
from scipy import constants
from matplotlib import pyplot as plt
import pyLPD.MLtools as mlt
c = constants.c

def time_stamp(precision_minute = True, precision_second = True):
    if not precision_minute:
        return time.strftime("%Y-%m-%d_%H")
    elif not precision_second:
        return time.strftime("%Y-%m-%d-%H-%M")
    else:
        return time.strftime("%Y-%m-%d-%H-%M-%S")

def folder(my_folder):
    if not os.path.exists(my_folder):
        os.makedirs(my_folder)

    return my_folder

def scope_avg(scope, channels):    
    scope.measurement.initiate()    
    time.sleep(scope.acquisition.time_per_record)
    vmean = []
    for channel in channels:
        vmean.append(scope.channels[channel].measurement.fetch_waveform_measurement("voltage_average"))
    return vmean

def balanced_att(val_total, val_in, lst_att_in, lst_att_out):
    for att_in in lst_att_in:
        att_in.set_att(val_in)
    for att_out in lst_att_out:
        att_out.set_att(val_total-val_in)

sg_wind = 19
sg_o = 2
pkdet = 3
def spectra_smooth(x, y, floor, fig_size=(5,3), 
                    sg_wind = sg_wind, sg_o = sg_o, pkdet = pkdet):

    y[y<floor] = floor
    y_sg = mlt.savitzky_golay(y, window_size = sg_wind, order = sg_o)

    ind_max, maxtab, ind_min, mintab=mlt.peakdet(y_sg, pkdet)

    Ω = []
    if len(ind_max)>1:
        Ω = c*np.diff(x[ind_max])/(x[ind_max[0]])**2
        

    output = {
        'x': x,
        'y':y,
        'y_sg':y_sg,
        'Ω':Ω,
        'λ_peaks':x[ind_max],
        'pow_peaks':maxtab,
    }
    
    return output

def spectra_plot(dict_, fig_size=(5,3)):
    x = dict_['x']
    y = dict_['y']
    y_sg = dict_['y_sg']
    λ_peaks = dict_['λ_peaks']
    Ω = dict_['Ω']
    
    f, ax = plt.subplots(figsize=fig_size)
    ax.plot(x, y, '.-', alpha = 0.5, c='r')
    ax.plot(x, y_sg, '-', linewidth = 2)       
    ax.axvline(λ_peaks[0], ls='--', c='k')
    
    for Ω_peak, x_peak in zip(Ω, λ_peaks[1:]):
        plt.axvline(x_peak, c='k')
        ax.annotate('{:.3f} GHz'.format(Ω_peak), (x_peak+0.01, -40), rotation=70)





if __name__=='__main__':
    import pandas as pd

    print(time_stamp())
    f_osa = "C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-09-13_PiezoScan\\2021-09-13-20_OpticalTransmission_BareSphere-267umDiameter_OSA_steps-Pol1_lbd1550\\2021-09-13-22-15-08_Att_in5_OSA_scan_osa_table.csv"
    f_lbd = 'C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-09-13_PiezoScan\\2021-09-13-20_OpticalTransmission_BareSphere-267umDiameter_OSA_steps-Pol1_lbd1550\\2021-09-13-22-15-12_Att_in5_OSA_scan_lbd_table.csv'
    
    osa_tab = pd.read_csv(f_osa).values[:,1:]
    lbd_tab = 1e9*pd.read_csv(f_lbd).values[:,1:]

    for ii in range(5):
        x = lbd_tab[:, ii]
        y = osa_tab[:, ii]

        t0 =time.time()
        out = spectra_smooth(x,y, floor = -65)
        print("smooth time: ", time.time()-t0)
        if len(out['λ_peaks'])>1:
            ax = spectra_plot(out)
            plt.show()


# %%

