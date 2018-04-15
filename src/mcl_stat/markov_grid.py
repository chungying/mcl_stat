import numpy as np
import os
import yaml
import matplotlib.pyplot as plt
print 'plt.rcParams agg.path.chunksize  is',plt.rcParams['agg.path.chunksize']
plt.rcParams['agg.path.chunksize'] = 20000
print 'plt.rcParams agg.path.chunksize  is',plt.rcParams['agg.path.chunksize']
from mpl_toolkits.mplot3d import Axes3D
from rosbag import Bag
from math import pi,floor,log
from sys import float_info
from mcl_stat.mclmap.maputil import *
from mcl_stat.util import ori2heading

markov_topics = ['/indices','/positions','/histograms']

def shrink_grid(grid,shrink_scales):
  shape = (grid.shape[0]/shrink_scales[0], grid.shape[1]/shrink_scales[1], grid.shape[2]/shrink_scales[2])
  shrink = np.zeros(shape)
  for a in xrange(shape[0]): 
    for b in xrange(shape[1]): 
      for c in xrange(shape[2]): 
        shrink[a,b,c] = np.sum(grid[a*shrink_scales[0]:(a+1)*shrink_scales[0], b*shrink_scales[1]:(b+1)*shrink_scales[1], c*shrink_scales[2]:(c+1)*shrink_scales[2]])
  return shrink

def kld(p1,p2):
  return np.sum(np.multiply(p1,np.log(p1+float_info.epsilon)-np.log(p2+float_info.epsilon)))

def kld2(p1,p2):
  kld = 0.0
  for a in xrange(p1.shape[0]):
    for b in xrange(p1.shape[1]):
      for c in xrange(p1.shape[2]):
        if p1[a,b,c] == 0.0:
          w = 0.0
        else:
          w = p1[a,b,c]*(log(p1[a,b,c]+float_info.epsilon)-log(p2[a,b,c]+float_info.epsilon))
        kld += w
  return kld

def read_bag_yaml(filename = '/home/jolly/ex4/topleft/markov/ex4-bag.yaml'):
  dirname = os.path.dirname(filename)
  yamldict = None
  with open(filename,'r') as bagyaml:
    yamldict = yaml.load(bagyaml)
  assert 'mapyaml' in yamldict
  mapfile = '/'.join([dirname, yamldict['mapyaml']])
  if os.path.isfile(mapfile):
    yamldict['mapyaml'] = mapfile
  else:
    raise ValueError('could not find map file(%s) in file system.' % (mapfile))
  assert 'bagfile' in yamldict
  bagfile = '/'.join([dirname, yamldict['bagfile']])
  if os.path.isfile(bagfile):
    yamldict['bagfile'] = bagfile
  else:
    raise ValueError('could not find bag file(%s) in file system.' % (bagfile))
  return yamldict

def read_markov_bag(filename = '/home/jolly/ex4/topleft/markov/markov_mp2000_ri1_2018-03-05-15-07-59.bag'):
  #with Bag(filename,'r') as mkbag:
    mkbag = Bag(filename,'r') 
    _,idcs,_ = mkbag.read_messages(topics=markov_topics[0]).next()
    _,poss,_ = mkbag.read_messages(topics=markov_topics[1]).next()
    _,msg,t  = mkbag.read_messages(topics=markov_topics[2]).next()
    #hist = [msg]
    hist_itr = mkbag.read_messages(topics=markov_topics[2])
    hist_count = mkbag.get_message_count(topic_filters=markov_topics[2])
    #mkbag.close()
    #size3D = hist[0].array.layout.dim[1].stride
    size3D = msg.array.layout.dim[1].stride
    markovdict = {}
    markovdict['indices'] = idcs
    markovdict['positions'] = poss
    #markovdict['histograms'] = hist
    markovdict['histograms_generator'] = hist_itr
    markovdict['histograms_count'] = hist_count
    markovdict['size3D'] = size3D
    markovdict['bag'] = mkbag
    return markovdict
  #raise IOError('could not read bagfile(%s)' % (filename))

def read_map_yaml(filename = '/home/jolly/ex4/topleft/markov/willowgarage-topleft.yaml'):
  dirname = os.path.dirname(filename)
  yamldict = None
  with open(filename,'r') as mapyaml:
    yamldict = yaml.load(mapyaml)
  assert 'origin' in yamldict
  assert len(yamldict['origin']) == 3
  assert 'resolution' in yamldict
  assert 'negate' in yamldict
  assert 'occupied_thresh' in yamldict
  assert 'free_thresh' in yamldict
  assert 'image' in yamldict
  pgmfile = '/'.join([dirname,yamldict['image']])
  if os.path.isfile(pgmfile):
    yamldict['pgmfile'] = pgmfile
  else:
    raise ValueError('could not find pgm file(%s) in file system.' % (pgmfile))
  return yamldict

def read_pgm_shape(filename = '/home/jolly/ex4/topleft/markov/willowgarage-topleft.pgm'):
  "This function read shape of a pgm file"
  with open(filename,'r') as pgmf:
    assert pgmf.readline() == 'P5\n'
    comment = pgmf.readline()
    #print comment,
    (width, height) = [int(i) for i in pgmf.readline().split()]
    depth = int(pgmf.readline())
    assert depth <= 255
    return (width, height)

def msgs2grid2(mmap, possmsg, histmsg, shape = (500, 683, 4)):
  """
    This function convert poses and histograms messages into a histogram grid with defined shape
  """
  poss_std = possmsg.layout.dim[1].stride
  assert histmsg.array.layout.dim[1].stride == shape[2]
  grid = np.zeros(shape)
  for i in xrange(0,possmsg.layout.dim[0].size):
    pose_x = possmsg.data[i*poss_std]
    pose_y = possmsg.data[i*poss_std + 1]
    x,y = map_gxwx(mmap, pose_x), map_gywy(mmap, pose_y)
    if x >= shape[1]:
      print 'pose_x',pose_x,'to',x,'is out of bound so using', shape[1]-1,'instead'
      x = shape[1]-1
    if y >= shape[0]:
      print 'pose_y',pose_y,'to',y,'is out of bound so using', shape[0]-1,'instead'
      y = shape[0]-1
    if x < 0: x = 0
    if y < 0: y = 0
    for angidx in xrange(0,shape[2]):
      grid[y, x, angidx] = histmsg.array.data[i*shape[2] + angidx]
  total = np.sum(grid)
  grid = grid/total
  return grid

def msgs2grid(idcsmsg, histmsg, shape = (500, 683, 4)):
  """
  shape = (height, width, angular)
  """
  #check angidx is within the range
  idcsstd = idcsmsg.layout.dim[1].stride
  histstd = histmsg.array.layout.dim[1].stride
  assert shape[2] == histstd
  grid = np.zeros(shape)
  for i in xrange(0,idcsmsg.layout.dim[0].size):
    x = idcsmsg.data[i*idcsstd + 1]
    y = idcsmsg.data[i*idcsstd]
    for angidx in xrange(0,shape[2]):
      grid[x,y,angidx] = histmsg.array.data[i*histstd + angidx]
  total = np.sum(grid)
  grid = grid/total
  return grid

def size3D2ares(size3D):
  return 2.0*pi/float(size3D)

def angidx2ang(angidx, size3D):
  return -pi+angidx*size3D2ares(size3D)

def ang2angidx(ang, size3D):
  return int(floor((ang+pi)/pi * (size3D/2) + 0.5))%size3D

saveIdx=0
def plotgrid(grid,step=12,saveFlag=False, showFlag=False):
  X,Y = np.meshgrid(np.linspace(0,1,grid.shape[1]),np.linspace(0,1,grid.shape[0]))
  fig = plt.figure(figsize=(18,10))
  ax = fig.add_subplot(111, projection='3d')
  for i in xrange(0,grid.shape[2],step):
    offset = angidx2ang(i,grid.shape[2])
    ax.contourf(X, Y, grid[:,:,i], zdir='z', offset=offset)
  ax.set_zlim((angidx2ang(0,grid.shape[2]),angidx2ang(grid.shape[2]-1,grid.shape[2])))
  #print np.array(range(grid.shape[2]))*size3D2ares(grid.shape[2]) - pi
  if saveFlag:
    global saveIdx
    plt.savefig('{}.png'.format(saveIdx))
    saveIdx+=1
  if showFlag:
    plt.show()

saveIdx2=0
def plotgrid2(grid,saveFlag=False,suffix='test',saveIdx=0):
  for i in xrange(grid.shape[2]):
    fig = plt.figure(figsize=(18,10))
    ax = fig.add_subplot(111)
    offset = angidx2ang(i,grid.shape[2])
    name = '{}-{}-{}-{}'.format(saveIdx,i,offset,suffix)
    ax.set_title(name)
    plt.imshow(grid[:,:,i])
    if saveFlag:
      plt.savefig('{}.png'.format(name))
    plt.close(fig)

def plotgrid3(grid, part, saveIdx, saveFlag=False, showFlag=False, suffix='test'):
  hist1 = grid.flatten()
  hist2 = part.flatten()
  fig = plt.figure(figsize=(18,10))
  name = '{}_{}'.format(saveIdx, suffix)
  fig.suptitle(name)
  ax1 = fig.add_subplot(211)
  ax1.plot(hist1, 'b-')
  ax2 = fig.add_subplot(212)
  ax2.plot(hist2, 'r-')
  if saveFlag:
    plt.savefig('{}.png'.format(name))
  if showFlag:
    plt.show()
  plt.close(fig) 

def plotgrid4(grid, part, saveIdx, saveFlag=False, showFlag=False, suffix='test', figure=None):
  hist1 = grid.flatten()
  hist2 = part.flatten()
  thres1 = np.amax(hist1)
  thres2 = np.amax(hist2)
  barwidth = 100.0/hist1.shape[0]
  if figure is None:
    fig = plt.figure(figsize=(18,10))
  else:
    fig = figure
  name = '{}_{}'.format(saveIdx, suffix)
  fig.suptitle(name)
  ax1 = fig.add_subplot(211)
  ax2 = fig.add_subplot(212)
  ax1.set_xlim(0,100)
  ax2.set_xlim(0,100)
  ax1.set_ylim(0,thres1)
  ax2.set_ylim(0,thres2)
  for i, (h1, h2) in enumerate(zip(hist1, hist2)):
    if h1 > 0.01*thres1:
      ax1.bar(i*barwidth, h1, barwidth, align='edge')
    if h2 > 0.01*thres2:
      ax2.bar(i*barwidth, h2, barwidth, align='edge')
  if saveFlag:
    plt.savefig('{}.png'.format(name))
  if showFlag:
    plt.show()
  plt.close(fig) 
  return name

def cloudmsg2grid(cloudmsg, mmap, shape):
  particle_grid = np.zeros(shape)
  #convert particle cloud to a grid
  for pose in cloudmsg.poses:
    #pose x -> index x
    #pose y -> index y
    #pose a -> index a
    x,y,a = map_gxwx(mmap, pose.position.x), map_gywy(mmap, pose.position.y), ang2angidx(ori2heading(pose.orientation), shape[2])
    #boundry check
    if x >= shape[1]: x = shape[1]-1
    if y >= shape[0]: y = shape[0]-1
    if a >= shape[2]: a = shape[2]-1
    if x < 0: x = 0
    if y < 0: y = 0
    if a < 0: a = 0
    particle_grid[y,x,a] +=1

  particle_sum = np.sum(particle_grid)
  particle_grid = particle_grid / particle_sum
  return particle_grid
