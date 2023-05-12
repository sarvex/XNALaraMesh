import struct

from . import xps_const


# Format
class TypeFormat:
    SByte = '<b'
    Byte = '<B'
    Int16 = '<h'
    UInt16 = '<H'
    Int32 = '<i'
    UInt32 = '<I'
    Int64 = '<l'
    UInt64 = '<L'
    Single = '<f'
    Double = '<d'


def roundToMultiple(numToRound, multiple):
    return (numToRound + multiple - 1) // multiple * multiple


def readByte(file):
    numberBin = file.read(1)
    return struct.unpack(TypeFormat.Byte, numberBin)[0]


def writeByte(number):
    return struct.pack(TypeFormat.Byte, number)


def readUInt16(file):
    numberBin = file.read(2)
    return struct.unpack(TypeFormat.UInt16, numberBin)[0]


def writeUInt16(number):
    return struct.pack(TypeFormat.UInt16, number)


def readInt16(file):
    numberBin = file.read(2)
    return struct.unpack(TypeFormat.Int16, numberBin)[0]


def writeInt16(number):
    return struct.pack(TypeFormat.Int16, number)


def readUInt32(file):
    numberBin = file.read(4)
    return struct.unpack(TypeFormat.UInt32, numberBin)[0]


def writeUInt32(number):
    return struct.pack(TypeFormat.UInt32, number)


def readSingle(file):
    numberBin = file.read(4)
    return struct.unpack(TypeFormat.Single, numberBin)[0]


def writeSingle(number):
    return struct.pack(TypeFormat.Single, number)


def readString(file, length):
    try:
        pos1 = file.tell()
        byteString = file.read(length)
        pos2 = file.tell()
        string = ''
        string = decodeBytes(byteString)
    except Exception:
        print('*' * 40)
        print('pos len', pos1)
        print('pos str', pos2)
        print('pos', file.tell())
        print('len', length)
        print('str', byteString)
        string = decodeBytes(byteString)
    return string


def writeString(string):
    return encodeString(string)


def decodeBytes(bytes):
    # print(bytes)
    return bytes.decode(xps_const.ENCODING_READ)


def encodeString(string):
    # print(string)
    return string.encode(xps_const.ENCODING_WRITE)


def hasHeader(fileformat='.xps'):
    return fileformat == '.xps'


def hasTangentVersion(verMayor, verMinor, hasHeader=True):
    return (verMinor <= 12 and verMayor <= 2) if hasHeader else True


def hasVariableWeights(verMayor, verMinor, hasHeader=True):
    return (verMayor >= 3) if hasHeader else False
