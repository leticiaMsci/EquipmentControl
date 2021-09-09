# %%

import socket
import time

class T100R:
    """ Instrument control of Tunics T100R - Tunable Laser

    Created on Tue Aug 24 21 18:00:31

    @author: Leticia Magalhaes
    """
    #definitions
    ip = 'yetula.ifi.unicamp.br'
    wavelength_mode = 'BASIC' #Options: 'HWA' (High Wavelength Accuracy mode), 'MHF' (Mode Hop Free mode), and 'BASIC'
    sweep_mode = 'CONTinuous' #Options: STEPped (step-by-step scanning of the wavelength range), 'CONTinuous' (continuous scanning of the wavelength range)
    sweep_repeat_mode = 'ONEWay' #Options: 'ONEWay' (One Way repeat mode), 'TWOWay' (Two Way repeat mode)
    sweep_max_cycles = 5 #Maximum number of cycles for wavelength sweep
    
    def __init__(self, ip = ip, wavelength_mode = wavelength_mode, print_bool = True):
        print('Initializing ' + ip, end="")
        self.ip_addr = ip
        self.print_bool = print_bool

        try:
            self.tunics =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(".",  end="")
        except OSError as msg:
            self.tunics = None
            raise Exception('Could not open socket.')

        self.tunics.connect((ip, 50000))
        print(".",  end="")
        try:
            self.tunics.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print(".",  end="")
        except:
            print('Error setting socket options')
        
        #Setting wavelength mode
        self.wavelength_mode = wavelength_mode
        self.query('SOURce:WAVelength:MODE '+ wavelength_mode)
        print("Tunics was successfully initialized.")

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
        self.send('*OPC?')
        self.read(input_buffer=input_buffer)

        self.send(msg)
        return self.read(input_buffer=input_buffer) 

    def power_on(self, power = None, power_unit = 'MW', lbd = None, lbd_unit = 'NM'):
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
            self.wavelength(lbd, lbd_unit=lbd_unit)
            print('Wavelength set to {:.2f} '.format(lbd)+lbd_unit)

        if power is not None:
            self.query('SOURce:POWer {:.2f} '.format(power)+power_unit)
            print('Power set to '+ str(power)+power_unit)

        if self.query('SOURce:POWer:STATe?') == '1':
            print('Power ON: Output Power Already Enabled')
            output = 'OK'
        else:
            output=self.query('SOURce:POWer:STATe ON')
            print('Power ON: ' + output)
            time.sleep(1)
        return output


    def power_off(self):
        if self.query('SOURce:POWer:STATe?') == '0':
            print('Power OFF: Output Power Already Disabled')
            output = 'OK'
        else:
            output=self.query('SOURce:POWer:STATe OFF')
            print('Power OFF: ' + output)
        return output



    def sweep_config(self, lbd_nm_ini , lbd_nm_end, lbd_nms_speed, 
            lbd_unit = 'NM', lbd_speed_unit = 'NM/S',
            sweep_mode = sweep_mode, sweep_repeat_mode = sweep_repeat_mode, 
            sweep_max_cycles = sweep_max_cycles):
        '''

        '''
        self.query("SOURce:WAVelength:SWEep:DWELl MIN")
        self.query('SOURce:WAVelength:SWEep:MODE '+sweep_mode)
        self.query('SOURce:WAVelength:SWEep:CYCLES '+ str(sweep_max_cycles))
        self.query('SOURce:WAVelength:SWEep:REPeat '+sweep_repeat_mode)
        self.query('SOURce:WAVelength:SWEep:STARt {:.3f} '.format(lbd_nm_ini)+lbd_unit)
        self.query('SOURce:WAVelength:SWEep:STOP {:.3f} '.format(lbd_nm_end)+lbd_unit)
        self.query('SOURce:WAVelength:SWEep:SPEed {:.3f} '.format(lbd_nms_speed)+lbd_speed_unit)
        return self.query('*OPC?')

    def sweep_start(self):
        self.send('SOURce:WAVelength:SWEep:STATe?')
        is_sweeping = self.read()
        if is_sweeping =='+1':
            print('Wavelength Sweep Already Running')
            output = 'OK'
        else:
            self.send('SOURce:WAVelength:SWEep:STATe START')
            output = self.read()
            print('Wavelength Sweep Starting')
        return output


    def sweep_stop(self):
        self.send('SOURce:WAVelength:SWEep:STATe STOP')
        output =self.read()
        return output

    def sweep_is_running(self):
        self.send("SOURce:WAVelength:SWEep:STATe?")
        return int(self.read())
    
    def sweep_wait(self, max_time):
        time0 = time.time()
        while time.time()-time0<max_time:
            if self.sweep_is_running():
                if self.print_bool: print(".", end="")
            else:
                if self.print_bool: print("Sweep finished")
                return 1
        print("sweep not finished")
        return 0

    def wavelength(self, lbd_nm, lbd_unit = 'NM', lbd_step = None, lbd_step_unit = 'NM'):
        if lbd_step is not None:
            self.query('SOURce:WAVelength:SWEep:STEP:WIDTh {:.3f} '.format(lbd_step) + lbd_step_unit)
        
        return self.query('SOURce:WAVelength {:.3f} '.format(lbd_nm) + lbd_unit)
        
    
    def wavelength_step(self):
        self.send('SOURce:WAVelength:SWEep:STEP:NEXT')

    def loop_search(self):
        lbd = 0
        while True:
            input_ = input("Input tunics wavelength. To stop type 'stop'.")
            try:
                lbd = float(input_)
                self.wavelength(lbd)
                print(lbd)
            except ValueError:
                break
            
        return lbd





if __name__ == '__main__':
    print('main')
    tunics = T100R()
    tunics.wavelength(1550)
    tunics.power_on(power=1)
    #tunics.wavelength_step(0.002)
    #print(tunics.query('SOURce:WAVelength:SWEep:STEP:WIDTh?'))

 

    




# %%
