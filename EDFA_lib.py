#%%
import visa
import time
#import numpy as np

class KeopsysEDFA:
    def __init__(self, gpib_port):
        self.rm = visa.ResourceManager()
        self.instr_id = 'GPIB0::'+str(gpib_port)+'::INSTR'
        self.edfa = rm.open_resource(self.instr_id)
        self.edfa.read_termination = '\x00'
        
        idn = self.query("*IDN?")
        print("Keopsys EDFA connected. IDN:"+idn)

    def query(self, msg):
        return self.edfa.query(msg)

    def write(self, msg):
        self.edfa.write(msg)

    def read(self):
        return self.edfa.read()

    def pump_on(self, wait = True):
        self.write("K1")
        
        if wait:
            time.sleep(3)

    def pump_off(self):
        self.write("K0")

#%%
if __name__=='__main__':
    import time

    edfa = KeopsysEDFA(gpib_port=3)
    edfa.pump_on(wait=False)
    print("testing time to turn on")
    for ii in range(10):
        time.sleep(.5)
        print(ii)
    edfa.pump_off()


#%%
#rm = visa.ResourceManager()

#rm.list_resources()
#%%
#gpib_port = 3
#instr_id = 'GPIB0::'+str(gpib_port)+'::INSTR'
#edfa = rm.open_resource(instr_id)
#edfa.query("*IDN?") #works
#edfa.query("CPU?")
#edfa.write("K0")
#edfa.write("MD?")
#print(edfa.read())
#edfa.query("MD?") #works
#edfa.query_ascii_values("PUS?")
#edfa.write("PUS?")
#output = edfa.read_raw()
#print(output.decode('UTF-8'))
#edfa.query("PUE?")
#edfa.write("K1") #works
# %%
