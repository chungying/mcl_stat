"""
This python script is for modifying old-version pickle files that is without the file name of map.
addpair.py MAPNAME PKLFILES...
PKLFILES are the pickle files each of which storing a dictionary without 'map' key.
"""
#! /usr/bin/env python
import sys
import pickle
FTYPE = '.pkl'

def help():
  print "addpair.py MAPNAME PKLFILES..."


if __name__=='__main__':
  if len(sys.argv) <= 2:
    print 'please enter arguments'
    help()
    exit(1)

  pkls = []
  mapname = None
  #if sys.argv[1].lower() == 'true':
  if 'pkl' not in sys.argv[1]:
    mapname = sys.argv[1]
    pkls += sys.argv[2:]
  else: 
    print 'please enter arguments'
    help()
    exit(1)
  if len(pkls)==0:
    print 'no pkl file'
    exit(1)
  for pkl in pkls:
    #TODO read a pkl
    with open(pkl,'r') as inputpkl:
      #TODO read an object
      obj = pickle.load(inputpkl)
      #TODO add a pair to the object
      obj['map'] = mapname
      with open(pkl+'.bak','w') as outputpkl:
        #TODO write the object into a new file ended in bak
        pickle.dump(obj,outputpkl)
