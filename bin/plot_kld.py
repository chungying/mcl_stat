#! /usr/bin/env python
#TODO an example for reading multiple kld_output_name
import sys
import os
import pickle
import mcl_stat.plotutil as pu
import argparse
from collections import OrderedDict as od

def main():
  pkl_files = []
  dic={'mcl':{},'amcl':{},'mixmcl':{},'mcmcl':{}}
  odic=od()
  print sys.argv[1]
  with open(sys.argv[1],'r') as openfile:
    for filename in openfile:
      pkl_files.append(filename[:-1])
  print "Now we have", len(pkl_files),"files"
  
  #pkl_names = map(lambda pkl_file: os.path.basename(pkl_file).split('.')[0], pkl_files) #extract each filename from pkl_files
  for i in pkl_files:
    sp=i.split('_')
    dic[sp[0]][sp[1]]=i
  
  odic['mcl']=dic['mcl']
  odic['amcl']=dic['amcl']
  odic['mixmcl']=dic['mixmcl']
  odic['mcmcl']=dic['mcmcl']
  filenames=[]
  for k,v in odic.items():
    filenames.extend(v.values())
  
  pkl_input = map(lambda pkl_file: open(pkl_file), filenames) #open each pkl_file of filenames
  dict_list = map(lambda input: pickle.load(input), pkl_input)#load each input of pkl_input
  #for i in range(4): pu.plot_same_mcl_errorbar(i, dict_list)
  #for i in range(5): pu.plot_same_mp_errorbar(i, dict_list) #TODO uncomment
  for i in range(5): pu.plot_same_timestep_kld_violin(i, dict_list)

if __name__ == '__main__':
  main()

