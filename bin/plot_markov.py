#! /usr/bin/env python
import mcl_stat.ioutil as iu
import mcl_stat.util as ut
from mcl_stat.markov_grid import *
from collections import OrderedDict as od
from sys import float_info as fi
eps = fi.epsilon

#bagyaml = read_bag_yaml('/home/irlab/ex4/markov/size3Dis72/ex4-markov-72.yaml')
#bagyaml = read_bag_yaml('/media/jolly/storejet/ex4/topleft/markov/size3D72.yaml')
bagyaml = read_bag_yaml('/home/jolly/ex4/topleft/markov/size3Dis4/ex4-bag.yaml')
mapyaml = read_map_yaml(bagyaml['mapyaml'])
pgm_shape = read_pgm_shape(mapyaml['pgmfile'])
markov_dict = read_markov_bag(bagyaml['bagfile'])
grid_shape = (pgm_shape[1], pgm_shape[0], markov_dict['size3D'])
#ares   size3D2ares(size3D) 
#width  grid_shape[1]
#height grid_shape[0]
#origin mapyaml['origin']
#resolution mapyaml['resolution']
numbered = enumerate(markov_dict['histograms_generator'])
for idx, (topic, histmsg, t) in numbered:
  print 'reading',idx,'-th histogram message...',
  grid = msgs2grid(markov_dict['indices'],histmsg,grid_shape)
  #TODO normalize grid and check if any element is zero
  print 'the first value is',histmsg.array.data[0]
  #read target algorithm bag
  #mclbagfile = ''
  mclbagfile = '/media/jolly/Local Disk/ex3/topleft/amcl_mp3000_ri1/amcl_mp3000_ri1_2018-02-04-11-55-01.bag'
  truth = od()
  guess = od()
  cloud = od()
  iu.readbag(mclbagfile, truth, guess, cloud)
  #find the closest stamp to current
  idx = ut.takeClosest(cloud.keys(),histmsg.header.stamp)
  #TODO convert particle cloud to a grid
  
  for pose in cloud.values()[idx].poses:
    pose.position.x
    pose.position.y
    pose.orientation
  #TODO conversion between pose and index
  #TODO normalize grid and check if any element is zero
  #TODO pose x <-> index x
  #TODO pose y <-> index y
  #TODO pose a <-> index a

print 'finished reading markov grid with shape ', grid_shape, '. then plotting...'
#plotgrid(grid)
