#%%
import visa

_sigen_visa = 'USB0::0x0957::0x2B07::MY52701124::INSTR'

#%%

class Sigen:
    def __init__(self, sigen_visa = _sigen_visa):
        self.rm = visa.ResourceManager()
        try:
            self.sigen = self.rm.open_resource(_sigen_visa)
            print("Sigen IDN: "+self.sigen.query("*IDN?"))
        except:
            raise Exception("Could not open signal generator "+_sigen_visa)

    def __del__(self):
        self.output_off()
        self.sigen.close()
    
    def opc(self):
        return self.sigen.query('*OPC?')

    def write(self, msg):
        self.sigen.write(msg)

    def output_on(self):
        self.write('OUTPut ON')
        return self.opc()

    def output_off(self):
        self.write('OUTPut OFF')
        return self.opc()

    def ramp_config(self, symmetry, frequency, amplitude, offset):
        """Defines ramp output function with necessary parameters

        Args:
            symmetry (float): from 0 to 100
            frequency (float): waveform frequency
            amplitude (float): ramp amplitude
            offset (float): voltage offset

        Returns:
            str: expected output is "1\n" of "*OPC?" command
        """
        self.write('FUNCtion RAMP')

        if symmetry>=0 and symmetry<= 100:
            self.write('FUNCtion:RAMP:SYMMetry {:.3f}'.format(symmetry))
        else:
            raise Exception("Symmetry value is out of bounds. It should be in the interval [0,100].")

        self.write('FREQ {:.3f}'.format(frequency))
        self.write('VOLTage {:.3f}'.format(amplitude))
        self.write('VOLTage:OFFSet {:.3f}'.format(offset))
        return self.opc()

    def sine_config(self, frequency, volt_high, volt_low, phase):
        """defines sinusoidal wave as output function
        Args:
            frequency (float): WAVEFORM FREQUENCY
            volt_high (float): maximum voltage
            volt_low (float): minimum voltage
            phase (float): phase in degrees

        Returns:
            str: expected output is "1\n" of "*OPC?" command
        """
        self.write("FUNCtion SIN")
        self.write('FREQ {:.3f}'.format(frequency))
        self.write("VOLTage:HIGH {:.3f}".format(volt_high))
        self.write("VOLTage:LOW {:.3f}".format(volt_low))
        self.write("PHASe {:.3f}".format(phase))
        return self.opc()
        
# %%
if __name__=='__main__':
     sigen = Sigen(_sigen_visa)
     output = sigen.ramp_config(symmetry = 90, frequency = 3, amplitude = 4, offset= 1)
     print(output)
# %%
