#! /usr/bin/env python
"""
This python script analyses statistics of single bag files recording AMCL results respectively.
please enter names of rosbag files
plot_singles.py PLOTSAVEFLAG BAG1 BAG2 ...
When PLOTSAVEFLAG is true, plot figures for all bag files.
BAG is the filename of a bag file.
"""
import mcl_stat.util as ut
import mcl_stat.statutil as su
import mcl_stat.ioutil as iu
import mcl_stat.plotutil as pu
from mcl_stat.util import ori2heading
from mcl_stat.mclmap import *
import re
import sys
import rosbag
from collections import OrderedDict as od
import matplotlib.pyplot as plt
import numpy as np
from math import pi
import os
import argparse

BEGIN=None
fileIdx = 0
thres_d = 2
thres_a = pi*15/180
tfm={True: 'Succeeded', False: 'Failed'}

def parse_arguments():
  parser = argparse.ArgumentParser(description='This script analyses statistics of multiple bag files recording algorithm results.')
  parser.add_argument('-b','--bag-files', nargs='+', help='<Required> A list of bag files with relative path to current folder', required=True)
  parser.add_argument('--output-dir', help='<Optional> The folder for storing a pickle file of algorithm statistics. The default is current folder')
  parser.add_argument('--save-pkl', action='store_true', help='<Optional:False> Whether save algorithm statistics into a pickle file')
  parser.add_argument('--save-img', action='store_true', help='<Optional:False> Whether save plotted figures for all bag files')
  return parser.parse_args()

def process(bagfile, plotflag = True, errtime=None, clouddict=None):
  """
  Reads a bag that records all topics amcl subscribes from and publishes to.
  Plots a image with eight figures plotted by pu.ploteach.
  errtime and clouddict are output
  Additionally, this function returns status, distance_diff, and orientation_diff.
  status: if True, the final pose of this bagfile is close to the ground truth pose.
  distance_diff: the distance between the final pose to the ground truth pose.
  orientation_diff: the orientation difference between the final pose and the ground truth pose.
  rmse: root mean square position error of this trajectory
  """
  #read bagfile
  truth = od()
  guess = od()
  cloud = od()
  global fileIdx
  if iu.readbag(bagfile, truth, guess, cloud):
    fileIdx += 1
    #check time order
  else:
    print 'failed to read',bagfile

  if not iu.ifsorted(truth):
    print 'going to sort truth in',bagfile
    truth = od(sorted(truth.items(), key=lambda t: t[0]))
  if not iu.ifsorted(guess):
    print 'going to sort guess in',bagfile
    guess = od(sorted(guess.items(), key=lambda t: t[0]))
  if not iu.ifsorted(cloud):
    print 'going to sort cloud in',bagfile
    cloud = od(sorted(cloud.items(), key=lambda t: t[0]))

  #block 2
  #input:fileIdx, plotflag, bagfile, truth, guess
  #output: ploting a figure, dic
  tkeys = truth.keys()
  #check begin time of groud truth
  global BEGIN
  if BEGIN == None:
    BEGIN = tkeys[0]
  else:
    if BEGIN != tkeys[0]: raise Exception('base_pose_groud_truth is not sychronized.')
  #check time order
  gkeys = guess.keys()
  ckeys = cloud.keys()
  prev = gkeys[0]
  for idx, gk in enumerate(gkeys):
    if gk < prev:
      raise Exception('guess is not time-ordered.')
    if ckeys[idx] != gk:
      print '/particlecloud and /mcl_pose is not synchronized.'
    prev = gk
  #processing messages
  plotmat = np.arange(12*len(gkeys),dtype=float).reshape(12,len(gkeys))
  errmat = np.arange(2*len(gkeys),dtype=float).reshape(2,len(gkeys))
  st = []
  if clouddict is None:
    clouddict = {
      'timestamp':[], 
      'total_number':[], 
      'good_hyp_number':[], 
      'all_dd':[], 
      'all_da':[]
    }
  else:
    clouddict['timestamp']=[] 
    clouddict['total_number']=[] 
    clouddict['good_hyp_number']=[] 
    clouddict['all_dd']=[] 
    clouddict['all_da']=[]
    
  for col_idx, gk in enumerate(gkeys):
    # geometry_msgs/PoseWithCovarianceStamped
    tk = ut.takeClosest(tkeys, gk)
    status, dd, da = ut.ifSucc(truth[tk].pose.pose, guess[gk].pose.pose)
    if errtime is not None:
      errtime[guess[gk].header.stamp.to_sec()-BEGIN.to_sec()]=dd#Euclidean distance
    st.append(status)
    errmat[0, col_idx] = dd#Euclidean distance
    errmat[1, col_idx] = da

    good_number = 0
    allhyp_dd = []
    allhyp_da = []
    for hyp_idx, hyppose in enumerate(cloud[gk].poses):
      #calculate the error of pose and ground truth
      status, dd, da = ut.ifSucc(hyppose, truth[tk].pose.pose)
      if status: 
        good_number += 1
      allhyp_dd.append(dd)
      allhyp_da.append(da)
    clouddict['timestamp'].append(guess[gk].header.stamp.to_sec()-BEGIN.to_sec())
    clouddict['good_hyp_number'].append(good_number)
    clouddict['total_number'].append(len(cloud[gk].poses))
    clouddict['all_dd'].append(allhyp_dd)
    clouddict['all_da'].append(allhyp_da)

    if plotflag:
      plotmat[0, col_idx] = truth[tk].pose.pose.position.x
      plotmat[1, col_idx] = truth[tk].pose.pose.position.y
      plotmat[2, col_idx] = ut.ori2heading(truth[tk].pose.pose.orientation)
      plotmat[3, col_idx] = guess[gk].pose.pose.position.x
      plotmat[4, col_idx] = guess[gk].pose.pose.position.y
      plotmat[5, col_idx] = ut.ori2heading(guess[gk].pose.pose.orientation)
      stddev = su.sqrt0(guess[gk].pose.covariance[0])
      plotmat[6, col_idx] = plotmat[3, col_idx] + 2*stddev
      plotmat[7, col_idx] = plotmat[3, col_idx] - 2*stddev
      stddev = su.sqrt0(guess[gk].pose.covariance[7])
      plotmat[8, col_idx] = plotmat[4, col_idx] + 2*stddev
      plotmat[9, col_idx] = plotmat[4, col_idx] - 2*stddev
      stddev = su.sqrt0(guess[gk].pose.covariance[35])
      plotmat[10, col_idx] = plotmat[5, col_idx] + 2*stddev
      plotmat[11, col_idx] = plotmat[5, col_idx] - 2*stddev

  #TODO confirm the equation of RMSE
  rmsefunc = lambda a: su.sqrt0(a.dot(a)/len(a))
  rmse = rmsefunc(errmat[0,:])
  avged = np.mean(errmat[0,:])
  avgea = np.mean(errmat[1,:])
  stded = np.std(errmat[0,:])
  stdea = np.std(errmat[1,:])
  print 'processing {idx}-th {status}, d: {avgd}+-{stdd}, h:{avga}+-{stda}, final: {fed} {fea}, rmse: {rms}'.format(idx=fileIdx, status=tfm[st[-1]], avgd=avged, stdd=stded, avga=avgea, stda=stdea, fed=errmat[0,-1], fea=errmat[1,-1], rms=rmse)

  if plotflag:
    imgname = bagfile.split('.bag',1)[0]
    if st[-1]:
      imgname += '-succeeded'
    else:
      imgname += '-failed'
    if errtime is not None:
      #XXX This function saves the figure it plots
      pu.ploteach(fileIdx, imgname, errtime.keys(), errmat, plotmat, clouddict['good_hyp_number'], clouddict['total_number'])
  return (st[-1], float(errmat[0,-1]), float(errmat[1,-1]), rmse)

#TODO using argparse
def help():
  print "please enter names of rosbag files"
  print "plot_singles.py PLOTSAVEFLAG BAG1 BAG2 ..."
  print "When PLOTSAVEFLAG is true, plot figures."
  print "BAG is the filename of a bag file."

if __name__=='__main__':
  #TODO using argparse
  # parse argument bag_files and bag_files_dir
  args = parse_arguments()
  plotflag = args.save_img
  bag_files = []
  bag_files_dir_path = None
  abs_output_dir=None
  if args.bag_files is not None:
    bag_files_dir_path = None
    for p in args.bag_files:
      abs_path = os.path.abspath(p)
      if not os.path.isfile(abs_path):
        raise RuntimeError('cannot find {}'.format(abs_path))
      bag_files.append(abs_path)
      bag_files_dir_path = os.path.dirname(abs_path)
  if args.output_dir is None:
    abs_output_dir = bag_files_dir_path
  else:
    abs_output_dir = os.path.abspath(args.output_dir)

  if len(bag_files) == 1:
    print "only got one bag file, saving the figure"
    s, d, a, rmse = process( sys.argv[1], True)
    exit(0)

  total = len(bag_files)
  print "there are ", total, " files."
  sucCount = 0
  #using ioutil to create dic
  #create dic for this batch of bag files
  dic = {'list_final_ed':[], 'list_final_ea':[], 'list_rmse':[],'folder':bag_files_dir_path}
  
  #TODO using a function wrap this part returning a dictionary for updating dic
  abs_batch_name = os.path.basename(bag_files[0]).split('_2018',1)[0]
  abs_output_path = abs_output_dir+'/'+abs_batch_name+'.pkl'
  print bag_files[0]
  print "saving pkl file to", (abs_output_path)
   
  words = re.split('[/_]',abs_batch_name)
  if 'amcl' in words: dic['mclpkg'] = 'amcl'
  elif 'mixmcl' in words: dic['mclpkg'] = 'mixmcl'
  elif 'mcmcl' in words: dic['mclpkg'] = 'mcmcl'
  elif 'mcl' in words: dic['mclpkg'] = 'mcl'
  else:
    print 'cannot identify mclpkg by method2'
  ls = re.split('[ /_]',abs_batch_name)
  for s in ls:
    if 'mp' in s:
      dic['mp'] = int(s.split('mp')[-1])
    if 'ri' in s:
      dic['ri'] = int(s.split('ri')[-1])
    if 'ita' in s:
      dic['ita'] = float(s.split('ita')[-1])
    if 'gamma' in s:
      dic['gamma'] = int(s.split('gamma')[-1])

  errtime_list = []
  clouddict_list = []
  for each in bag_files:
    if each.find(".bag") == -1:
      print each, " is not a rosbag file."
    else:
      errtime_dict = od()
      clouddict = od()
      s, d, a, rmse = process(each, plotflag, errtime=errtime_dict, clouddict=clouddict)
      if s: 
        sucCount += 1
      dic['list_final_ed'].append(d)
      dic['list_final_ea'].append(a)
      dic['list_rmse'].append(rmse)
      errtime_list.append(errtime_dict)
      clouddict_list.append(clouddict)
  dic['list_errtimestatmat'],dic['mat_error_time'] = su.errtimestat(errtime_list)

  #cloud stat 
  dic['list_cloudstat'] = su.cloudstat(clouddict_list)

  print "successfual rate: ", sucCount, " out of ", total, " = ", 1.0*sucCount/total*100.0, "%"

  iu.data2pkl(abs_output_path, dic)
  exit(0)

