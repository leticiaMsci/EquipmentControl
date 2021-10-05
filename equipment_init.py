import ivi
import os
import sys
equip_control_path = 'C:/Users/lpd/Documents/Leticia/DFS/EquipmentControl'
sys.path.insert(1, equip_control_path)

import att_lib, tunics_lib, aq63XX, sigen_lib, PXA_lib, thorlabs_pm_lib
import piezo_routines as piezo
import VOA.VOA_lib as VOA_lib
import leticia_lib as llb

#equipment id
daq_port = 'Dev1/ao1'
att_in_id = 'ASRL5::INSTR'
att_r_id = 'ASRL13::INSTR'
tunics_ip = 'yetula.ifi.unicamp.br'
sigen_id = 'USB0::0x0957::0x2B07::MY52701124::INSTR'
scope_id = 'TCPIP0::nano-osc-ag9254a::hislip0::INSTR'
osa1_id = 'nano-osa-aq6370c.ifi.unicamp.br'
osa2_id = '143.106.72.222'
VOA_calib_path = 'VOA\calib_U00306.json'
pm_id = 'USB0::0x1313::0x80B0::p3000966::0::INSTR'

#scope channels
ch_reflection = 0
ch_transmission = 1
ch_mzi = 2
ch_hcn=3

#other details
pm_delta_dB = 18.33

def init_equip():
    #attenuators
    att_out = VOA_lib.VOA(daq_port, os.path.join(equip_control_path, VOA_calib_path))
    att_in = att_lib.Att(resource_str = att_in_id)
    att_r = att_lib.Att(resource_str = att_r_id)

    #other equipment
    pxa = PXA_lib.N9030A()
    tunics = tunics_lib.T100R(ip=tunics_ip)
    tunics.connect()
    scope = ivi.agilent.agilentDSOX92504A(scope_id, prefer_pyvisa = True)
    sigen = sigen_lib.Sigen(sigen_id = sigen_id)

    osa1 = aq63XX.AQ63XX()
    osa1.ConnectOSA(isgpib = False, iseth = True, ethip = osa1_id, ipuser = 'anonymous', ippass='123456')
    osa1.osa.write('AUTO OFFSET OFF')
    osa1.InitOSA(print_bool=False)

    osa2 = aq63XX.AQ63XX()
    osa2.ConnectOSA(isgpib = False, iseth = True, ethip = osa2_id, ipuser = '', ippass='')
    osa2.osa.write('AUTO OFFSET OFF')
    osa2.InitOSA(print_bool=False)

    pm = thorlabs_pm_lib.PM200(pm_id)


    print("All Equipment Initialized Successfully")

    equip = {
        'att_out' : att_out,
        'att_in' : att_in,
        'att_r' : att_r,

        'pxa' : pxa,
        'tunics' : tunics,
        'scope' : scope,
        'sigen' : sigen,

        'scope_ch_r' : ch_reflection,
        'scope_ch_t' : ch_transmission,
        'scope_ch_mzi' : ch_mzi,
        "scope_ch_hcn" : ch_hcn,

        'osa1' : osa1,
        'osa2' : osa2,

        'pm':pm
    }

    return equip