#%%
from sympy import symbols, sqrt, diff, lambdify
from scipy import constants, interpolate, signal, optimize
import pyLPD.MLtools as mlt
import pandas as pd
import numpy as np

c = constants.c
π = constants.pi
ħ=constants.hbar

nist_path = 'C:/Users/lpd/Documents/Leticia/DFS/EquipmentControl/hcn_nist.csv'
nist= pd.read_csv(nist_path, sep = ',')
nist.head()


#%%
B1, B2, B3 = 0.6961663, 0.4079426, 0.8974794
C1, C2, C3 = 68.4043, 116.2414, 9896.161 # in nm

x = symbols('x')
n = sqrt(1+(B1*x**2)/(x**2-C1**2)+(B2*x**2)/(x**2-C2**2)+(B3*x**2)/(x**2-C3**2))
ng = n - x*diff(n, x)

L = 1.49e-3 # in km
print('ΔL_mzi = {0:.3} m'.format(1e3*L))

#--------------------------------
S0 = 0.082 # 0.082(3) ps/(nm².km)
Lamb0 = 1280 # 1280(40) nm

D = S0/4*(x-Lamb0**4/x**3) # in ps/(nm.km)

β1 = 1e15*(ng/c) # ps/km
# global D1_mzi #= 1/β1/L # in THz
D1_mzi = 1/β1/L # in THz

β2 = -1e3*(x**2/2/π/c)*D # in ps²/km
# global D2_mzi
D2_mzi = -(2*π*β2/β1)*(1/β1/L)**2 # in THz

β3 = 1e6*x**3/(2*π*c)**2*(2*D+x*S0) # in ps³/km
# global D3_mzi# = (4*π**2/L**3/β1**5)*(3*β2**2-β1*β3) # in THz
D3_mzi = (4*π**2/L**3/β1**5)*(3*β2**2-β1*β3) # in THz

D1_mzi = 1/β1/L # in THz


if __name__=='__main__':
    import glob, os
    path ="C:\\Users\\lpd\\Documents\\Leticia\\DFS\\2021-09-02_OpticalTransmission\\2021-09-06-16_OpticalTransmission_BareSphere-238umDiameter_Tunics-Laser-5nms-Pol1_C-Band"#os.getcwd()
    data_folder=""#'2021-09-03-12_OpticalTransmission_BareSphere-238umDiameter_Tunics-Laser-5nms-Pol1_C-Band'#'Data_Folder'
    extension = '.parq'

    flist = sorted(glob.glob(os.path.join(path, data_folder, "*"+extension)), key = os.path.getmtime)
    N = 0
    fname = flist[N]

    df = pd.read_parquet(fname)
    
    ylower, df['yupper_cav'] = mlt.envPeak(df.cav.values, delta=0.01,  smooth=0.1, sg_order=1)
    df['cav_n'] = df.cav/(df['yupper_cav'])

    df['ylower_mzi'], df['yupper_mzi'] = mlt.envPeak(df.mzi.values, delta=0.01, sg_order=1) # Finding lower and upper envelope
    df['mzi_n'] = (df.mzi-df['ylower_mzi'])/(df['yupper_mzi']-df['ylower_mzi']) # Normalizing data
    df['mzi_s'] = mlt.savitzky_golay(df.mzi_n.values, window_size = 7, order = 2)

    delta = 0.3
    ind_max, maxtab, ind_min, mintab = mlt.peakdet(df.mzi_n.values, delta)
    ind_peaks = np.sort(np.concatenate((ind_min, ind_max), axis=0))

    df['hcn_n'] = (df.hcn - df.hcn.min())/(df.hcn.max() - df.hcn.min())

    ind_max_hcn, maxtab_hcn, ind_min_hcn, mintab_hcn = mlt.peakdet(df.hcn_n.values, 0.2)

