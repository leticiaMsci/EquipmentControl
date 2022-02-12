#%%
import visa
import numpy as np
import time
import sys

ip = '143.106.72.137'

class _basic():
    def _write(self, msg):
        self.outer.write(msg)

    def _query(self, msg):
        return self.outer.query(msg)

class N9030A:
    def __init__(self, ip_addr = ip):
        self.rm = visa.ResourceManager()
        self.mode = ""
        self.operation = ""

        self.connect(ip=ip_addr)
        self.preset()
        self.sa = self.SA(self)
        self.rt = self.RTSA(self)
        self.gate = self.Gate(self)

        self.supported_modes = ["SA\n", "RTSA\n"]

    def connect(self, ip = ip):
        visa_id = "TCPIP::"+ip+"::INSTR"
        self.pxa = self.rm.open_resource(visa_id)

        print("Connecting PXA. IDN:", self.query("*IDN?"))

    def query(self, msg):
        return self.pxa.query(msg)

    def write(self, msg):
        self.pxa.write(msg)

    def preset(self):
        self.write(":SYSTem:PRESet")

    def peak_search(self):
        self.write(":CALCulate:MARKer:MAXimum")

    def trace(self):
        if self.query(":INSTrument?") in self.supported_modes:
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
    
    def max_hold(self, trace=1):
            self.write("TRAC"+str(trace)+":TYPE MAXH")

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

    def _flatten(self, a):
        return np.array([item for sublist in a for item in sublist])

    class SA (_basic):
        def __init__(self, outer):
            self.outer = outer

        def config(self):
            print("Configuring Spectrum Analyzer")
            self._write(":INSTrument SA")
            self.outer.mode  = "SA"

        def fspan(self, start_freq = None, stop_freq = None, freq_unit = "GHz",
                    bw = None, bw_unit = "KHZ"):
            if self._query(":INSTrument?")!="SA\n":
                self.config()

            if start_freq is not None:
                self._write(":FREQuency:STARt {:.6f} ".format(start_freq)+freq_unit)
            
            if stop_freq is not None:
                self._write(":FREQuency:STOP {:.6f} ".format(stop_freq)+freq_unit)

            if bw is not None:
                self._write("SENSe:BANDwidth:RESolution {:.6f} ".format(bw)+bw_unit)

        def max_hold(self, trace=1):
            self._write("TRAC"+str(trace)+":TYPE MAXH")

        def wait_hold(self, wait_time, config=True, ask=False, start_freq = None, stop_freq = None, freq_unit = "GHz",
                    bw = None, bw_unit = "KHZ", trace=1):
            if config:
                if self._query(":INSTrument?")!="SA\n":
                    print(self._query(":INSTrument?"))
                    self.config()

                self.outer.continuous()
                self.fspan(start_freq = start_freq, stop_freq = stop_freq, freq_unit = freq_unit,
                        bw = bw, bw_unit = bw_unit)
                self.max_hold(trace=trace)
            if ask:
                input_= input("PXA wait_hold: Proceed?")
            else:
                _countdown(wait_time)

            return self.outer.trace()


    class RTSA (_basic):
        def __init__(self, outer):
            self.outer = outer       
            self.step = None
        
        def config(self):
            self._write(":INSTrument RTSA")
            self.outer.mode  = "RTSA"

        def fcenter(self, freq, freq_unit = 'GHz'):
            self._write("FREQ:CENT {:.3f}".format(freq)+freq_unit)

        def fstep(self, step, step_unit = 'MHz'):
            if self.step != str(step) + step_unit:
                self._write("FREQ:CENT:STEP {:.3f}".format(step)+step_unit)
                self.step = str(step) + step_unit
                print("Step")

            self._write("FREQ:CENT UP")

        def stitching(self, freq_lst, acqtime, freq_unit='GHz', max_hold = True):
            
            if self._query(":INSTrument?")!="RTSA\n":
                self.config()

            self.outer.continuous()
            
            if max_hold: self._write(":TRAC:TYPE MAXH")

            xlist=[]
            ylist=[]
            for freq in freq_lst:
                self.fcenter(freq)
                time.sleep(acqtime)
                x,y = self.outer.trace()
                xlist.append(x)
                ylist.append(y)

            xflat =self.outer._flatten(xlist)
            yflat =  self.outer._flatten(ylist)
            idx = np.argsort(xflat)

            return xflat[idx], yflat[idx]
  
    class Gate (_basic):
        def __init__(self, outer):
            self.outer = outer
            

        def setup(self, gate_time, gate_delay = None, freq_unit = 'GHz'):
            "Setting up Gated Measurement"
            if self._query(":INSTrument?")!="SA\n":
                self.outer.sa.config()
            #self._write("FREQ:CENT {:.3f}".format(freq)+freq_unit)
            self._write(":SWEep:EGATe ON")
            self._write("SWEep:EGATe:VIEW ON")
            self._write("SWEep:EGATe:TIME " + str(gate_time))
            if gate_delay is not None:
                self._write("SWEep:EGATe:DELay " + str(gate_delay))

        def fspan(self, start_freq = None, stop_freq = None, freq_unit = "GHz",
                    bw = None, bw_unit = "KHZ"):
            if self._query(":INSTrument?")!="SA\n":
                self.config()

            if start_freq is not None:
                self._write(":FREQuency:STARt {:.6f} ".format(start_freq)+freq_unit)
            
            if stop_freq is not None:
                self._write(":FREQuency:STOP {:.6f} ".format(stop_freq)+freq_unit)

            if bw is not None:
                self._write("SENSe:BANDwidth:RESolution {:.6f} ".format(bw)+bw_unit)
        
        def span_meas(self):
            self._write("SWEep:EGATe:VIEW OFF")
            return self.outer.trace()

        def off(self):
            self._write(":SWEep:EGATe OFF")

        #Gate
        def search_delay(self, step=0.2):
            while True:
                input_ = input("Input gate delay in ms, or + for next step or - for previous. To stop type enter.")
                delay = 1e3*float(self._query("SWEep:EGATe:DELay?"))
                if input_ =='+':
                    self._write("SWEep:EGATe:DELay "+str(1e-3*(delay+step)))
                    print("Step Forward")
                elif input_ =='-':
                    self._write("SWEep:EGATe:DELay "+str(1e-3*(delay-step)))
                    print("Step Backwards")
                else:              
                    try:
                        delay = float(input_)
                        self._write("SWEep:EGATe:DELay "+str(1e-3*(delay)))
                        print("Delay", input_)
                    except ValueError:
                        break
            return 1e3*float(self._query("SWEep:EGATe:DELay?"))


# define the countdown func.
def _countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        print_ = 'Countdown timer: {:02d}:{:02d}'.format(mins, secs)
        sys.stdout.write('\r'+print_)
        sys.stdout.flush()
        
        time.sleep(1)
        t -= 1
    print_ = 'Countdown timer: {:02d}:{:02d}'.format(0, 0)
    sys.stdout.write('\r'+print_)
      
    print(' Ready!')

#%%
if __name__=='__main__':
    import numpy as np
    import matplotlib.pyplot as plt
    import time

    pxa = N9030A()

    pxa.gate.setup(13e-3, 1e-3)
    pxa.gate.fspan(9, 10)
    pxa.gate.search_delay()



    


# %%
