#! /usr/bin/env python
import argparse
import numpy as np
from math import ceil
from mcl_stat.motion import *
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm

if __name__=='__main__':
  parser = argparse.ArgumentParser(description='Plot probability map of motion model.')
  #parser.add_argument('-p','--pklfiles', nargs='+', help='<Required> Set flag', required=True)
  #parser.add_argument('-r','--radius', nargs=2, type=float, action='append', help='definition of deprivation radius, (meter degree)', required=True)
  parser.add_argument('--headings', nargs='+', type=float, help='the heading of new poses', required=True)
  parser.add_argument('-L','--limits', nargs=2, type=float, help='definition of limits, (minimum maximum)', required=True)
  parser.add_argument('-R','--resolution', type=float, help='resolution of each grid axis', required=True)
  parser.add_argument('--saveflag', action='store_true', required=False)
  args = parser.parse_args()
  #print args.pklfiles
  #print args.radius
  if args.saveflag: print 'saveflag on'
  else: print 'saveflag off'

  origin_pose = Pose(0.0,0.0,eul2rad(30.0))
  ut = Delta(5.0, eul2rad(20.0), eul2rad(20.0), origin_pose)
  lim = tuple(args.limits)
  grid_res = args.resolution
  mvf = np.vectorize(motionModel)
  ppose = lambda pose: (pose.x, pose.y, pose.a)
  pposes = np.vectorize(ppose)

  headings = args.headings
  row = 2
  col = int(ceil(float(len(headings))/2.0))
  fig,axs = plt.subplots(row,col)
  fig3d = plt.figure(figsize=(18,10))
  for i, angle in enumerate(headings):
    poses=[]
    X = np.linspace(lim[0], lim[1], grid_res)
    Y = np.linspace(lim[0], lim[1], grid_res)
    for x in X:
      for y in Y:
        poses.append(Pose(x,y,eul2rad(angle)))
    probs = mvf(poses,ut,origin_pose,0.8,0.8,.8,.8)
    bools = (probs>=1e-7) + np.zeros(len(probs))
    probmat = np.reshape(probs,(grid_res,grid_res))
    boolsmat = np.reshape(bools,(grid_res,grid_res))
    XX, YY = np.meshgrid(X,Y)
    ax = fig3d.add_subplot(row,col,i,projection='3d')
    ax.plot_surface(XX, YY, probmat, cmap=cm.coolwarm)
    r = i/col
    c = i%col
    axs[r,c].matshow(boolsmat)
  #plt.matshow(probmat)
  plt.show()
  
