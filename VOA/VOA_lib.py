"""
    This module offers tools to control MEMS-based Electronic Variable Optical Attenuators (VOAs).
    The electronic VOA are controlled 

    Raises:
        FileNotFoundError: [description]
        Exception: [description]
        Exception: [description]

    Returns:
        [type]: [description]
"""

#%%
import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
import json


###############################################################################################
### definitions for calibration use ONLY

# to calibrate the device, you should connect the following equipment:
# 
#                     ┌─────────┐           ┌───────┐               ┌─────────────┐
# Optical connections:│  Laser  ├──────────►│  VOA  ├──────────────►│Photodetector│
#                     └─────────┘           └───────┘               └─────────────┘
#                                               |                          |
#                                               ▼                          ▼
#                               ┌────────────────────────────┐  ┌───────────────────────────┐
# BNC connections:              |DAQ output port(_dev_write) |  | DAQ Input port (_dev_read)|
#                               └────────────────────────────┘  └───────────────────────────┘
#

# set variables according to the device to be calibrated.
#   the _calib_function is usually a sigmoid-type function with a second order polinomial in the exponent.
#   there is no special reason for that other than I found it to fit the transmission well.
#   the _calib_function should be defined as a string containing the command for a lambda function.
#   the _inverse_function should be defined similarly;
#       if transmission = _calib_function of the voltage, i.e., t = f(x),
#       then _inverse_function is the inverse: x = f^-1(t)

_serial_number = "187622-1"
_max_voltage = 6
_calib_function = "lambda x, *param: param[0]/(1+np.exp(param[1]+x*param[2]+param[3]*x**2))"
_inverse_function = "lambda t, *param: -0.5*param[2]/param[3]+np.sqrt((np.log(param[0]/t-1) -param[1]+0.25*param[2]**2/param[3])/param[3])"
_dev_read = "Dev1/ai1" # DAQ input channel
_dev_write = "Dev1/ao1" # DAQ output channel
_calib_filename = 'calib_'+_serial_number+'.json' #calibration filename for output

class VOA:
    """
    docstring
    """

    def __init__(self, daq_port, calib_filename):
        """initializes VOA attenuator

        Args:
            daq_port (str): string refering to daq output channel
            calib_filename (str): file path to calibration file

        Raises:
            FileNotFoundError: [description]
            Exception: [description]
        """
        try:
            with open(calib_filename, "r") as jsonfile:
                calib_info = json.load(jsonfile)
                print("Calibration file read successfully")
        except FileNotFoundError as error:
            print(error)
            raise FileNotFoundError('Please select a valid calibration file or perform calibration.') from None
        
        for key in ["max_voltage", "calib_function", "calib_param", "serial_number"]:
            if key not in calib_info:
                raise Exception("Necessary information lacking in calibration file. Missing: "+key)

              
        self.daq_port = daq_port
        self.serial_number = calib_info["serial_number"]
        self.calib_filename = calib_filename
        self.max_voltage = calib_info["max_voltage"]
        self.calib_function = eval(calib_info["calib_function"])
        self.calib_param = calib_info["calib_param"]
        self.inverse_function = eval(calib_info["inverse_function"])

    def daq_write_voltage(self, voltage):

        dev_id = self.daq_port
        with nidaqmx.Task() as analog_output:
            analog_output.ao_channels.add_ao_voltage_chan(dev_id)
            analog_output.write(voltage)

    def att_dB(self, att_value):
        transmission = 10**(-att_value/10)
        voltage = self.inverse_function(transmission, *self.calib_param)
        
        if voltage>self.max_voltage:
            print("VOA "+self.serial_number+": Desired attenuation is too high. Voltage ({:.3f}) was set to maximum.".format(voltage))
            voltage = self.max_voltage
        self.daq_write_voltage(voltage)








if __name__ == '__main__': #calibration routine
    # quick DAQ functions
    def _daq_write_voltage(voltage, dev_id = _dev_write):
        with nidaqmx.Task() as analog_output:
            analog_output.ao_channels.add_ao_voltage_chan(dev_id)
            analog_output.write(voltage)

    def _daq_read_voltage(dev_id = _dev_read):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(dev_id)
            return np.mean(task.read(number_of_samples_per_channel=3))



    write_list = np.linspace(0, _max_voltage, 100)
    read_list = np.zeros(len(write_list))
    
    # write voltage on VOA and read photodetector output
    for ii, v in enumerate(write_list):
        _daq_write_voltage(v)
        read_list[ii] = _daq_read_voltage()
    
    # manipulate and fit data
    read_list = read_list/np.max(read_list)
    funcfit1 =  lambda x, *p: p[0]/(1+np.exp(p[1]+x*p[2]+p[3]*x**2))
    pfit1, pcov1 = curve_fit(funcfit1,write_list, read_list, [1,1,0,0])
    perr1=np.sqrt(np.diag(pcov1))
    print("Parameters relative errors:\n   ", perr1/pfit1, "Parameters values:\n   ", pfit1)

    #plot outputs
    plt.plot(write_list, read_list, '.')
    plt.plot(write_list,funcfit1(write_list,*pfit1))
    plt.show()

    #saves info if calibration is successful
    if all(perr1/pfit1<0.1): # fit has low residues
        #define calibration dict
        calib = {
            "serial_number" : _serial_number,
            "max_voltage" : _max_voltage,
            "calib_function" : _calib_function,
            "inverse_function" : _inverse_function,
            "calib_param" : pfit1.tolist(),
            "calib_data_input" : write_list.tolist(),
            "calib_data_output": read_list.tolist()
        }
        calib_json = json.dumps(calib, indent=4, sort_keys=False)
        #write json file
        with open(_calib_filename, 'w') as jsonfile:
            jsonfile.write(calib_json)
            print("Write successful: "+_calib_filename)
    else:
        raise Exception('Poor calibration data. Fitting parameters not saved.')

    
    #sanity check -- testing att_dB
    voa = VOA(daq_port =_dev_write , calib_filename=_calib_filename)

    att_lst = np.linspace(.1,30, 150)
    t_lst = np.zeros(len(att_lst))
    for ii, att in enumerate(att_lst):
        voa.att_dB(att)
        t_lst[ii] = _daq_read_voltage(dev_id=_dev_read)

    plt.plot(10*np.log10(att_lst), t_lst, '.-')
# %%
