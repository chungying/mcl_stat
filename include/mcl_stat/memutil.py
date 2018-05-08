import os
import psutil

def memory_usage():
    # return the memory usage in percentage like top
    process = psutil.Process(os.getpid())
    if 'get_memory_percent' in dir(process):
      mem = process.get_memory_percent()
      return mem
    if 'memory_percent' in dir(process):
      mem = process.memory_percent()
      return mem
    return -1.0#
    
    
