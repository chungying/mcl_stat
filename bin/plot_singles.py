#! /usr/bin/env python
"""
This python script analyses statistics of single bag files recording AMCL results respectively.
please enter names of rosbag files
mcl_stat.py SAVEFLAG BAG1 BAG2 ...
When SAVEFLAG is true, save figures for all bag files.
BAG is the filename of a bag file.
"""
import mcl_stat.util as ut
import mcl_stat.statutil as su
import mcl_stat.ioutil as iu
import mcl_stat.plotutil as pu
import re
import sys
import rosbag
from collections import OrderedDict as od
import matplotlib.pyplot as plt
import numpy as np
from math import pi

BEGIN=None
fileIdx = 0
thres_d = 2
thres_a = pi*15/180
tfm={True: 'Succeeded', False: 'Failed'}

#TODO Deprecated
def comphelper(tup, *vartuple):
  print 'in comparition'
  print tup
  for var in vartuple:
    print var
  return tup[0].to_nsec()


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
      pu.ploteach(fileIdx, imgname, errtime.keys(), errmat, plotmat, clouddict['good_hyp_number'], clouddict['total_number'])
  return (st[-1], float(errmat[0,-1]), float(errmat[1,-1]), rmse)

#TODO using argparse
def help():
  print "please enter names of rosbag files"
  print "mcl_stat.py SAVEFLAG BAG1 BAG2 ..."
  print "When SAVEFLAG is true, save figures."
  print "BAG is the filename of a bag file."

if __name__=='__main__':
  #TODO make this function main()
  #TODO using argparse
  if len(sys.argv) == 1:
    help()
    exit(1)
  elif len(sys.argv) == 2:
    if sys.argv[1].find(".bag") == -1:
      print sys.argv[1], " is not bag file"
      help()
      exit(1)
    elif sys.argv[1].find(".bag") >= 0:
      print "only got one bag file, saving the figure"
      s, d, a, rmse = process( sys.argv[1], True)
    exit(0)
  print "there are more than two arguments"
  plotflag = False
  bagfiles = []
  if sys.argv[1].find(".bag") == -1:
    if sys.argv[1].lower() == "true": 
      plotflag = True
    else: 
      plotflag = False
    bagfiles += sys.argv[2:]
  else:
    plotflag = False
    bagfiles += sys.argv[1:]

  total = len(bagfiles)
  print "there are ", total, " files."
  sucCount = 0
  #create dic for this batch of bag files
  dic = {'list_final_ed':[], 'list_final_ea':[], 'list_rmse':[]}
  errtime_list = []
  clouddict_list = []
  for each in bagfiles:
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
  dic['list_errtimestatmat'] = su.errtimestat(errtime_list)
  #cloud stat 
  dic['list_cloudstat'] = su.cloudstat(clouddict_list)
  #TODO using os.path.basename() or os.path.dirname() to obtain the information of batch name, mp, ri, ita
  #TODO using a function wrap this part returning a dictionary for updating dic
  batch_name = bagfiles[0].split('_2018',1)[0]
  dic['folder'] = '/'.join(batch_name.split('/')[0:-1])
  words = re.split('[/_]',batch_name)
  if 'amcl' in words: dic['mclpkg'] = 'amcl'
  elif 'mixmcl' in words: dic['mclpkg'] = 'mixmcl'
  elif 'mcmcl' in words: dic['mclpkg'] = 'mcmcl'
  elif 'mcl' in words: dic['mclpkg'] = 'mcl'
  else:
    print 'cannot identify mclpkg by method2'
  ls = re.split('[ /_]',batch_name)
  for s in ls:
    if 'mp' in s:
      dic['mp'] = int(s.split('mp')[-1])
    if 'ri' in s:
      dic['ri'] = int(s.split('ri')[-1])
    if 'ita' in s:
      dic['ita'] = float(s.split('ita')[-1])
    if 'gamma' in s:
      dic['gamma'] = int(s.split('gamma')[-1])
  print "successfual rate: ", sucCount, " out of ", total, " = ", 1.0*sucCount/total*100.0, "%"
  print "saving file:", (batch_name+'.pkl')
  iu.data2pkl(batch_name+'.pkl', dic)
  exit(0)
