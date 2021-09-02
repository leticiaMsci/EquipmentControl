#%%
import time
import os

def time_stamp():
    return time.strftime("%Y-%m-%d_%H-%M-%S")

def folder(my_folder):
    if not os.path.exists(my_folder):
        os.makedirs(my_folder)



#def scope_avg(scope, channel):    
#    scope.measurement.initiate()    
#    time.sleep(timebase)
#    vmean = scope.channels[channel].measurement.fetch_waveform_measurement("voltage_average")
#    return vmean


if __name__=='__main__':
    print(time_stamp())
# %%

# %%
