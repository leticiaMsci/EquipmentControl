#%%
#%%
import time
import os
import re
import numpy as np
from scipy import constants
from scipy import interpolate
from matplotlib import pyplot as plt
from matplotlib import ticker
import pyLPD.MLtools as mlt
import sys
import json
c = constants.c
osa2_delta = 0.428

def open_json(filename):
    with open(filename, "r") as jsonfile:
        return json.load(jsonfile)
                
def save_json(dict_, filename):
    lbd_json = json.dumps(dict_, indent=4, sort_keys=False)
    with open(filename, 'w') as jsonfile:
        jsonfile.write(lbd_json)
        print("Write successful: "+filename)

def countdown(time_):
    time_steps = time_/10
    for ii in range(10):
        time.sleep(time_steps)
        print_ = 'Countdown: Time {:6.3f}s of {}s'.format(time_steps*(ii+1), time_)
        sys.stdout.write('\r'+print_)
        sys.stdout.flush()

def countdown_timer(t):
    while t:
        mins, secs = divmod(t, 60)
        print_ = 'Countdown timer: {:02d}:{:02d}'.format(mins, secs)
        sys.stdout.write('\r'+print_)
        sys.stdout.flush()
        
        time.sleep(1)
        t -= 1
    print_ = 'Countdown timer: {:02d}:{:02d}'.format(0, 0)
    sys.stdout.write('\r'+print_)
      
    print(' Ready!')

def flatten(a):
    return [item for sublist in a for item in sublist]
    
def time_stamp(precision_minute = True, precision_second = True):
    if not precision_minute:
        return time.strftime("%Y%m%d-%H")
    elif not precision_second:
        return time.strftime("%Y%m%d-%H%M")
    else:
        return time.strftime("%Y%m%d-%H%M%S")

def folder(my_folder):
    if not os.path.exists(my_folder):
        os.makedirs(my_folder)

    return my_folder

def get_values_from_str(s):
    numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
    rx = re.compile(numeric_const_pattern, re.VERBOSE)
    return rx.findall(s)

def get_values_in_path(flist, idx):
    lst = np.zeros(len(flist))
    for ii, f in enumerate(flist):
        info = get_values_from_str(f)
        lst[ii] = float(info[idx])
        
    return lst

def base_name(flst):
    return [os.path.basename(f) for f in flst]

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
def spectra_smooth(x, y, floor, λ_ref = None, #fig_size=(5,3), 
                    sg_wind = sg_wind, sg_o = sg_o, pkdet = pkdet):

    y[y<floor] = floor
    y_sg = mlt.savitzky_golay(y, window_size = sg_wind, order = sg_o)

    ind_max, maxtab, ind_min, mintab=mlt.peakdet(y_sg, pkdet)

    Ω = []
    λ_peaks=[]
    λ_in = x[ind_max][0]
    if len(ind_max)>1:
        if λ_ref is None:
            Ω = c*np.diff(x[ind_max])/(x[ind_max[0]])**2
            λ_peaks = x[ind_max[1:]]
            λ_in = x[ind_max[0]] 
        else:
            Ω=c*(x[ind_max] - λ_ref)/(x[ind_max[0]])**2
            sortΩ = np.argsort(np.abs(Ω))
            Ω=Ω[sortΩ[1:]]
            λ_peaks = x[ind_max][sortΩ[1:]]
            λ_in = x[ind_max][sortΩ[0]]  
    
    output = {
        'x': x,
        'y':y,
        'y_sg':y_sg,
        'Ω':Ω,
        'λ_peaks':λ_peaks,
        'λ_in' : λ_in,
        'pow_peaks':maxtab,
    }
    
    return output

def spectra_plot(dict_, ax=None, plot_axv = True, y_annotation = -40, color=None):
    x = dict_['x']
    y = dict_['y']
    y_sg = dict_['y_sg']
    λ_peaks = dict_['λ_peaks']
    Ω = dict_['Ω']
    λ_in = dict_['λ_in']
    
    #f, ax = plt.subplots(figsize=fig_size)
    if ax is None:
        ax = plt.gca()

    if color is not None:
        line, = ax.plot(x, y, '.-', alpha = 0.5, color=color)
    else:
        line, = ax.plot(x, y, '.-', alpha = 0.5)

    ax.plot(x, y_sg, '-', linewidth = 2, color = line.get_color())       
    
    if plot_axv:
        ax.axvline(λ_in, ls='--', c='k')
        for Ω_peak, x_peak in zip(Ω, λ_peaks):
            ax.axvline(x_peak, c='k')
            ax.annotate('{:.3f} GHz'.format(Ω_peak), (x_peak+0.01, y_annotation), rotation=70)


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

        center_lst, λ_center_lst = spectra_cycle(osa2_cycle, lbd2_cycle, δ_lst1, sg_w =sg_w, peakdet_floor = peakdet_floor, plot_bool=plot_bool)

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
    hist['f_lst'] = f_lst
    return hist


def spectra_histogram(hist, title = None):
    fig, (ax1,ax2)=plt.subplots(1, 2, figsize=(13,3.5), sharey=True, sharex='col')

    if title is not None:
        fig.suptitle(title)

    map1=ax1.scatter(hist['λ'], hist['Ω'], marker='h', c=np.array(hist['Δpow']), s=65, alpha=0.8, cmap='Blues')
    ax1.set_ylabel('Frequency Shift [GHz]')
    ax1.set_xlabel('Input Wavelength [nm]')
    ax1.yaxis.tick_left()
    ax1.set_title('Frequency Shifts for Pump Wavelengths')
    ax1.set_ylim(1, 20)


    counts, bins, patches=ax2.hist(hist['Ω'], orientation=u'horizontal', log=True, alpha=0.9)
    bin_centers =  bins[:-1] - 0.5 * np.diff(bins)
    ax2.set_xlabel('Occurence')
    ax2.set_xlim(0.5, max(counts)*3)
    ax2.tick_params(axis='y', which='both', labelleft=False, labelright=True)
    ax2.yaxis.tick_right()
    ax2.set_title('Frequency Shift Histogram')


    for count, x in zip(counts, bin_centers):
        if count >0.01*len(hist['λ']):
            plt.annotate('{:.1f}%'.format(100*count/sum(counts)), xy=( count, x), xycoords=('data', 'data'),
                xytext=(0, 18), textcoords='offset points', va='top', ha='left')
    # 
    #fig.colorbar(map1, ax=ax2)

    cbar= fig.add_axes([0.45, 0.56, 0.01, 0.3])

    cb=fig.colorbar(map1, cax=cbar)
    tick_locator = ticker.MaxNLocator(nbins=4)
    cb.locator = tick_locator
    cb.update_ticks()
    # cb.set_label('Fraction of Power')
    ax = cb.ax
    ax.text(-1.52,0.8,r'$P_1-P_0$ [dB]',rotation=90)
    #ax.set_title(r'$P_1-P_0$ [dB]')
    plt.subplots_adjust(wspace=.02, hspace=0)
    return fig


if __name__=='__main__':
    import pandas as pd

    print(time_stamp())
    f_osa1 = "C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-10-04\\2021-10-05-11_OpticalTransmission_BareSphere-267umDiameter_PiezoPowerScan-Pol1_lbd1550\\2021-10-05-12-31-11_Power7.37_OSA_scan_osa1_table.csv"
    f_lbd1 = "C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-10-04\\2021-10-05-11_OpticalTransmission_BareSphere-267umDiameter_PiezoPowerScan-Pol1_lbd1550\\2021-10-05-12-31-11_Power7.37_OSA_scan_lbd1_table.csv"

    f_osa2 = "C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-10-04\\2021-10-05-11_OpticalTransmission_BareSphere-267umDiameter_PiezoPowerScan-Pol1_lbd1550\\2021-10-05-12-31-12_Power7.37_OSA_scan_osa2_table.csv"
    f_lbd2 = "C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-10-04\\2021-10-05-11_OpticalTransmission_BareSphere-267umDiameter_PiezoPowerScan-Pol1_lbd1550\\2021-10-05-12-31-12_Power7.37_OSA_scan_lbd2_table.csv"
      
    osa1_tab = pd.read_csv(f_osa1).values[:,1:]
    lbd1_tab = 1e9*pd.read_csv(f_lbd1).values[:,1:]

    osa2_tab = pd.read_csv(f_osa2).values[:,1:]
    lbd2_tab = 1e9*pd.read_csv(f_lbd2).values[:,1:]+osa2_delta

    for ii in range(len(osa1_tab[0, :])):
        x = lbd1_tab[:, ii]
        y = osa1_tab[:, ii]

        t0 =time.time()
        out = spectra_smooth(x,y, floor = -65)
        #print("smooth time: ", time.time()-t0)
        if len(out['λ_peaks'])>1:
            ax = spectra_plot(out)
            plt.show()

    hist = spectra_center(osa1_tab, lbd1_tab, osa2_tab, lbd2_tab,
                            L_cycle = 50, δλ_0 =-0.09, δλ_f =0.3, len_δ_lst=100,
                            sg_w = 15, peakdet_floor = -50, plot_bool = False)

    fig = spectra_histogram(hist)
    plt.show()


# %%

