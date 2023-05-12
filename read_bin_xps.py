import io
import ntpath

from . import bin_ops
from . import read_ascii_xps
from . import xps_const
from . import xps_types


def flagName(flag):
    flagList = {
        0: xps_const.BACK_FACE_CULLING,
        1: xps_const.ALWAYS_FORCE_CULLING,
        2: xps_const.MODEL_CAST_SHADOWS,
        3: xps_const.TANGENT_SPACE_RED,
        4: xps_const.TANGENT_SPACE_GREEN,
        5: xps_const.TANGENT_SPACE_BLUE,
        6: xps_const.GLOSS,
        7: xps_const.HAS_BONE_DIRECTIONS,
    }
    return flagList.get(flag, flag)


def flagsDefault():
    return {
        xps_const.BACK_FACE_CULLING: False,
        xps_const.ALWAYS_FORCE_CULLING: False,
        xps_const.MODEL_CAST_SHADOWS: True,
        xps_const.TANGENT_SPACE_RED: 0,  # Straight X channel
        xps_const.TANGENT_SPACE_GREEN: 1,  # Invert Y channel
        xps_const.TANGENT_SPACE_BLUE: 0,  # Straight Z channel
        xps_const.GLOSS: 10,
        xps_const.HAS_BONE_DIRECTIONS: False,
    }


def flagValue(flag, value):
    # Flags
    # 00: Backface culling
    # 01: Always force culling
    # 02: Model cast shadows
    # 06: Save current bump specular gloss

    if flag in (0, 1, 2, 6, 7):
        return bool(value)
    # Flags
    # 03: X space
    # 04: Y space
    # 05: Z space
    elif flag in (3, 4, 5):
        return (value % 2)
    else:
        return value


def intToCoords(flag):
    flagValue = {
        0: '+',
        1: '-',
    }
    return flagValue.get(flag, 'Uk')


def printNormalMapSwizzel(tangentSpaceRed, tangentSpaceGreen, tangentSpaceBlue):
    # Default XPS NormalMapTangentSpace == 0 1 0 == X+ Y- Z+
    print('Tangent Space Normal Map Swizzel Coordinates:')
    print(
        f'X{intToCoords(tangentSpaceRed)} Y{intToCoords(tangentSpaceGreen)} Z{intToCoords(tangentSpaceBlue)}'
    )
    print('')


def readFilesString(file):
    lengthByte1 = bin_ops.readByte(file)

    lengthByte2 = bin_ops.readByte(file) if (lengthByte1 >= xps_const.LIMIT) else 0
    length = (lengthByte1 % xps_const.LIMIT) + (lengthByte2 * xps_const.LIMIT)

    return bin_ops.readString(file, length)


def readVertexColor(file):
    r = bin_ops.readByte(file)
    g = bin_ops.readByte(file)
    b = bin_ops.readByte(file)
    a = bin_ops.readByte(file)
    return [r, g, b, a]


def readUvVert(file):
    x = bin_ops.readSingle(file)  # X pos
    y = bin_ops.readSingle(file)  # Y pos
    return [x, y]


def readXYZ(file):
    x = bin_ops.readSingle(file)  # X pos
    y = bin_ops.readSingle(file)  # Y pos
    z = bin_ops.readSingle(file)  # Z pos
    return [x, y, z]


def read4Float(file):
    x = bin_ops.readSingle(file)
    y = bin_ops.readSingle(file)
    z = bin_ops.readSingle(file)
    w = bin_ops.readSingle(file)
    return [x, y, z, w]


def read4Int16(file):
    r = bin_ops.readInt16(file)
    g = bin_ops.readInt16(file)
    b = bin_ops.readInt16(file)
    a = bin_ops.readInt16(file)
    return [r, g, b, a]


def readTriIdxs(file):
    face1 = bin_ops.readUInt32(file)
    face2 = bin_ops.readUInt32(file)
    face3 = bin_ops.readUInt32(file)
    return [face1, face2, face3]


def readHeader(file):
    xpsHeader = xps_types.XpsHeader()
    flags = flagsDefault()

    # MagicNumber
    magic_number = bin_ops.readUInt32(file)
    # XPS Version
    version_mayor = bin_ops.readUInt16(file)
    version_minor = bin_ops.readUInt16(file)
    # XNAaral Name
    xna_aral = readFilesString(file)
    # Settings Length
    settingsLen = bin_ops.readUInt32(file)
    # MachineName
    machineName = readFilesString(file)
    # UserName
    userName = readFilesString(file)
    # File-->File
    filesString = readFilesString(file)
    xpsPoseData = None

    if hasTangent := bin_ops.hasTangentVersion(version_mayor, version_minor):
        # print('OLD Format')
        settingsStream = io.BytesIO(file.read(settingsLen * 4))
    else:
        # print('NEW Format')
        valuesRead = 0
        hash = bin_ops.readUInt32(file)
        valuesRead += 1 * 4
        items = bin_ops.readUInt32(file)
        valuesRead += 1 * 4
        # print('hash', hash)
        # print('items', items)
        for _ in range(items):
            # print('valuesRead', valuesRead)
            optType = bin_ops.readUInt32(file)
            valuesRead += 1 * 4
            optcount = bin_ops.readUInt32(file)
            valuesRead += 1 * 4
            optInfo = bin_ops.readUInt32(file)
            valuesRead += 1 * 4

            # print('------')
            # print('count',i)
            # print('optType',optType)
            # print('optcount',optcount)
            # print('optInfo',optInfo)

            if (optType == 0):
                # print('Read None')
                readNone(file, optcount)
                valuesRead += optcount * 2
            elif (optType == 1):
                # print('Read Pose')
                xpsPoseData = readDefaultPose(file, optcount, optInfo)
                readCount = bin_ops.roundToMultiple(optcount, xps_const.ROUND_MULTIPLE)
                valuesRead += readCount
            elif (optType == 2):
                # print('Read Flags')
                flags = readFlags(file, optcount)
                valuesRead += optcount * 2 * 4
            else:
                # print('Read Waste')
                loopStart = valuesRead // 4
                loopFinish = settingsLen
                # print (loopStart, loopFinish)
                for _ in range(loopStart, loopFinish):
                    # print('waste',j - loopStart)
                    waste = bin_ops.readUInt32(file)

    xpsHeader.magic_number = magic_number
    xpsHeader.version_mayor = version_mayor
    xpsHeader.version_minor = version_minor
    xpsHeader.xna_aral = xna_aral
    xpsHeader.settingsLen = settingsLen
    xpsHeader.machine = machineName
    xpsHeader.user = userName
    xpsHeader.files = filesString
    xpsHeader.pose = xpsPoseData
    xpsHeader.flags = flags
    return xpsHeader


def findHeader(file):
    header = None

    # Check for MAGIC_NUMBER
    number = bin_ops.readUInt32(file)
    file.seek(0)

    if (number == xps_const.MAGIC_NUMBER):
        print('Header Found')
        header = readHeader(file)

    # logHeader(header)
    return header


def readNone(file, optcount):
    for _ in range(optcount):
        waste = bin_ops.readUInt32(file)


def readFlags(file, optcount):
    flags = {}
    for _ in range(optcount):
        flag = bin_ops.readUInt32(file)
        value = bin_ops.readUInt32(file)
        flags[flagName(flag)] = flagValue(flag, value)
    printNormalMapSwizzel(flags[flagName(3)], flags[flagName(4)], flags[flagName(5)])
    return flags


def logHeader(xpsHeader):
    print("MAGIX:", xpsHeader.magic_number)
    print('VER MAYOR:', xpsHeader.version_mayor)
    print('VER MINOR:', xpsHeader.version_minor)
    print('NAME:', xpsHeader.xna_aral)
    print('SETTINGS LEN:', xpsHeader.settingsLen)
    print('MACHINE:', xpsHeader.machine)
    print('USR:', xpsHeader.user)
    print('FILES:', xpsHeader.files)
    print('SETTING:', xpsHeader.settings)
    print('DEFAULT POSE:', xpsHeader.pose)


def readBones(file, header):
    bones = []
    # Bone Count
    boneCount = bin_ops.readUInt32(file)

    for boneId in range(boneCount):
        boneName = readFilesString(file)
        parentId = bin_ops.readInt16(file)
        coords = readXYZ(file)

        xpsBone = xps_types.XpsBone(boneId, boneName, coords, parentId)
        bones.append(xpsBone)
    return bones


def readMeshes(file, xpsHeader, hasBones):
    meshes = []
    meshCount = bin_ops.readUInt32(file)

    hasHeader = bool(xpsHeader)

    verMayor = xpsHeader.version_mayor if hasHeader else 0
    verMinor = xpsHeader.version_minor if hasHeader else 0

    hasTangent = bin_ops.hasTangentVersion(verMayor, verMinor, hasHeader)
    hasVariableWeights = bin_ops.hasVariableWeights(verMayor, verMinor, hasHeader)

    for _ in range(meshCount):
        # Name
        meshName = readFilesString(file)
        if not meshName:
            meshName = 'unnamed'
        # print('Mesh Name:', meshName)
        # uv Count
        uvLayerCount = bin_ops.readUInt32(file)
        # Textures
        textures = []
        textureCount = bin_ops.readUInt32(file)
        for texId in range(textureCount):
            textureFile = ntpath.basename(readFilesString(file))
            # print('Texture file', textureFile)
            uvLayerId = bin_ops.readUInt32(file)

            xpsTexture = xps_types.XpsTexture(texId, textureFile, uvLayerId)
            textures.append(xpsTexture)

        # Vertices
        vertex = []
        vertexCount = bin_ops.readUInt32(file)

        for vertexId in range(vertexCount):
            coord = readXYZ(file)
            normal = readXYZ(file)
            vertexColor = readVertexColor(file)

            uvs = []
            for _ in range(uvLayerCount):
                uvVert = readUvVert(file)
                uvs.append(uvVert)
                if hasTangent:
                    tangent = read4Float(file)

            boneWeights = []
            if hasBones:
                weightsCount = bin_ops.readInt16(file) if hasVariableWeights else 4
                boneIdx = [bin_ops.readInt16(file) for _ in range(weightsCount)]
                boneWeight = [bin_ops.readSingle(file) for _ in range(weightsCount)]
                boneWeights.extend(
                    xps_types.BoneWeight(boneIdx[idx], boneWeight[idx])
                    for idx in range(len(boneIdx))
                )
            xpsVertex = xps_types.XpsVertex(
                vertexId, coord, normal, vertexColor, uvs, boneWeights)
            vertex.append(xpsVertex)

        # Faces
        faces = []
        triCount = bin_ops.readUInt32(file)
        for _ in range(triCount):
            triIdxs = readTriIdxs(file)
            faces.append(triIdxs)
        xpsMesh = xps_types.XpsMesh(
            meshName, textures, vertex, faces, uvLayerCount)
        meshes.append(xpsMesh)
    return meshes


def readIoStream(filename):
    with open(filename, "rb") as a_file:
        ioStream = io.BytesIO(a_file.read())
    return ioStream


def readXpsModel(filename):
    print('File:', filename)

    ioStream = readIoStream(filename)
    print('Reading Header')
    xpsHeader = findHeader(ioStream)
    print('Reading Bones')
    bones = readBones(ioStream, xpsHeader)
    hasBones = bool(bones)
    print('Read', len(bones), 'Bones')
    print('Reading Meshes')
    meshes = readMeshes(ioStream, xpsHeader, hasBones)
    print('Read', len(meshes), 'Meshes')

    return xps_types.XpsData(xpsHeader, bones, meshes)


def readDefaultPose(file, poseLenghtUnround, poseBones):
    # print('Import Pose')
    poseBytes = b''
    if poseLenghtUnround:
        for _ in range(0, poseBones):
            poseBytes += file.readline()

    poseLenght = bin_ops.roundToMultiple(
        poseLenghtUnround, xps_const.ROUND_MULTIPLE)
    emptyBytes = poseLenght - poseLenghtUnround
    file.read(emptyBytes)
    poseString = bin_ops.decodeBytes(poseBytes)
    return read_ascii_xps.poseData(poseString)


if __name__ == "__main__":
    readfilename = r'G:\3DModeling\XNALara\XNALara_XPS\Young Samus\Generic_Item.mesh'

    print('----READ START----')
    xpsData = readXpsModel(readfilename)
    print('----READ END----')
