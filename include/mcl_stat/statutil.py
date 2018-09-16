import mcl_stat.util as ut
import numpy as np
from math import sqrt
from collections import OrderedDict as od
def sqrt0(value):
  if value<=0:
    return 0.0
  else:
    return sqrt(value)

def cloudstat(clouddict_list):
  longest  = (0,len(clouddict_list[0]))
  longest  = (0,len(clouddict_list[0]['timestamp']))
  shortest = (0,len(clouddict_list[0]))
  shortest = (0,len(clouddict_list[0]['timestamp']))
  for i, each in enumerate(clouddict_list):
    length = len(each['timestamp'])
    if longest[1] < length: longest = (i, length)
    if shortest[1] > length: shortest = (i,length)
  rows = len(clouddict_list)
  cols = len(clouddict_list[shortest[0]]['timestamp'])
  cloudstat = {}
  cloudstat['timestamp']=[] 
  cloudstat['total_number']=[] 
  cloudstat['all_dd']=[] 
  cloudstat['all_da']=[]
  for idx_col, timestamp in enumerate(clouddict_list[shortest[0]]['timestamp']):
    #cloudstat[timestamp] = []
    cloudstat['timestamp'].append(timestamp)
    total_number_list = []
    all_dd_list = []
    all_da_list = []
    for idx_row, clouddict in enumerate(clouddict_list):
      time_idx = idx_col
      if len(clouddict['timestamp']) != shortest[1]:
        time_idx = ut.takeClosestIdx(clouddict['timestamp'], timestamp)
      total_number_list.append(clouddict['total_number'][time_idx])
      all_dd_list.append(clouddict['all_dd'][time_idx])
      all_da_list.append(clouddict['all_da'][time_idx])
    cloudstat['total_number'].append(total_number_list)
    cloudstat['all_dd'].append(all_dd_list)
    cloudstat['all_da'].append(all_da_list)
  return cloudstat

def errtimestat(errtime_list):
  longest = (0,len(errtime_list[0]))
  shortest = (0,len(errtime_list[0]))
  for i, each in enumerate(errtime_list):
    length = len(each)
    if longest[1] < length: longest = (i, length)
    if shortest[1] > length: shortest = (i,length)
  if shortest[1] == 0: print "longest:",longest, ", shortest: ", shortest
  #align all to the timeline of the shortest and produce a matrix
  rows = len(errtime_list)
  cols = len(errtime_list[shortest[0]])
  mat_error_time = np.arange(rows*cols,dtype=float).reshape(rows,cols)
  prev_time = None
  for time, err in errtime_list[shortest[0]].items():
    if prev_time is None:
      prev_time = time
    else:
      if prev_time >= time:
        raise Exception('errtime of {}-th bag is not time-ordered'.format(shortest[0]))
      prev_time = time
  for bag_idx, each in enumerate(errtime_list):
    if len(each) != shortest[0]:
      for time_idx, (time, not_used_err) in enumerate(errtime_list[shortest[0]].items()):
        closestkey = ut.takeClosest(each.keys(), time)
        mat_error_time[bag_idx, time_idx] = each[closestkey]
    else:
        mat_error_time[bag_idx, :] = np.array(each.values())
  #each column is a timestep
  #produce mean, std, minimum, maximum in a matrix
  errtime_mat = np.arange(6*cols,dtype=float).reshape(6,cols)
  for time_idx, (timestep, not_used_err) in enumerate(errtime_list[shortest[0]].items()):
    m = np.mean(mat_error_time[:,time_idx])
    ms = np.mean(np.square(mat_error_time[:,time_idx]))#mean square
    errtime_mat[:,time_idx] = np.array([timestep, m, np.std(mat_error_time[:,time_idx]), m-np.min(mat_error_time[:,time_idx]), np.max(mat_error_time[:,time_idx])-m, ms])
  return errtime_mat, mat_error_time

def align_errtime(errtime_list):
  """
  errtime list is a list of bag results. Each bag result is a dictionary with the format time:error  
  """
  longest = (0,len(errtime_list[0]))
  shortest = (0,len(errtime_list[0]))
  for i, each in enumerate(errtime_list):
    length = len(each)
    if longest[1] < length: longest = (i, length)
    if shortest[1] > length: shortest = (i,length)
  if shortest[1] == 0: print "longest:",longest, ", shortest: ", shortest
  #align all to the timeline of the shortest and produce a matrix
  rows = len(errtime_list)# rows is the number of bag resutls
  cols = len(errtime_list[shortest[0]]) # cols is the number of the shortest time steps
  mat = np.arange(rows*cols,dtype=float).reshape(rows,cols)
  prev_time = None
  for time, err in errtime_list[shortest[0]].items():
    if prev_time is None:
      prev_time = time
    else:
      if prev_time >= time:
        raise Exception('errtime of {} is not time-ordered'.format(idx_row))
      prev_time = time
  for idx_row, each in enumerate(errtime_list):
    if len(each) != shortest[0]:
      for idx_col, (time, err) in enumerate(errtime_list[shortest[0]].items()):
        closestkey = ut.takeClosest(each.keys(), time)
        mat[idx_row, idx_col] = each[closestkey]
    else:
        mat[idx_row, :] = np.array(each.values())
  #each column is a timestep
  #produce mean, std, minimum, maximum in a matrix
  return mat

def calculate_errtime_stat_from_errtime_mat(errtime_mat):
  errtime_stat = np.arange(6*errtime_mat.shape[1],dtype=float).reshape(6,errtime_mat.shape[1])
  for idx_col, (time, err) in enumerate(errtime_list[shortest[0]].items()):
    m = np.mean(errtime_mat[:,idx_col])
    ms = np.mean(np.square(errtime_mat[:,idx_col]))#mean square
    ###XXX timesteps, mean, std, min, max, mean square 
    errtime_stat[:,idx_col] = np.array([time, m, np.std(errtime_mat[:,idx_col]), m-np.min(errtime_mat[:,idx_col]), np.max(errtime_mat[:,idx_col])-m, ms])
  return errtime_stat

