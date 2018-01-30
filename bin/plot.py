#! /usr/bin/env python
import sys
import mcl_stat.plotutil as pu
import mcl_stat.ioutil as iu

FTYPE = '.pkl'

def help():
  print "plot.py [SAVEFLAG] GROUPSIZE TEXTFILES..."


if __name__=='__main__':
  if len(sys.argv) <= 2:
    print 'please enter arguments'
    help()
    exit(1)

  args = []
  saveFlag = False
  groupsize = None
  if sys.argv[1].lower() == 'true':
    saveFlag = True
    if sys.argv[2].find(FTYPE) == -1:
      groupsize = int(sys.argv[2])
      args += sys.argv[3:]
    else:
      print 'please enter arguments'
      help()
      exit(1)
  elif sys.argv[1].lower() == 'false':
    saveFlag = False
    if sys.argv[2].find(FTYPE) == -1:
      groupsize = int(sys.argv[2])
      args += sys.argv[3:]
    else:
      print 'please enter arguments'
      help()
      exit(1)
  else: 
    saveFlag = False
    if sys.argv[1].find(FTYPE) == -1:
      groupsize = int(sys.argv[1])
      args += sys.argv[2:]
    else:
      print 'please enter arguments'
      help()
      exit(1)
  if len(args)==1:
    print 'only one file'
    #TODO print it not plot
    exit(0)
  dims, objs = iu.readpkl(args)
  #for key,value in objs.iteritems():
  #  print key
  #print dims
  #TODO variables mp, ri, ita, gamma
  #fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1','ri2'])
  fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mcl'], alwdri=['ri1','ri2'])
  fig = pu.plotting(objs, dims, 'mp', alwdmcl=['amcl'], alwdri=['ri1','ri2'])
  fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mixmcl'], alwdri=['ri1','ri2'])
  fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mcmcl'], alwdri=['ri1','ri2'])
  fig = pu.plotting(objs, dims, 'mp', alwdri=['ri1'])
  fig = pu.plotting(objs, dims, 'mp', alwdri=['ri2'])
  fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri1'])
  fig = pu.plotting(objs, dims, 'mp', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri2'])
  #fig = pu.plotting(objs, dims, 'ita', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri1'])
  #fig = pu.plotting(objs, dims, 'ita', alwdmcl=['mixmcl','mcmcl'], alwdri=['ri2'])
  #fig = pu.plotting(objs, dims, 'gamma', alwdmcl=['mcmcl'], alwdri=['ri1'])
  #fig = pu.plotting(objs, dims, 'gamma', alwdmcl=['mcmcl'], alwdri=['ri2'])

  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['amcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mixmcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mcmcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mcmcl','mcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mcmcl','amcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mixmcl', 'mcmcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mixmcl', 'amcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['mixmcl', 'mcl'])
  pu.ploterrtime(objs, captype='minmax', alwdmcl=['amcl', 'mcl'])

