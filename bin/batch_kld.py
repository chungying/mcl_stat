#! /usr/bin/env python
import mcl_stat.ioutil as iu
import mcl_stat.util as ut
from mcl_stat.util import ori2heading
from mcl_stat.markov_grid import *
from mcl_stat.mclmap import *
from collections import OrderedDict as od
import Queue
import threading
import time
import multiprocessing

#TODO prefixing globals with an underscope 
#TODO function names to be like this this_is_a_function(...)
#TODO variable names to be the same as function names
#TODO constants with captital words separated by underscopes

######## for reading target algorithm bag ########
#mclbagfile = '/media/jolly/Local Disk/ex3/topleft/mcl_mp5000_ri1/mcl_mp5000_ri1_2018-02-03-23-08-27.bag'
#TODO argparse a list of bags of an algorithm
_bag_files_dir = '/media/jolly/Local Disk/ex3/topleft/mcl_mp5000_ri1'# directory of _bag_files
#TODO parse argument
_bag_files = ['mcl_mp5000_ri1_2018-02-03-23-08-27.bag']#filenames of _bag_files from argument
_save_flag = False
_show_flag = True
_parallel_flag = False

#_kld_dict stores klds at all timestamps of each mcl bagfile 
#{timeIdcs, {bagIdcs, [kld, shrink kld, ...]} }
_kld_dict={}

MAX_MSG_SIZE = 3
ADMIN_THREAD_NO = 1
#ADMIN_THREAD_NO = multiprocessing.cpu_count()-1
QUEUE_SIZE = MAX_MSG_SIZE - ADMIN_THREAD_NO if MAX_MSG_SIZE - ADMIN_THREAD_NO > 1 else 1
READ_THREAD_NO = 3 # the number of reading threads that each AdminThread can control
print 'MAX_MSG_SIZE   :', MAX_MSG_SIZE   
print 'ADMIN_THREAD_NO:', ADMIN_THREAD_NO
print 'QUEUE_SIZE     :', QUEUE_SIZE     
print 'READ_THREAD_NO :', READ_THREAD_NO 
_admin_threads = []
_markov_msg_queue_lock = threading.Lock()
_markov_hist_msg_queue = Queue.Queue(QUEUE_SIZE)
_output_lock = threading.Lock()
_exit_flag = 0

#global variables that are created in functions
_markov_hist_msg_dict = None
_markov_grid_hist_shape = None
_mcl_map = None

def calculate_kld_from_bag(bag_filename, hist_msg_stamp, mcl_map, markov_grid_hist_shape, markov_grid_hist):
  print 'calculate_kld_from_bag'
  #find particle cloud message at the same time as histogram message
  particle_cloud_msg = find_particle_clud_msg(bag_filename, hist_msg_stamp)
  #transform the particles to a histomgram
  print 'cloudmsg2grid'
  particle_cloud_grid_hist = cloudmsg2grid(particle_cloud_msg, mcl_map, markov_grid_hist_shape)
  #calculate kld value for this bag at the timestamp
  print 'kld'
  return kld(particle_cloud_grid_hist, markov_grid_hist)

def find_particle_clud_msg(filename, msg_stamp):
  #read particle cloud to particle_cloud_msgs
  particle_cloud_msgs = od()
  iu.readbag(filename, cloud=particle_cloud_msgs, msg_start_time=msg_stamp, msg_end_time=msg_stamp)
  #find the closest stamp to current
  if len(particle_cloud_msgs) == 0:
    msg_idx = 0
  elif len(particle_cloud_msgs) >= 1:
    msg_idx = ut.takeClosestIdx(particle_cloud_msgs.keys(),msg_stamp)
  elif len(particle_cloud_msgs) == 0:
    iu.readbag(filename, cloud=particle_cloud_msgs)
    msg_idx = ut.takeClosestIdx(particle_cloud_msgs.keys(),msg_stamp)
  return particle_cloud_msgs.values()[msg_idx]

def run_kld_task(kld_list_of_bag, bag_file, hist_msg_stamp, mcl_map, markov_grid_hist_shape, markov_grid_hist):
  kld_value = calculate_kld_from_bag(bag_file, hist_msg_stamp, mcl_map, markov_grid_hist_shape, markov_grid_hist)
  #store the result to output
  kld_list_of_bag.append(kld_value)

#global variables: _markov_grid_hist_shape, _mcl_map, _markov_hist_msg_dict['positions'], _bag_files
def run_admin_task(time_idx, hist_msg):
  ######## Reading markov ########
  print 'run_admin_task'
  markov_grid_hist = msgs2grid2(_mcl_map, _markov_hist_msg_dict['positions'], hist_msg, _markov_grid_hist_shape)

  #create a dict for storing klds of _bag_files at this time stamp time_idx
  kld_of_all_bags_dict = {}
  if not _parallel_flag:
    print 'not parallel'
    for bag_idx, bag_file in enumerate(_bag_files):
      full_path = _bag_files_dir+'/'+bag_file
      kld_of_all_bags_dict[bag_idx] = []
      #without parallelization
      kld_value = calculate_kld_from_bag(full_path, hist_msg.header.stamp, _mcl_map, _markov_grid_hist_shape, markov_grid_hist)
      #store the result to output
      kld_of_all_bags_dict[bag_idx].append(kld_value)

  if _parallel_flag:
    print 'parallel'
    kld_threads = []
    for bag_idx, bag_file in enumerate(_bag_files):
      full_path = _bag_files_dir+'/'+bag_file
      thread = threading.Thread(
                  target=run_kld_task, 
                  args=(kld_of_all_bags_dict[bag_idx], 
                        full_path, 
                        hist_msg.header.stamp, 
                        _mcl_map, 
                        _markov_grid_hist_shape, 
                        markov_grid_hist))
      kld_threads.append(thread)
      thread.start()

    for thread in kld_threads:
      thread.join()
  print 'leave run_admin_task'

  return kld_of_all_bags_dict#return all of kld values of _bag_files at this time_idx

def process_data():
  while not _exit_flag:
    if not _markov_hist_msg_queue.empty():
      _markov_msg_queue_lock.acquire()
      queue_data = _markov_hist_msg_queue.get()
      _markov_msg_queue_lock.release()
      #kld_of_all_bags = {badIdcs, [kld, shrink kld, ...]}
      kld_of_all_bags = run_admin_task(queue_data[0], queue_data[1])
      _output_lock.acquire()
      print 'acquired _output_lock'
      #queue_data[0] is time_idx
      _kld_dict[queue_data[0]] = kld_of_all_bags
      _output_lock.release()
      print 'released _output_lock'

class AdminThread (threading.Thread):
  def __init__(self, thread_id):
    threading.Thread.__init__(self)
    self.thread_id = thread_id
  def run(self):
    print "Starting Thread %d" % (self.thread_id)
    process_data()
    print "Exiting Thread %d" % (self.thread_id)

def main():
  ######## reading markov grid histogram bag file##########
  #bagyaml = read_bag_yaml('/media/irlab/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
  #bagyaml = read_bag_yaml('/media/jolly/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
  bagyaml = read_bag_yaml('/home/jolly/ex3/topleft/markov/ex3-markov-72.yaml')
  mapyaml = read_map_yaml(bagyaml['mapyaml'])
  pgm_shape = read_pgm_shape(mapyaml['pgmfile'])
  global _markov_hist_msg_dict
  _markov_hist_msg_dict = read_markov_bag(bagyaml['bagfile'])
  global _markov_grid_hist_shape
  _markov_grid_hist_shape = (pgm_shape[1], pgm_shape[0], _markov_hist_msg_dict['size3D'])

  ####### reading map information in the format of MCL map
  #ares   size3D2ares(size3D)
  #width  _markov_grid_hist_shape[1]
  #height _markov_grid_hist_shape[0]
  #origin_position mapyaml['origin']
  #resolution mapyaml['resolution']
  global _mcl_map
  _mcl_map = MclMap( mapyaml['origin'][0], mapyaml['origin'][1], mapyaml['resolution'], pgm_shape[0], pgm_shape[1])
  print 'MclMap is',_mcl_map

  #TODO parse argument _bag_files

  #create _admin_threads and start them
  for tidx in range(ADMIN_THREAD_NO):
    thread = AdminThread(tidx)
    #print "Starting Thread %d" % (thread.thread_id)
    thread.start()
    _admin_threads.append(thread)

  # Fill task to _markov_hist_msg_queue
  numbered = enumerate(_markov_hist_msg_dict['histograms_generator'])
  for time_idx, (topic, hist_msg, t) in numbered:
    #if time_idx < 14:
    #  print 'skipped',time_idx
    #  continue
    if time_idx > 2:
      print 'break',time_idx
      break
  
    put_flag = False
    while not put_flag:
      if _markov_hist_msg_queue.full():
        print 'main thread sleep 1 sec'
        time.sleep(1)
        continue
      else:
        _markov_msg_queue_lock.acquire()
        print 'main thread is putting the %d-th task to _markov_hist_msg_queue' % (time_idx)
        _markov_hist_msg_queue.put((time_idx, hist_msg))
        put_flag = True
        _markov_msg_queue_lock.release()
        print 'main thread releasing _markov_msg_queue_lock'

  # Wait for queue to empty
  while not _markov_hist_msg_queue.empty():
    pass

  # Notify _admin_threads it's time to exit
  global _exit_flag
  _exit_flag = 1

  # Wait for all _admin_threads to complete
  for t in _admin_threads:
    t.join()
    print "Exiting Thread %d" % (t.thread_id)

  print 'finished reading markov grid with shape ', _markov_grid_hist_shape, '. then plotting...'

  #plot kld against time of a bagfile
  #require: _kld_dict, _bag_files, _bag_files_dir
  #_kld_dict = {timeIdcs, {bagIdcs, [kld, shrink kld, ...]} }
  sorted_kld_dict = od(sorted(_kld_dict.items(), key=lambda k: k[0]))#sort _kld_dict acoording to time_idx
  first_kld_of_all_bags = sorted_kld_dict.values()[0]#get kld_of_all_bags of the first time_idx 
  bag_number = len(first_kld_of_all_bags) # the number of bags at the first timestamp
  kld_lines_number = len(first_kld_of_all_bags.values()[0]) # the number of kld settings for each bag
  #TODO implement for loop
  #plot a figure for each bag
  res = np.ndarray((bag_number, 1+kld_lines_number, len(sorted_kld_dict)))
  for idx, (time_idx, kld_of_all_bags) in enumerate(sorted_kld_dict.items()):
    for bag_idx, kld_values in kld_of_all_bags.items():
      res[bag_idx, 0 , idx] = time_idx
      res[bag_idx, 1:, idx] = np.array(kld_values)
  #TODO save res as pkl files
  
  import matplotlib.pyplot as plt
  for bag_idx in range(bag_number):
    fig = plt.figure(figsize=(18,10))
    fig_name = '{}'.format(_bag_files[bag_idx].split('.')[0])
    fig.suptitle('kld of {}-th bag file'.format(bag_idx))
    for line_idx in range(kld_lines_number):
      plt.plot(res[bag_idx, 0, :], res[bag_idx, line_idx+1, :])
    if _save_flag:
      plt.savefig('{}.png'.format(fig_name))
    if _show_flag:
      plt.show()

if __name__ == '__main__':
  main()

