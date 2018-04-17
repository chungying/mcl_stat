import os
import psutil

def memory_usage():
    # return the memory usage in percentage like top
    process = psutil.Process(os.getpid())
    mem = process.get_memory_percent()
    return mem
