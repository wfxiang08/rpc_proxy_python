# -*- coding:utf-8 -*-
#
# Autogenerated by Thrift Compiler (1.0.0-dev)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py:slots
#

from __future__ import absolute_import
from thrift.Thrift import TType, TMessageType, TException, TApplicationException

from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol, TProtocol
try:
  from rpc_thrift.cython.cybinary_protocol import TCyBinaryProtocol
except:
  TCyBinaryProtocol = None



class Location:
  """
  Attributes:
   - city
   - province
   - names
  """

  __slots__ = [ 
    'city',
    'province',
    'names',
   ]

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'city', None, None, ), # 1
    (2, TType.STRING, 'province', None, None, ), # 2
    (3, TType.LIST, 'names', (TType.STRING,None), None, ), # 3
  )

  def __init__(self, city=None, province=None, names=None,):
    self.city = city
    self.province = province
    self.names = names

  def read(self, iprot):
    if iprot.__class__ == TCyBinaryProtocol and self.thrift_spec is not None:
      iprot.read_struct(self)
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.city = iprot.readString()
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.STRING:
          self.province = iprot.readString()
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.LIST:
          self.names = []
          (_etype3, _size0) = iprot.readListBegin()
          for _i4 in xrange(_size0):
            _elem5 = iprot.readString()
            self.names.append(_elem5)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TCyBinaryProtocol and self.thrift_spec is not None:
      oprot.write_struct(self)
      return
    oprot.writeStructBegin('Location')
    if self.city is not None:
      oprot.writeFieldBegin('city', TType.STRING, 1)
      oprot.writeString(self.city)
      oprot.writeFieldEnd()
    if self.province is not None:
      oprot.writeFieldBegin('province', TType.STRING, 2)
      oprot.writeString(self.province)
      oprot.writeFieldEnd()
    if self.names is not None:
      oprot.writeFieldBegin('names', TType.LIST, 3)
      oprot.writeListBegin(TType.STRING, len(self.names))
      for iter6 in self.names:
        oprot.writeString(iter6)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.city)
    value = (value * 31) ^ hash(self.province)
    value = (value * 31) ^ hash(self.names)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, getattr(self, key))
      for key in self.__slots__]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    for attr in self.__slots__:
      my_val = getattr(self, attr)
      other_val = getattr(other, attr)
      if my_val != other_val:
        return False
    return True

  def __ne__(self, other):
    return not (self == other)


class Locations:
  """
  Attributes:
   - locations
   - strs
   - ints
   - id2name
   - id2loc
   - loc
   - loc_list
   - list_map
  """

  __slots__ = [ 
    'locations',
    'strs',
    'ints',
    'id2name',
    'id2loc',
    'loc',
    'loc_list',
    'list_map',
   ]

  thrift_spec = (
    None, # 0
    (1, TType.LIST, 'locations', (TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 1
    (2, TType.LIST, 'strs', (TType.STRING,None), None, ), # 2
    (3, TType.LIST, 'ints', (TType.I32,None), None, ), # 3
    (4, TType.MAP, 'id2name', (TType.I32,None,TType.STRING,None), None, ), # 4
    (5, TType.MAP, 'id2loc', (TType.I32,None,TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 5
    (6, TType.STRUCT, 'loc', (Location, Location.thrift_spec), None, ), # 6
    (7, TType.LIST, 'loc_list', (TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 7
    (8, TType.LIST, 'list_map', (TType.MAP,(TType.I32,None,TType.STRUCT,(Location, Location.thrift_spec))), None, ), # 8
  )

  def __init__(self, locations=None, strs=None, ints=None, id2name=None, id2loc=None, loc=None, loc_list=None, list_map=None,):
    self.locations = locations
    self.strs = strs
    self.ints = ints
    self.id2name = id2name
    self.id2loc = id2loc
    self.loc = loc
    self.loc_list = loc_list
    self.list_map = list_map

  def read(self, iprot):
    if iprot.__class__ == TCyBinaryProtocol and self.thrift_spec is not None:
      iprot.read_struct(self)
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.LIST:
          self.locations = []
          (_etype10, _size7) = iprot.readListBegin()
          for _i11 in xrange(_size7):
            _elem12 = Location()
            _elem12.read(iprot)
            self.locations.append(_elem12)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.LIST:
          self.strs = []
          (_etype16, _size13) = iprot.readListBegin()
          for _i17 in xrange(_size13):
            _elem18 = iprot.readString()
            self.strs.append(_elem18)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.LIST:
          self.ints = []
          (_etype22, _size19) = iprot.readListBegin()
          for _i23 in xrange(_size19):
            _elem24 = iprot.readI32()
            self.ints.append(_elem24)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      elif fid == 4:
        if ftype == TType.MAP:
          self.id2name = {}
          (_ktype26, _vtype27, _size25 ) = iprot.readMapBegin()
          for _i29 in xrange(_size25):
            _key30 = iprot.readI32()
            _val31 = iprot.readString()
            self.id2name[_key30] = _val31
          iprot.readMapEnd()
        else:
          iprot.skip(ftype)
      elif fid == 5:
        if ftype == TType.MAP:
          self.id2loc = {}
          (_ktype33, _vtype34, _size32 ) = iprot.readMapBegin()
          for _i36 in xrange(_size32):
            _key37 = iprot.readI32()
            _val38 = Location()
            _val38.read(iprot)
            self.id2loc[_key37] = _val38
          iprot.readMapEnd()
        else:
          iprot.skip(ftype)
      elif fid == 6:
        if ftype == TType.STRUCT:
          self.loc = Location()
          self.loc.read(iprot)
        else:
          iprot.skip(ftype)
      elif fid == 7:
        if ftype == TType.LIST:
          self.loc_list = []
          (_etype42, _size39) = iprot.readListBegin()
          for _i43 in xrange(_size39):
            _elem44 = Location()
            _elem44.read(iprot)
            self.loc_list.append(_elem44)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      elif fid == 8:
        if ftype == TType.LIST:
          self.list_map = []
          (_etype48, _size45) = iprot.readListBegin()
          for _i49 in xrange(_size45):
            _elem50 = {}
            (_ktype52, _vtype53, _size51 ) = iprot.readMapBegin()
            for _i55 in xrange(_size51):
              _key56 = iprot.readI32()
              _val57 = Location()
              _val57.read(iprot)
              _elem50[_key56] = _val57
            iprot.readMapEnd()
            self.list_map.append(_elem50)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TCyBinaryProtocol and self.thrift_spec is not None:
      oprot.write_struct(self)
      return
    oprot.writeStructBegin('Locations')
    if self.locations is not None:
      oprot.writeFieldBegin('locations', TType.LIST, 1)
      oprot.writeListBegin(TType.STRUCT, len(self.locations))
      for iter58 in self.locations:
        iter58.write(oprot)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    if self.strs is not None:
      oprot.writeFieldBegin('strs', TType.LIST, 2)
      oprot.writeListBegin(TType.STRING, len(self.strs))
      for iter59 in self.strs:
        oprot.writeString(iter59)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    if self.ints is not None:
      oprot.writeFieldBegin('ints', TType.LIST, 3)
      oprot.writeListBegin(TType.I32, len(self.ints))
      for iter60 in self.ints:
        oprot.writeI32(iter60)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    if self.id2name is not None:
      oprot.writeFieldBegin('id2name', TType.MAP, 4)
      oprot.writeMapBegin(TType.I32, TType.STRING, len(self.id2name))
      for kiter61,viter62 in self.id2name.items():
        oprot.writeI32(kiter61)
        oprot.writeString(viter62)
      oprot.writeMapEnd()
      oprot.writeFieldEnd()
    if self.id2loc is not None:
      oprot.writeFieldBegin('id2loc', TType.MAP, 5)
      oprot.writeMapBegin(TType.I32, TType.STRUCT, len(self.id2loc))
      for kiter63,viter64 in self.id2loc.items():
        oprot.writeI32(kiter63)
        viter64.write(oprot)
      oprot.writeMapEnd()
      oprot.writeFieldEnd()
    if self.loc is not None:
      oprot.writeFieldBegin('loc', TType.STRUCT, 6)
      self.loc.write(oprot)
      oprot.writeFieldEnd()
    if self.loc_list is not None:
      oprot.writeFieldBegin('loc_list', TType.LIST, 7)
      oprot.writeListBegin(TType.STRUCT, len(self.loc_list))
      for iter65 in self.loc_list:
        iter65.write(oprot)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    if self.list_map is not None:
      oprot.writeFieldBegin('list_map', TType.LIST, 8)
      oprot.writeListBegin(TType.MAP, len(self.list_map))
      for iter66 in self.list_map:
        oprot.writeMapBegin(TType.I32, TType.STRUCT, len(iter66))
        for kiter67,viter68 in iter66.items():
          oprot.writeI32(kiter67)
          viter68.write(oprot)
        oprot.writeMapEnd()
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    if self.locations is None:
      raise TProtocol.TProtocolException(message='Required field locations is unset!')
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.locations)
    value = (value * 31) ^ hash(self.strs)
    value = (value * 31) ^ hash(self.ints)
    value = (value * 31) ^ hash(self.id2name)
    value = (value * 31) ^ hash(self.id2loc)
    value = (value * 31) ^ hash(self.loc)
    value = (value * 31) ^ hash(self.loc_list)
    value = (value * 31) ^ hash(self.list_map)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, getattr(self, key))
      for key in self.__slots__]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    for attr in self.__slots__:
      my_val = getattr(self, attr)
      other_val = getattr(other, attr)
      if my_val != other_val:
        return False
    return True

  def __ne__(self, other):
    return not (self == other)

