import visa

class MN9625A:
    def __init__(self, gpib, read_str='\n'):
        self.resource_str = 'GPIB0::{}::INSTR'.format(gpib)
        self.rm=visa.ResourceManager()

        try:
            self.att =self.rm.open_resource(self.resource_str)
            self.att.read_termination = '\n'
        except:
            raise Exception('Could not open resource ('+self.resource_str+').')
            
    def set_att(self, att):
        self.att.write("ATT {}".format(att))

    def query_att(self):
        return self.att.query("ATT?")