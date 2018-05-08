from .MclMap import *
from math import pi, floor

# Convert from map index to world coords
def map_wxgx(mmap, i):
  return float(mmap.origin_x + ((i) - mmap.size_x / 2) * mmap.scale)

def map_wygy(mmap, j):
  return float(mmap.origin_y + ((j) - mmap.size_y / 2) * mmap.scale)

# Convert from world coords to map coords
def map_gxwx(mmap, x):
  return int(floor((x - mmap.origin_x) / mmap.scale + 0.5) + mmap.size_x / 2)

def map_gywy(mmap, y):
  return int(floor((y - mmap.origin_y) / mmap.scale + 0.5) + mmap.size_y / 2)

#convert from angle to index
#def ANG2IDX(ang, ares):
#  return int(floor( (ang + pi) / pi * (180.0/ares) + 0.5 ))
#
##convert from index to angle
#def IDX2ANG(idx, ares):
#  return float(-pi+((idx*ares)/180.0)*pi)

