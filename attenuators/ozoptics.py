# %%
import visa
import numpy as np

# todo: create '*WAI' commands to clear/wait for query kjdgbkjdhf

class DA100:
    """
    docstr
    """
    def __init__(self, resource_str, i_loss=None, att_value = None,
                read_str='\n', write_str='\r', query_delay=0.5, timeout=10):
        """
        # Delay in seconds
        # Timeout seconds
        """
        
        self.resource_str = resource_str
        self.rm=visa.ResourceManager()

        try:
            self.att =self.rm.open_resource(resource_str)
            self.set_terminations(read_str, write_str, query_delay, timeout)
        except:
            raise Exception('Could not open resource ('+resource_str+').')
            
        
        if i_loss is not None:
            self.set_insertion_loss(i_loss)
            self.i_loss = i_loss          

        if att_value is not None:
            self.set_att(att_value)

    def query(self, command):
        '''
        function NOT WORKING PROPERLY
        it seems to give a delayed output
        '''
        self.att.open()
        output = self.att.query(command)
        self.att.close()

        return output


    def set_att(self, val):
        """
        sets attenuation level by value 'val' in dB
        """
        self.att.open()
        try:
            self.att.write('A'+str(val))
            self.att.close()
        except:
            raise Exception('Error: Could not set attenuation.')
            self.att.close()
        


    def set_insertion_loss(self, i_loss):
        """
        sets insertion loss by level 'i_loss' in dB
        """
        self.att.open()
        try:
            self.att.write('L'+str(i_loss))
            self.att.close()
        except:
            raise Exception('Error: Could not set insertion loss.')
            self.att.close()


    def set_terminations(self, read_str='\n', write_str='\r', query_delay=0.5, timeout=10):
        try:
            self.att.read_termination, self.att.write_termination = read_str, write_str
            self.att.query_delay, self.att.timeout = query_delay, timeout
        except:
            raise Exception('Could not set terminations and/or query delay.')


# %%
if __name__=='__main__':
    print('main')
    att_in = DA100('ASRL5::INSTR', i_loss=1.12)
    att_in.set_att(37)

# %%
