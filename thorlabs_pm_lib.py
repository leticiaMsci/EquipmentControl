#%%
import visa
import numpy as np
_delta_dB = 18.33
class PM200:
    def __init__(self, resource_id, delta_dB = _delta_dB):
        self.rm = visa.ResourceManager()
        self.pm = self.connection(resource_id)
        self.delta_dB = delta_dB

    def connection(self, resource_id):
        '''
        Simple visa connection 
        
        Parameters
        ----------
        resource_id: string
            Resource id obtained from  visa.ResourceManager().list_resources()
        '''
        print("Thorlabs PM200", end = '')
        pm = self.rm.open_resource(resource_id)
        pm.write_termination = '\r'
        pm.read_termination = '\n'
        pm.query_delay = 0.5 # delay in seconds
        pm.timeout = 10 # timeout seconds
        print(" connected. IDN:", pm.query('*IDN?'))
        pm.close()
        
        return pm

    def query(self, msg):
        self.pm.open()
        output =  self.pm.query(msg)
        self.pm.close()

        return output

    def write(self, msg):
        self.pm.open()
        self.pm.write(msg)
        self.pm.close()

    def pow_dBm(self, delta_input = False):
        pow_str = self.query('MEAS:POW?')
        pow_float = 10*np.log10(float(pow_str)*1e3)

        if delta_input:
            return pow_float+self.delta_dB
        else:
            return pow_float

    


#%%
if __name__=='__main__':
    resource_id = 'USB0::0x1313::0x80B0::p3000966::0::INSTR'
    pm = PM200(resource_id)

    print(pm.meas_pow(unit = 'dBm'))
#%%