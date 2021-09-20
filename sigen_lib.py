"""[summary]

    Raises:
        Exception: [description]
        Exception: [description]

    Returns:
        [type]: [description]
"""


#%%
import visa
_sigen_id = 'USB0::0x0957::0x2B07::MY52701124::INSTR'


class Sigen:
    def __init__(self, sigen_id = _sigen_id, 
                high_impedance = True, v_limits = True):
        self.rm = visa.ResourceManager()
        try:
            self.sigen = self.rm.open_resource(_sigen_id, read_termination="\n")
            print("Sigen IDN: "+self.sigen.query("*IDN?"))
        except:
            raise Exception("Could not open signal generator "+_sigen_id)
        
        #instantiating inner classes
        self.output = self.Output(self)
        self.waveforms = self.Waveforms(self)

        #setting output impedance and voltage limits for safety reasons
        if high_impedance: self.output.high_impedance()
        if v_limits: self.output.v_limits()

        #setting params
        self.function = "None"
        self.frequency = 0


    def __del__(self):
        self.output_off()
        self.sigen.close()
    
    def opc(self):
        return self.sigen.query('*OPC?')

    def write(self, msg):
        self.sigen.write(msg)

    def query(self, msg):
        return self.sigen.query(msg)

    class Output:
        def __init__(self, outer):
            self.outer = outer

        def _write(self, msg):
            self.outer.write(msg)

        def _opc(self):
            return self.outer.opc()

        def on(self):
            self._write('OUTPut ON')
            return self._opc()

        def off(self):
            self._write('OUTPut OFF')
            return self._opc()
        
        def high_impedance(self):
            self._write('OUTPut:LOAD INF')

        def ohm_impedance(self, ohm):
            self._write('OUTPut:LOAD {:.1f}'.format(ohm))

        def v_limits(self, v_low = -10, v_high = 10):
            self._write('VOLTage:LIMit:LOW {:.1f}'.format(v_low))
            self._write('VOLTage:LIMit:HIGH {:.1f}'.format(v_high))
            self._write('VOLTage:LIMit:STATe ON')

    class Waveforms:
        def __init__(self, outer):
            self.outer = outer

        def _write(self, msg):
            self.outer.write(msg)
        
        def _opc(self):
            return self.outer.opc()

        def ramp(self, symmetry = None, frequency= None, amplitude= None, offset= None):
            """Defines ramp output function with necessary parameters

            Args:
                symmetry (float): from 0 to 100
                frequency (float): waveform frequency
                amplitude (float): ramp amplitude
                offset (float): voltage offset

            Returns:
                str: expected output is "1\n" of "*OPC?" command
            """
            self._write('FUNCtion RAMP')
            self.outer.function = 'ramp'

            if symmetry is not None:
                if symmetry>=0 and symmetry<= 100:
                    self._write('FUNCtion:RAMP:SYMMetry {:.3f}'.format(symmetry))
                else:
                    raise Exception("Symmetry value is out of bounds. It should be in the interval [0,100].")

            if frequency is not None: 
                self._write('FREQ {:.3f}'.format(frequency))
                self.outer.frequency = frequency

            if amplitude is not None: 
                self._write('VOLTage {:.3f}'.format(amplitude))

            if offset is not None: 
                self._write('VOLTage:OFFSet {:.3f}'.format(offset))

            return self._opc()

        def sine(self, frequency = None, volt_high = None, volt_low = None, phase = None):
            """defines sinusoidal wave as output function
            Args:
                frequency (float): WAVEFORM FREQUENCY
                volt_high (float): maximum voltage
                volt_low (float): minimum voltage
                phase (float): phase in degrees

            Returns:
                str: expected output is "1" of "*OPC?" command
            """

            self._write("FUNCtion SIN")
            self.outer.function = 'sin'

            if frequency is not None:
                self._write('FREQ {:.3f}'.format(frequency))
                self.outer.frequency = frequency

            if volt_high is not None:  
                self._write("VOLTage:HIGH {:.3f}".format(volt_high))

            if volt_low is not None:  
                self._write("VOLTage:LOW {:.3f}".format(volt_low))

            if phase is not None:  
                self._write("PHASe {:.3f}".format(phase))

            return self._opc()



        
# %%
if __name__=='__main__':
    import time

    sigen = Sigen(_sigen_id)
    sigen.waveforms.ramp(symmetry=75, frequency=3.5, amplitude=2, offset=0)
    sigen.output.on()

    time.sleep(5)
    sigen.output.off()


     
     
# %%
