#%%
import time
import os
import numpy as np
from scipy import constants
from scipy import interpolate
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

def spectra_plot(dict_, ax=None, fig_size=(5,3)):
    x = dict_['x']
    y = dict_['y']
    y_sg = dict_['y_sg']
    λ_peaks = dict_['λ_peaks']
    Ω = dict_['Ω']
    
    #f, ax = plt.subplots(figsize=fig_size)
    if ax is None:
        ax = plt.gca()

    ax.plot(x, y, '.-', alpha = 0.5, c='r')
    ax.plot(x, y_sg, '-', linewidth = 2)       
    ax.axvline(λ_peaks[0], ls='--', c='k')
    
    for Ω_peak, x_peak in zip(Ω, λ_peaks[1:]):
        ax.axvline(x_peak, c='k')
        ax.annotate('{:.3f} GHz'.format(Ω_peak), (x_peak+0.01, -40), rotation=70)


def spectra_cycle(osa_cycle, lbd_cycle, δ_lst, 
        sg_w = 33, smooth_floor = -75,
        peakdet_floor = -55, plot_bool = False):
    
    l=len(osa_cycle[0,:])
    ii_lst = np.arange(l)
    peak_lst=np.zeros(l)
    ind_lst = np.zeros(l)
    lbd_lst = np.zeros(l)

    osa_smooth = np.zeros_like(osa_cycle)
    for ii in ii_lst:
        temp = osa_cycle[:, ii]
        temp[temp<smooth_floor] = smooth_floor
        temp = mlt.savitzky_golay(temp, window_size = sg_w, order = 2)
        for jj in range(len(temp)):    
            osa_smooth[jj, ii] = temp[jj]

        osa_peakdet = osa_smooth[::, ii]
        osa_peakdet[osa_peakdet<peakdet_floor] = peakdet_floor
        ind_max, maxtab, ind_min, mintab=mlt.peakdet(osa_peakdet, 3)
        lbd_lst[ii]=lbd_cycle[ind_max[0], ii]


    poly = np.polyfit(ii_lst, lbd_lst, 1)
    fit_y = poly[1]+ii_lst*poly[0]

    if plot_bool:
        plt.plot(lbd_lst, '.')
        plt.plot(fit_y)
        plt.show()


    center_lst = np.zeros((len(δ_lst), l))
    for ii in ii_lst:
        δ=fit_y[ii]
        interp=interpolate.interp1d(lbd_cycle[:, ii]-δ, osa_smooth[:, ii])
        center_lst[:, ii] = interp(δ_lst)
        
    return center_lst, fit_y

def spectra_shift(x, y, λ, δλ_lst, sg_w = 33,
            smooth_bool = False, smooth_floor = -70):   
    if smooth_bool:
        y[y<smooth_floor] = smooth_floor
        y = mlt.savitzky_golay(y, window_size = sg_w, order = 2)
    
    interp=interpolate.interp1d(x-λ, y)
    y_centered = interp(δλ_lst)
    
    return y_centered


def spectra_center(osa1_tab, lbd1_tab, osa2_tab, lbd2_tab, L_cycle, 
                   δλ_0 =-0.09, δλ_f =0.3, len_δ_lst=100,
                   sg_w = 15, peakdet_floor = -50, plot_bool = False):
    
    wavelength = np.zeros_like(osa2_tab[0, :])
    centered2_tab = np.zeros((len_δ_lst, len(wavelength)))
    centered1_tab = np.zeros((len_δ_lst, len(wavelength)))

    δ_lst1 = np.linspace(δλ_0, δλ_f, len_δ_lst)
    f_lst = c*δ_lst1/(1545)**2

    hist ={
        'λ':[],
        'Ω':[],
        'Δpow':[],
        'centered1_scan':[],
        'centered2_scan':[],
        'wavelength_scan':[],
    }

    for n in range(int(len(wavelength)/L_cycle)):
        osa2_cycle = osa2_tab[:, 1+L_cycle*n:1+L_cycle*(n+1)]
        lbd2_cycle = lbd2_tab[:, 1+L_cycle*n:1+L_cycle*(n+1)]

        osa1_cycle = osa1_tab[:, 1+L_cycle*n:1+L_cycle*(n+1)]
        lbd1_cycle = lbd1_tab[:, 1+L_cycle*n:1+L_cycle*(n+1)]


        if plot_bool:
            fig, axs = plt.subplots(1,2, figsize=(12,5))
            axs[0].imshow(osa2_cycle-np.min(osa2_cycle))
            axs[1].plot(osa2_cycle[:,0], '.-', label = 'first of cycle')
            axs[1].plot(osa2_cycle[:,-1], label='last of cycle')
            try:
                axs[1].plot(osa2_tab[:,1+L_cycle*(n+1)], label='first of following cycle')
            except IndexError:
                pass
            plt.legend()
            plt.show()

        l=len(osa2_cycle[0,:])

        center_lst, λ_center_lst = spectra_cycle(osa2_cycle, lbd2_cycle, δ_lst1, sg_w =sg_w, peakdet_floor = peakdet_floor)

        for kk, λ in enumerate(λ_center_lst):
            x1 = lbd1_cycle[:, kk]
            y1 = osa1_cycle[:, kk]
            output = spectra_smooth(x1,y1, -65, sg_wind = 25)

            if len(output['λ_peaks'])>1:
                f, ax1 = plt.subplots(1, figsize=(6,3))
                spectra_plot(output, ax=ax1)
                plt.plot(lbd2_cycle[:, kk], osa2_cycle[:, kk])
                plt.xlim(λ+δλ_0, λ+δλ_f)
                plt.show()

            for ll, Ω in enumerate(output['Ω']):
                hist['λ'].append(λ)
                hist['Ω'].append(Ω)
                hist['Δpow'].append(output['pow_peaks'][ll+1]-output['pow_peaks'][ll])

            centered1_tab[:, 1+L_cycle*n+kk] = spectra_shift(output['x'], output['y_sg'], λ, δ_lst1, smooth_bool = False)


        L = len(λ_center_lst)
        centered2_tab[:, 1+L_cycle*n: 1+L_cycle*n + L] = center_lst
        wavelength[1+L_cycle*n: L+1+L_cycle*n] = λ_center_lst
        
    hist['wavelength_scan'] = wavelength
    hist['centered2_scan'] = centered2_tab
    hist['centered1_scan'] = centered1_tab
    return hist


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

