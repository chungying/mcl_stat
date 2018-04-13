#! /usr/bin/env python
import mcl_stat.ioutil as iu
import mcl_stat.util as ut
from mcl_stat.util import ori2heading
from mcl_stat.markov_grid import *
from mcl_stat.mclmap import *
from collections import OrderedDict as od

bagyaml = read_bag_yaml('/media/irlab/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
#bagyaml = read_bag_yaml('/media/jolly/storejet/ex3/markov_ex3_parallel/ex3-markov-72.yaml')
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

#for each algorithm and each timestamp
tasks = []
######## read target algorithm bag ########
#mclbagfile = '/media/jolly/storejet/ex3/topleft/amcl_mp3000_ri1/amcl_mp3000_ri1_2018-02-04-11-55-01.bag'
mclbagfile = '/media/irlab/storejet/ex3/topleft/amcl_mp3000_ri1/amcl_mp3000_ri1_2018-02-04-11-55-01.bag'
truth = od()
guess = od()
cloud = od()
iu.readbag(mclbagfile, truth, guess, cloud)

numbered = enumerate(markov_dict['histograms_generator'])
for idx, (topic, histmsg, t) in numbered:
  #if idx < 14:
  #  print 'skipped',idx
  #  continue
  if idx > 1:
    print 'break',idx
    break

  #TODO make the following part as independent code for multithreading
  ######## Reading markov ########
  print 'reading',idx,'-th histogram message...',
  #markov_grid = msgs2grid(markov_dict['indices'],histmsg,markov_grid_shape)
  markov_grid = msgs2grid2(mmap, markov_dict['positions'],histmsg,markov_grid_shape)

  #find the closest stamp to current
  cldidx = ut.takeClosestIdx(cloud.keys(),histmsg.header.stamp)
  #create particle_grid
  particle_grid = cloudmsg2grid(cloud.values()[cldidx], mmap, markov_grid_shape)

  #plot histograms of markov_grid and particle_grid
  #plotgrid4(markov_grid, particle_grid, saveFlag=True,showFlag=False,saveIdx=idx,suffix='hist')
  #plot color heat map of markov_grid and particle_grid for each angle
  #plotgrid2(markov_grid, saveFlag=True,saveIdx=idx,suffix='markov')
  #plotgrid2(particle_grid, saveFlag=True,saveIdx=idx,suffix='particle')
  print 'kld of', cldidx,'is', kld(markov_grid,particle_grid),
  print 'invkld of', cldidx,'is', kld(particle_grid, markov_grid),

  #TODO shrink 2 or 4 times in all dimensions
  #shrink_scale = (10,10,4)
  #shrink1 = shrink_grid(markov_grid,  shrink_scale)
  #shrink2 = shrink_grid(particle_grid,shrink_scale)
  #plotgrid(shrink2,step=1,saveFlag=True,showFlag=False)
  #print 'kld of', cldidx,'is', kld(shrink1, shrink2)

  print ''

print 'finished reading markov grid with shape ', markov_grid_shape, '. then plotting...'
