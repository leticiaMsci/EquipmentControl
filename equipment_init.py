#%%
import ivi
import os
import sys
equip_control_path = 'C:/Users/lpd/Documents/Leticia/DFS/EquipmentControl'
sys.path.insert(1, equip_control_path)

import  tunics_lib, aq63XX, sigen_lib, PXA_lib, thorlabs_pm_lib, EDFA_lib, ted200c
import attenuators as atts
import piezo_routines as piezo
import leticia_lib as llb

#equipment id
daq_port_r = 'Dev1/ao1'

att_in_id = 'ASRL13::INSTR'
att_out_id = 21 #'ASRL9::INSTR'
tunics_ip = 'yetula.ifi.unicamp.br'
sigen_id = 'USB0::0x0957::0x2B07::MY52701124::INSTR'
scope_id = 'TCPIP0::nano-osc-ag9254a::hislip0::INSTR'
osa1_id = 'nano-osa-aq6370c.ifi.unicamp.br'
osa2_id = '143.106.72.187'#'nano-osa2-aq6370c.ifi.unicamp.br'
VOA_sn_r = 'U00306'

pm_id = 'USB0::0x1313::0x80B0::p3000966::0::INSTR'
edfa_gpib_port = 3

ted_read = "Dev1/ai0" # DAQ input channel
ted_write = "Dev1/ao0" # DAQ output channel

#scope channels
ch_reflection = 0
ch_transmission = 1
ch_mzi = 2
ch_hcn=3

#other details
pm_delta_dB = 18.33

def init_equip(**kwargs):#pxa_bool = True, tunics_bool = True, scope_bool = True, sigen_bool = True,
               # osa1_bool = True, osa2_bool = True, pm_bool = True, edfa_bool = True,
               # att_out_bool = True, att_in_bool = True, att_r_bool = True):

    equip = {
        'scope_ch_r' : ch_reflection,
        'scope_ch_t' : ch_transmission,
        'scope_ch_mzi' : ch_mzi,
        "scope_ch_hcn" : ch_hcn,
    }
    #attenuators
    if kwargs.get('att_out') is True: 
        #att_out = VOA_lib.VOA(daq_port_t, os.path.join(equip_control_path, VOA_calib_path_t))
        att_out = atts.MN9625A(gpib = att_out_id)
        equip['att_out'] = att_out

    if kwargs.get('att_in') is True:
        att_in = atts.DA100(resource_str = att_in_id)
        equip['att_in'] = att_in

    if kwargs.get('att_r') is True:
        #att_r = att_lib.Att(resource_str = att_r_id)
        att_r = atts.VOA(daq_port_r, VOA_sn_r)
        equip['att_r'] = att_r

    #other equipment
    if kwargs.get('pxa') is True:
        pxa = PXA_lib.N9030A()
        equip['pxa'] = pxa

    if kwargs.get('tunics') is True:
        tunics = tunics_lib.T100R(ip=tunics_ip)
        tunics.connect()
        equip['tunics'] = tunics

    if kwargs.get('scope') is True:
        scope = ivi.agilent.agilentDSOX92504A(scope_id, prefer_pyvisa = True)
        equip['scope'] = scope
    
    if kwargs.get('sigen') is True:
        sigen = sigen_lib.Sigen(sigen_id = sigen_id)
        equip['sigen'] = sigen

    if kwargs.get('osa1') is True:
        osa1 = aq63XX.AQ63XX()
        osa1.ConnectOSA(isgpib = False, iseth = True, ethip = osa1_id, ipuser = 'anonymous', ippass='123456')
        osa1.osa.write('AUTO OFFSET OFF')
        osa1.InitOSA(print_bool=False)
        equip['osa1'] = osa1


    if kwargs.get('osa2') is True:
        osa2 = aq63XX.AQ63XX()
        osa2.ConnectOSA(isgpib = False, iseth = True, ethip = osa2_id,  ipuser = 'anonymous', ippass='123456')
        osa2.osa.write('AUTO OFFSET OFF')
        osa2.InitOSA(print_bool=False)
        equip['osa2'] = osa2

    if kwargs.get('pm') is True:
        pm = thorlabs_pm_lib.PM200(pm_id)
        equip['pm'] = pm

    if kwargs.get('edfa') is True:
        edfa = EDFA_lib.KeopsysEDFA(gpib_port=edfa_gpib_port)
        equip['edfa'] = edfa

    if kwargs.get('ted') is True:
        ted = ted200c.TED200C(dev_read=ted_read, dev_write=ted_write)
        equip['ted'] = ted


    print("All Equipment Initialized Successfully")

    return equip


if __name__=='__main__':
    import visa
    rm = visa.ResourceManager()
    print(rm.list_resources())

    equip = init_equip(att_out=True, att_in = True)
    att_out = equip['att_out']
    att_in = equip['att_in']
    att_out.set_att(31)
    
# %%