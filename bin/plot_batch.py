#! /usr/bin/env python
"""
This python script analyses overall systematic statistics of a batch of bag files recording AMCL results.
"""
import sys
import mcl_stat.plotutil as pu
import mcl_stat.ioutil as iu
import matplotlib.pyplot as plt
anifig, aniax = plt.subplots()
FTYPE = '.pkl'

#TODO using argparse
def help():
  print "plot.py [SAVEFLAG] PKLFILES..."

#TODO using argparse
if __name__=='__main__':
  if len(sys.argv) <= 2:
    print 'please enter arguments'
    help()
    exit(1)

  args = []
  saveflag = False
  if sys.argv[1].lower() == 'true':
    saveflag = True
    if sys.argv[2].find(FTYPE) >= 0:
      args += sys.argv[2:]
    else:
      print 'please enter arguments'
      help()
      exit(1)
  elif sys.argv[1].lower() == 'false':
    saveflag = False
    if sys.argv[2].find(FTYPE) >= 0:
      args += sys.argv[2:]
    else:
      print 'please enter arguments'
      help()
      exit(1)
  else: 
    saveflag = False
    if sys.argv[1].find(FTYPE) >= 0:
      args += sys.argv[1:]
    else:
      print 'please enter arguments'
      help()
      exit(1)
  if len(args)==1:
    print 'only one file'
    #TODO print it not plot
    exit(0)
  dims, objs = iu.readpkl(args)
  folder = '//'.join(args[0].split('//')[0:-1])
  if len(folder) == 0: folder = '.'
  #TODO variables mp, ri, ita, gamma
  #fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1','ri2'])
  #fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mcl'], alwdri=['ri1','ri2'])
  #fig = pu.plotting(objs, dims, 'mp', alwdmcl=['amcl'], alwdri=['ri1','ri2'])
  #fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mixmcl'], alwdri=['ri1','ri2'])
  #fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mcmcl'], alwdri=['ri1','ri2'])
  fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1'], saveflag=saveflag, captype='minmax')
  fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1'], saveflag=saveflag, captype='std')
  #fig = pu.plotting(objs, dims, 'mp', alwdri=['ri2'])
  #fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri1'])
  #fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri2'])
  #fig = pu.plotting(objs, dims, 'ita', alwdmcl=['mixmcl'], alwdri=['ri1'], saveflag=saveflag, captype='minmax')
  #fig = pu.plotting(objs, dims, 'ita', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri1'])
  #fig = pu.plotting(objs, dims, 'ita', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri2'])
  #fig = pu.plotting(objs, dims, 'gamma', alwdmcl=['mcmcl'], alwdri=['ri1'])
  #fig = pu.plotting(objs, dims, 'gamma', alwdmcl=['mcmcl'], alwdri=['ri2'])

  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmcl=['mcl'])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmcl=['amcl'])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmcl=['mixmcl'])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmcl=['mcmcl'])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[10])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[100])
  pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[1000])
  pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[2000])
  pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[3000])
  pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[4000])
  pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[5000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[6000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[7000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[8000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[9000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[10000])

