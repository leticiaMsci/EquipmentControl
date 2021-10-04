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
        self.spec_analyzer = self.SA(self)

    def connect(self, ip = ip):
        visa_id = "TCPIP::"+ip+"::INSTR"
        self.pxa = self.rm.open_resource(visa_id)

        print("Connecting PXA. IDN:", self.query("*IDN?"))

    def query(self, msg):
        return self.pxa.query(msg)

    def write(self, msg):
        self.pxa.write(msg)

    def trace(self):
        if self.mode == "SA" or self.mode == "RTSA":
            self.write(':MMEM:STOR:TRAC:DATA TRACE1, "D:\\buffer.csv"')
            data = self.query(':MMEM:DATA?  "D:\\buffer.csv"')
            self.write(':MMEM:DEL? "D:\\buffer.csv"')

            num_data = data.split("\r\n")[89:]

            a=np.ones((len(num_data)-1, 2))
            for ii in range(len(num_data)-1):
                a[ii, :] = np.fromstring(num_data[ii], dtype=float, sep=",")

            return a[:, 0], a[:, 1]
        else:
            raise Exception("Measurement MODE is not supported. You should implement it.")

    class SA:
        def __init__(self, outer):
            self.outer = outer
            if self.outer.mode !="SA":
                self._write(":INSTrument SA")
                self.outer.mode  = "SA"
        
        def _write(self, msg):
            self.outer.write(msg)

        def _query(self, msg):
            self.outer.query(msg)

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

        def single(self):
            if self.outer.operation != "single":
                self._write(":INITiate:CONTinuous 0")
                self.outer.operation = "single"

            self._write("INIT")
            self._write("*WAI")

        def continuous(self):
            if self.outer.operation != "continuous":
                self._write(":INITiate:CONTinuous 1")
                self.outer.operation = "continuous"

            self._write("INIT")
        

    class RTSA:
        def __init__(self, outer):
            self.outer = outer

        def _write(self, msg):
            self.outer.write(msg)

        def config(self):
            self._write("INST:SEL RTSA")
    


#%%
if __name__=='__main__':
    import numpy as np
    import matplotlib.pyplot as plt
    import time

    pxa = N9030A()

    pxa.spec_analyzer.fspan(bw=300)
    pxa.spec_analyzer.continuous()

    pxa.spec_analyzer.fspan(start_freq=6, stop_freq=7)

    for ii in range(2):
        t0 = time.time()
        pxa.spec_analyzer.single()
        x, y = pxa.trace()
        print("--------time:", time.time()-t0, "s--------")
        plt.plot(x,y+25*ii)
    plt.show()

# %%