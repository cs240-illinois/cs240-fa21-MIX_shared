class Microservice:
  ip = None
  dependencies = []
  max_age = None
  name = None
  creator = None
  tile = None

  def __init__(self, host, d, name = None, creator = None, tile = None):
    self.ip = host
    self.dependencies = d
    self.max_age = 0
    self.name = name
    self.creator = creator
    self.tile = tile

  def __hash__(self) -> int:
    return hash(self.ip)
  
  def __eq__(self, other) -> bool:
    return self.ip == other.ip

  def __ne__(self, other) -> bool:
    return (not self.__eq__(other))
  
  def __repr__(self) -> str:
    return "{tile} {name} IM by {creator} at {ip}".format(tile = self.tile, name = self.name, creator = self.creator, ip = self.ip)
    