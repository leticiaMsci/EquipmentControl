# -*- coding: utf-8 -*-
#%%

# author: Paulo Felipe Jarschel (feb 2018)
# modified by: Leticia Magalhaes (aug 2021)

import visa
import numpy as np
import struct
import matplotlib.pyplot as plt
import time

class AQ63XX:
    #definitions
    gpib = True
    eth = False
    usb = False
    gpibAddr = 13
    ip = "192.168.1.2"
    port = 10001
    user = ""
    passwd = ""
    visarm = None
    visaOK = False
    osa = None
    osaOK = False
    osaID = ""
    binary = False
    traceLength = 0
    trace = "tra"
    tracen = 0
    
    #main functions
    def __init__(self):
        try:
            self.visarm = visa.ResourceManager('@ni')
            self.visaOK = True
        except:
            print("Error creating VISA Resource Manager! Is the GPIB Card connected?")
            pass
        if not self.visaOK:
            try:
                self.visarm = visa.ResourceManager('@py')
                self.visaOK = True
            except:
                print("Error creating VISA Resource Manager! Is the GPIB Card connected?")
                pass
    
    def __del__(self):
        self.CloseOSA()
        return 0
    
    #OSA functions
    
    def ConnectOSA(self, isgpib = True, address = gpibAddr, iseth = False, ethip = "192.168.1.2", ethport = 10001, ipuser = "", ippass = ""):
        if self.visaOK:
            self.gpib = isgpib
            self.gpibAddr = address
            self.eth = iseth
            self.ip = ethip
            self.port = ethport
            self.user = ipuser
            self.passwd = ippass
            try:
                if self.gpib:
                    osaname = "GPIB0::" + str(self.gpibAddr) + "::INSTR"
                    print(osaname)
                    self.osa = self.visarm.open_resource(osaname)
                elif self.eth:
                    osaname = "TCPIP0::" + self.ip + "::" + str(self.port) + "::SOCKET"
                    self.osa = self.visarm.open_resource(osaname, read_termination="\r\n", timeout = 5000)
                    self.osa.query('open "' + self.user + '"')
                    self.osa.query(self.passwd)
                if "AQ" in self.osa.query("*IDN?"):
                    self.osaOK = True
                else:
                    print("Error opening OSA! Is it connected? A")
            except:
                print("Error opening OSA! Is it connected? B")
                pass
    
    def InitOSA(self, fullInit=True, binarymode=True, tracen=0, write=True):
        if self.osaOK:
            self.binary = binarymode
            self.tracen = tracen
            if self.binary:
                self.osa.write("format:data real,32")
            else:
                self.osa.write("format:data ascii")

            #if(fullInit):    
            #    self.osa.write("disp:trace:y1:spac 0")
            #    self.osa.write("calc:mark:auto on")
            #    self.osa.write("calc:mark:max:srl:auto")
                #self.osa.write("sens:aver:coun 1")

            self.osa.write(':INITiate:SMODe SINGle')
            self.osa.write(':CALibration:ZERO off')
            self.osa.write(':CALibration:ZERO once')
            time.sleep(10)
            #osa.write('*WAI')
            
            self.ChangeTrace(self.tracen, wr=write)
            self.traceLength = self.GetTraceLength()
            
    def CloseOSA(self):
        if self.osaOK:
            try:
                #self.StopSweep()
                self.osa.write("cal:zero 1")
                self.osaOK = False
                if self.eth:
                    self.osa.write("close")
                self.osa.close()
            except:
                pass
    
    def Reconnect(self):
        if self.osaOK:
            self.CloseOSA()
            self.ConnectOSA()
            self.InitOSA(self.gpib, self.gpibAddr, self.alias)
        
    def ContinuousSweep(self):
        if self.osaOK:
            self.osa.write("init:smod repeat")
            self.osa.write("init")

    def SingleSweep(self):
        if self.osaOK:
            self.osa.write("init:smod single")
            self.osa.write("init")
    
    def StopSweep(self):
        if self.osaOK:
            self.osa.write("abor")
    
    def GetStartWavelength(self):
        if self.osaOK:
            resp = self.osa.query("sens:wav:start?")
            startwavelength = float(resp)*1e9
            return startwavelength
        else:
            return 0
    
    def SetStartWavelength(self, wl):
        if self.osaOK:
            wl = wl*1e-9
            self.osa.write("sens:wav:start " + str(wl))
    
    def GetStopWavelength(self):
        if self.osaOK:
            resp = self.osa.query("sens:wav:stop?")
            stopwavelength = float(resp)*1e9
            return stopwavelength
        else:
            return 0
    
    def SetStopWavelength(self, wl):
        if self.osaOK:
            wl = wl*1e-9
            self.osa.write("sens:wav:stop " + str(wl))
    
    def GetCenterWavelength(self):
        if self.osaOK:
            resp = self.osa.query("sens:wav:center?")
            centerwavelength = float(resp)*1e9
            return centerwavelength
        else:
            return 0
    
    def SetCenterWavelength(self, wl):
        if self.osaOK:
            wl = wl*1e-9
            self.osa.write("sens:wav:center " + str(wl))
    
    def GetSpanWavelength(self):
        if self.osaOK:
            resp = self.osa.query("sens:wav:span?")
            spanwavelength = float(resp)*1e9
            return spanwavelength
        else:
            return 0
    
    def SetSpanWavelength(self, wl):
        if self.osaOK:
            wl = wl*1e-9
            self.osa.write("sens:wav:span " + str(wl))
    
    def GetResBW(self):
        if self.osaOK:
            resp = self.osa.query("sens:bwid:res?")
            rb = float(resp)*1e9
            return rb
        else:
            return 0
    
    def SetResBW(self, wl):
        if self.osaOK:
            wl = wl*1e-9
            self.osa.write("sens:bwid:res " + str(wl))
    
    def GetSensMode(self):
        if self.osaOK:
            resp = self.osa.query("sens:sens?")
            sensMode = int(resp)
            
            sens = ""
            if sensMode == 0:
                sens = "Norm/Hold"
                
            if sensMode == 1:
                sens = "Norm/Auto"
            
            if sensMode == 2:
                sens = "Mid"
            
            if sensMode == 3:
                sens = "High1"
            
            if sensMode == 4:
                sens = "High2"
            
            if sensMode == 5:
                sens = "High3"
            
            if sensMode == 6:
                sens = "Normal"
                
            return sens
        else:
            return "Error"
    
    def SetSensMode(self, sens):
        if self.osaOK:
            sensMode = 0
            if sens == "Norm/Hold":
                sensMode = 0
            
            if sens == "Norm/Auto":
                sensMode = 1
            
            if sens == "Mid":
                sensMode = 2
            
            if sens == "High1":
                sensMode = 3
            
            if sens == "High2":
                sensMode = 4
            
            if sens == "High3":
                sensMode = 5
            
            if sens == "Normal":
                sensMode = 6        
    
            self.osa.write("sens:sens " + str(sensMode))    
    
    def SetTraceLength(self, length):
        if self.osaOK:
            if length == 0:
                self.osa.write("sens:swe:points:auto on")        
            else:
                self.osa.write("sens:swe:points " + str(length))
            self.traceLength = length    
    
    def GetTraceLength(self):
        if self.osaOK:
            resp = self.osa.query("sens:swe:points?")
            resp = resp.strip(" ")
            length = int(float(resp))
            self.traceLength = length
            return length
        else:
            return 0
    
    def SetAvrg(self, avg):
        if self.osaOK:
            self.osa.write("sens:aver:coun " + str(avg))
    
    def GetAvrg(self):
        if self.osaOK:
            resp = self.osa.query("sens:aver:coun?")
            resp = resp.strip(" ")
            avrg = int(resp)
            return avrg
        else:
            return 0
    
    def AutoMeas(self):
        if self.osaOK:
            self.osa.write("init:smod auto")
            self.osa.write("init")
    
    def PeakCenter(self):
        if self.osaOK:
            self.osa.write("calc:mark:auto on")
            self.osa.write("calc:mark:scen")
    
    def GetData(self):
        data_x = []
        data_y = []
        if self.binary:
            data_x, data_y = self.GetBinTrace()
        else:
            data_x, data_y = self.GetASCIITrace()
        return data_x, data_y
    
    def GetBinTrace(self):
        print('Bin')
        if self.osaOK:
            data_y = self.osa.query_binary_values("trac:data:y? " + self.trace, 
                                            datatype='f', is_big_endian=False)
            data_x = self.osa.query_binary_values("trac:data:x? " + self.trace, 
                                            datatype='f', is_big_endian=False)
            return data_x, data_y
        else:
            return np.zeros(self.traceLength), np.zeros(self.traceLength)
    
    def GetASCIITrace(self):
        if self.osaOK:
            print('OSA ok')
            data_y = self.osa.query("trac:data:y? " + self.trace)
            stringlist_y = data_y.split(",")
            numlist_y = []

            data_x = self.osa.query("trac:data:x? " + self.trace)
            stringlist_x = data_x.split(",")
            numlist_x = []
            
            for i in range(0, len(stringlist_y)):
                numlist_x.append(float(stringlist_x[i]))
                numlist_y.append(float(stringlist_y[i]))
            return numlist_x, numlist_y
        else:
            arr = []
            for i in range(0,self.traceLength):
                arr[i] = "0"
            return arr, arr
    
    def ChangeTrace(self, tr, wr=True):
        if self.osaOK:
            self.tracen = tr
            if tr == 0:
                self.trace = "tra"
            elif tr == 1:
                self.trace = "trb"                
            elif tr == 2:
                self.trace = "trc"                
            elif tr == 3:
                self.trace = "trd"                
            elif tr == 4:
                self.trace = "tre"                
            elif tr == 5:
                self.trace = "trf"
            elif tr == 6:
                self.trace = "trg"
                
            self.osa.write("trac:stat:tra fix")
            self.osa.write("trac:stat:trb fix")
            self.osa.write("trac:stat:trc fix")
            self.osa.write("trac:stat:trd fix")
            self.osa.write("trac:stat:tre fix")
            self.osa.write("trac:stat:trf fix")
            self.osa.write("trac:stat:trg fix")
        
            self.osa.write("trac:stat:tra off")
            self.osa.write("trac:stat:trb off")
            self.osa.write("trac:stat:trc off")
            self.osa.write("trac:stat:trd off")
            self.osa.write("trac:stat:tre off")
            self.osa.write("trac:stat:trf off")
            self.osa.write("trac:stat:trg off")
        
            self.osa.write("trac:act " + self.trace)
            self.osa.write("trac:stat:" + self.trace + " on")
    
            if wr:
                self.osa.write("trac:attr:" + self.trace + " write")
    
    def EndedSweep(self):
        if self.osaOK:
            resp = self.osa.query(":stat:oper:cond?")
            ended = bool(int(resp) & (1 << 0))
            return ended
        else:
            return True
            
    def SweepRange(self, lbd_ini, lbd_end, resolution,
                    lbd_unit = 'NM', resolution_unit = 'PM'):
           
        self.osa.write(':SENSe:WAVelength:STARt '+'{:.3f} '.format(lbd_ini)+lbd_unit)
        self.osa.write(':SENSe:WAVelength:STOP '+'{:.3f} '.format(lbd_end)+lbd_unit)
        self.osa.write(':SENSe:BANDwidth:RESolution '+'{:.3f}'.format(resolution)+resolution_unit)
        self.osa.write(':TRACe:ACTive TRA')


    def binblock_raw(self, data_in):
        '''
        This function interprets bytes as packed by binary data.
        It is supposed to get the output of the Yokogawa AQ6370C Optical Spectrum Analyser and convert to floats (regard-less of the span).
        '''
        
        #Grab the beginning section of the image file, which will contain the header.
        Header = str(data_in[0:12])
        #print("Header is " + str(Header))
        
        #Find the start position of the IEEE header, which starts with a '#'.
        startpos = Header.find("#")
        #print("Start Position reported as " + str(startpos))
        
        #Check for problem with start position.
        if startpos < 0:
            raise IOError("No start of block found")
            
        #Find the number that follows '#' symbol.  This is the number of digits in the block length.
        Size_of_Length = int(Header[startpos+1])
        #print("Size of Length reported as " + str(Size_of_Length))
        
        ##Now that we know how many digits are in the size value, get the size of the image file.
        Image_Size = int(Header[startpos+2:startpos+2+Size_of_Length])
        #print("Number of bytes in image file are: " + str(Image_Size))
        
        # Get the length from the header
        offset = startpos+Size_of_Length
        
        # Extract the data out into a list.
        data_raw = data_in[offset:offset+Image_Size]
        float_len=4 #A Float takes 4 chars en this packed data
        data_len=int( len(data_raw)/float_len )
        #print('Number of points in data ', data_len)
        
        output_vec=np.zeros(data_len)
        for i in range(data_len):
            output_vec[i]=struct.unpack('<f', data_raw[float_len*i:float_len*(i+1)])[0]
        
        
        return(output_vec)

    def trace_data(self, axis = "Y"):
        """
        TODO: figure out why OSA starts zeroing in the middle of scan and how to prevent this
                => possibility: insert try/except
        """
        self.osa.open()
        self.osa.write(':TRACe:'+axis+'? TRA')
        data_raw = self.osa.read_raw()
        t=0
        while not self.EndedSweep() and t<10:
            print("Sweep did not end")
            time.sleep(1)
            t=t+1
        
        return self.binblock_raw(data_raw) #np.array([1e9*float(i) for i in xraw.decode().split(',')]), xraw


# %%
if __name__ == '__main__':
    osa = AQ63XX()
    osa.ConnectOSA()
    osa.InitOSA()
    osa.SetSpanWavelength(2)
    osa.SetCenterWavelength(1550)
    osa.SingleSweep()
    x = osa.trace_x()
    y = osa.trace_y()

    plt.plot(x,y)

    osa.osa.write('AUTO OFFSET OFF')
# %%
