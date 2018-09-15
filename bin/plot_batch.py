#! /usr/bin/env python
"""
This python script analyses overall systematic statistics of a batch of bag files recording AMCL results.
INPUT: 
SAVEFLAG show or save figures, True or False
PKLFILES filenames of pickle files
OUTPUT: ??

"""
import sys
import mcl_stat.plotutil as pu
import mcl_stat.ioutil as iu
import matplotlib.pyplot as plt
FTYPE = '.pkl'

#TODO using argparse
def help():
  print "plot.py [SAVEFLAG] PKLFILES..."

#TODO using argparse
if __name__=='__main__':


###########Argument parser########################
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
###################################

  #readpkl reads pickle files with format from where??TODO
  dims, objs = iu.readpkl(args)
  folder = '//'.join(args[0].split('//')[0:-1])
  if len(folder) == 0: folder = '.'
  #TODO variables mp, ri, ita, gamma
  #fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1'], saveflag=saveflag, captype='minmax')
  #fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1'], saveflag=saveflag, captype='std')
  fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1'], saveflag=saveflag, captype='none')

  #pu.plot_rms_position_error(objs, saveflag=saveflag, dirpath=folder, alwdmp=[1000])
  #pu.plot_rms_position_error(objs, saveflag=saveflag, dirpath=folder, alwdmcl=['mcl'])
  #pu.plot_rms_position_error(objs, saveflag=saveflag, dirpath=folder, alwdmcl=['amcl'])
  #pu.plot_rms_position_error(objs, saveflag=saveflag, dirpath=folder, alwdmcl=['mixmcl'])
  #pu.plot_rms_position_error(objs, saveflag=saveflag, dirpath=folder, alwdmcl=['mcmcl'])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[1000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[2000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[3000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[4000])
  #pu.ploterrtime(objs, saveflag=saveflag, dirpath=folder, captype='minmax', alwdmp=[5000])

