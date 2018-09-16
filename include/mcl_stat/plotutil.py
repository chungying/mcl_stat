import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import re
from collections import OrderedDict
import os

plt.rc('text', usetex=True)
#plt.rc('font',**{'family':'serif','serif':['Palatino']})
plt.rc('font',**{'family':'serif','serif':['Helvetica']})
labelsize=16
titlesize=18
figuresize=(8.27,5.5)#(8.27,11.69)
def kword(obj):
  if obj['mclpkg']=='mcl': return 'v:'
  elif obj['mclpkg']=='amcl': return 'o-'
  elif obj['mclpkg']=='mixmcl': return '*--'
  elif obj['mclpkg']=='mcmcl': return '^-.'
  else: return 'P-'

def mcl2order(obj):
  if obj['mclpkg']=='mcl': return 1
  elif obj['mclpkg']=='amcl': return 2
  elif obj['mclpkg']=='mixmcl': return 3
  elif obj['mclpkg']=='mcmcl': return 4
  else: return 'UNKNOWN'
def mcl2name(obj):
  if obj['mclpkg']=='mcl': return 'MCL'
  elif obj['mclpkg']=='amcl': return 'AMCL'
  elif obj['mclpkg']=='mixmcl': return 'MIXMCL'
  elif obj['mclpkg']=='mcmcl': return 'DEMCMCL'
  else: return 'UNKNOWN'

def mcl2color(obj):
  if obj['mclpkg']=='mcl': return '#00ff00'
  elif obj['mclpkg']=='amcl': return '#ff0000'
  elif obj['mclpkg']=='mixmcl': return '#ff00ff'
  elif obj['mclpkg']=='mcmcl': return '#0000ff'
  else: return '#000000'

def plotting(objs, dims, tarvar='mp', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdri=['ri1','ri2'], captype='minmax', saveflag=False, dirpath='.'):
  """
  This plots the RMS position error versus target variable.
  tarvar is target variable which could be mp, ita, and gamma.
  """
  allLines = {}
  kwords = {}
  kcolors = {}
  klegends = {}
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
      kcolors[linek] = mcl2color(obj)
      if tarvar == 'mp': 
        klegends[linek]=mcl2name(obj)
      if tarvar == 'ita': 
        klegends[linek]=linek.replace('_',' ')
      if tarvar == 'gamma': 
        klegends[linek]=linek.replace('_',' ')


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
  #start plotting
  #fig = plt.figure(figsize=(18,8))
  fig = plt.figure(figsize=figuresize)
  # generate the string of x label
  xlbl = None
  if tarvar == 'mp': 
    xlbl = r'\textrm{Maximum number of particles}'
  if tarvar == 'ita': 
    xlbl = r'\textrm{Dual normalizer }\eta'
  if tarvar == 'gamma': 
    xlbl = r'\textrm{DEMC step size gamma}'

  # generate title string and ratio the plot
  if captype == 'std':
    title = r'\textrm{RMS position error wrt }' + xlbl + r'\textrm{ with standard deviation cap}'
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
    axes = plt.subplot(gs[0])
  elif captype == 'minmax':
    title = r'\textrm{RMS position error wrt }' + xlbl + r'\textrm{ with minimum and maximum caps}'
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
    axes = plt.subplot(gs[0])
    if tarvar == 'ita': 
      axes.set_xscale('log',nonposx='clip')
  else:
    title = r'\textrm{RMS position error wrt }' + xlbl

  #XXX
  #plt.title('${}$'.format(title),fontsize=titlesize)
  plt.xlabel('${}$'.format(xlbl),fontsize=labelsize)
  plt.ylabel(r'\textrm{RMS position error}',fontsize=labelsize)

  # start plotting lines
  for k,v in allLines.items():
    #legend = r'{}'.format(k.replace('_',' '))
    if captype == 'std':
      plt.errorbar(v.keys(), v.values(), yerr=errs[k].values(), fmt=kwords[k], label=klegends[k], capsize=10, capthick=2, linewidth=2, markersize=10)
      plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
    elif captype == 'minmax':
      plt.errorbar(v.keys(), v.values(), yerr=yerrs[k], fmt=kwords[k], label=klegends[k], capsize=10, capthick=2, linewidth=2, markersize=10)
      plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
    else:
      plt.plot(v.keys(), v.values(), kwords[k], color=kcolors[k], label=klegends[k], linewidth=1, markersize=5)
      plt.legend()

  plt.autoscale(enable=True,tight=False)
  if captype == 'std':
    plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  elif captype == 'minmax':
    plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  else:
    #plt.legend(loc=2, bbox_to_anchor=(1.0, 1), borderaxespad=0.)
    plt.legend(fontsize=labelsize)

  if saveflag:
    namelist = []
    namelist.extend(alwdmcl)
    namelist.extend(map(str, alwdri))
    namelist.append(captype)
    filename = '_'.join(namelist)
    filepath = '{}/{}.pdf'.format(dirpath,filename)
    plt.savefig(filepath, format='pdf')
    print 'saving file',filepath
  else:
    plt.show()
  plt.close(fig)
  return fig

def rad2key(radtup):
  return 'distrad{:.0f}_anglrad{:.0f}'.format(radtup[0], radtup[1])

def plotcloudstat(objs, saveflag=False, dirpath='.', captype='minmax', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdmp=None, alwdrad=None, imgformat='pdf'):
  """
  This plots deprivation degree figure or health rate figure.
  """
  #fig = plt.figure(figsize=(18,8))
  fig = plt.figure(figsize=figuresize)
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

def plot_rms_position_error(objs, saveflag=False, dirpath='.', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdmp=[1000, 2000, 3000, 4000, 5000]):
  """
  This plots the RMS error figure against time steps.
  """
  fig = plt.figure(figsize=figuresize)
  #gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
  #plt.subplot(gs[0])
  handle_dic={}
  legend_dic={}
  for objk, obj in objs.iteritems():
    if obj['mclpkg'] not in alwdmcl or obj['mp'] not in alwdmp or obj['ri'] != 1:
      continue
    #legend = r'{}'.format(objk.replace('_',' '))
    legend = ''
    if len(alwdmcl)>1:
      legend = legend + '{}'.format(mcl2name(obj))
    if len(alwdmp)>1:
      legend = legend + '{}'.format(obj['mp'])
    mat = obj['list_errtimestatmat']
    #timestep, RMS error
    key='{}_{}'.format(mcl2order(obj),obj['mp'])
    #handle_dic[key]=plt.plot(mat[0,:], np.sqrt(mat[5,:]), kword(obj), color=mcl2color(obj), label=legend, linewidth=1, markersize=5)[0]
    handle_dic[key]=plt.plot(mat[0,:], np.sqrt(mat[5,:]), label=legend, linewidth=1, markersize=5)[0]
    legend_dic[key]=legend
  plt.xlabel('Time (second)',fontsize=labelsize)
  plt.ylabel('RMS position error (metre)',fontsize=labelsize)
  #plt.title('RMS position error wrt time')
  #plt.legend(loc=2, bbox_to_anchor=(1.0, 1), borderaxespad=0.)
  handle_od=OrderedDict(sorted(handle_dic.items(), key=lambda k:k[0]))
  legend_od=OrderedDict(sorted(legend_dic.items(), key=lambda k:k[0]))
  print type(handle_od.values()[0])
  print legend_od.values()[0],type(legend_od.values()[0])
  plt.legend(handle_od.values(),legend_od.values())
  if saveflag:
    namelist = []
    namelist.extend(alwdmcl)
    namelist.extend(map(str, alwdmp))
    filename = '_'.join(namelist)
    filepath = '{}/{}.pdf'.format(dirpath,filename)
    plt.savefig(filepath, format='pdf')
  else:
    plt.show()
  return fig

def ploterrtime(objs, saveflag=False, dirpath='.', captype='minmax', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdmp=[10, 100, 1000, 10000], errortype='rms'):
  """
  This plots the RMS error figure against time steps.
  captype could be minmax or std.
  """
  fig = plt.figure(figsize=figuresize)
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
  plt.subplot(gs[0])
  errtype = None
  for objk, obj in objs.iteritems():
    legend = r'{}'.format(objk.replace('_',' '))
    if obj['mclpkg'] not in alwdmcl or obj['mp'] not in alwdmp or obj['ri'] != 1:
      continue
    mat = obj['list_errtimestatmat']
    #if mat.shape[0] == 5:
    if errortype == 'mean':
      #timestep, mean error
      plt.errorbar(mat[0,:], mat[1,:], yerr=yer(mat), fmt=kword(obj), label=legend, capsize=10, capthick=2, linewidth=2, markersize=10)
      errtype = r'mean position error (metre)'
      if captype == 'minmax':
        yer = lambda matrix: matrix[[3,4],:]
        title = r'position error wrt time with minimum and maximum caps'
      else:
        yer = lambda matrix: matrix[2,:]
        title = r'position error wrt time with standard deviation cap'
    elif errortype == 'rms':
      #timestep, RMS error
      plt.errorbar(mat[0,:], np.sqrt(mat[5,:]), fmt=kword(obj), label=legend, capsize=10, capthick=2, linewidth=2, markersize=10)
      errtype = 'RMS position error (metre)'
      title = 'RMS position error wrt time'
  plt.xlabel('time (second)',fontsize=labelsize)
  plt.ylabel(errtype,fontsize=labelsize)
  plt.title(title)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
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
  """
  Save figure
  This function plots 6 figures in one image.
  figure 1: trajectory
  figure 2: position error
  figure 3: heading error
  figure 4: x wrt time
  figure 5: y wrt time
  figure 6: heading wrt time
  """
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
  fig = plt.figure(figsize=figuresize)
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
#         green     red       purple    blue
lcolors=('#00ff00','#ff0000','#ff00ff','#0000ff','#00ffff')
hcolors=('#00aa00','#aa0000','#aa00aa','#0000aa')
suptitles_mcl=[
'MCL',#mcl 
'AMCL',#amcl 
'MIXMCL',#mixmcl
'DEMCMCL'#demcmcl
]
suptitles_mp=[
'1000 Maximum Particles',
'2000 Maximum Particles',
'3000 Maximum Particles',
'4000 Maximum Particles',
'5000 Maximum Particles'
]

r=('#ff0000','#ff2222')
b=('#1f77b4','#1f77b4')
g=('#1f77b4','#1f77b4')
import matplotlib.colors as cl
def plot_same_mcl_errorbar(start_idx, pkl_dict):
  #start_idx between 0~3
  #0:amcl
  #1:mcl
  #2:mcmcl
  #3:mixmcl
  #sort pkl data according to mcl_pkg, mp, ri
  indices=np.array([0,20,40,-1])
  fig, axes = plt.subplots(nrows=4, ncols=1, figsize=figuresize)
  for i,idx in enumerate(range(start_idx*5,start_idx*5+4,1)):#XXX discard mp5000
    y=i%4
    x=(i-y)/1
    timestep=np.arange(1,pkl_dict[idx]['bag_lines'].shape[2]+1)
    #parts = axes[i].violinplot(pkl_dict[idx]['bag_lines'][:,0,:],timestep,showmeans=False,showmedians=True,widths=3,bw_method=0.1)
    parts = axes[i].violinplot(pkl_dict[idx]['bag_lines'][:,0,indices],timestep[indices],showmeans=True,showmedians=True,widths=3,bw_method=0.5)
    # Make all the violin statistics marks red:
    for vp in parts['bodies']:
      vp.set_facecolor(lcolors[start_idx])
      print 'color:',vp.get_facecolor()
    for partname in ('cbars','cmins','cmaxes','cmedians'):
      parts[partname].set_edgecolor(lcolors[start_idx])
    legend = os.path.basename(pkl_dict[idx]['bag_files_dir']).replace('_',' ')
    axes[i].set_title(suptitles_mp[i], fontsize=18)
  for ax in axes.flatten():
    ax.grid(linestyle='-')
    ax.set_ylabel(r'$\mathrm{D_{KL}}$', fontsize=16)
    ax.set_xlim([0,70])
    ax.set_ylim([0,35])
  axes.flatten()[-1].set_xlabel("time step index", fontsize=16)
  #fig.suptitle("Violin Plotting for KLD wrt Time Step Index", fontsize=22)
  fig.suptitle(suptitles_mcl[start_idx], fontsize=20)
  fig.subplots_adjust(hspace=0.4)
  #plt.show()
  plt.savefig('{}_kld.pdf'.format(suptitles_mcl[start_idx].replace(' ','_')), format='pdf')
  

def plot_same_mp_errorbar(start_idx, pkl_dict):
  """
  This plots kld distance against time index.
  """
  #start_idx between 0~4
  #0:mp1000
  #1:mp2000
  #2:mp3000
  #3:mp4000
  #4:mp5000
  #sort pkl data according to mcl_pkg, mp, ri
  indices=np.array([0,20,40,-1])
  fig, axes = plt.subplots(nrows=4, ncols=1, figsize=figuresize)
  for i,idx in enumerate(range(start_idx, 20, 5)):
    y=i%4
    x=(i-y)/1
    timestep=np.arange(1,pkl_dict[idx]['bag_lines'].shape[2]+1)
    #parts = axes[i].violinplot(pkl_dict[idx]['bag_lines'][:,0,:],timestep,showmeans=False,showmedians=True,widths=3,bw_method=0.1)
    parts = axes[i].violinplot(pkl_dict[idx]['bag_lines'][:,0,indices],timestep[indices],showmeans=True,showmedians=True,widths=3,bw_method=0.5)

    # Make all the violin statistics marks red:
    for partname in ('cbars','cmins','cmaxes','cmedians'):
      parts[partname].set_edgecolor(lcolors[i])
    for vp in parts['bodies']:
      vp.set_facecolor(lcolors[i])
    legend = os.path.basename(pkl_dict[idx]['bag_files_dir']).replace('_',' ')
    axes[i].set_title(suptitles_mcl[i], fontsize=18)
  for ax in axes.flatten():
    ax.grid(linestyle='-')
    ax.set_ylabel(r'$\mathrm{D_{KL}}$', fontsize=16)
    ax.set_xlim([0,70])
    ax.set_ylim([0,35])
  axes.flatten()[-1].set_xlabel("time step index", fontsize=16)
  #fig.suptitle("Violin Plotting for KLD wrt Time Step Index", fontsize=22)
  fig.suptitle(suptitles_mp[start_idx], fontsize=20)
  fig.subplots_adjust(hspace=0.4)
  #plt.show()
  plt.savefig('{}_kld.pdf'.format(suptitles_mp[start_idx].replace(' ','_')), format='pdf')

def plot_same_timestep_kld_violin(start_idx,pkl_dict):
#def plot_same_timestep_kld_violin(timesteps, pkl_dict):
  """
  This plots kld distance at TIMESTEPS against different algorithms.
  TIMESTEPS is a list of timesteps.
  """
  #start_idx between 0~4
  #0:mp1000
  #1:mp2000
  #2:mp3000
  #3:mp4000
  #4:mp5000
  #sort pkl data according to mcl_pkg, mp, ri
  timesteps=np.array([0,20,40,67])
  #fig, axes = plt.subplots(nrows=len(timesteps), ncols=1, figsize=(8.27,5.85))
  fig, axes = plt.subplots(nrows=len(timesteps), ncols=1, figsize=figuresize)
  #for each timestep ti
  #for aidx,ti in enumerate(timesteps):
  for ti,ax in enumerate(axes):
    #for each particle number
    for mcl,dict_idx in enumerate(range(start_idx, 20, 5)):
      #parts = axes[ti].violinplot(pkl_dict[dict_idx]['bag_lines'][:,0,ti],aidx,showmeans=True,showmedians=True,widths=3,bw_method=0.5)
      parts = ax.violinplot(pkl_dict[dict_idx]['bag_lines'][:,0,timesteps[ti]],[mcl+1],showmeans=False,showmedians=True,widths=0.5,bw_method=0.5)
      for partname in ('cbars','cmins','cmaxes','cmedians'):
        parts[partname].set_edgecolor(lcolors[mcl])
      for vp in parts['bodies']:
        vp.set_facecolor(lcolors[mcl])
      legend = os.path.basename(pkl_dict[dict_idx]['bag_files_dir']).replace('_',' ')
    ax.set_title('Time step {}'.format(timesteps[ti]), fontsize=titlesize)
    ax.grid(linestyle='-')
    ax.set_ylabel(r'$\mathrm{D_{KL}}$', fontsize=labelsize)
    #ax.set_ylim([0,35])
    #
    ax.get_xaxis().set_tick_params(direction='out')
    ax.get_xaxis().set_ticklabels([])
    ax.xaxis.set_ticks_position('bottom')
    ax.set_xticks(np.arange(1, len(suptitles_mcl) + 1))
    ax.set_xlim(0.25, len(suptitles_mcl) + 0.75)
  axes[-1].set_xticklabels(suptitles_mcl, fontsize=labelsize)
  #axes[-1].set_xlabel('Algorithms', fontsize=16)
    #axes[aidx].set_title('KLD distribution at time step {}'.format(ti), fontsize=18)
    #axes[aidx].grid(linestyle='-')
    #axes[aidx].set_ylabel(r'$\mathrm{D_{KL}}$', fontsize=16)
    #axes[aidx].set_ylim([0,35])
  #axes.flatten()[-1].set_xlabel("time step index", fontsize=16)
  #fig.suptitle("Violin Plotting for KLD wrt Time Step Index", fontsize=22)
  #fig.suptitle(r'Violin plotting of $\mathrm{D_{KL}}$ distributions from algorithms with ' + '{}'.format(suptitles_mp[start_idx]), fontsize=20)
  fig.subplots_adjust(hspace=0.4)
  #plt.show()
  plt.savefig('{}_kld_vs_mcl.pdf'.format(suptitles_mp[start_idx].replace(' ','_')), format='pdf')

def plot_same_timestep_distance_violin(objs,dims,timesteps=[0,20,40,67],mps=[1000,2000,3000,4000,5000]):#,pkl_dict):
  """
  This plots distance error distance at TIMESTEPS against different algorithms.
  TIMESTEPS is a list of timesteps.
  OBJS is a list of dictionary objects.
  A dictionary object contains all of information of a mcl with the same particle number and its distance, angular, mean square errors.
  """
  #start_idx between 0~4
  #0:mp1000
  #1:mp2000
  #2:mp3000
  #3:mp4000
  #4:mp5000
  all_lines = {}#allLines
  kwords = {}
  kcolors = {}
  klegends = {}
  error_dict = {}#errs
  yerrdict = {}
  yerrs = {}
  for mp in alwdmp:
    for obj_key, obj in objs.items():
      linek = obj_key
      valuex = mp
      if linek in all_lines:  
        all_lines[linek] = {}
        error_dict = {}
        kwords[linek] = kword(obj)
        kcolors[linek] = mcl2color(obj)
        klegends[linek] = mcl2name(obj)
    obj['list_final_ed']
