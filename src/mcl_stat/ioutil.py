from collections import OrderedDict as od
import mcl_stat.memutil as mu
import pickle
import rosbag
from os import system as cmd
from threading import Lock
TRUTH='/p3dx/base_pose_ground_truth'
POSE='/mcl_pose'
CLOUD = '/particlecloud'

def ifsorted(od):
  #check time order
  if od is None: 
    return True
  prev_time = od.keys()[0]
  sortflag = True
  for t, msg in od.items():
    if prev_time > t:
      sortflag = False
      break
    prev_time = t
  return sortflag

_disk_lock = Lock()
#_data_buffer = { bagname, { truth_buf, guess_buf, cloud_buf } }
_data_buffer = {}
_buffer_lock = Lock()
def read_bag_from_hdd(bagname, truth=None, guess=None, cloud=None, msg_start_time=None, msg_end_time=None):
  #TODO check buffer for the bagname, truth, guess, and cloud between message's start and end timestamps
  #read-only part
  #if the condition is met
  global _data_buffer
  tmp_truth = None
  tmp_guess = None
  tmp_cloud = None
  if bagname in _data_buffer:
    #copy data from _data_buffer to truth, guess, cloud
    readbag_flag = False
    #truth
    if truth is not None and len(_data_buffer[bagname]['truth'])>0:
      for k,v in _data_buffer[bagname]['truth'].items():
        if k < msg_start_time:
          continue
        elif k > msg_end_time:
          continue
        truth[k] = v
    else:
      readbag_flag = True
      tmp_truth = od()

    #guess
    if guess is not None and len(_data_buffer[bagname]['guess'])>0:
      for k,v in _data_buffer[bagname]['guess'].items():
        if k < msg_start_time:
          continue
        elif k > msg_end_time:
          continue
        guess[k] = v
    else:
      readbag_flag = True
      tmp_guess = od()

    #cloud
    if cloud is not None and len(_data_buffer[bagname]['cloud'])>0:
      for k,v in _data_buffer[bagname]['cloud'].items():
        if k < msg_start_time:
          continue
        elif k > msg_end_time:
          continue
        cloud[k] = v
    else:
      readbag_flag = True
      tmp_cloud = od()

    #return
    if not readbag_flag:
      return 
  
  if truth is not None and tmp_truth is None:
    tmp_truth = od()
  if guess is not None and tmp_guess is None:
    tmp_guess = od()
  if cloud is not None and tmp_cloud is None:
    tmp_cloud = od()

  #the part avoiding HDD contention
  _disk_lock.acquire()
  readbag(bagname, tmp_truth, tmp_guess, tmp_cloud, msg_start_time=None, msg_end_time=None)
  _disk_lock.release()

  #if output has not been updated, update it
  if truth is not None and tmp_truth is not None and len(truth) == 0:
    for k,v in tmp_truth.items():
      if k < msg_start_time:
        continue
      elif k > msg_end_time:
        continue
      truth[k] = v

  #if output has not been updated, update it
  if guess is not None and tmp_guess is not None and len(guess) == 0:
    for k,v in tmp_guess.items():
      if k < msg_start_time:
        continue
      elif k > msg_end_time:
        continue
      guess[k] = v

  #if output has not been updated, update it
  if cloud is not None and tmp_cloud is not None and len(cloud) == 0:
    for k,v in tmp_cloud.items():
      if k < msg_start_time:
        continue
      elif k > msg_end_time:
        continue
      cloud[k] = v

  # check memory usage of current process in percentage
  # if there is space of system memory for storing those information put them into a buffer
  if mu.memory_usage() < 85.0:
    #TODO the part require write privilege
    _buffer_lock.acquire()

    if bagname not in _data_buffer:
      _data_buffer[bagname] = { 'truth':od(), 'guess':od(), 'cloud':od() }
      print '_buffer_lock is acquired and _data_buffer size is {}'.format(len(_data_buffer))

    if tmp_truth is not None and len(_data_buffer[bagname]['truth']) == 0:
      _data_buffer[bagname]['truth'].clear()
      _data_buffer[bagname]['truth'].update(tmp_truth)

    if tmp_guess is not None and len(_data_buffer[bagname]['guess']) == 0:
      _data_buffer[bagname]['guess'].clear()
      _data_buffer[bagname]['guess'].update(tmp_guess)

    if tmp_cloud is not None and len(_data_buffer[bagname]['cloud']) == 0:
      _data_buffer[bagname]['cloud'].clear()
      _data_buffer[bagname]['cloud'].update(tmp_cloud)

    _buffer_lock.release()


def readbag(bagname, truth=None, guess=None, cloud=None, msg_start_time=None, msg_end_time=None):
  bag = None
  msg = None
  if truth is None and guess is None and cloud is None:
    return

  try:
    #read rosbag
    bag = rosbag.Bag(bagname)
    try:
      if bag.get_message_count(TRUTH) == 0 or bag.get_message_count(POSE) == 0 or bag.get_message_count(CLOUD) == 0:
        print "The file is incomplete. Please check if the rosbag file contains", CLOUD, ',',  POSE, "and ", TRUTH, " topics."
        print "Please type:"
        print "rosbag info ", bagname, '| grep "mcl_pose\|base_pose\|cloud"'
        return False

      #extract TRUTH, POSE, and CLOUD topics
      tpcs = [TRUTH, POSE]
      if cloud is not None: tpcs.append(CLOUD)
      for topic, msg, t in bag.read_messages(topics=tpcs):
        if msg_start_time and msg.header.stamp < msg_start_time: 
          continue 
        if msg_end_time and msg.header.stamp > msg_end_time: 
          continue
        if truth is not None and topic == TRUTH: 
          truth[msg.header.stamp] = msg
        elif guess is not None and topic == POSE: 
          guess[msg.header.stamp] = msg
        elif cloud is not None and topic == CLOUD:
          cloud[msg.header.stamp] = msg
    finally:
      bag.close()
  except rosbag.ROSBagException:
    print "Cannot open ", bagname
    return False
  except rosbag.ROSBagFormatException:
    print bagname, " is corrupted."
    return False
  if truth is not None and len(truth) == 0:
    print "cannot read", TRUTH
    return False
  if guess is not None and len(guess) == 0:
    print "cannot read", POSE
    return False
  if cloud is not None and len(cloud) == 0:
    print "cannot read", CLOUD
    return False

  return True

def ifexist(filename):
  return cmd('test -e {}'.format(filename)) == 0

def cloud2pkl(filename, l):
  #check if filename exist
  finalname = filename
  count = 0
  while ifexist(finalname):
    count += 1
    finalname = filename.replace('.pkl', '_{}.pkl'.format(count))
  #TODO save l to finalname
  with open(finalname, 'w') as out:
    pickle.dump(l, out)
  return True

def readcloudpkl(filename):
  return None

def data2pkl(filename, d):
  if 'mclpkg' not in d:
    print 'without mclpkg key'
    return False
  if 'mp' not in d:
    print 'without mp key'
    return False
  if 'ri' not in d:
    print 'without ri key'
    return False
  if d['mclpkg'].find('amcl') >= 0:
    print 'it is amcl'
  elif d['mclpkg'].find('mixmcl') >= 0:
    print 'it is mixmcl'
    if 'ita' not in d:
      print 'without ita for mixmcl'
      return False
  elif d['mclpkg'].find('mcmcl') >= 0:
    print 'it is mcmcl'
    if 'ita' not in d:
      print 'without ita for mcmcl'
      return False
    if 'gamma' not in d:
      print 'without gamma for mcmcl'
      return False
  if 'folder' not in d:
    print 'without folder name'
    return False
  if 'list_final_ed' not in d:
    print 'without final error distance list'
    return False
  if 'list_final_ea' not in d:
    print 'without final error heading list'
    return False
  #if d has list_cloudstat, separately save
  if 'list_cloudstat' in d:
    cloudstat_list = d.pop('list_cloudstat',None)
    cloud2pkl(filename.replace('.pkl','_cloudstat.pkl'), cloudstat_list)
  with open(filename, 'w') as out:
    print 'saving data to', filename
    pickle.dump(d, out)
  return True

# convert meta information to a string which is used as key of dict
def obj2key(obj):
  key = '{0}_mp{1}_ri{2}'.format(obj['mclpkg'], obj['mp'], obj['ri'])
  if 'ita' in obj: 
    key += '_ita{0}'.format(obj['ita'])
  if 'gamma' in obj:
    key += '_gamma{0}'.format(obj['gamma'])
  if 'map' in obj:
    key += '_{}'.format(obj['map'])
  return key

# read mcl statistics from each pickle file of args
def readpkl(args):
  dims = {'mclpkg': {}, 'mp': {}, 'ri': {}, 'ita': {}, 'gamma': {}}
  objs = {}
  for each in args:
    with open(each, 'r') as pkl:
      try:
        obj = pickle.load(pkl)
        if obj['mclpkg'] not in dims['mclpkg']:
          dims['mclpkg'][obj['mclpkg']] = 1
        else:
          dims['mclpkg'][obj['mclpkg']] += 1

        k = 'mp{}'.format(obj['mp'])
        if obj['mp'] not in dims['mp']:
          dims['mp'][k] = 1
        else:
          dims['mp'][k] += 1

        k = 'ri{}'.format(obj['ri'])
        if obj['ri'] not in dims['ri']:
          dims['ri'][k] = 1
        else:
          dims['ri'][k] += 1
        
        #key = '{0}_mp{1}_ri{2}'.format(obj['mclpkg'], obj['mp'], obj['ri'])
        if 'ita' in obj: 
          #key += '_ita{0}'.format(obj['ita'])
          k = 'ita{}'.format(obj['ita'])
          if obj['ita'] not in dims['ita']:
            dims['ita'][k] = 1
          else:
            dims['ita'][k] += 1

        if 'gamma' in obj: 
          #key += '_gamma{0}'.format(obj['gamma'])
          k = 'gamma{}'.format(obj['gamma'])
          if obj['gamma'] not in dims['gamma']:
            dims['gamma'][k] = 1
          else:
            dims['gamma'][k] += 1

        if 'map' in obj:
          #key += '_{}'.format(obj['map'])
          if 'map' not in dims:
            dims['map'] = {}

          if obj['map'] not in dims['map']:
            dims['map'][obj['map']] = 1
          else:
            dims['map'][obj['map']] += 1
        #if obj has list_cloudstat, dump it
        if 'list_cloudstat' in obj:
          obj.pop('list_cloudstat',None)
        key = obj2key(obj)
        objs[key] = obj
      except EOFError:
        print 'cannot read file', each
  objs = od(sorted(objs.items(), key=lambda t: (t[1]['mclpkg'], t[1]['mp'], t[1]['ri'])))
  return (dims, objs)
