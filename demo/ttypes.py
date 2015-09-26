# -*- coding:utf-8 -*-
#
# Autogenerated by Thrift Compiler (1.0.0-dev)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from __future__ import absolute_import
from thrift.Thrift import TType, TMessageType, TException, TApplicationException

from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol, TProtocol
try:
  from thrift.protocol import fastbinary
except:
  fastbinary = None



class Location:
  """
  Attributes:
   - city
   - province
   - names
  """

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
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
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
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
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
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class Locations:
  """
  Attributes:
   - locations
   - strs
   - ints
  """

  thrift_spec = (
    None, # 0
    (1, TType.LIST, 'locations', (TType.STRUCT,(Location, Location.thrift_spec)), None, ), # 1
    (2, TType.LIST, 'strs', (TType.STRING,None), None, ), # 2
    (3, TType.LIST, 'ints', (TType.I32,None), None, ), # 3
  )

  def __init__(self, locations=None, strs=None, ints=None,):
    self.locations = locations
    self.strs = strs
    self.ints = ints

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
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
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('Locations')
    if self.locations is not None:
      oprot.writeFieldBegin('locations', TType.LIST, 1)
      oprot.writeListBegin(TType.STRUCT, len(self.locations))
      for iter25 in self.locations:
        iter25.write(oprot)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    if self.strs is not None:
      oprot.writeFieldBegin('strs', TType.LIST, 2)
      oprot.writeListBegin(TType.STRING, len(self.strs))
      for iter26 in self.strs:
        oprot.writeString(iter26)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    if self.ints is not None:
      oprot.writeFieldBegin('ints', TType.LIST, 3)
      oprot.writeListBegin(TType.I32, len(self.ints))
      for iter27 in self.ints:
        oprot.writeI32(iter27)
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
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)