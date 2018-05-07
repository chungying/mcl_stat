import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import re
from collections import OrderedDict
import os

plt.rc('text', usetex=True)
plt.rc('font',**{'family':'serif','serif':['Palatino']})
#plt.rc('font',**{'family':'serif','serif':['Helvetica']})

def kword(obj):
  if obj['mclpkg']=='amcl': return 'o-'
  elif obj['mclpkg']=='mixmcl': return '*--'
  elif obj['mclpkg']=='mcmcl': return '^-.'
  elif obj['mclpkg']=='mcl': return 'v:'
  else: return 'P-'

def plotting(objs, dims, tarvar='mp', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdri=['ri1','ri2'], captype='minmax', saveflag=False, dirpath='.'):
  "tarvar is target variable. It could be mp, ita, and gamma."
  allLines = {}
  kwords = {}
  errs = {}
  yerrdict = {}
  yerrs = {}
  #TODO if tarvar == 'gamma'
  #alwdmcl has to be ['mcmcl']
  #TODO if tarvar == 'ita'
  #alwdmcl has to at least one of  ['mcmcl', 'mixmcl']
  for objk, obj in objs.iteritems():
    #objk='mcl_mpXXXXX_riX_itaXXXX_gammaX
    if obj['mclpkg'] not in alwdmcl:
      continue
    if 'ri{}'.format(obj['ri']) not in alwdri:
      continue
    linek = None
    valuex = None
    targetstr = tarvar+'{}'.format(obj[tarvar])
    for valuestr, count in dims[tarvar].iteritems():
      if valuestr == targetstr:
        ss = []
        for s in objk.split('_'):
          word = s.replace(valuestr,'')
          ss.append(word)
        linek = '_'.join(filter(None,ss))
        valuex = float(valuestr.split(tarvar)[-1])
        break
    if linek not in allLines:
      allLines[linek] = {}
      errs[linek] = {}
      yerrdict[linek] = {}
      kwords[linek] = kword(obj)
    #TODO parameterize list_final_ed and list_rmse
    #allLines[linek][valuex] = np.mean(obj['list_rmse'])
    #errs[linek][valuex] = np.std(obj['list_rmse'])
    meanvalue = np.mean(obj['list_final_ed'])
    allLines[linek][valuex] = meanvalue
    errs[linek][valuex] = np.std(obj['list_final_ed'])
    if valuex not in yerrdict[linek]:
      yerrdict[linek][valuex] = [[],[]]
    yerrdict[linek][valuex][0].append(meanvalue - np.min(obj['list_final_ed']))
    yerrdict[linek][valuex][1].append(np.max(obj['list_final_ed']) - meanvalue)

  allLines = OrderedDict(sorted(allLines.items(), key=lambda t: t[0]))
  for lk, ltuple in allLines.iteritems():
    allLines[lk] = OrderedDict(sorted(ltuple.items(), key=lambda t: t[0]))
    errs[lk] = OrderedDict(sorted(errs[lk].items(), key=lambda t: t[0]))
    yerrdict[lk] = OrderedDict(sorted(yerrdict[lk].items(), key=lambda t: t[0]))
    yerrs[lk] = [[],[]]
    for key, tupvalue in yerrdict[lk].iteritems():
      yerrs[lk][0].append(tupvalue[0][0])
      yerrs[lk][1].append(tupvalue[1][0])
  fig = plt.figure(figsize=(18,8))
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
  axes = plt.subplot(gs[0])
  xlbl = None
  if tarvar == 'mp': 
    xlbl = r'\textrm{maximum number of particles}'
  if tarvar == 'ita': 
    xlbl = r'\textrm{dual normalizer }\eta'
    axes.set_xscale('log',nonposx='clip')
  if tarvar == 'gamma': 
    xlbl = r'\textrm{DEMC step size gamma}'
  plt.xlabel('${}$'.format(xlbl))
  plt.ylabel(r'\textrm{RMS position error (meter)}')
  if captype == 'std':
    title = r'\textrm{RMS position error wrt }' + xlbl + r'\textrm{ with standard deviation cap}'
  elif captype == 'minmax':
    title = r'\textrm{RMS position error wrt }' + xlbl + r'\textrm{ with minimum and maximum caps}'

  plt.title('${}$'.format(title))
  for k,v in allLines.items():
    legend = r'{}'.format(k.replace('_',' '))
    if captype == 'std':
      plt.errorbar(v.keys(), v.values(), yerr=errs[k].values(), fmt=kwords[k], label=legend, capsize=10, capthick=2, linewidth=2, markersize=10)
    elif captype == 'minmax':
      plt.errorbar(v.keys(), v.values(), yerr=yerrs[k], fmt=kwords[k], label=legend, capsize=10, capthick=2, linewidth=2, markersize=10)
    else:
      plt.errorbar(v.keys(), v.values(), yerr=errs[k].values(), fmt=kwords[k], label=legend, capsize=10, capthick=2, linewidth=2, markersize=10)
      captype = 'std'
  axes.autoscale(enable=True,tight=False)
  #xmin, xmax = plt.xlim()
  #plt.xlim(xmin, xmax+500)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  plt.show()
  if saveflag:
    namelist = []
    namelist.extend(alwdmcl)
    namelist.extend(map(str, alwdri))
    namelist.append(captype)
    filename = '_'.join(namelist)
    filepath = '{}/{}.png'.format(dirpath,filename)
    plt.savefig(filepath, format='png')
    print 'saving file',filepath
  plt.close(fig)
  return fig

def rad2key(radtup):
  return 'distrad{:.0f}_anglrad{:.0f}'.format(radtup[0], radtup[1])

def plotcloudstat(objs, saveflag=False, dirpath='.', captype='minmax', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdmp=None, alwdrad=None, imgformat='eps'):
  fig = plt.figure(figsize=(18,8))
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
  plt.subplot(gs[0])
  if captype == 'minmax':
    yer = lambda matrix: matrix[[3,4],:]
    title = r'mean deprivation degree wrt time with minimum and maximum caps'
  else:
    yer = lambda matrix: matrix[2,:]
    title = r'mean deprivation degree wrt time with standard deviation cap'
  plt.title(title)
  #check data exist
  for objk, obj in objs.items():
    if 'cloudstatmat' not in obj:
      print objk,'is incomplete. Skipped'
      continue
    if obj['mclpkg'] not in alwdmcl:
      continue
    if alwdmp is not None and obj['mp'] not in alwdmp:
      continue
    if alwdrad is not None and obj['radius_tup'] not in alwdrad:
      continue
    mat = obj['cloudstatmat']
    legend = r'{}'.format(objk.replace('_',' '))
    plt.errorbar(mat[0,:], mat[1,:], yerr=yer(mat), fmt=kword(obj), label=legend, capsize=10, capthick=2, linewidth=2, markersize=10)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  if saveflag:
    namelist = []
    namelist.extend(alwdmcl)
    namelist.extend(map(str, alwdmp))
    namelist.extend(map(rad2key, alwdrad))
    namelist.append(captype)
    filename = '_'.join(namelist)
    filepath = '{}/{}.{}'.format(dirpath,filename, imgformat)
    plt.savefig(filepath, format=imgformat)
  else:
    plt.show()
  plt.close(fig)
  return fig

def ploterrtime(objs, saveflag=False, dirpath='.', captype='minmax', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdmp=[10, 100, 1000, 10000]):
  "captype could be minmax or std."
  fig = plt.figure(figsize=(18,8))
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
  plt.subplot(gs[0])
  plt.xlabel(r'\textrm{time (second)}')
  if captype == 'minmax':
    yer = lambda matrix: matrix[[3,4],:]
    title = r'position error wrt time with minimum and maximum caps'
  else:
    yer = lambda matrix: matrix[2,:]
    title = r'position error wrt time with standard deviation cap'
  plt.title(title)
  errtype = None
  for objk, obj in objs.iteritems():
    if obj['mclpkg'] not in alwdmcl or obj['mp'] not in alwdmp or obj['ri'] != 1:
      continue
    mat = obj['list_errtimestatmat']
    if mat.shape[0] == 5:
      err = lambda matrix: matrix[1,:]#ME
      errtype = r'\textrm{mean position error (meter)}'
    elif mat.shape[0] == 6:
      err = lambda matrix: matrix[5,:]#RMSE
      errtype = r'\textrm{RMS position error (meter)}'
    legend = r'{}'.format(objk.replace('_',' '))
    #            timestep, mean err       
    #            timestep, RMS err       
    plt.errorbar(mat[0,:], mat[1,:], yerr=yer(mat), fmt=kword(obj), label=legend, capsize=10, capthick=2, linewidth=2, markersize=10)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  plt.ylabel(errtype)
  if saveflag:
    namelist = []
    namelist.extend(alwdmcl)
    namelist.extend(map(str, alwdmp))
    namelist.append(captype)
    filename = '_'.join(namelist)
    filepath = '{}/{}.png'.format(dirpath,filename)
    plt.savefig(filepath, format='png')
  else:
    plt.show()
  return fig

ROWS = 2
COLS = 4
def ploteach(fileidx, imgname, timestamp, errmat, plotmat, good_numbers, totals):
  # figure 1: trajectory
  # figure 2: position error
  # figure 3: heading error
  # figure 4: x wrt time
  # figure 5: y wrt time
  # figure 6: heading wrt time
  #ploting figures
  fig = plt.figure(fileidx)
  fig.subplots_adjust(hspace=0.4)
  fig.subplots_adjust(wspace=0.3)
  fig.set_size_inches(16, 10, forward=True)
  ax1 = plt.subplot(ROWS,COLS,1)
  ax1.set_title(r'\textrm{trajectory}')
  ax1.set_xlabel(r'\textrm{x}')
  ax1.set_ylabel(r'\textrm{y}')
  ax1.plot(plotmat[0,:],plotmat[1,:])
  ax1.plot(plotmat[3,:],plotmat[4,:])

  ax2 = plt.subplot(ROWS,COLS,2)
  ax2.set_title(r'\textrm{position error}')
  ax2.set_xlabel(r'\textrm{time (second)}')
  ax2.set_ylabel(r'\textrm{meter}')
  ax2.plot(timestamp, errmat[0,:])

  ax3 = plt.subplot(ROWS,COLS,3)
  ax3.set_title(r'\textrm{heading error}')
  ax3.set_xlabel(r'\textrm{time (second)}')
  ax3.set_ylabel(r'\textrm{rad}')
  ax3.plot(timestamp, errmat[1,:])

  ax4 = plt.subplot(ROWS,COLS,4)
  ax4.set_title(r'\textrm{x wrt time}')
  ax4.set_xlabel(r'\textrm{time (second)}')
  ax4.set_ylabel(r'\textrm{meter}')
  ax4.set_ylim(-28, 23)
  ax4.plot(timestamp, plotmat[0,:], color='blue')
  ax4.plot(timestamp, plotmat[3,:], color='red')
  ax4.plot(timestamp, plotmat[6,:], timestamp, plotmat[7,:], linestyle='None')
  ax4.fill_between(timestamp, plotmat[3,:], plotmat[6,:], where=[True]*len(timestamp), facecolor=(0.5, 0, 0, 0.1), linestyle='-.', linewidth=0.5, color='red')
  ax4.fill_between(timestamp, plotmat[3,:], plotmat[7,:], where=[True]*len(timestamp), facecolor=(0.5, 0, 0, 0.1), linestyle='-.', linewidth=0.5, color='red')

  ax5 = plt.subplot(ROWS,COLS,5)
  ax5.set_title(r'\textrm{y wrt time}')
  ax5.set_xlabel(r'\textrm{time (second)}')
  ax5.set_ylabel(r'\textrm{meter}')
  ax5.set_ylim(-11, 39)
  ax5.plot(timestamp, plotmat[1,:], color='blue')
  ax5.plot(timestamp, plotmat[4,:], color='red')
  ax5.plot(timestamp, plotmat[8,:], timestamp, plotmat[9,:], linestyle='None')
  ax5.fill_between(timestamp, plotmat[4,:], plotmat[8,:], where=[True]*len(timestamp), facecolor=(0.5, 0, 0, 0.1), linestyle='-.', linewidth=0.5, color='red')
  ax5.fill_between(timestamp, plotmat[4,:], plotmat[9,:], where=[True]*len(timestamp), facecolor=(0.5, 0, 0, 0.1), linestyle='-.', linewidth=0.5, color='red')

  ax6 = plt.subplot(ROWS,COLS,6)
  ax6.set_title(r'\textrm{heading wrt time}')
  ax6.set_xlabel(r'\textrm{time (second)}')
  ax6.set_ylabel(r'\textrm{rad}')
  ax6.set_ylim(-3.15, 3.15)
  ax6.plot(timestamp, plotmat[2,:], color='blue')
  ax6.plot(timestamp, plotmat[5,:], color='red')
  ax6.plot(timestamp, plotmat[10,:], timestamp, plotmat[11,:], linestyle='None')
  ax6.fill_between(timestamp, plotmat[5,:], plotmat[11,:], where=[True]*len(timestamp), facecolor=(0.5, 0, 0, 0.1), linestyle='-.', linewidth=0.5, color='red')
  ax6.fill_between(timestamp, plotmat[5,:], plotmat[11,:], where=[True]*len(timestamp), facecolor=(0.5, 0, 0, 0.1), linestyle='-.', linewidth=0.5, color='red')

  ax7 = plt.subplot(ROWS,COLS,7)
  ax7.set_title(r'\textrm{number of good hypotheses}')
  ax7.set_xlabel(r'\textrm{time (second)}')
  ax7.plot(timestamp, good_numbers)

  ax8 = plt.subplot(ROWS,COLS,8)
  ax8.set_title(r'\textrm{degree of good hypotheses}')
  ax8.set_xlabel(r'\textrm{time (second)}')
  ax8.plot(timestamp, np.divide(good_numbers,totals,dtype=float))

  plt.draw()
  #saving figures
  title = ' '.join(imgname.split('_')) 
  plt.suptitle(r'\textrm{{{}}}'.format(title), fontsize=16)
  filename = imgname + ".png"
  print "saving to ", filename
  #TODO save flag
  plt.savefig(filename)
  #TODO show flag
  #plt.show()

def plot_kld(lines, timestamps = None, name='plotutil_plot_kld_test', save_flag = False, show_flag = False, abs_output_dir = None):
  #TODO formatting and font
  fig = plt.figure(figsize=(18,8))
  fig_name = name.replace('_',' ')
  fig.suptitle('kld of {}'.format( fig_name))
  for line_idx in range(lines.shape[0]):
    if timestamps is None:
      plt.plot(range(len(lines[line_idx, :])), lines[line_idx, :])
    else:
      plt.plot(timestamps, lines[line_idx, :])
  if save_flag:
    output_dir = abs_output_dir if abs_output_dir is not None else './'
    plt.savefig('{}/{}_kld.png'.format(output_dir, name))
  if show_flag:
    plt.show()
  plt.close(fig)


#TODO implement me!
#xlabel
#ylabel
#suptitle
def plot_same_mcl_errorbar(start_idx, pkl_dict):
  #start_idx between 0~3
  #0:amcl
  #1:mcl
  #2:mcmcl
  #3:mixmcl
  #sort pkl data according to mcl_pkg, mp, ri
  fig = plt.figure(figsize=(18,8))
  plt.subplot(gridspec.GridSpec(1,2,width_ratios=[3,1])[0])
  plt.ylabel(r'\textrm{kld}')
  plt.xlabel(r'\textrm{timestamp index}')
  plt.title(r'\textrm{KLD wrt time with maximum and minimum caps}')
  for idx in range(start_idx*5,start_idx*5+5,1):
    timestamps = pkl_dict[idx]['timestamps']
    legend = os.path.basename(pkl_dict[idx]['bag_files_dir']).replace('_',' ')
    average = pkl_dict[idx]['bag_lines'].mean(axis=0).flatten()
    maximum = pkl_dict[idx]['bag_lines'].max(axis=0).flatten()
    minimum = pkl_dict[idx]['bag_lines'].min(axis=0).flatten()
    plt.errorbar(range(average.shape[0]),average, yerr=[average-minimum, maximum-average], label=legend, capthick=2,linewidth=2,markersize=10,elinewidth=0.01)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  plt.show()

def plot_same_mp_errorbar(start_idx, pkl_dict):
  #start_idx between 0~4
  #0:mp1000
  #1:mp2000
  #2:mp3000
  #3:mp4000
  #4:mp5000
  #sort pkl data according to mcl_pkg, mp, ri
  fig = plt.figure(figsize=(18,8))
  plt.subplot(gridspec.GridSpec(1,2,width_ratios=[3,1])[0])
  plt.ylabel(r'\textrm{kld}')
  plt.xlabel(r'\textrm{timestamp index}')
  plt.title(r'\textrm{KLD wrt time with maximum and minimum caps}')
  for idx in range(start_idx, 20, 5):
    timestamps = pkl_dict[idx]['timestamps']
    legend = os.path.basename(pkl_dict[idx]['bag_files_dir']).replace('_',' ')
    average = pkl_dict[idx]['bag_lines'].mean(axis=0).flatten()
    maximum = pkl_dict[idx]['bag_lines'].max(axis=0).flatten()
    minimum = pkl_dict[idx]['bag_lines'].min(axis=0).flatten()
    plt.errorbar(range(average.shape[0]),average, yerr=[average-minimum, maximum-average], label=legend, capthick=2,linewidth=2,markersize=10,elinewidth=0.01)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  plt.show()

