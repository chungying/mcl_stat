import numpy
from bisect import bisect_left
from math import sqrt, pi, cos, sin, atan2
from tf.transformations import euler_from_quaternion as q2e
from tf.transformations import quaternion_from_euler as e2q

def angleStat(angs):
  #TODO 
  s = 0.0
  c = 0.0
  for ang in angs:
    s += sin(ang)
    c += cos(ang)

def qm(q1, q2):
  "quaternion multiplication"
  return numpy.array([
                     q1[0] * q2[3] + q1[1] * q2[2] - q1[2] * q2[1] + q1[3] * q2[0], #x
                    -q1[0] * q2[2] + q1[1] * q2[3] + q1[2] * q2[0] + q1[3] * q2[1], #y
                     q1[0] * q2[1] - q1[1] * q2[0] + q1[2] * q2[3] + q1[3] * q2[2], #z
                    -q1[0] * q2[0] - q1[1] * q2[1] - q1[2] * q2[2] + q1[3] * q2[3] ],dtype=numpy.float64)
def conj(q):
  "conjugate quaternion"
  id4 = numpy.identity(4)
  id4 *= -1
  id4[3,3] *= -1
  return id4.dot(q)

conjugate = numpy.array(
[[-1.0, 0.0, 0.0, 0.0],#x
 [0.0, -1.0, 0.0, 0.0],#y
 [0.0, 0.0, -1.0, 0.0],#z
 [0.0, 0.0, 0.0, 1.0]] #w
,dtype=numpy.float64)

def angDiff(q1, q2):
  "difference angle between two quaternions"
  #conjugate q2
  invq2 = conj(q2)
  return qm(q1, invq2)

def ori2arr(ori):
  return numpy.array([ori.x, ori.y, ori.z, ori.w])

def ori2heading(ori):
  '''
  ori is _geometry_msgs__Quaternion type
  returns radian of yaw in the interval of [-pi, pi]
  '''
  ang = q2e(ori2arr(ori))[2]
  return atan2(sin(ang), cos(ang))

def msgErr(tpose, gpose):
  diff_q = angDiff(ori2arr(tpose.orientation), ori2arr(gpose.orientation))
  diff_e = q2e(diff_q)#note that diff_a is 3-d vector and only z euler angle is needed
  diff_d = posDiff(tpose.position, gpose.position)
  return (diff_d, abs(diff_e[2]))

def posDiff(p1, p2):
  return sqrt((p1.x - p2.x)*(p1.x - p2.x) + (p1.y - p2.y)*(p1.y - p2.y))

def ifSucc(truthpose, guesspose, thres_d = 2, thres_a = pi*15/180):
  "if guess is close to truth"
  diff_d, diff_a = msgErr(truthpose, guesspose)
  status = diff_d < thres_d and diff_a < thres_a
  return (status, diff_d, diff_a)

def takeClosestIdx(myList, myNumber):
    """
    Assumes myList is sorted. Returns the idx of the closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
      return pos
    if pos == len(myList):
      return pos
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
      return pos#after
    else:
      return pos-1#before
    
def takeClosest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
       return after
    else:
       return before
