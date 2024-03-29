"""This module contains functions to automatically calibrate in
frequency our experimental data containing a fiber-MZI and a
Wavelength Reference Gas cell.

This module must be acompanied by a .csv file containing the
reference wavelength data.

Your data must be passed as a dataframe with columns:
    [\'cav\', \'mzi\', \'hcn\'].


Example 1 - Using out of the box:
-------
import wavelength_calibration as wc
import pandas as pd

data_raw = pd.read_parquet('some_experiment.parq')
data_calibrated = wc.auto_calibrate(data_raw, 'path_for_saving_calibrated_data')
# this will output a plot showing the calibrated HCN spectrum and will save a file
# named 'path_for_saving_calibrated_data_Processed.parq'


Example 2 - How to change parameters:
-------
import wavelength_calibration as wc

#first, you must first check if MZI and HCN peaks are being identified correctly:
wc.param['plot_steps_bool'] = True
wc.mzi_treat(data_raw)
wc.mzi_peaks(data_raw)
wc.hcn_peaks(data_raw)

#change the following parameters to smooth and normalize the data adequately
wc.param['mzi_envPeak_delta'] = 0.01
wc.param['mzi_envPeak_sg'] = 2
wc.param['mzi_savitz_window'] = 5
wc.param['mzi_savitz_order'] = 2

#if peaks are not identified correctly, tune the following parameter
#until wc.mzi_peaks gets the peaks correctly
wc.param['mzi_peakdet_delta'] = 0.3

#same for the hcn data:
param['hcn_peakdet_delta'] = 0.33

#plot again to see if it got any better
wc.mzi_treat(data_raw)
wc.mzi_peaks(data_raw)
wc.hcn_peaks(data_raw)

Raises:
--------
    NistFileNotFound: Raises error if reference file cannot be loded (probaly because it is not in the same directory).
        (TODO: Embed possibility of using acetylen reference and make it easy for the end-user.)
    NistIncorrectKeys: Raised if nist file does not contain the correct column keys.
    CalibrationUnsuccessful: Raises error if it couldn't optimize the reference wavelength to minimize errors when comparing the other HCN peaks.
    DataIncorrectKeys: Raises error if data does not contain correct colums keys.
"""

#%%
import os
import itertools
import sys
import numpy as np
import pandas as pd
import pyLPD.MLtools as mlt

from matplotlib import pyplot as plt
from sympy import symbols, sqrt, diff, lambdify
from scipy import constants, interpolate, signal, optimize
from itertools import chain

π = constants.pi
c = constants.c

nist_file = 'hcn_nist.csv'
nist_dir = os.path.dirname(os.path.realpath(__file__))


param = {
    'nist_path' : os.path.join(nist_dir, nist_file),
    'hcn_peakdet_delta':0.3,

    'mzi_fiber_length': 1.49e-3, #in km
    'mzi_envPeak_delta': 0.01,
    'mzi_envPeak_sg': 1,
    'mzi_savitz_window': 7,
    'mzi_savitz_order': 2,
    'mzi_peakdet_delta': 0.3,

    'cav_envPeak_delta': 0.01,
    'cav_envPeak_smooth': 0.1,
    'cav_envPeak_sg': 1,

    'plot_steps_bool': False,
    'err_tshd': 0.01 #(in THz) default threshold of maximum calibration error
}


class CalibrationUnsuccessful(Exception):
    """Exception raised for errors in the input salary.

    Attributes:
        salary -- input salary which caused the error
        message -- explanation of the error
    """

    def __init__(self, err_tshd, message = "Error not under defined threshold"):
        self.err_tshd = err_tshd
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} {self.err_tshd}. Consider reversing your data with function reverse(data).'

class NistFileNotFound(Exception):
    def __init__(self, path, message = "Could not load nist reference."):
        self.path =path
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return f'{self.message} Path: \'{self.path}\'. Please make sure that the file is in the same directory of '+__path__ +'\nAlternatively (not recommended) update file path on param[\'nist_path\']'

class NistIncorrectKeys(Exception):
    def __init__(self, expected, given, message = "Nist Wavelength Reference file has incorrect data or incorrect keys."):
        self.expected = expected
        self.given = given
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return f'{self.message}\nExpected {self.expected}\nReceived {self.given}'

class DataIncorrectKeys(Exception):
    def __init__(self, expected, given, message ="Dataframe does no contain the necessary information or incorrect keys (cav, mzi, hcn)."):
        self.expected = expected
        self.given = given
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return f'{self.message}\nExpected {self.expected}\nReceived {self.given}'


def load_nist(nist_path):
    try:
        nist= pd.read_csv(nist_path,sep=',')
        print("Successfully loaded wavelength reference file "+nist_path)
    except:
        raise NistFileNotFound(nist_path)
    
    handles =['R Branch','R-wavelength(nm)','P Branch','P-wavelength(nm)']
    for key in handles:
        if key not in nist.keys():
            raise NistIncorrectKeys(handles, nist.keys())

    return nist

    
def reverse(data):
    data = data[::-1].reset_index().copy()
    return data

def cav_treat(data, envPeak_delta = None, envPeak_smooth = None, envPeak_sg = None):
    """If wavelength is increasing, inverts data. It also normalizes the 'cav' entry by its upper envelope.

    Args:
        data (dataframe): raw data acquired. Should have 'cav' key.
        increasing_wlg (bool, optional): envPeak parameter.
        envPeak_delta (float, optional): envPeak parameter.
        envPeak_smooth (float, optional): envPeak parameter.
        envPeak_sg (int, optional): envPeak parameter.
    """
    #setting default values (as defined in params) if not given:
    if envPeak_delta is None: envPeak_delta = param['cav_envPeak_delta']
    if envPeak_smooth is None: envPeak_smooth = param["cav_envPeak_smooth"]
    if envPeak_sg is None: envPeak_sg = param["cav_envPeak_sg"]

    #actual function
    ylower, data['yupper_cav'] = mlt.envPeak(data.cav.values, delta=envPeak_delta,  smooth=envPeak_smooth, sg_order=envPeak_sg)
    data['cav_n'] = data.cav/(data['yupper_cav'])

    return data


def mzi_dispersion(L = None): # in km
    """Defines dispersion functions of fiber-based MZI's.

    Args:
        L (float, optional): fiber length in kilometers. Defaults to 1.49e-3.

    Returns:
        symbolic dispersions
    """
    #setting default values if not given
    if L is None: L = param['mzi_fiber_length']

    #actual function
    π = constants.pi
    c = constants.c
    B1, B2, B3 = 0.6961663, 0.4079426, 0.8974794
    C1, C2, C3 = 68.4043, 116.2414, 9896.161 # in nm

    x = symbols('x')
    n = sqrt(1+(B1*x**2)/(x**2-C1**2)+(B2*x**2)/(x**2-C2**2)+(B3*x**2)/(x**2-C3**2))
    ng = n - x*diff(n, x)


    #--------------------------------
    S0 = 0.082 # 0.082(3) ps/(nm².km)
    Lamb0 = 1280 # 1280(40) nm

    D = S0/4*(x-Lamb0**4/x**3) # in ps/(nm.km)

    β1 = 1e15*(ng/c) # ps/km
    D1_mzi = 1/β1/L # in THz

    β2 = -1e3*(x**2/2/π/c)*D # in ps²/km
    D2_mzi = -(2*π*β2/β1)*(1/β1/L)**2 # in THz

    β3 = 1e6*x**3/(2*π*c)**2*(2*D+x*S0) # in ps³/km
    D3_mzi = (4*π**2/L**3/β1**5)*(3*β2**2-β1*β3) # in THz
    
    return x, D1_mzi, D2_mzi, D3_mzi

def mzi_treat(data, envPeak_delta = None, envPeak_sg = None,
             savitz_window = None, savitz_order=None, plot_steps_bool = None):
    """Normalizes MZI using lower and upper envelopes. It also smooths the MZI signal using a savitz golay filter.

    Args:
        data (dataframe): raw data acquired. Should have 'mzi' key.
        envPeak_delta (float, optional): envPeak parameter.
        envPeak_sg (int, optional): envPeak parameter.
        savitz_window (int, optional): savitz golay parameter.
        savitz_order (int, optional): savitz golay parameter. 
        plot_steps_bool (bool, optional): If true plots MZI signal and smoothed. Defaults to False.
    """
    #setting default values if not given
    if envPeak_delta is None: envPeak_delta = param['mzi_envPeak_delta']
    if envPeak_sg is None: envPeak_sg = param['mzi_envPeak_sg']
    if savitz_window is None: savitz_window = param['mzi_savitz_window']
    if savitz_order is None: savitz_order=param['mzi_savitz_order']
    if plot_steps_bool is None: plot_steps_bool = param['plot_steps_bool']

    #actual function
    ylower_mzi, yupper_mzi = mlt.envPeak(data.mzi.values, delta=envPeak_delta, sg_order=envPeak_sg)# Finding lower and upper envelope
    data['mzi_n'] = (data.mzi-ylower_mzi)/(yupper_mzi-ylower_mzi) # Normalizing data
    
    if savitz_window%2==0: savitz_window=savitz_window+1

    data['mzi_s'] = mlt.savitzky_golay(data.mzi_n.values, window_size = savitz_window, order = savitz_order)
    
    if plot_steps_bool:
        plt.figure(figsize=(12,3))
        mid_data = len(data)//2
        delta_data = min(100, int(0.1*mid_data))
        plt.plot(data['mzi_n'].values[mid_data-delta_data:mid_data+delta_data], '.', alpha=0.5, label = 'normalized')
        plt.plot(data['mzi_s'].values[mid_data-delta_data:mid_data+delta_data], label = 'smoothed')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.show()

    return data
    
def mzi_peaks(data, peakdet_delta=None, plot_steps_bool = None):
    """determines MZI peaks

    Args:
        data (dataframe): raw data acquired. Should have 'mzi' key.
        peakdet_delta (float, optional): peakdet parameter.
        plot_steps_bool (bool, optional): If true displays plot of identified MZI peaks.

    Returns:
        [array]: returns indexes (in data) of mzi peaks.
    """
    #setting default values if not given
    if peakdet_delta is None: peakdet_delta = param['mzi_peakdet_delta']
    if plot_steps_bool is None: plot_steps_bool = param['plot_steps_bool']

    #actual function
    ind_max, maxtab, ind_min, mintab = mlt.peakdet(data.mzi_n.values, delta=peakdet_delta)
    ind_peaks_mzi = np.sort(np.concatenate((ind_min, ind_max), axis=0))
    
    if plot_steps_bool:
        plt.figure(figsize=(12,3))
        npeaks = min(70, int(0.05*len(ind_max)))
        plt.plot(data.time[:ind_max[npeaks]], data.mzi_n[:ind_max[npeaks]], label='MZI')
        plt.scatter(data.time[:ind_min[npeaks]][ind_min[:npeaks]], mintab[:npeaks], s=50, c='r', label='min')
        plt.scatter(data.time[:ind_max[npeaks]][ind_max[:npeaks]], maxtab[:npeaks], s=50, c='g', label='max')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.show()
         
    return ind_peaks_mzi

def hcn_peaks(data, peakdet_delta=None):
    """identifies and return peaks in HCN (wavelength reference) data.

    Args:
        data (dataframe): raw data acquired. Should have 'hcn' key.
        peakdet_delta (float, optional): peakdet parameter.
        plot_steps_bool (bool, optional): If true displays detected peaks in HCN data.

    Returns:
        [array, array]: indexes in data of hcn peaks, y value of hcn peaks.
    """
    #setting default values if not given
    if peakdet_delta is None: peakdet_delta = param['hcn_peakdet_delta']

    #actual function
    data['hcn_n'] = (data.hcn - data.hcn.min())/(data.hcn.max() - data.hcn.min())
    ind_max_hcn, maxtab_hcn, ind_min_hcn, mintab_hcn = mlt.peakdet(data.hcn_n.values, peakdet_delta)
    
    if param['plot_steps_bool']:
        plt.figure(figsize=(21,4))
        plt.plot(data.time[:], data.hcn_n[:], label='HCN')
        plt.scatter(data.time[ind_min_hcn], mintab_hcn, c='g', s=50, label='min')

        ax = plt.gca()
        for ii in range(0,len(ind_min_hcn)):
            ax.annotate(ii, (data.time[ind_min_hcn[ii]], mintab_hcn[ii]), color='r', fontsize=15)

        plt.xlabel('Time (s)')
        plt.ylabel('Norm. Trans.')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.tight_layout()
        plt.show()
    
    return ind_min_hcn, mintab_hcn

def calibration(data, λ0, peak_hcn, ind_min_hcn, ind_peaks_mzi):
    """Performs frequency calibration:
            1-setting reference peak (λ0) in the 'peak_hcn'-th peak in measured hcn spectra.
            2-using mzi peaks as frequency ruler.

    Args:
        data (dataframe): data to undergo frequency calibration
        λ0 (float): wavelength reference peak.
        peak_hcn (int): index of measured hcn peak that will be set as λ0.
        ind_min_hcn (array): indexes in data of hcn peaks
        ind_peaks_mzi (array): indexes (in data) of mzi peaks.

    Returns:
        dataframe: copy of data with calibrated frequency for each row.
                    Notice that the data will be trimmed at the first and last mzi peaks.
    """
    
    c = constants.c
    freq0 = 1e-3*c/λ0
    
    idx_central = np.argmin(np.abs(ind_min_hcn[peak_hcn] - ind_peaks_mzi))
    range_vector = (np.arange(len(ind_peaks_mzi)) - idx_central)/2
    
    x, D1_mzi, D2_mzi, D3_mzi = mzi_dispersion()
    D1_mzi = lambdify(x, D1_mzi)(λ0) # FSR for MZI in THz
    D2_mzi = lambdify(x, D2_mzi)(λ0) # D2/2pi for MZI in THz
    D3_mzi = lambdify(x, D3_mzi)(λ0) # D3/2pi for MZI in THz
    
    freq_r = freq0 + D1_mzi*range_vector + D2_mzi/2*range_vector**2 + D3_mzi/6*range_vector**3

    freq_ifunc = interpolate.interp1d(data.time[ind_peaks_mzi], freq_r)

    data_i = data.iloc[min(ind_peaks_mzi):max(ind_peaks_mzi),:].copy()
    data_i['freq'] = freq_ifunc(data_i.time)
    data_i.reset_index(drop=True, inplace=True)
    
    return data_i

def freq_ruler(λ0, ind_peaks_mzi):
    """Performs frequency calibration:
            1-setting reference peak (λ0) in the 'peak_hcn'-th peak in measured hcn spectra.
            2-using mzi peaks as frequency ruler.

    Args:
        data (dataframe): data to undergo frequency calibration
        λ0 (float): wavelength reference peak.
        peak_hcn (int): index of measured hcn peak that will be set as λ0.
        ind_min_hcn (array): indexes in data of hcn peaks
        ind_peaks_mzi (array): indexes (in data) of mzi peaks.

    Returns:
        dataframe: copy of data with calibrated frequency for each row.
                    Notice that the data will be trimmed at the first and last mzi peaks.
    """
    
    idx_central = int(len(ind_peaks_mzi)/2)
    range_vector = (np.arange(len(ind_peaks_mzi)) - idx_central)/2
    
    x, D1_mzi, D2_mzi, D3_mzi = mzi_dispersion()
    D1_mzi = lambdify(x, D1_mzi)(λ0) # FSR for MZI in THz
    D2_mzi = lambdify(x, D2_mzi)(λ0) # D2/2pi for MZI in THz
    D3_mzi = lambdify(x, D3_mzi)(λ0) # D3/2pi for MZI in THz
    
    freq_r = D1_mzi*range_vector + D2_mzi/2*range_vector**2 + D3_mzi/6*range_vector**3

    freq_ifunc = interpolate.interp1d(ind_peaks_mzi, freq_r)

    freq_ruler = freq_ifunc(np.arange(min(ind_peaks_mzi),max(ind_peaks_mzi)))

    return freq_ruler

def plot_calibration(data_i, ind_min_hcn, mintab_hcn, nist, save_bool, base_name = "./"):
    """Plots resulting calibration overlayered by expected peaks of wavelength reference.

    Args:
        data_i (dataframe): calibrated data.
        ind_min_hcn (array): indexes in data of hcn peaks
        mintab_hcn (array): y values of hcn peaks
        nist (dataframe): table of reference wavelengths
        save_bool (bool): If true will save pdf of calibration plot in path 'base_name'
        base_name (str, optional): Path and root name of output pdf file. Defaults to "./".
    """
    plt.figure(figsize=(19,5))
    plt.plot(data_i.freq[:], data_i.hcn_n[:])
    plt.scatter(data_i.freq[ind_min_hcn], mintab_hcn)
    colors = itertools.cycle(['r', 'g', 'm'])
    #----
    plt.stem(1e-3*c/nist['R-wavelength(nm)'], 1.5*np.ones(len(nist)),
             'r',markerfmt='o',label='R-branch')
    plt.stem(1e-3*c/nist['P-wavelength(nm)'], 1.5*np.ones(len(nist)),
             'b',markerfmt='o',label='P-branch')
    #---- Annotations
    ax = plt.gca()
    for ii in range(0,len(ind_min_hcn)):
        ax.annotate('{:.3f} nm'.format(1e-3*c/data_i.freq[ind_min_hcn[ii]]),
                    (data_i.freq[ind_min_hcn[ii]]*1.00002, 0.5),
                    color=next(colors), rotation=90)
    #----
    for ii in range(0,len(nist)-1):
        ax.annotate(nist['R Branch'][ii], (1e-3*c/nist['R-wavelength(nm)'][ii], 1.2),
                    color='r', fontsize=15)
        ax.annotate(nist['P Branch'][ii], (1e-3*c/nist['P-wavelength(nm)'][ii], 1.2), 
                    color='b', fontsize=15)
    plt.grid(True)
    plt.legend()
    plt.xlabel('Frequency (THz)')
    plt.ylabel('Norm. Trans.')
    plt.xlim(data_i.freq.values[0], data_i.freq.values[-1])
    
    
    if save_bool: plt.savefig(base_name+'frequency_calibration.pdf',bbox_inches='tight') 
    
    plt.show()

def optimize_reference(data, ind_min_hcn, mintab_hcn, 
                       ind_peaks_mzi, nist, save_bool, base_name,
                       err_tshd = None):
    """Chooses the middle hcn data peak and scans the reference wavelength to find the one that
    minimizes the error for the other hcn peaks.

    Args:
        data (dataframe): data.
        ind_min_hcn (int array): indexes in data of hcn peaks.
        mintab_hcn (float array): y values of hcn peaks
        ind_peaks_mzi (int array): indexes (in data) of mzi peaks.
        nist (dataframe): table of reference wavelengths
        save_bool (bool): If true will save pdf of calibration plot in path 'base_name'
        base_name (str, optional): Path and root name of output pdf file. Defaults to "./".

    Raises:
        CalibrationUnsuccessful: if none of the lbd_guess in lbd_ref engender a calibration 
        error of other peaks within err_tshd

    Returns:
        dataframe: calibrated data.
    """
    #setting default values if not given
    if err_tshd is None: err_tshd = param['err_tshd']
    
    #actual function
    c = constants.c

    peak_guess = len(ind_min_hcn)//2
    lbd_ref = np.array(list(chain(*zip(nist['R-wavelength(nm)'].values[::-1], nist['P-wavelength(nm)'].values[:-1]))))
    
    print("Optimizing reference wavelength:")
    for jj, lbd_guess in enumerate(lbd_ref[:]):
        data_i = calibration(data, lbd_guess,  peak_guess, ind_min_hcn, ind_peaks_mzi)
        meas_freq = data_i.freq.values[ind_min_hcn]
        error_tab = []
        
        error_tab = [min(np.abs(f - 1e-3*c/lbd_ref)) for f in meas_freq]
        max_error = max(error_tab)

        print_ = 'λ0 = {:8.5f} nm, ν0 = {:.5f} THz Max error = {:.3f} THz'.format(lbd_guess, 1e-3*c/lbd_guess, max_error)
        sys.stdout.write('\r'+print_)
        sys.stdout.flush()
        
        if max_error<err_tshd:      
            plot_calibration(data_i, ind_min_hcn, mintab_hcn, nist, save_bool = save_bool, base_name = base_name)
            return data_i
    raise CalibrationUnsuccessful(err_tshd)

def test_optimize(data, ind_min_hcn, mintab_hcn, 
                       ind_peaks_mzi, nist, save_bool, base_name,
                       err_tshd = None):
    """Chooses the middle hcn data peak and scans the reference wavelength to find the one that
    minimizes the error for the other hcn peaks.

    Args:
        data (dataframe): data.
        ind_min_hcn (int array): indexes in data of hcn peaks.
        mintab_hcn (float array): y values of hcn peaks
        ind_peaks_mzi (int array): indexes (in data) of mzi peaks.
        nist (dataframe): table of reference wavelengths
        save_bool (bool): If true will save pdf of calibration plot in path 'base_name'
        base_name (str, optional): Path and root name of output pdf file. Defaults to "./".

    Raises:
        CalibrationUnsuccessful: if none of the lbd_guess in lbd_ref engender a calibration 
        error of other peaks within err_tshd

    Returns:
        dataframe: calibrated data.
    """
    #setting default values if not given
    if err_tshd is None: err_tshd = param['err_tshd']
    
    #actual function
    c = constants.c

    peak_guess = len(ind_min_hcn)//2
    lbd_ref = np.array(list(chain(*zip(nist['R-wavelength(nm)'].values[::-1], nist['P-wavelength(nm)'].values[:-1]))))
    err_lst = np.zeros_like(lbd_ref)
    print("Optimizing reference wavelength:")
    for jj, lbd_guess in enumerate(lbd_ref[:]):
        data_i = calibration(data, lbd_guess,  peak_guess, ind_min_hcn, ind_peaks_mzi)
        meas_freq = data_i.freq.values[ind_min_hcn]
        error_tab = []
        
        error_tab = [min(np.abs(f - 1e-3*c/lbd_ref)) for f in meas_freq]
        max_error = max(error_tab)

        print_ = 'λ0 = {:8.5f} nm, ν0 = {:.5f} THz Max error = {:.3f} THz'.format(lbd_guess, 1e-3*c/lbd_guess, max_error)
        sys.stdout.write('\r'+print_)
        sys.stdout.flush()
        
        err_lst[jj] = max_error
        #if max_error<err_tshd:      
        #    plot_calibration(data_i, ind_min_hcn, mintab_hcn, nist, save_bool = save_bool, base_name = base_name)
        #    return data_i
    
    jj_min = np.argmin(err_lst)
    error = err_lst[jj_min]
    lbd_guess = lbd_ref[jj_min]
    print("\n Error:{:.3f}".format(error))
    data_i = calibration(data, lbd_guess,  peak_guess, ind_min_hcn, ind_peaks_mzi)
    plot_calibration(data_i, ind_min_hcn, mintab_hcn, nist, save_bool = save_bool, base_name = base_name)
    return data_i

    #raise CalibrationUnsuccessful(err_tshd)

def auto_calibrate(data_in, base_name, nist_path = None, forward_lbd_scan = True):
    if nist_path is None: nist_path = param['nist_path']
    nist = load_nist(nist_path)

    for key in ['cav', 'mzi', 'hcn']:
        if key not in data_in.keys():
            raise DataIncorrectKeys(['cav', 'mzi', 'hcn'] , data_in.keys())

    if forward_lbd_scan:
        data_raw = data_in[::-1].reset_index().copy()

    
    data_raw = cav_treat(data_raw)
    data_raw = mzi_treat(data_raw)

    ind_peaks_mzi_ = mzi_peaks(data_raw)
    ind_min_hcn_, mintab_hcn_ = hcn_peaks(data_raw)
    data_i = optimize_reference(data_raw, ind_min_hcn_, mintab_hcn_, ind_peaks_mzi_, nist, 
                    save_bool = True, base_name = base_name)
    

    data = pd.DataFrame()

    data['freq'] = data_i.freq
    data['mzi'] = data_i.mzi_s
    data['cav'] = data_i.cav_n
    data['hcn'] = data_i.hcn
    data['reflec'] = data_i.reflec

    print(base_name+'_Processed.parq')

    data.to_parquet(base_name+'_Processed.parq', compression='brotli')
    return data
#%%
if __name__=='__main__':
    fname='C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-09-02_OpticalTransmission\\2021-09-07-11_OpticalTransmission_BareSphere-238umDiameter_Tunics-Laser-5nms-Pol1_C-Band\\2021-09-07-11-44_Att_in34_C-BandSweep.parq'
    data_raw = pd.read_parquet(fname)
    nist = load_nist(param['nist_path'])
    #try:
    if False:
        data_raw = cav_treat(data_raw)
        data_raw = mzi_treat(data_raw)

        ind_peaks_mzi_ = mzi_peaks(data_raw)
        ind_min_hcn_, mintab_hcn_ = hcn_peaks(data_raw)
        data_i = optimize_reference(data_raw, ind_min_hcn_, mintab_hcn_, ind_peaks_mzi_, nist, save_bool = False, base_name = fname[:-5])
    #except CalibrationUnsuccessful:
    if False:
        data_raw = reverse(data_raw)

        ind_peaks_mzi_ = mzi_peaks(data_raw)
        ind_min_hcn_, mintab_hcn_ = hcn_peaks(data_raw)
        data_i = optimize_reference(data_raw, ind_min_hcn_, mintab_hcn_, ind_peaks_mzi_, nist, save_bool = False, base_name = fname[:-5])

    base_name = fname[:-6]
    auto_calibrate(data_raw, base_name, forward_lbd_scan = True)



# %%
