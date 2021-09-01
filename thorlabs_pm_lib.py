import visa

rm = visa.ResourceManager()
rm.list_resources()

def visa_object(resource_id):
    '''
    Simple visa connection 
    
    Parameters
    ----------
    resource_id: string
        Resource id obtained from  visa.ResourceManager().list_resources()
    write_term: string
        Read termination character
    read_term: string
        Write termination character
    '''
    att = rm.open_resource(resource_id)
    att.write_termination = '\r'
    att.read_termination = '\n'
    att.query_delay = 0.5 # delay in seconds
    att.timeout = 10 # timeout seconds
    print(att.query('*IDN?'))
    att.close() 
    return att

    #%%
string = 'USB0::0x1313::0x80B0::p3000966::0::INSTR'
thorlab = visa_object(string)
thorlab.open()

thorlab.query('MEAS:POW?')