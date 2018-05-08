#! /usr/bin/env python
"""
usage: batch_kld.py [-h] -b BAG_FILES [BAG_FILES ...]
                    [--output-dir OUTPUT_DIR] [--save-pkl] [--save-img]
                    [--show-img] [--read-hdd]
rosrun mcl_stat batch_kld.py -b /media/jolly/localdisk/ex3/topleft/mcl_mp5000_ri1/mcl_mp5000_ri1_2018-02-03-23-08-27.bag /media/jolly/localdisk/ex3/topleft/mcl_mp5000_ri1/mcl_mp5000_ri1_2018-02-03-23-07-05.bag /media/jolly/localdisk/ex3/topleft/mcl_mp5000_ri1/mcl_mp5000_ri1_2018-02-03-23-07-24.bag /media/jolly/localdisk/ex3/topleft/mcl_mp5000_ri1/mcl_mp5000_ri1_2018-02-03-23-07-44.bag --output-dir /media/jolly/localdisk/ex3/topleft/mcl_mp5000_ri1 --save-pkl --save-img --read-hdd
"""
import os
import mcl_stat.ioutil as iu
import mcl_stat.plotutil as pu
import mcl_stat.util as ut
from mcl_stat.util import ori2heading
from mcl_stat.markov_grid import *
from mcl_stat.mclmap import *
from collections import OrderedDict as od
import Queue
import threading
import time
import argparse

#NOTE prefixing globals with an underscope 
#NOTE function names to be like this this_is_a_function(...)
#NOTE variable names to be the same as function names
#NOTE constants with captital words separated by underscopes

######## for reading target algorithm bag ########
# directory of _bag_files
_bag_files_dir = '/media/jolly/Local Disk/ex3/topleft/mcl_mp5000_ri1'
#filenames of _bag_files from argument
_bag_files = ['mcl_mp5000_ri1_2018-02-03-23-08-27.bag','mcl_mp5000_ri1_2018-02-03-23-07-05.bag','mcl_mp5000_ri1_2018-02-03-23-07-24.bag','mcl_mp5000_ri1_2018-02-03-23-07-44.bag']
_parallel_flag = True

#_kld_dict stores klds at all timestamps of each mcl bagfile 
#{ rospy.Time, { bag_idx, [kld, shrink kld, ...] } }
_kld_dict={}

_thread_no_for_bag_files = 3 # the number of reading threads that each AdminThread can control
_markov_hist_msg_queue = None
_admin_threads = []
_markov_msg_queue_lock = threading.Lock()
_output_lock = threading.Lock()
_exit_flag = 0

#global variables that are created in functions
_markov_bag_dict = None
_mcl_map = None
_hdd_disk_flag = False

def calculate_kld_from_bag(bag_filename, hist_msg_stamp, mcl_map, markov_grid_hist_shape, markov_grid_hist):
  #find particle cloud message at the same time as histogram message
  particle_cloud_msg = find_particle_clud_msg(bag_filename, hist_msg_stamp)
  #transform the particles to a histomgram
  particle_cloud_grid_hist = cloudmsg2grid(particle_cloud_msg, mcl_map, markov_grid_hist_shape)
  #calculate kld value for this bag at the timestamp
  return kld(particle_cloud_grid_hist, markov_grid_hist)

def find_particle_clud_msg(filename, msg_stamp):
  #read particle cloud to particle_cloud_msgs
  particle_cloud_msgs = od()
  if _hdd_disk_flag:
    iu.read_bag_from_hdd(filename, cloud=particle_cloud_msgs, msg_start_time=msg_stamp, msg_end_time=msg_stamp)
  else:
    iu.readbag(filename, cloud=particle_cloud_msgs, msg_start_time=msg_stamp, msg_end_time=msg_stamp)
  #find the closest stamp to current
  if len(particle_cloud_msgs) == 0:
    msg_idx = 0
  elif len(particle_cloud_msgs) >= 1:
    msg_idx = ut.takeClosestIdx(particle_cloud_msgs.keys(),msg_stamp)
  elif len(particle_cloud_msgs) == 0:
    if _hdd_disk_flag:
      iu.read_bag_from_hdd(filename, cloud=particle_cloud_msgs, msg_start_time=msg_stamp, msg_end_time=msg_stamp)
    else:
      iu.readbag(filename, cloud=particle_cloud_msgs, msg_start_time=msg_stamp, msg_end_time=msg_stamp)
    msg_idx = ut.takeClosestIdx(particle_cloud_msgs.keys(),msg_stamp)
  return particle_cloud_msgs.values()[msg_idx]

def run_kld_task(thread_idx, exit_event, queue_lock, data_queue):
  #print 'Thread {} starts'.format(thread_idx)
  while exit_event.is_set() is not True:
    # acquire queue lock
    queue_lock.acquire()
    if data_queue.empty():
      queue_lock.release()
    else:
      # get element from the queue
      data = data_queue.get()
      queue_lock.release()
      #print 'Thread {} got data'.format(thread_idx)
      # calculate kld from bag
      #kld_value = calculate_kld_from_bag(bag_file, hist_msg_stamp, mcl_map, markov_grid_hist_shape, markov_grid_hist)
      kld_value = calculate_kld_from_bag(data[0], data[1], data[2], data[3], data[4])
      #save result to independent output array list
      data[5].append(kld_value)
  #print 'Thread {} exits'.format(thread_idx)

#global variables: _mcl_map, _markov_bag_dict['positions'], _bag_files
def run_admin_task(admin_thread_idx, time_idx, hist_msg):
  ######## Reading markov ########
  print 'Thread {} started {}-th task'.format(admin_thread_idx, time_idx)
  markov_grid_hist = msgs2grid2(_mcl_map, _markov_bag_dict['positions'], hist_msg, _markov_bag_dict['shape'])

  #create a dict for storing klds of _bag_files at this time stamp time_idx
  kld_of_all_bags_dict = {}
  if not _parallel_flag:
    for bag_idx, bag_file in enumerate(_bag_files):
      full_path = _bag_files_dir+'/'+bag_file
      kld_of_all_bags_dict[bag_idx] = []
      #without parallelization
      kld_value = calculate_kld_from_bag(full_path, hist_msg.header.stamp, _mcl_map, _markov_bag_dict['shape'], markov_grid_hist)
      #store the result to output
      kld_of_all_bags_dict[bag_idx].append(kld_value)

  if _parallel_flag:
    kld_threads = []
    exit_event = threading.Event()
    queue_lock = threading.Lock()
    data_queue = Queue.Queue()
    for i in range(_thread_no_for_bag_files):
      thread_idx = admin_thread_idx * 10 + i
      thread = threading.Thread(target=run_kld_task, args=(thread_idx, exit_event, queue_lock, data_queue))
      thread.start()
      kld_threads.append(thread)

    # fill data to data_queue
    for bag_idx, bag_file in enumerate(_bag_files):
      kld_of_all_bags_dict[bag_idx] = []
      full_path = _bag_files_dir+'/'+bag_file
      element_data=(full_path, 
                    hist_msg.header.stamp, 
                    _mcl_map, 
                    _markov_bag_dict['shape'], 
                    markov_grid_hist,
                    kld_of_all_bags_dict[bag_idx])
      queue_lock.acquire()
      data_queue.put(element_data)
      queue_lock.release()

    # wait queue to be empty
    while True:
      queue_lock.acquire()
      if data_queue.empty():
        queue_lock.release()
        # send exit event to threads
        exit_event.set()
        break
      else:
        queue_lock.release()
        #time.sleep(1)

    # wait threads to be joined
    for thread in kld_threads:
      thread.join()

  print 'Thread {} finished {}-th task'.format(admin_thread_idx, time_idx)
  
  #return all of kld values of _bag_files at this time_idx
  return kld_of_all_bags_dict

def process_data(thread_id):
  while not _exit_flag:
    _markov_msg_queue_lock.acquire()
    if not _markov_hist_msg_queue.empty():
      queue_data = _markov_hist_msg_queue.get()
      _markov_msg_queue_lock.release()
      #kld_of_all_bags = {badIdcs, [kld, shrink kld, ...]}
      kld_of_all_bags = run_admin_task(thread_id, queue_data[0], queue_data[1])
      _output_lock.acquire()
      #queue_data[0] is rospy.Time
      _kld_dict[queue_data[1].header.stamp] = kld_of_all_bags
      _output_lock.release()
    else:
      _markov_msg_queue_lock.release()

class AdminThread (threading.Thread):
  def __init__(self, thread_id):
    threading.Thread.__init__(self)
    self.thread_id = thread_id
  def run(self):
    print "Starting Thread %d" % (self.thread_id)
    process_data(self.thread_id)
    print "Exiting Thread %d" % (self.thread_id)

def main():
  ######## reading markov grid histogram bag file##########
  #TODO make this filename as an argument
  global _markov_bag_dict
  #_markov_bag_dict = read_markov_bag_from_yaml('/media/irlab/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
  #_markov_bag_dict = read_markov_bag_from_yaml('/media/jolly/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
  _markov_bag_dict = read_markov_bag_from_yaml('/home/jolly/ex3/topleft/markov/ex3-markov-72.yaml')

  ####### reading map information in the format of MCL map
  #origin_position _markov_bag_dict['origin']
  #width  _markov_bag_dict['shape'][1]
  #height _markov_bag_dict['shape'][0]
  #ares _markov_bag_dict['shape'][2]
  #resolution _markov_bag_dict['resolution']
  global _mcl_map
  _mcl_map = MclMap( _markov_bag_dict['origin'][0], _markov_bag_dict['origin'][1], _markov_bag_dict['resolution'], _markov_bag_dict['width'], _markov_bag_dict['height'] )
  print 'MclMap is',_mcl_map

  parser = argparse.ArgumentParser(description='Calculate KLD values of bag files against to markov grid histogram')
  parser.add_argument('-b','--bag-files', nargs='+', help='<Required> A list of bag files with relative path', required=True)
  parser.add_argument('--output-dir', help='<Optional> The folder for storing a pickle file of KLD statistics. The default is the folder of the last bag file.')
  parser.add_argument('--save-pkl', action='store_true', help='<Optional:False> Whether save KLD statistics into a pickle file')
  parser.add_argument('--save-img', action='store_true', help='<Optional:False> Whether save images of histogram figures')
  parser.add_argument('--show-img', action='store_true', help='<Optional:False> Whether showing figures when plotting histograms of Grid-based Markov Localization')
  parser.add_argument('--read-hdd', action='store_true', help='<Optional:False> Whether using a thread as proxy to read bag files in Hard Disk Drive.')
  parser.add_argument('-tnfmm', '--thread-no-for-kld', default=1, help='<Optional:1> the number of threads taking a markov msg for calculating KLD to all of bag files')
  parser.add_argument('-qsfmm', '--queue-size-for-markov-msgs', default=1, help='<Optional:1> the size of queue storing markov messages')
  parser.add_argument('-tnfbf', '--thread-no-for-bag-files', default=3, help='<Optional:3> the number of threads reading each bag file')
  args = parser.parse_args()

  # parse argument _bag_files and _bag_files_dir
  if args.bag_files is not None:
    dir_path = None
    bag_files = []
    for p in args.bag_files:
      abs_path = os.path.abspath(p)
      if not os.path.isfile(abs_path):
        raise RuntimeError('cannot fine {}'.format(abs_path))
      dir_path = os.path.dirname(abs_path)
      bag_files.append(os.path.basename(abs_path))
    global _bag_files
    del _bag_files[:]
    _bag_files.extend(bag_files)
    global _bag_files_dir
    _bag_files_dir = dir_path

  # kld_output_name is the prefix of a pickle file where kld values of all bags are saved
  # abs_output_dir is the location of the pickle file: either args.output_dir of command-line arguments or _bag_files_dir of _bag_files
  abs_output_dir = None
  if args.output_dir is None:
    abs_output_dir = _bag_files_dir
  else:
    abs_output_dir = os.path.abspath(args.output_dir)
  kld_output_name = os.path.basename(abs_output_dir)+'_kld'

  save_pkl_flag = args.save_pkl
  show_img_flag = args.show_img 
  save_img_flag = args.save_img 
  global _hdd_disk_flag
  _hdd_disk_flag = args.read_hdd

  thread_no_for_kld = args.thread_no_for_kld
  queue_size_for_markov_msgs = args.queue_size_for_markov_msgs
  global _thread_no_for_bag_files
  _thread_no_for_bag_files = args.thread_no_for_bag_files
  print 'thread_no_for_kld: {}\n_queue_size_for_markov_msgs: {}\n_thread_no_for_bag_files: {}'.format(thread_no_for_kld, queue_size_for_markov_msgs, _thread_no_for_bag_files)
  
  print _bag_files
  print _bag_files_dir
  print kld_output_name
  print abs_output_dir
  print save_pkl_flag
  print save_img_flag
  print show_img_flag
  print _hdd_disk_flag
  #return

  # create _admin_threads and start them
  for tidx in range(thread_no_for_kld):
    thread = AdminThread(tidx)
    thread.start()
    _admin_threads.append(thread)

  # Fill task to _markov_hist_msg_queue
  global _markov_hist_msg_queue
  _markov_hist_msg_queue = Queue.Queue(queue_size_for_markov_msgs)
  assert(_markov_hist_msg_queue.qsize() is queue_size_for_markov_msgs)
  numbered = enumerate(_markov_bag_dict['histograms_generator'])
  for time_idx, (topic, hist_msg, t) in numbered:
    #if time_idx < 14:
    #  print 'skipped',time_idx
    #  continue
    #if time_idx > 2:
    #  print 'break',time_idx
    #  break
    #print 'main thread has read a new hist_msg at {}'.format(hist_msg.header.stamp)
  
    put_flag = False
    while not put_flag:
      if _markov_hist_msg_queue.full():
        #print '_markov_hist_msg_queue is full, main thread sleep 1 second'
        time.sleep(1)
        continue
      else:
        #print 'main thread is waiting for acquiring _markov_msg_queue_lock'
        _markov_msg_queue_lock.acquire()
        #print 'main thread is putting the %d-th task to _markov_hist_msg_queue' % (time_idx)
        _markov_hist_msg_queue.put((time_idx, hist_msg))
        put_flag = True
        _markov_msg_queue_lock.release()
        #print 'main thread released _markov_msg_queue_lock'

  # Wait for queue to empty
  while not _markov_hist_msg_queue.empty():
    pass

  # Notify _admin_threads it's time to exit
  global _exit_flag
  _exit_flag = 1

  # Wait for all _admin_threads to complete
  for t in _admin_threads:
    t.join()

  print 'finished reading markov grid with shape ', _markov_bag_dict['shape'], '. then saving ...'

  ####### plot kld against time of a bagfile ######
  #require: _kld_dict, _bag_files, _bag_files_dir
  #sort _kld_dict in chronological order
  #_kld_dict = { rospy.Time, { bag_idx, [kld, shrink kld, ...] } }
  sorted_kld_dict = od(sorted(_kld_dict.items(), key=lambda k: k[0]))

  # the number of timestamps
  timestamp_number = len(sorted_kld_dict)
  # get the first time_idx
  first_time_idx = sorted_kld_dict.values()[0]
  # the number of bags at the first timestamp
  bag_number = len(first_time_idx)
  # get the first bag at the first timestamp
  first_bag_of_first_time_idx = first_time_idx.values()[0]
  # the number of kld settings for each bag
  kld_lines_number = len(first_bag_of_first_time_idx)

  # create timestamps and bag_lines for storing kld_values wrt time for saving these information in a pickle file later
  timestamps = np.zeros(timestamp_number)
  bag_lines = np.ndarray((bag_number, kld_lines_number, timestamp_number))
  for idx, (time_idx, kld_of_all_bags) in enumerate(sorted_kld_dict.items()):
    # save current timestamp in the term of seconds
    timestamps[idx] = sorted_kld_dict.keys()[idx].to_sec()
    # retrive kld_values for each bag at current timestamp time_idx
    for bag_idx, kld_values in kld_of_all_bags.items():
      bag_lines[bag_idx, :, idx] = np.array(kld_values)

  #TODO define a function in ioutil
  # because ioutil is in charge of pickle files input/output for this package
  if save_pkl_flag:
    import pickle
    with open('{}/{}.pkl'.format(abs_output_dir, kld_output_name),'w') as output:
      output_dict = {}
      output_dict['bag_files_dir'] = _bag_files_dir
      output_dict['bag_files'] = _bag_files 
      output_dict['timestamps'] = timestamps 
      output_dict['bag_lines'] = bag_lines 
      pickle.dump(output_dict, output)
  
  #input fig_name, timestamps, bag_lines[bag_idx,:,:]
  if show_img_flag or save_img_flag:
    for bag_idx in range(bag_number):
      fig_name = '{}'.format(_bag_files[bag_idx].split('.')[0])
      pu.plot_kld(bag_lines[bag_idx, :, :], name = fig_name, show_flag = show_img_flag, save_flag=save_img_flag, abs_output_dir=abs_output_dir)

if __name__ == '__main__':
  main()

#TODO an example for reading multiple kld_output_name
#import sys
#import os
#import pickle
#pkl_files = sys.argv[2:]
#pkl_names = map(lambda pkl_file: os.path.basename(pkl_file).split('.')[0], pkl_files)
#pkl_input = map(lambda pkl_file: open(pkl_file), pkl_files)
#dict_list = map(lambda input: pickle.load(input), pkl_input)
#import mcl_stat.plotutil as pu
#for i in range(5): pu.plot_same_mcl_errorbar(i, dict_list)
#for i in range(5): pu.plot_same_mp_errorbar(i, dict_list)
#
