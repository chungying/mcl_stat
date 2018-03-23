#! /usr/bin/env python
import mcl_stat.ioutil as iu
import mcl_stat.util as ut
from mcl_stat.util import ori2heading
from mcl_stat.markov_grid import *
from mcl_stat.mclmap import *
from collections import OrderedDict as od

bagyaml = read_bag_yaml('/home/irlab/ex4/markov/size3Dis72/ex4-markov-72.yaml')
#bagyaml = read_bag_yaml('/media/jolly/storejet/ex4/topleft/markov/size3D72.yaml')
#bagyaml = read_bag_yaml('/home/jolly/ex4/topleft/markov/size3Dis4/ex4-bag.yaml')
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
numbered = enumerate(markov_dict['histograms_generator'])

#for each algorithm and each timestamp
tasks = []
######## read target algorithm bag ########
#mclbagfile = '/home/irlab/.ros/mcmcl_mp2000_ri1_ita1e-2_gamma2_2018-03-22-18-39-18.bag'#good
mclbagfile = '/home/irlab/.ros/mcl_mp100000_ri1_2018-03-23-11-45-27.bag'#good
#mclbagfile = '/media/jolly/Local Disk/ex3/topleft/amcl_mp3000_ri1/amcl_mp3000_ri1_2018-02-04-11-55-01.bag'
truth = od()
guess = od()
cloud = od()
iu.readbag(mclbagfile, truth, guess, cloud)

for idx, (topic, histmsg, t) in numbered:
  ######## Reading markov ########
  print 'reading',idx,'-th histogram message...',
  #markov_grid = msgs2grid(markov_dict['indices'],histmsg,markov_grid_shape)
  markov_grid = msgs2grid2(mmap, markov_dict['positions'],histmsg,markov_grid_shape)
  particle_grid = np.zeros(markov_grid.shape)
  #print 'the first value is',histmsg.array.data[0]
  
  #find the closest stamp to current
  #for i, k in enumerate(cloud.keys()):
  #  print i, ':', k.to_nsec(), ', ', histmsg.header.stamp, ', diff:', (k-histmsg.header.stamp).to_sec()
  cldidx = ut.takeClosestIdx(cloud.keys(),histmsg.header.stamp)
  #convert particle cloud to a grid
  
  for pose in cloud.values()[cldidx].poses:
    #pose x -> index x
    #pose y -> index y
    #pose a -> index a
    x,y,a = map_gxwx(mmap, pose.position.x), map_gywy(mmap, pose.position.y), ang2angidx(ori2heading(pose.orientation), markov_grid_shape[2])
    #boundry check
    if x >= particle_grid.shape[1]: x = particle_grid.shape[1]-1
    if y >= particle_grid.shape[0]: y = particle_grid.shape[0]-1
    if a >= particle_grid.shape[2]: a = particle_grid.shape[2]-1
    if x < 0: x = 0
    if y < 0: y = 0
    if a < 0: a = 0
    particle_grid[y,x,a] +=1
    #print particle_grid[y,x,a]

  particle_sum = np.sum(particle_grid)
  print 'particle grid dtype',particle_grid.dtype, ', sum', particle_sum,
  particle_grid = particle_grid / particle_sum
  plotgrid2(particle_grid, saveFlag=True,saveIdx=idx,suffix='particle')
  plotgrid2(markov_grid  , saveFlag=True,saveIdx=idx,suffix='markov')
  #TODO too fine and small
  #plotgrid(particle_grid)
  #plotgrid(markov_grid)
  #print 'kld of', cldidx,'is', kld(markov_grid,particle_grid)
  print 'invkld of', cldidx,'is', kld(particle_grid, markov_grid)

  #TODO shrink 2 or 4 times in all dimensions
  #shrink_scale = (10,10,4)
  #shrink1 = shrink_grid(markov_grid,  shrink_scale)
  #shrink2 = shrink_grid(particle_grid,shrink_scale)
  #plotgrid(shrink2,step=1,saveFlag=True,showFlag=False)
  #print 'kld of', cldidx,'is', kld(shrink1, shrink2)

print 'finished reading markov grid with shape ', markov_grid_shape, '. then plotting...'
