#%%
import visa
import numpy as np


ip = '143.106.72.137'


class N9030A:
    def __init__(self, ip_addr = ip):
        self.rm = visa.ResourceManager()
        self.mode = ""
        self.operation = ""

        self.connect(ip=ip_addr)
        self.sa = self.SA(self)
        self.rt = self.RTSA(self)

    def connect(self, ip = ip):
        visa_id = "TCPIP::"+ip+"::INSTR"
        self.pxa = self.rm.open_resource(visa_id)
        #self.pxa.read_termination = '\n'

        print("Connecting PXA. IDN:", self.query("*IDN?"))

    def query(self, msg):
        return self.pxa.query(msg)

    def write(self, msg):
        self.pxa.write(msg)

    def trace(self):
        if self.mode == "SA" or self.mode == "RTSA":
            self.write(':MMEM:STOR:TRAC:DATA TRACE1, "D:\\new.csv"')
            
            data = self.query(':MMEM:DATA?  "D:\\new.csv"')
            
            self.write(':MMEM:DEL? "D:\\new.csv"')

            num_data = data.split("\r\n")[89:]

            a=np.ones((len(num_data)-1, 2))
            for ii in range(len(num_data)-1):
                a[ii, :] = np.fromstring(num_data[ii], dtype=float, sep=",")

            return a[:, 0], a[:, 1]
        else:
            raise Exception("Measurement MODE is not supported. You should implement it.")

    def single(self):
        if self.operation != "single":
            self.write(":INITiate:CONTinuous 0")
            self.operation = "single"

        self.write("INIT")
        self.write("*WAI")

    def continuous(self):
        if self.operation != "continuous":
            self.write(":INITiate:CONTinuous 1")
            self.operation = "continuous"

        self.write("INIT")

    class SA:
        def __init__(self, outer):
            self.outer = outer
            if self.outer.mode !="SA":
                self.config()
                self.outer.mode  = "SA"
        
        def _write(self, msg):
            self.outer.write(msg)

        def _query(self, msg):
            self.outer.query(msg)

        def config(self):
            self._write(":INSTrument SA")

        def fspan(self, start_freq = None, stop_freq = None, freq_unit = "GHz",
                    bw = None, bw_unit = "KHZ"):
            if self.outer.mode !="SA":
                self._write(":INSTrument SA")
                self.outer.mode  = "SA"

            if start_freq is not None:
                self._write(":FREQuency:STARt {:.6f} ".format(start_freq)+freq_unit)
            
            if stop_freq is not None:
                self._write(":FREQuency:STOP {:.6f} ".format(stop_freq)+freq_unit)

            if bw is not None:
                self._write("SENSe:BANDwidth:RESolution {:.6f} ".format(bw)+bw_unit)

        def max_hold(self, trace=1):
            self._write("TRAC"+str(trace)+":TYPE MAXH")

    class RTSA:
        def __init__(self, outer):
            self.outer = outer
            if self.outer.mode !="RTSA":
                self.config()
                self.outer.mode  = "RTSA"

            self.step = None

        def _write(self, msg):
            self.outer.write(msg)
        
        def config(self):
            self._write(":INSTrument RTSA")

        def fcenter(self, freq, freq_unit = 'GHz'):
            self._write("FREQ:CENT {:.3f}".format(freq)+freq_unit)

        def fstep(self, step, step_unit = 'MHz'):
            if self.step != str(step) + step_unit:
                self._write("FREQ:CENT:STEP {:.3f}".format(step)+step_unit)
                self.step = str(step) + step_unit
                print("Step")

            self._write("FREQ:CENT UP")


        #def stitching(self, freq0, freqf, unit = 'GHz'):




        
    
#%%
if __name__=='__main__':
    import numpy as np
    import matplotlib.pyplot as plt
    import time

    pxa = N9030A()

    pxa.sa.fspan(bw=300)
    pxa.continuous()
    pxa.sa.fspan(start_freq=6, stop_freq=7)
    #pxa.rt.fcenter(6)
    #pxa.continuous()
    for ii in range(3):
        pxa.single()
        x,y = pxa.trace()
        plt.plot(x, y+5*ii)

        pxa.rt.fstep(100)

    plt.show()


    


# %%
