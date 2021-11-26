#%%
import nidaqmx
import numpy as np


_dev_read = "Dev1/ai0" # DAQ input channel
_dev_write = "Dev1/ao0" # DAQ output channel

#auxiliary functions and custom errors
def _daq_write_voltage(voltage, dev_id = _dev_write):
    with nidaqmx.Task() as analog_output:
        analog_output.ao_channels.add_ao_voltage_chan(dev_id)
        analog_output.write(voltage)

def _daq_read_voltage(dev_id = _dev_read):
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(dev_id)
        return np.mean(task.read(number_of_samples_per_channel=3))

class VoltageAboveRange(Exception):
    def __init__(self, err_tshd, message = "Desired voltage is above range supported sensor."):
        self.err_tshd = err_tshd
        self.message = message
        super().__init__(self.message)

class VoltageBelowRange(Exception):
    def __init__(self, err_tshd, message = "Desired voltage is below range supported sensor."):
        self.err_tshd = err_tshd
        self.message = message
        super().__init__(self.message)


#AD590 sensor
class AD590:
    def __init__(self):
        self.temp_range = [-45, 145] #C
        self.volt_range = [-2.25, 7.25] #V

    def volt(self, temp):
        v =  temp/20
        if v > self.volt_range[1]:
            raise VoltageAboveRange()
        elif v<self.volt_range[0]:
            raise VoltageBelowRange()
        else:
            return v
            
    def temp(self, volt):
        return 20*(volt)

#TED200C control
class TED200C:
    def __init__(self, dev_read=_dev_read, dev_write=_dev_write, sensor = 'AD590'):
        if sensor.upper() == 'AD590':
            self.sensor = AD590()
        
        self.dev_read = dev_read
        self.dev_write = dev_write

    def read_temp(self):
        volt = _daq_read_voltage(dev_id=self.dev_read)
        return self.sensor.temp(volt)

    def write_temp(self, temp):
        volt = self.sensor.volt(temp)
        print("TED200C - Desired temperature is: {:.2f} C, applied voltage: {:.2f} V".format(temp,  volt))
        _daq_write_voltage(volt)

    def high_temp_diff(self, temp, steps = 10, wait_time=30):
        temp0 = self.read_temp()
        delta_temp = temp - temp0
        temp_steps = delta_temp/steps
        
        for ii in range(steps):
            self.write_temp(temp0+temp_steps*(ii+1))
            time.sleep(wait_time)
        self.write_temp(temp)

        
    


#%
import matplotlib.pyplot as plt
import time
import pandas as pd

if __name__=='__main__':
    ted = TED200C()
    
    temp_0 = ted.read_temp()


    temp_f =70.0
    for temp_f in range(21, 26):
        print("temp_f", temp_f)
        observation = 'PID_testing_P0_I0_disabled_Dhalf_'
        save_name = 'Tempf{:.1f}_Temp0{:.1f}_LPD'.format(float(temp_f), float(temp_0))
        save_path = './TED200C_characterization/'+observation+save_name

        
        time0 = time.time()
        ted.write_temp(temp_f)

        temp_lst=[]
        time_lst =[]
        temp = 0
        counter=0
        while counter<3600:#temp<0.99*temp_f and counter<5*60:
            time_ = time.time()
            temp = ted.read_temp()

            time_lst.append(time_-time0)
            temp_lst.append(temp)

            time.sleep(.1)
            counter = counter+1

        ted.write_temp(temp_0)
        plt.plot(time_lst, temp_lst)
        plt.title("temp_f: {} [C] ".format(temp_f)+observation)
        plt.xlabel("time [s]")
        plt.ylabel(r"Temperature [$^o$C]")
        plt.show()

        dict_ = {'time':time_lst, 'temp':temp_lst}
        df = pd.DataFrame(dict_)
        df.to_csv(save_path+'.csv')
        time.sleep(120)
# %%


# %%
