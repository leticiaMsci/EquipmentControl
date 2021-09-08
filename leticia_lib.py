#%%
import time
import os

def time_stamp(precision_minute = True, precision_second = True):
    if not precision_minute:
        return time.strftime("%Y-%m-%d_%H")
    elif not precision_second:
        return time.strftime("%Y-%m-%d-%H-%M")
    else:
        return time.strftime("%Y-%m-%d-%H-%M-%S")

def folder(my_folder):
    if not os.path.exists(my_folder):
        os.makedirs(my_folder)



def scope_avg(scope, channels):    
    scope.measurement.initiate()    
    time.sleep(scope.acquisition.time_per_record)
    vmean = []
    for channel in channels:
        vmean.append(scope.channels[channel].measurement.fetch_waveform_measurement("voltage_average"))
    return vmean




if __name__=='__main__':
    print(time_stamp())
# %%

# %%
