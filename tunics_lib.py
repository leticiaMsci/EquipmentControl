# %%
"""
Author: Leticia Magalhaes
Date: Sep 2021
Email: leticiamagalhaes5@gmail.com
"""

import socket
import time

#definitions
ip = 'yetula.ifi.unicamp.br'
wavelength_mode = 'BASIC' #Options: 'HWA' (High Wavelength Accuracy mode), 'MHF' (Mode Hop Free mode), and 'BASIC'
sweep_mode = 'CONTinuous' #Options: STEPped (step-by-step scanning of the wavelength range), 'CONTinuous' (continuous scanning of the wavelength range)
sweep_repeat_mode = 'ONEWay' #Options: 'ONEWay' (One Way repeat mode), 'TWOWay' (Two Way repeat mode)
sweep_max_cycles = 5 #Maximum number of cycles for wavelength sweep


class T100R:
    """ Instrument control of Tunics T100R - Tunable Laser
    Created on Tue Aug 24 21 18:00:31
    @author: Leticia Magalhaes
    """
    
    def __init__(self, ip = ip, wavelength_mode = wavelength_mode, print_bool = True):
        
        #setting parameters:
        self.sweep_mode = sweep_mode
        self.sweep_repeat_mode = sweep_repeat_mode
        self.sweep_max_cycles = sweep_max_cycles
        self.wavelength_mode = wavelength_mode
        self.ip_addr = ip
        self.print_bool = print_bool


        #instantiating inner classes
        self.power = self.Power(self)
        self.wavelength = self.Wavelength(self)
        self.sweep = self.Sweep(self)
  
        #Setting wavelength mode
    
    def connect(self):
        #print('Initializing Tunics', end="")
        #opening connection
        try:
            self.tunics =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except OSError as msg:
            self.tunics = None
            raise Exception('Tunics T100R: Could not open socket.')

        self.tunics.connect((self.ip_addr, 50000))
        try:
            self.tunics.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            print('Tunics T100R:Error setting socket options')
            
        self.query('SOURce:WAVelength:MODE '+ wavelength_mode)
        print("Tunics connected. IDN: ", self.query("*IDN?"))
        

    def read(self, input_buffer = 2**33):
        '''
        Tunics read
        '''
        idn = self.tunics.recv(input_buffer)
        return idn.decode('ascii')

    def send(self, msg):
        """ Sends command to tunics.
        Args:
            msg (str): any command defined in the manual.
        """
        try:
            self.tunics.send(msg.encode('ascii'))
        except:
            raise Exception('TUNICS: Error sending msg.')


    def query(self, msg, input_buffer = 2**33):
        """ Queries tunics: send a message and reads the output.
        Args:
            msg (str): Any of the commands defined in the manual
            input_buffer (int, optional):  Defaults to 2**33.
        Returns:
            [type]: [description]
        """
        #self.send('*OPC?')
        #self.read(input_buffer=input_buffer)

        self.send(msg)
        return self.read(input_buffer=input_buffer)


    class Power():
        def __init__(self, outer):
            self.outer = outer

        def _query(self, msg):
            return self.outer.query(msg)

        def set_pow(self, pow_val, pow_unit = 'MW'):
            return self._query('SOURce:POWer {:.2f} '.format(pow_val)+pow_unit)

        def on(self, pow_val = None, pow_unit = 'MW', lbd = None, lbd_unit = 'NM'):
            """
            Enables power output.
            Args:
                power (float, optional): If define by user, will set the power output to this value.
                                            Defaults to None.
                power_unit (str, optional): Power unit (can be: 'W', 'MW', 'UW', 'NW', 'PW', 'DBM').
                                            Defaults to 'MW'.
                lbd (float, optional): Wavelength. If set by user, will change the wavelength to this
                                        value before enabling power output. Defaults to None.
                lbd_unit (str, optional): Wavelength unit (can be: 'M', 'NM'). Defaults to 'NM'.
            Returns:
                str: returns 'OK' if everything worked out.
            """
            if lbd is not None:
                self.outer.wavelength.set_lbd(lbd, lbd_unit=lbd_unit)
                print('Wavelength set to {:.2f} '.format(lbd)+lbd_unit)

            if pow_val is not None:
                #self._query('SOURce:POWer {:.2f} '.format(power)+power_unit)
                self.set_pow(pow_val, pow_unit)
                print('Power set to '+ str(pow_val)+pow_unit)

            if self._query('SOURce:POWer:STATe?') == '1':
                print('Power ON: Output Power Already Enabled')
                output = 'OK'
            else:
                output=self._query('SOURce:POWer:STATe ON')
                print('Power ON: ' + output)
                time.sleep(0.3)
            return output


        def off(self):
            if self._query('SOURce:POWer:STATe?') == '0':
                print('Power OFF: Output Power Already Disabled')
                output = 'OK'
            else:
                output=self._query('SOURce:POWer:STATe OFF')
                print('Power OFF: ' + output)
            return output

    class Wavelength:
        def __init__(self, outer):
            self.outer = outer

        def _query(self, msg):
            return self.outer.query(msg)

        def _send(self, msg):
            self.outer.send(msg)
        
        def set_lbd(self, lbd_nm, lbd_unit = 'NM'):
            output = self._query('SOURce:WAVelength {:.3f} '.format(lbd_nm) + lbd_unit)
            self._query("*OPC?")
            return output

        def set_step(self, step, step_unit = "NM"):
            return self._query('SOURce:WAVelength:SWEep:STEP:WIDTh {:.3f} '.format(step) + step_unit)

        def step_next(self):
            self._query('SOURce:WAVelength:SWEep:STEP:NEXT')

        def step_prev(self):
            self._query('SOURce:WAVelength:SWEep:STEP:PREVious')

        def sense(self):
            return self._query('SOURce:WAVelength?')

        def search(self):
            lbd = 0
            while True:
                input_ = input("Input tunics wavelength, or + for next step or - for previous. To stop type enter.")
                
                if input_ =='+':
                    self.step_next()
                    print("Step Forward")
                elif input_ =='-':
                    self.step_prev()
                    print("Step Backwards")
                else:              
                    try:
                        lbd = float(input_)
                        self.set_lbd(lbd)
                        print("Wavelength", input_)
                    except ValueError:
                        break        
            return self.sense()

    class Sweep:
        def __init__(self, outer):
            self.outer = outer

        def _query(self, msg):
            return self.outer.query(msg)

        def _send(self, msg):
            self.outer.send(msg)

        def _read(self):
            return self.outer.read()

        def config(self, lbd_nm_ini , lbd_nm_end, lbd_nms_speed, 
                lbd_unit = 'NM', lbd_speed_unit = 'NM/S',
                sweep_mode = None, sweep_repeat_mode = None, 
                sweep_max_cycles = None):
            '''
            '''
            #optional parameters
            if sweep_mode is None:
                self._query('SOURce:WAVelength:SWEep:MODE '+self.outer.sweep_mode)
            else:
                self._query('SOURce:WAVelength:SWEep:MODE '+sweep_mode)

            if sweep_repeat_mode is None:
                self._query('SOURce:WAVelength:SWEep:REPeat '+self.outer.sweep_repeat_mode)
            else:
                self._query('SOURce:WAVelength:SWEep:REPeat '+sweep_repeat_mode)

            if sweep_max_cycles is None:
                self._query('SOURce:WAVelength:SWEep:CYCLES '+ str(self.outer.sweep_max_cycles))
            else:
                self._query('SOURce:WAVelength:SWEep:CYCLES '+ str(sweep_max_cycles))
            
            #non-optional
            self._query("SOURce:WAVelength:SWEep:DWELl MIN")
            self._query('SOURce:WAVelength:SWEep:STARt {:.3f} '.format(lbd_nm_ini)+lbd_unit)
            self._query('SOURce:WAVelength:SWEep:STOP {:.3f} '.format(lbd_nm_end)+lbd_unit)
            self._query('SOURce:WAVelength:SWEep:SPEed {:.3f} '.format(lbd_nms_speed)+lbd_speed_unit)
            return self._query('*OPC?')

        def start(self):
            self._send('SOURce:WAVelength:SWEep:STATe?')
            is_sweeping = self._read()

            if is_sweeping =='+1':
                print('Wavelength Sweep Already Running')
                output = 'OK'
            else:
                self._send('SOURce:WAVelength:SWEep:STATe START')
                output = self._read()
                print('Wavelength Sweep Starting')
            return output

        def stop(self):
            self._send('SOURce:WAVelength:SWEep:STATe STOP')
            output =self._read()
            return output

        def is_running(self):
            self._send("SOURce:WAVelength:SWEep:STATe?")
            return int(self._read())
        
        def wait(self, max_time):
            time0 = time.time()
            while time.time()-time0<max_time:
                if self.is_running():
                    if self.outer.print_bool: print(".", end="")
                else:
                    if self.outer.print_bool: print("Sweep finished")
                    return 1
            print("sweep not finished")
            return 0

#%%

if __name__ == '__main__':
    print('main')
    tunics = T100R()
    tunics.connect()

    tunics.wavelength.set_lbd(1551)
    tunics.wavelength.set_step(0.003)
    tunics.power.on(pow_val=1)
    
    print(tunics.query('SOURce:WAVelength:SWEep:STEP:WIDTh?'))

    for ii in range(100):
        tunics.wavelength.step_next()

    #tunics.power.off()

 

    




# %%


# %%
