#! /usr/bin/env python
import sys
import mcl_stat.ioutil as iu
import pickle
FTYPE = '.pkl'

# This is deprecated.
# cloudstat and mcl statistics was put together in the same pickle file
# so I use this script to separate cloudstat from mcl statistics
# after that cloudstat and mcl statistics are saved in MCLNAME.pkl and MCLNAME_cloudstat.pkl respectively
if __name__=='__main__':
  if len(sys.argv) != 2:
    print 'please enter only one pkl filename'
    print sys.argv
    exit(1)
  pklname = sys.argv[1]
  outname = pklname.replace('.pkl','_1.pkl')
  out2name = pklname.replace('.pkl','_cloudstat.pkl')
  obj = None
  cloudstat_list = None
  with open(pklname, 'r') as pkl:
    try:
      obj = pickle.load(pkl)
      cloudstat_list = obj.pop('list_cloudstat',None)
    except EOFError:
      print 'cannot read file', pklname
  iu.data2pkl(outname, obj)
  iu.cloud2pkl(out2name,cloudstat_list)
