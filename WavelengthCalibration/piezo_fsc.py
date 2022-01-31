import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pandas as pd
import numpy as np
import pyLPD.MLtools as mlt
import sys
equip_control_path = 'C:/Users/lpd/Documents/Leticia/DFS/EquipmentControl'
sys.path.insert(1, equip_control_path)
import WavelengthCalibration.wavelength_calibration as wc

from scipy import constants, interpolate, signal
c = constants.c


def cluster_bools(points):
    clusters = []
    idxs = []
    curr_point = points[0]
    curr_cluster = [curr_point]
    curr_idxs = [0]
    for ii, point in enumerate(points[1:]):
        if point == curr_point:
            curr_cluster.append(point)
            curr_idxs.append(ii+1)
        else:
            clusters.append(curr_cluster)
            idxs.append(curr_idxs)
            curr_cluster = [point]
            curr_idxs = [ii+1]
        curr_point = point
    clusters.append(curr_cluster)
    idxs.append(curr_idxs)
    
    true_idx = []
    false_idx = []
    for jj in range(len(clusters)):
        if clusters[jj][0] == True:
            true_idx.append(idxs[jj])
        else:
            false_idx.append(idxs[jj])
    return true_idx, false_idx

def piezo_crop_cycle(data, lbd, increasing_lbd = True, envPeak_delta = 0.04, savitz_window = 39,
                     peakdet_delta=0.5, plot_steps_bool=False):
    
    data = wc.mzi_treat(data, envPeak_delta = envPeak_delta, 
                        savitz_window = savitz_window, plot_steps_bool=plot_steps_bool)
    data['freq_ruler'] = False
    data['cycle'] = False
    ind_peaks_mzi = wc.mzi_peaks(data, peakdet_delta=peakdet_delta, plot_steps_bool=plot_steps_bool)
    
    diff = np.diff(ind_peaks_mzi)
    diff_mean = np.mean(diff)

    diff_s = mlt.savitzky_golay(diff, window_size = 5, order = 1)
    true_idx, false_idx = cluster_bools(diff_s>diff_mean) #not sure it would work well for symmetric fsc

    for ii, cycle in enumerate(true_idx[1:]):
        idx_0 = ind_peaks_mzi[cycle][0]
        idx_f = ind_peaks_mzi[cycle][-1]

        if increasing_lbd:
            freq_ruler = -wc.freq_ruler(lbd, ind_peaks_mzi[cycle])
        else:
            freq_ruler = wc.freq_ruler(lbd, ind_peaks_mzi[cycle])
            
        data.loc[idx_0:idx_f-1, 'freq_ruler'] = freq_ruler[:]
        data.loc[idx_0:idx_f-1, 'cycle']  = ii
        
        if plot_steps_bool:
            plt.plot(freq_ruler, data.mzi_s.values[idx_0:idx_f])
            plt.title("Cycle {}".format(ii))
            plt.show()
    return data

def freq_shift_for_dummies(a1, b1): #a1, b1 are frequencies of peaks
    a = np.sort(a1)
    b=np.sort(b1)
    
    diff = np.array([[np.abs(ai - bj) for bj in b] for ai in a])

    min_j = np.zeros_like(a)
    min_v = np.zeros_like(a)
    
    for i in range(len(a)):
        j = np.argmin(diff[i, :])
        min_j[i] = j
        min_v[i] = diff[i,j]
    
    i0 = np.argmax(min_v)
    j0 = int(min_j[i0])
    print(i0, j0)

    if a[i0]>b[j0]:
        return a[i0]-b[j0]
    else:
        return -a[i0]+b[j0]

def freq_shift_correlation(x1, y1, x2, y2, n = None, plot_bool = False):
    if n is None: n = min(len(x1)//2, len(x2)//2) #careful with time constraints when calculating corr
        
    span = 0.99*min(np.abs(x1[0]), np.abs(x1[-1]), np.abs(x2[0]), np.abs(x2[-1]))
    x_sample = np.linspace(-span, span, n)[1:-1]

    ifunc1 = interpolate.interp1d(x1, y1)
    y1_sample = ifunc1(x_sample)
    ifunc2 = interpolate.interp1d(x2, y2)
    y2_sample = ifunc2(x_sample)

    corr = signal.correlate(np.max(y2_sample)-y2_sample,np.max(y2_sample)-y1_sample, mode='same')
    imatch = np.argmax(corr)
    print('matching index =',imatch)

    if plot_bool:
        plt.plot(x1, y1, '.')
        plt.plot(x_sample, y1_sample)
        plt.plot(x2-x_sample[imatch], y2, '.')
        plt.plot(x_sample-x_sample[imatch], y2_sample)
        plt.show()
    
    return x_sample[imatch], corr[imatch]

def get_sizes(intervals):
    diff = np.diff(intervals)
    sizes = [diff[i][0]/diff[0][0] for i in range(len(diff))]
    
    return sizes

def make_marks(ax, d1, d2, left = True, right = True):
    kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
    kwargs.update(transform=ax.transAxes)
    if right:
        ax.plot((1 - d1, 1 + d1), (-d2, +d2), **kwargs)
        ax.plot((1 - d1, 1 + d1), (1 - d2, 1 + d2), **kwargs)
    if left:
        ax.plot((-d1, +d1), (1-d2, +d2+1), **kwargs)
        ax.plot(( - d1,  d1), (-d2, +d2), **kwargs)

def pxa_peaks(x, y, thshd, fig, ax, xintervals, yinterval = [-70, -10], d = .015,
                window_size_sg = 17, peakdet_delta=5, plot_bool = True, plot_filt = True):
    mask = y>thshd
    x = x[mask]
    y=y[mask]

    y_s = mlt.savitzky_golay(y, window_size = window_size_sg, order = 1)
    posmax, maxtab, posmin, mintab= mlt.peakdet(y_s,peakdet_delta)

    Ω = x[posmax]
    PΩ = y[posmax]
    
    if plot_bool==False:
        return Ω, PΩ
        
    sizes = get_sizes(xintervals)
    divider = make_axes_locatable(ax)
     
    for ii in range(len(xintervals)):
        if ii>0:
            ax = divider.new_horizontal(size="{}%".format(100*sizes[ii]), pad=0.2)
            fig.add_axes(ax)

        if plot_filt:
            line, = ax.plot(x, y, alpha=0.3)
            ax.plot(x, y_s, color = line.get_color())
        else:
            ax.plot(x, y)

        ax.set_xlim(xintervals[ii][0], xintervals[ii][1])
        ax.set_ylim(yinterval[0], yinterval[1])
        
        if ii == 0 and ii+1 != len(xintervals):
            right = True
            left = False
            ax.tick_params(left=True, labelleft=True)
        elif ii+1 == len(xintervals) and ii!=0:
            right = False
            left = True
            ax.tick_params(right=True, labelright=True, left=False, labelleft=False)
        elif ii != 0 and ii+1 != len(xintervals):
            right = False
            left = False
            ax.tick_params(left=False, labelleft=False)
        else:
            right = False
            left = False
    
        ax.spines['left'].set_visible(not left)
        ax.spines['right'].set_visible(not right)
        make_marks(ax, d/sizes[ii], d, left=left, right=right) 
        
    return Ω, PΩ


def is_above_noise(y, gain):
    #if gain ==1e4:
    #    thshd = 0.15
    #else:
    #    thshd = 0.05
    thshd = max(np.mean(y)+2*np.std(y), 0.11)

    return any(y>thshd)