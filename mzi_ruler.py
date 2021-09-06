#%%
from sympy import symbols, sqrt, diff, lambdify
from scipy import constants, interpolate, signal, optimize

c = constants.c
π = constants.pi
ħ=constants.hbar
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