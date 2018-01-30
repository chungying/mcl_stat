#! /usr/bin/env python
import rosbag
import sys
from collections import OrderedDict
if __name__=='__main__':
  bagfiles = sys.argv[1:]
  files={}
  for each in bagfiles:
    files[each]={}
    with rosbag.Bag(each) as bag:
      truth={}
      for topic, msg, t in bag.read_messages(topics=['/p3dx/base_pose_ground_truth']):
        truth[msg.header.stamp]=msg
      files[each] = OrderedDict(sorted(truth.items(), key=lambda t: t[0]))
      init=False
      t1=files[each].keys()[0]
      for k,v in files[each].items():
        if init == False:
          if t1 != k:
            print "files[each].keys()[0] is not the first of items()"
            break;
          init=True
        elif k < t1:
          print "sorting is useless.", k, '<', t1, "shouldn't happen"
          break

  count=0
  begtime=files.values()[0].keys()[0]
  for each,truth in files.items():
    k = truth.keys()[0]
    if k != begtime:
      count+=1
      print k, "!=", begtime 
  print "there are",count,"differences."

