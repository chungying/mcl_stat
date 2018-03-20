import numpy as np
import os
import yaml
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from rosbag import Bag
from math import pi

markov_topics = ['/indices','/positions','/histograms']

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
  with Bag(filename,'r') as mkbag:
    _,idcs,_ = mkbag.read_messages(topics=markov_topics[0]).next()
    _,poss,_ = mkbag.read_messages(topics=markov_topics[1]).next()
    hist = []
    for top,msg,t in mkbag.read_messages(topics=markov_topics[2]):
      hist.append(msg)
    mkbag.close()
    size3D = hist[0].array.layout.dim[1].stride
    markovdict = {}
    markovdict['indices'] = idcs
    markovdict['positions'] = poss
    markovdict['histograms'] = hist
    markovdict['size3D'] = size3D
    return markovdict
  raise IOError('could not read bagfile(%s)' % (filename))

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

def msgs2grid(idcsmsg, histmsgs, shape = (500, 683, 4)):
  #check angidx is within the range
  idcsstd = idcsmsg.layout.dim[1].stride
  histstd = histmsgs[0].array.layout.dim[1].stride
  assert shape[2] == histstd
  grid = np.zeros(shape)
  for i in xrange(0,idcsmsg.layout.dim[0].size):
    x = idcsmsg.data[i*idcsstd + 1]
    y = idcsmsg.data[i*idcsstd]
    for angidx in xrange(0,shape[2]):
      grid[x,y,angidx] = histmsgs[0].array.data[i*histstd + angidx]
  return grid

def size3D2ares(size3D):
  return 2.0*pi/float(size3D)

def angidx2ang(angidx, size3D):
  return -pi+angidx*size3D2ares(size3D)

def plotgrid(grid):
  X,Y = np.meshgrid(np.linspace(0,1,grid.shape[1]),np.linspace(0,1,grid.shape[0]))
  fig = plt.figure(figsize=(18,10))
  ax = fig.add_subplot(111, projection='3d')
  for i in xrange(grid.shape[2]):
    offset = angidx2ang(i,grid.shape[2])
    ax.contourf(X, Y, grid[:,:,i], zdir='z', offset=offset)
  ax.set_zlim((angidx2ang(0,grid.shape[2]),angidx2ang(grid.shape[2]-1,grid.shape[2])))
  #print np.array(range(grid.shape[2]))*size3D2ares(grid.shape[2]) - pi
  plt.show()
