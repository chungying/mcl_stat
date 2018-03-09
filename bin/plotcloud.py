#! /usr/bin/env python
import argparse
import sys
import mcl_stat.plotutil as pu
import mcl_stat.ioutil as iu
import pickle
import numpy as np
from copy import deepcopy
from math import pi
from collections import OrderedDict as od
FTYPE = '.pkl'

def help():
  print "plotcloud.py [SAVEFLAG] PKLFILES..."

if __name__=='__main__':
  #dims, objs = iu.readpkl(args)
  folder = '.'
  parser = argparse.ArgumentParser(description='Plot particle cloud statistics.')
  parser.add_argument('-p','--pklfiles', nargs='+', help='<Required> Set flag', required=True)
  parser.add_argument('-r','--radius', nargs=2, type=float, action='append', help='definition of deprivation radius, (meter degree)', required=True)
  parser.add_argument('--saveflag', action='store_true', required=False)
  args = parser.parse_args()
  print args.pklfiles
  print args.radius
  if args.saveflag: print 'saveflag on'
  else: print 'saveflag off'
  pklfiles = args.pklfiles
  metafiles = []
  for pklfile in pklfiles:
    metafile = pklfile.replace('_cloudstat','')
    metafiles.append(metafile)
  tuplist = zip(metafiles, pklfiles)
  #plot statistics of degree of deprivation at each timestamp
  #for each cloudpkl
  objs = {}
  for metafile, cloudfile in tuplist:
    #read metadata, mclpkg, mp, ri, ita, gamma
    metaobj = None
    try:
      with open(metafile, 'r') as metapkl:
        metaobj = pickle.load(metapkl)
    except Exception:
        print 'cannot read file', metafile
        raise
    #read cloudstat
    cloudstat = None
    try:
      with open(cloudfile, 'r') as cloudpkl:
        cloudstat = pickle.load(cloudpkl)
    except Exception:
        print 'cannot read file', cloudfile
        raise
    #read timestamp from cloudstat
    timestamp = cloudstat['timestamp']
    cols = len(timestamp)
    #for each deprivation definition of radius tuples (meter, radian)
    #generate a pair of key and value, where
    #key is metaobjkey+radias
    #value is degree of deprivation
    metakey = iu.obj2key(metaobj)
    for radtup in args.radius:
      #obj = metaobj#TODO clone metaobj or it is just copy the reference
      obj = deepcopy(metaobj)
      obj['radius_tup'] = radtup
      cloudstat_mat = np.arange(5*cols,dtype=float).reshape(5,cols)
      cloudstat_mat[0,:] = timestamp
      #calculate the degree of deprivation based on radtup
      for time_idx, time in enumerate(timestamp):
        list_deprived_degree = []
        for cloud_idx, total_hyp in enumerate(cloudstat['total_number'][time_idx]):
          good_hyp_number = 0
          for hyp_idx, hyp_dd in enumerate(cloudstat['all_dd'][time_idx][cloud_idx]):
            hyp_da = cloudstat['all_da'][time_idx][cloud_idx][hyp_idx]
            if hyp_dd <= radtup[0] and hyp_da <= pi*radtup[1]/180.0:
              good_hyp_number += 1
          cloud_deprived_degree = 1.0*good_hyp_number/total_hyp
          if cloud_deprived_degree > 1.0:
            print 'it should not exceed 1.'
          list_deprived_degree.append(cloud_deprived_degree)
        cloudstat_mat[1,time_idx] = np.mean(list_deprived_degree)
        cloudstat_mat[2,time_idx] = np.std(list_deprived_degree)
        cloudstat_mat[3,time_idx] = cloudstat_mat[1,time_idx] - np.min(list_deprived_degree)
        cloudstat_mat[4,time_idx] = np.max(list_deprived_degree) - cloudstat_mat[1,time_idx]
      obj['cloudstatmat'] = cloudstat_mat
      radkey = pu.rad2key(radtup)
      objk = metakey+'_'+radkey
      objs[objk] = obj

  objs = od(sorted(objs.items(),key=lambda t: (t[1]['mclpkg'], t[1]['mp'], t[1]['ri'], t[1]['radius_tup'][0], t[1]['radius_tup'][1])))
  for captype in ['minmax','std']:
    for radtup in args.radius:
      for mp in range(1000, 6000, 1000):
        pu.plotcloudstat(objs, alwdmp=[mp], alwdrad=[radtup], saveflag=args.saveflag, captype=captype)
  #pu.plotcloudstat(objs, alwdmp=[1000])
  #pu.plotcloudstat(objs, alwdmp=[2000])
  #pu.plotcloudstat(objs, alwdmp=[3000])
  #pu.plotcloudstat(objs, alwdmp=[4000])
  #pu.plotcloudstat(objs, alwdmp=[5000])
