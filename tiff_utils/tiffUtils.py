# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 14:27:38 2020

@author: awatson
"""
"""
Revisions:
2020-02-16 
    Added rounding to resolution tag in writeTiff to stop a very rare circumstance
    where certain resoltions could cause to tifffile to throw the follwing exception
    during save:  struct.error: 'I' format requires 0 <= number <= 4294967295
    
2020-04-14
    -Commented skimage external tifffile at import and changed function 'tiffGetImage' to use tifffile
    - Added conda cli to import imagecodecs if it does not work.  Can also uncomment pip (maybe more reliable)
"""

"""
This set of functions are tools for dealing with complex TIFF writes:
    eg. extractions and writing of tags to TIFF files, bigTIFF, compression, etc
    
"""

import os
import glob
# from skimage.external import tifffile
import tifffile
from skimage import io
from skimage import img_as_ubyte, img_as_uint, img_as_float, img_as_float32, img_as_float64
import numpy as np
import copy


# def condaInstall(package):
#     print('Attempting to install conda ' + package + ' package')
#     try:
#         import conda.cli
#         conda.cli.main('conda', 'install',  '-y', package)
#     except Exception:
#         print('conda ' + package + ' package failed to install or import')
#         raise

# def pipInstall(package):
#     import pip
#     if hasattr(pip, 'main'):
#         pip.main(['install', package])
#     else:
#         from pip._internal import main
#         main(['install', package])


# ## Attempt import if it fails, then install using conda
# for ii in ['tifffile','imagecodecs']:
#     try:
#         exec('import ' + ii)
#     except Exception:
#         try:
#             condaInstall(ii)
#             exec('import ' + ii)
#         except Exception:
#             pipInstall(ii)
            # exec('import ' + ii)
        

# try:
#     import imagecodecs
# except Exception:
#     # pass
#     print('Attempting to install conda imagecodecs package')
#     try:
#         import conda.cli
#         conda.cli.main('conda', 'install',  '-y', 'imagecodecs')
#         import imagecodecs
#     except Exception:
#         print('conda imagecodecs package failed to install or import')
#         raise
    # import pip



##################################################################################

def extractTags(fileName):
    ## NOTE: This version of tifffile reads tags as all lowercase
    ## Newer version of skimage may require edits 
    with tifffile.TiffFile(fileName) as tif:
        tif_tags = {}
        for tag in tif.pages[0].tags.values():
            name, value = tag.name, tag.value
            tif_tags[name] = value
    return tif_tags

##################################################################################        

def bigTiffRequired(tiffClass):
    """
    TiffClass with .image array
    Returns True if the size and data type of the array and bit type form >= 2GB and 
    requires a BifTiff format
    
    Else returns False
    """
    bifTiffCutoff = (2**32 - 2**25)/1024/1024/1024/2  ##Converted to GB (/1024/1024/1024) '/2' required to bring below 2GB or tiff fails to write
    # fileSize = tiffClass.image.shape[0]*tiffClass.image.shape[1]
    
    for num, ii in enumerate(tiffClass.image.shape):
        if num==0:
            fileSize = ii
        else:
            fileSize *= ii
        
    if str(tiffClass.image.dtype) == 'uint16':
        fileSize = fileSize*16-1
    if str(tiffClass.image.dtype) == 'uint8' or str(tiffClass.image.dtype) == 'ubyte':
        fileSize = fileSize*8-1
    fileSize = fileSize/8/1024/1024/1024
    if fileSize < bifTiffCutoff:
        return False
    else:
        return True

###################################################################################

def writeTiff(tiffClass,compression=0, tile=(512,512)):
    ## NOTE: This version of tifffile requires all lowercase
    ## and does not allow export of metadata
    ## Does not allow specification of compression other than lzma
    ## Newer version of skimage may require edits 
    
    bigTiff = bigTiffRequired(tiffClass)
    # bigTiff = True
    
    if hasattr(tiffClass,'y_resolution') == False:
        tiffClass = tiffNewResolution(tiffClass, 1, unit='microns')
        
    
    with tifffile.TiffWriter(tiffClass.filePathComplete,bigtiff=bigTiff) as tifout: ###############Change True to bigTiff
        
        ## Round is used in resolution to limit the size of the numbers passed
        ## to tifout.save.  If the number is too big, it throws an exception
        resolution=(round(10000/tiffClass.res_x_microns,4),
                    round(10000/tiffClass.res_y_microns,4),
                    'CENTIMETER')
    
        if tile is None:
            if len(tiffClass.image.shape) == 3 and tiffClass.image.shape[-1] == 3:
                tifout.save(tiffClass.image,
                         photometric='rgb',
                         tile=tile,
                         compression=compression,
                         resolution=resolution)
            else:
                
                tifout.save(tiffClass.image,
                         photometric='minisblack',
                         compression=compression,
                         resolution=resolution)
        
        else:
            if len(tiffClass.image.shape) == 3 and tiffClass.image.shape[-1] == 3:
                tifout.save(tiffClass.image,
                         photometric='rgb',
                         tile=tile,
                         compression=compression,
                         resolution=resolution)
            else:
                    
                tifout.save(tiffClass.image,
                             photometric='minisblack',
                             tile=tile,
                             compression=compression,
                             resolution=resolution)

###################################################################################

class tiff:
    from skimage import io
    def __init__(self, file=None, array=None, loadImage = True):
        
        if (file is None) and (array is None):
            raise ValueError('A file, array or both must be provided')
            
        elif isinstance(file, str) and os.path.exists(file)==True and (array is None):
            
            self = tiffParseFileName(self, file)
            
            self = tiffGetTags(self)
            
            if loadImage == True:
                self = tiffGetImage(self)
                
        elif isinstance(file, str) and os.path.exists(file)==False and isinstance(array,np.ndarray):
            
            self = tiffParseFileName(self, file)
            
            self = tiffNewArray(self, array)
        
        elif isinstance(file, str) and os.path.exists(file)==True and isinstance(array,np.ndarray):
            
            self = tiffNewArray(self, array)
            self = tiffNewFileName(self, file)
            
        elif isinstance(file, str) and (os.path.exists(file))==False and array is None:
            self = tiffParseFileName(self, file)
            
        elif file == None and isinstance(array,np.ndarray):
            self = tiffNewArray(self, array)
            
    def write(self,compression=0, tile=(512,512)):
        writeTiff(self,compression=compression, tile=tile)
    
    def read(self):
        self = tiffGetImage(self)
        self = tiffGetTags(self, array)
    
    def show(tiffClass):
        io.imshow(tiffClass.image)
        
    def newFileName(self, newFilePath):
        self = tiffNewFileName(self, newFilePath)
    
    def newResolution(self, resolution, unit='microns'):
        self = tiffNewResolution(self, resolution, unit=unit)
        
    def to16bit(self):
        self = convertTo16bit(self)
        
    def to8bit(self):
        self = convertTo8bit(self)
        
    def toFloat(self):
        self = convertToFloat(self)
        

#########################################################################################

def show(tiffClass):
    io.imshow(tiffClass.image)

def tiffClone(tiffClass, newFilePath=None, array=None, newResolutionMicrons=None):
    """
    This funcion will clone a tiff class to a new fileName and array
    
    newFilePath = a full path: if None it will remain unchanged
    array = a numpy array: if None it will remain unchanged
    newResolutionMicrons = is the resolution as specified in function tiffNewResolution
    """
    
    newClass = copy.deepcopy(tiffClass)
    if array is None:
        pass
    else:
        newClass.image = array
        newClass.shape = newClass.image.shape
        newClass.image_length = newClass.shape[0]
        newClass.image_width = newClass.shape[1]
        if hasattr(tiffClass,'tags'):
            newClass.tags['image_length'] = newClass.shape[0]
            newClass.tags['image_width'] = newClass.shape[1]
        
    if newFilePath is None:
        pass
    else:
        newClass = tiffNewFileName(newClass, newFilePath)
        
    if newResolutionMicrons is None:
        pass
    else:
        newClass = tiffNewResolution(newClass, newResolutionMicrons, unit='microns')
        
    return newClass

####################################################################################    
    
def tiffNewFileName(tiffClass, newFilePath):
    """
    This funcion will replace the fileName
    
    newFilePath = a full path: if None it will remain unchanged
    """
    
    tiffClass.filePathComplete = newFilePath
    tiffClass.filePathBase = os.path.split(newFilePath)[0]
    tiffClass.fileName = os.path.split(newFilePath)[1]
    tiffClass.fileExtension = os.path.splitext(tiffClass.fileName)[1]
    
    return tiffClass

####################################################################################

def tiffNewResolution(tiffClass, resolution, unit='microns'):
    """
    This funcion will replace the resolution
    
    resolution = a number in the units specified, it can also be a tuple (yres,xres)
    unit = microns - this is the only option currently - it assumes that all units will be converted to metric (centimeters is what goes into tags)
    """
    
    if isinstance(resolution, tuple) == True:
        yres, xres = resolution
        
    else:
        yres = xres = resolution
    yres = float(yres)
    xres = float(xres)
    
    if unit == 'microns':
        tiffClass.res_y_microns = yres
        tiffClass.res_x_microns = xres
        
        tiffClass.y_resolution = (yres/10000).as_integer_ratio() #divide by 10000 to convert to centimeters
        tiffClass.x_resolution = (xres/10000).as_integer_ratio()
        
        if hasattr(tiffClass,'tags'):
            tiffClass.tags['YResolution'] = tiffClass.y_resolution
            tiffClass.tags['XResolution'] = tiffClass.x_resolution
    
    
    tiffClass.resolution_unit = 3
    if hasattr(tiffClass,'tags'):
        tiffClass.tags['ResolutionUnit'] = 3
    
    return tiffClass
    
    
def tiffNewArray(tiffClass, array):
    tiffClass.image = array
    tiffClass.shape = tiffClass.image.shape
    tiffClass.image_length = tiffClass.shape[0]
    tiffClass.image_width = tiffClass.shape[1]
    
    return tiffClass

#####################################################################################

def tiffGetTags(tiffClass):
    
    tiffClass.tags = extractTags(tiffClass.filePathComplete)

    try:
        tiffClass.shape = (tiffClass.tags['ImageLength'],tiffClass.tags['ImageWidth'])
        tiffClass.image_length = tiffClass.tags['ImageLength']
        tiffClass.image_width = tiffClass.tags['ImageWidth']    
    except:
        pass
    
    try:
        tiffClass.y_resolution = tiffClass.tags['YResolution']
        tiffClass.x_resolution = tiffClass.tags['XResolution']
        tiffClass.resolution_unit = int(tiffClass.tags['ResolutionUnit'])
        
        if tiffClass.resolution_unit == 3:  ## Centimeter
            tiffClass.res_y_microns = (tiffClass.y_resolution[1] / tiffClass.y_resolution[0]) * 10000
            tiffClass.res_x_microns = (tiffClass.x_resolution[1] / tiffClass.x_resolution[0]) * 10000
            
        elif tiffClass.resolution_unit == 2: ## Inch
            tiffClass.res_y_microns = (tiffClass.y_resolution[1] / tiffClass.y_resolution[0]) * 25400
            tiffClass.res_x_microns = (tiffClass.x_resolution[1] / tiffClass.x_resolution[0]) * 25400
            
        else:
            pass
    except:
                pass
    return tiffClass
########################################################################################

def tiffParseFileName(tiffClass, file):
    tiffClass.filePathComplete = file
    tiffClass.filePathBase = os.path.split(file)[0]
    tiffClass.fileName = os.path.split(file)[1]
    tiffClass.fileExtension = os.path.splitext(tiffClass.fileName)[1]
    return tiffClass
 

########################################################################################
    
def tiffGetImage(tiffClass):
    tiffClass.image = tifffile.imread(tiffClass.filePathComplete)
    # tiffClass.image = io.imread(tiffClass.filePathComplete)
    return tiffClass

########################################################################################

def cropOutOfRange(tiffClass):
    if ('uint16' in str(tiffClass.image.dtype)) == True:
        tiffClass.image[tiffClass.image < 0] = 0
        tiffClass.image[tiffClass.image > 65534] = 65534
    
    if ('float' in str(tiffClass.image.dtype)) == True:
        tiffClass.image[tiffClass.image < 0] = 0
        tiffClass.image[tiffClass.image > 1] = 1
        
    if ('uint8' in str(tiffClass.image.dtype)) == True:
        tiffClass.image[tiffClass.image < 0] = 0
        tiffClass.image[tiffClass.image > 255] = 255
    return tiffClass

########################################################################################

def convertTo16bit(tiffClass):
    cropOutOfRange(tiffClass)
    tiffClass.image = img_as_uint(tiffClass.image)
    return tiffClass

#######################################################################################
    
def convertTo8bit(tiffClass):
    cropOutOfRange(tiffClass)
    tiffClass.image = img_as_ubyte(tiffClass.image)
    return tiffClass

#######################################################################################
    
def convertToFloat(tiffClass):
    cropOutOfRange(tiffClass)
    tiffClass.image = img_as_float(tiffClass.image)
    return tiffClass

#######################################################################################
    
def resizeImage(tiffClass,resolution,unit='microns'):
    
    """
    This funcion will resize the image to the specified resolution
    
    resolution = a number in the units specified, it can also be a tuple (yres,xres)
    unit = microns - this is the only option currently - it assumes that all units will be converted to metric (centimeters is what goes into tags)
    
    returns a tiffClass without a filename as a safety to be sure that the origional 
    file is not accidently overwritten.
    """
    from skimage.transform import rescale
    
    if isinstance(resolution, tuple) == True:
        yres, xres = resolution
        
    else:
        yres = xres = resolution
    yres = float(yres)
    xres = float(xres)
    
    yResizeFactor = tiffClass.res_y_microns / yres
    xResizeFactor = tiffClass.res_x_microns / xres
    
    if yResizeFactor < 1 or xResizeFactor < 1:
        newImage = tiff(file=None, array=rescale(tiffClass.image,(yResizeFactor,xResizeFactor),anti_aliasing=True))
    else:
        newImage = tiff(file=None, array=rescale(tiffClass.image,(yResizeFactor,xResizeFactor),anti_aliasing=False))
    
    newImage.newResolution((yres,xres), unit=unit)
    
    return newImage






