#! /usr/bin/env python
"""
This python script filters out messages from /tf and /p3dx/base_pose_ground_truth and resets their timestamps.
e.g. python ground_truth.py INPUT.bag OUTPUT.bag
"""
import sys
import mcl_stat.plotutil as pu
import mcl_stat.ioutil as iu
import matplotlib.pyplot as plt
import rosbag
import geometry_msgs.msg
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage

def msg2tf(msg):
  t = TransformStamped()
  t.header.frame_id = msg.header.frame_id
  t.header.stamp = msg.header.stamp
  t.child_frame_id = 'ground_truth'
  t.transform.translation.x = msg.pose.pose.position.x
  t.transform.translation.y = msg.pose.pose.position.y
  t.transform.translation.z = msg.pose.pose.position.z
  t.transform.rotation.x = msg.pose.pose.orientation.x
  t.transform.rotation.y = msg.pose.pose.orientation.y
  t.transform.rotation.z = msg.pose.pose.orientation.z
  t.transform.rotation.w = msg.pose.pose.orientation.w
  return TFMessage([t])


def main(inputname='input.bag', outputname='output.bag'):
  print "processing", inputname, "and", outputname
  with rosbag.Bag(outputname, 'w') as outbag:
    for topic, msg, t in rosbag.Bag(inputname).read_messages():
      # This also replaces tf timestamps under the assumption 
      # that all transforms in the message share the same timestamp
      if topic == "/tf" and msg.transforms:
        outbag.write(topic, msg, msg.transforms[0].header.stamp)
      else:
        if topic == '/p3dx/base_pose_ground_truth':
          
          outbag.write("/tf", msg2tf(msg), msg.header.stamp if msg._has_header else t)
        outbag.write(topic, msg, msg.header.stamp if msg._has_header else t)


if __name__=='__main__':
  main(sys.argv[1], sys.argv[2])
