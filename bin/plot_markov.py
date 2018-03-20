#! /usr/bin/env python
import mcl_stat.ioutil as iu
from mcl_stat.markov_grid import *

bagyaml = read_bag_yaml('/home/jolly/ex4/topleft/markov/size3Dis4/ex4-bag.yaml')
#bagyaml = read_bag_yaml('/home/jolly/ex4/topleft/markov/ex4-bag.yaml')
mapyaml = read_map_yaml(bagyaml['mapyaml'])
pgm_shape = read_pgm_shape(mapyaml['pgmfile'])
markov_dict = read_markov_bag(bagyaml['bagfile'])
grid_shape = (pgm_shape[1], pgm_shape[0], markov_dict['size3D'])
grid = msgs2grid(markov_dict['indices'],markov_dict['histograms'],grid_shape)
print 'finished', grid_shape
#plotgrid(grid)
#ares width height origin
#TODO read target algorithm bag

#TODO conversion between pose and index
#TODO pose x <-> index x
#TODO pose y <-> index y
#TODO pose a <-> index a

#mclbagfile = ''
#truth = od()
#guess = od()
#cloud = od()
#iu.readbag(mclbagfile, truth, guess, cloud):
