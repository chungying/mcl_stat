class MclMap(object):
  """
  from mcl_stat.markov_grid import read_map_yaml
  mapyaml = read_map_yaml('MAPFILENAME.yaml')
  mcl_map = MclMap( mapyaml['origin'][0], mapyaml['origin'][1], mapyaml['resolution'], mapyaml['width'], mapyaml['height'] )
  
  """
  def __init__(self, origin_x, origin_y, scale, size_x, size_y):
    self.origin_x = origin_x + (size_x / 2) * scale
    self.origin_y = origin_y + (size_y / 2) * scale
    self.scale = scale
    self.size_x = size_x
    self.size_y = size_y

  def __repr__(self):
    return 'MclMap(origin_x={}, origin_y={}, scale={}, size_x={}, size_y={})'.format(self.origin_x, self.origin_y, self.scale, self.size_x, self.size_y)

  def __str__(self):
    return 'origin_x={}, origin_y={}, scale={}, size_x={}, size_y={}'.format(self.origin_x, self.origin_y, self.scale, self.size_x, self.size_y)
