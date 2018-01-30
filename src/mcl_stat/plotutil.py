import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import re
from collections import OrderedDict

def kword(obj):
  if obj['mclpkg']=='amcl': return 'o-'
  elif obj['mclpkg']=='mixmcl': return '*--'
  elif obj['mclpkg']=='mcmcl': return '^-.'
  elif obj['mclpkg']=='mcl': return 'x:'
  else: return 'P-'

def plotting(objs, dims, tarvar='mp', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdri=['ri1','ri2']):
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
      #print obj['mclpkg'], "is not in", alwdmcl
      continue
    if 'ri{}'.format(obj['ri']) not in alwdri:
      #print 'ri{}'.format(obj['ri']), "is not in", alwdri
      continue
    linek = None
    valuex = None
    for valuestr, count in dims[tarvar].iteritems():
    #eg.'mp1000',     1    dims[  'mp']
    #eg.'mp2000',     2    dims[  'mp']
      s = '_'.join(objk.split(valuestr+'_'))#['mcl_', 'riX_itaXXXX_gammaX']
      ss = re.split('[_]', s)#['mcl', 'riX', 'itaXXXX', 'gammaX']
      k = '_'.join(filter(None, ss))#'mcl_riX_itaXXXX_gammaX'
      linek = k
      valuex = float(valuestr.split(tarvar)[-1])
      if k != objk:
        linek = k
        valuex = float(valuestr.split(tarvar)[-1])
        break
    #print objk, 'is', (linek, valuex)
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
  plt.subplot(gs[0])
  plt.rc('text', usetex=True)
  plt.rc('font',**{'family':'serif','serif':['Palatino']})
  #plt.rc('font',**{'family':'serif','serif':['Helvetica']})
  xlbl = None
  if tarvar == 'mp': 
    xlbl = r'\textrm{max particles}'
  if tarvar == 'ita': 
    xlbl = r'\textrm{dual normalizer }\eta'
  if tarvar == 'gamma': 
    xlbl = r'\textrm{DEMC step size gamma}'
  plt.xlabel('${}$'.format(xlbl))
  plt.ylabel(r'\textrm{error (meter)}')
  title = xlbl + r'\textrm{ vs error}'
  plt.title('${}$'.format(title))
  for k,v in allLines.items():
    #print (k, k.replace('_','\_')), ',', v
    legend = r'{}'.format(k.replace('_',' '))
    plt.errorbar(v.keys(), v.values(), yerr=errs[k].values(), fmt=kwords[k], label=legend)
    #plt.errorbar(v.keys(), v.values(), yerr=yerrs[k], fmt=kwords[k], label=legend, capsize=10)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  plt.show()
  return fig

def ploterrtime(objs, captype='minmax', alwdmcl=['mcl','amcl','mixmcl','mcmcl'], alwdmp=[1000, 5000, 10000]):
  "captype could be minmax or std."
  fig = plt.figure(figsize=(18,8))
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
  plt.subplot(gs[0])
  plt.rc('text', usetex=True)
  plt.rc('font',**{'family':'serif','serif':['Palatino']})
  plt.xlabel(r'\textrm{time (seconds)}')
  plt.ylabel(r'\textrm{error (metres)}')
  if captype == 'minmax':
    yer = lambda matrix: matrix[[3,4],:]
    plt.title(r'error curve wrt time with min/max caps')
  else:
    yer = lambda matrix: matrix[2,:]
    plt.title(r'error curve wrt time with std caps')
  for objk, obj in objs.iteritems():
    if obj['mclpkg'] not in alwdmcl or obj['mp'] not in alwdmp or obj['ri'] != 1:
      continue
    mat = obj['list_errtimestatmat']
    legend = r'{}'.format(objk.replace('_',' '))
    #print legend
    plt.errorbar(mat[0,:], mat[1,:], yerr=yer(mat), fmt=kword(obj), label=legend)
  plt.legend(loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
  plt.show()
  return fig


