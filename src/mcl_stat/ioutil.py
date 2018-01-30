from collections import OrderedDict
import pickle

def data2pkl(filename, d):
  if 'mclpkg' not in d:
    print 'without mclpkg key'
    return False
  if 'mp' not in d:
    print 'without mp key'
    return False
  if 'ri' not in d:
    print 'without ri key'
    return False
  if d['mclpkg'].find('amcl') >= 0:
    print 'it is amcl'
  elif d['mclpkg'].find('mixmcl') >= 0:
    print 'it is mixmcl'
    if 'ita' not in d:
      print 'without ita for mixmcl'
      return False
  elif d['mclpkg'].find('mcmcl') >= 0:
    print 'it is mcmcl'
    if 'ita' not in d:
      print 'without ita for mcmcl'
      return False
    if 'gamma' not in d:
      print 'without gamma for mcmcl'
      return False
  if 'folder' not in d:
    print 'without folder name'
    return False
  if 'list_final_ed' not in d:
    print 'without final error distance list'
    return False
  if 'list_final_ea' not in d:
    print 'without final error heading list'
    return False
  with open(filename, 'w') as out:
    pickle.dump(d, out)
  return True

def readpkl(args):
  dims = {'mclpkg': {}, 'mp': {}, 'ri': {}, 'ita': {}, 'gamma': {}}
  objs = {}
  for each in args:
    with open(each, 'r') as pkl:
      try:
        obj = pickle.load(pkl)

        if obj['mclpkg'] not in dims['mclpkg']:
          dims['mclpkg'][obj['mclpkg']] = 1
        else:
          dims['mclpkg'][obj['mclpkg']] += 1

        k = 'mp{}'.format(obj['mp'])
        if obj['mp'] not in dims['mp']:
          dims['mp'][k] = 1
        else:
          dims['mp'][k] += 1

        k = 'ri{}'.format(obj['ri'])
        if obj['ri'] not in dims['ri']:
          dims['ri'][k] = 1
        else:
          dims['ri'][k] += 1
        
        key = '{0}_mp{1}_ri{2}'.format(obj['mclpkg'], obj['mp'], obj['ri'])
        if 'ita' in obj: 
          key += '_ita{0}'.format(obj['ita'])
          k = 'ita{}'.format(obj['ita'])
          if obj['ita'] not in dims['ita']:
            dims['ita'][k] = 1
          else:
            dims['ita'][k] += 1

        if 'gamma' in obj: 
          key += '_gamma{0}'.format(obj['gamma'])
          k = 'gamma{}'.format(obj['gamma'])
          if obj['gamma'] not in dims['gamma']:
            dims['gamma'][k] = 1
          else:
            dims['gamma'][k] += 1

        objs[key] = obj
      except EOFError:
        print 'cannot read file', each
  objs = OrderedDict(sorted(objs.items(), key=lambda t: t[0]))
  return (dims, objs)
