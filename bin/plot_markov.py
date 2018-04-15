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

######## for reading markov histogram ##########
#bagyaml = read_bag_yaml('/media/irlab/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
bagyaml = read_bag_yaml('/media/jolly/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
mapyaml = read_map_yaml(bagyaml['mapyaml'])
pgm_shape = read_pgm_shape(mapyaml['pgmfile'])
markov_dict = read_markov_bag(bagyaml['bagfile'])
markov_grid_shape = (pgm_shape[1], pgm_shape[0], markov_dict['size3D'])
#ares   size3D2ares(size3D)
#width  markov_grid_shape[1]
#height markov_grid_shape[0]
#origin_position mapyaml['origin']
#resolution mapyaml['resolution']
mmap = MclMap( mapyaml['origin'][0], mapyaml['origin'][1], mapyaml['resolution'], pgm_shape[0], pgm_shape[1])
print 'MclMap is',mmap

######## for reading target algorithm bag ########
#kldDict stores klds against time of each mcl bagfile 
kldDict={}#{timeIdcs, {bagIdcs, [kld, shrink kld, ...]} }
#mclbagfile = '/media/jolly/storejet/ex3/topleft/amcl_mp3000_ri1/amcl_mp3000_ri1_2018-02-04-11-55-01.bag'
#mclbagfile = '/media/irlab/storejet/ex3/topleft/amcl_mp3000_ri1/amcl_mp3000_ri1_2018-02-04-11-55-01.bag'
#mclbagfile = '/media/irlab/storejet/ex3/topleft/mcl_mp5000_ri1/mcl_mp5000_ri1_2018-02-03-23-08-27.bag'
mclbagfile = '/media/jolly/storejet/ex3/topleft/mcl_mp5000_ri1/mcl_mp5000_ri1_2018-02-03-23-08-27.bag'
cloud = od()
iu.readbag(mclbagfile, cloud=cloud)

#TODO argparse a list of bags of an algorithm
bagdir = ''# directory of bagfiles
#TODO parse argument
bagfiles = []#filenames of bagfiles from argument
scales=[(5,5,2),(10,10,4)]
bagkldDict={}#(bagIdx, (timeIdx, [kld, shrink kld...]))

maxQueueSize = 5
exitFlag = 0
threadNb = 3
threadNb = multiprocessing.cpu_count()-1
print 'number of threads is', threadNb
queueLock = threading.Lock()
queueSize = maxQueueSize - threadNb
workQueue = Queue.Queue(queueSize if queueSize > 1 else 1)
threads = []
dictLock = threading.Lock()

def BagsTask(timeIdx, histmsg):#global variables: markov_grid_shape, mmap, markov_dict, bagfiles
  ######## Reading markov ########
  #markovGrid = msgs2grid(markov_dict['indices'],histmsg,markov_grid_shape)
  markovGrid = msgs2grid2(mmap, markov_dict['positions'],histmsg,markov_grid_shape)

  bagsKLD = {}#create a dict for storing klds of bagfiles at this time stamp timeIdx
  for bagIdx, bagfile in enumerate(bagfiles):
    #read particle cloud to bagCloud
    bagCloud = od()
    iu.readbag(bagfile, cloud=bagCloud)
    #find the closest stamp to current
    cldIdx = ut.takeClosestIdx(bagCloud.keys(),histmsg.header.stamp)
    #create particle_grid for this bagCloud
    bagCloudGrid = cloudmsg2grid(bagCloud.values()[cldIdx], mmap, markov_grid_shape)
    bagsKLD[bagIdx] = []
    bagsKLD[bagIdx].append(kld(bagCloudGrid, markovGrid))#calculate kld() and store it into kldTuple

  return bagsKLD#return all of KLDs of bagfiles

def independentTask(idx, histmsg):#global variables: markov_grid_shape, mmap, markov_dict, cloud
  ######## Reading markov ########
  #print 'reading',idx,'-th histogram message...',
  #markov_grid = msgs2grid(markov_dict['indices'],histmsg,markov_grid_shape)
  markov_grid = msgs2grid2(mmap, markov_dict['positions'],histmsg,markov_grid_shape)

  #find the closest stamp to current
  cldidx = ut.takeClosestIdx(cloud.keys(),histmsg.header.stamp)
  #create particle_grid
  particle_grid = cloudmsg2grid(cloud.values()[cldidx], mmap, markov_grid_shape)

  shrink_scale = (5,5,2)
  shrink_markov = shrink_grid(markov_grid, shrink_scale)
  shrink_particle = shrink_grid(particle_grid, shrink_scale)

  #plot histograms of markov_grid and particle_grid
  #plotgrid4(markov_grid, particle_grid, saveFlag=True,showFlag=False,saveIdx=idx,suffix='hist')
  #suf = 'hist_shrunk_{}_{}_{}'.format(shrink_markov.shape[0],shrink_markov.shape[1],shrink_markov.shape[2])
  #plotgrid4(shrink_markov, shrink_particle, saveFlag=True,showFlag=False,saveIdx=idx,suffix=suf)

  #plot color heat map of markov_grid and particle_grid for each angle
  #plotgrid2(markov_grid, saveFlag=True,saveIdx=idx,suffix='markov')
  #plotgrid2(particle_grid, saveFlag=True,saveIdx=idx,suffix='particle')

  #plotgrid(shrink_particle,step=1,saveFlag=True,showFlag=False)

  k1 = kld(particle_grid, markov_grid)
  k2 = kld(shrink_particle, shrink_markov)

  KLDs = {}
  #there is only one mclbagfile so bagIdx is 0
  bagIdx = 0
  KLDs[bagIdx]=[]
  KLDs[bagIdx].append(k1)
  KLDs[bagIdx].append(k2)

  #klds = (idx, [])
  #klds[1].append(k1)
  #klds[1].append(k2)

  output=''
  #for val in klds[1]:
  for val in KLDs[bagIdx]:
    output+='{} '.format(val)
  print '%d-th task klds %s' % (cldidx, output)
  #return klds
  return KLDs

def process_data(threadIdx):
  while not exitFlag:
    queueLock.acquire()
    if not workQueue.empty():
      data = workQueue.get()
      queueLock.release()
      #KLDs is {badIdcs, [kld, shrink kld, ...]}
      KLDs = independentTask(data[0], data[1])
      dictLock.acquire()
      kldDict[data[0]] = KLDs#data[0] is timeIdx
      dictLock.release()
    else:
      queueLock.release()

class myThread (threading.Thread):
  def __init__(self, threadID):
    threading.Thread.__init__(self)
    self.threadID = threadID
  def run(self):
    process_data(self.threadID)

#start a thread pool
for tidx in range(threadNb):
  thread = myThread(tidx)
  print "Starting Thread %d" % (thread.threadID)
  thread.start()
  threads.append(thread)

# Fill the queue
numbered = enumerate(markov_dict['histograms_generator'])
for timeIdx, (topic, histmsg, t) in numbered:
  #if timeIdx < 14:
  #  print 'skipped',timeIdx
  #  continue
  if timeIdx > 4:
    print 'break',timeIdx
    break

  putFlag = False
  while not putFlag:
    if workQueue.full():
      time.sleep(1)
      continue
    else:
      queueLock.acquire()
      #print 'main thread is putting the %d-th task to workQueue' % (idx)
      workQueue.put((timeIdx, histmsg))
      putFlag = True
      queueLock.release()
      #print 'main thread releasing queueLock'
    #independentTask(timeIdx, histmsg)

# Wait for queue to empty
while not workQueue.empty():
  pass


# Notify threads it's time to exit
exitFlag = 1

# Wait for all threads to complete
for t in threads:
  t.join()
  print "Exiting Thread %d" % (t.threadID)

print 'finished reading markov grid with shape ', markov_grid_shape, '. then plotting...'

#plot kld against time of a bagfile
#require: kldDict, bagfile name
kldOd = od(sorted(kldDict.items(), key=lambda k: k[0]))#sort kldDict acoording to timeIdx
bagsKLDs = kldOd.values()[0]#get bagsKLDs of the first timeIdx 
KLDs = bagsKLDs.values()[0]#get KLDs of the first bagfile, dtype is array
lineNo = len(KLDs)
bagNo = len(bagsKLDs)
#plot a figure for each bag
res = np.ndarray((bagNo, 1+lineNo, len(kldOd)))
for idx, (timeIdx, bagsKLDs) in enumerate(kldOd.items()):
  for bagIdx, KLDs in bagsKLDs.items():
    res[bagIdx, 0 , idx] = timeIdx
    res[bagIdx, 1:, idx] = np.array(KLDs)

import matplotlib.pyplot as plt
for bagIdx in range(bagNo):
  fig = plt.figure(figsize=(18,10))
  fig.suptitle('kld of {}-th bag file'.format(bagIdx))
  for lineIdx in range(lineNo):
    plt.plot(res[bagIdx, 0, :], res[bagIdx, lineIdx+1, :])
  plt.show()
