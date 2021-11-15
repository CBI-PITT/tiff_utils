# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 14:27:38 2020

@author: awatson
"""

"""
This class is a simple way of managing tiff files:
    The class can be used to read and write tiffs.  
    
    -During reads, all tags are collected and resolutions are extracted in microns
        a) loadImage=False can be specified winstantiating the class to load only tags and resolution information
        b) image can be loaded manually by calling class method: .loadImage()
    
    -During writes, the class.write() method will automatically determine whether
        a) BigTiff is required (files >= 2GB)
        b) Manage compression (currently defaults to 'zlib')
        c) Manage tiled-tiff writed (currently defaults to (512,512))
    
        CAUTION: be careful when calling .write() because it will overwrite the origional image
            if the file name was not changed.
    
    -Class methods enable easy:
        a) replace the image with a differnt np.array: .newImage(array)
        b) assign a new file name: .newFileName(fileNameString)
        c) conversion of dtype:
            i)  .to8bit()
            ii) .to16bit()
            ii) .toFloat()
            vi) .toFloat32()
            v)  .toFloat64()
            vi) .toDtype(np.dtype)
        d) assigning of new resolution in microns: .newResolution((yres,xres))
        e) resizing of image to a specified resolution in microns: .resizeImage((x_res,y_res)) or .resizeImage(int)
        f) clone an image class: newClass = currentClass.clone(newFilePath=None, array=None, newResolutionMicrons=None)
    
    eg. extractions and writing of tags to TIFF files, bigTIFF, compression, etc
    
"""


"""
Revisions:
2021-11-15
    Significant rewrite of class to include proper class methods.  
2020-02-16 
    Added rounding to resolution tag in writeTiff to stop a very rare circumstance
    where certain resolutions could cause to tifffile to throw the following exception
    during save:  struct.error: 'I' format requires 0 <= number <= 4294967295
    
2020-04-14
    -Commented skimage external tifffile at import and changed function 'tiffGetImage' to use tifffile
    - Added conda cli to import imagecodecs if it does not work.  Can also uncomment pip (maybe more reliable)
"""



import os
import copy
import tifffile
from skimage.transform import rescale
from skimage import io, img_as_ubyte, img_as_uint, img_as_float, img_as_float32, img_as_float64
import numpy as np



# testImage = r"H:\Acquire\CEBRA\02CL89\brain_stack4\brain_layer821\488\images\brain_col0009.tif"


class tiff:
    
    def __init__(self, file=None, array=None, loadImage=True):
        
        if (file is None) and (array is None):
            raise ValueError('A file, array or both must be provided')
            
        elif isinstance(file, str) and os.path.exists(file)==True and (array is None):
            
            self.newFileName(file)
            if loadImage == True:
                self.loadImage()
            else:
                self.tiffGetTags()
                
        elif isinstance(file, str) and os.path.exists(file)==False and isinstance(array,np.ndarray):
            
            self.newFileName(file)
            self.newImage(array)
        
        elif isinstance(file, str) and os.path.exists(file)==True and isinstance(array,np.ndarray):
            
            self.newImage(array)
            self.newFileName(file)
            
        elif isinstance(file, str) and (os.path.exists(file))==False and array is None:
            self.newFileName(file)
            
        elif file == None and isinstance(array,np.ndarray):
            self.newImage(array)
            
    #########################################################################################################
    '''
    END __init__
    Below are class methods
    '''
    #########################################################################################################
    
    
    def extractTags(self):
        ## NOTE: This version of tifffile reads tags as all lowercase
        ## Newer version of skimage may require edits 
        with tifffile.TiffFile(self.filePathComplete) as tif:
            tif_tags = {}
            for tag in tif.pages[0].tags.values():
                name, value = tag.name, tag.value
                tif_tags[name] = value
        self.tags = tif_tags
    
    def read(self):
        self.loadImage()
        self.tiffGetTags()
    
    def show(self):
        io.imshow(self.image)
        
    def to16bit(self, cropOutOfRange=True):
        if cropOutOfRange==True:
            self.cropOutOfRange()
        self.image = img_as_uint(self.image)
    
    def to8bit(self, cropOutOfRange=True):
        if cropOutOfRange==True:
            self.cropOutOfRange()
        self.image = img_as_ubyte(self.image)
        
    def toFloat(self, cropOutOfRange=True):
        if cropOutOfRange==True:
            self.cropOutOfRange()
        self.image = img_as_float(self.image)
    
    def toFloat32(self, cropOutOfRange=True):
        if cropOutOfRange==True:
            self.cropOutOfRange()
        self.image = img_as_float32(self.image)
    
    def toFloat64(self, cropOutOfRange=True):
        if cropOutOfRange==True:
            self.cropOutOfRange()
        self.image = img_as_float64(self.image)
    
    def toDtype(self, dtype):
        if dtype == np.uint8:
            self.to8bit()
        elif dtype == np.uint16:
            self.to16bit()
        elif dtype == 'float' or dtype == np.float:
            self.toFloat()
        elif dtype == 'float32':
            self.toFloat32()
        elif dtype == 'float64':
            self.toFloat64()
        
    
    def tiffGetTags(self):
        
        self.extractTags()

        try:
            self.shape = (self.tags['ImageLength'],self.tags['ImageWidth'])
            self.image_length = self.tags['ImageLength']
            self.image_width = self.tags['ImageWidth']    
        except:
            pass
        
        try:
            self.y_resolution = self.tags['YResolution']
            self.x_resolution = self.tags['XResolution']
            self.resolution_unit = int(self.tags['ResolutionUnit'])
            
            if self.resolution_unit == 3:  ## Centimeter
                self.res_y_microns = (self.y_resolution[1] / self.y_resolution[0]) * 10000
                self.res_x_microns = (self.x_resolution[1] / self.x_resolution[0]) * 10000
                
            elif self.resolution_unit == 2: ## Inch
                self.res_y_microns = (self.y_resolution[1] / self.y_resolution[0]) * 25400
                self.res_x_microns = (self.x_resolution[1] / self.x_resolution[0]) * 25400
                
            else:
                pass
        except:
            pass
    
    def loadImage(self):
        self.image = tifffile.imread(self.filePathComplete)
        # self.image = io.imread(self.filePathComplete)
        
    def newImage(self, array):
        self.image = array
        self.shape = self.image.shape
        self.image_length = self.shape[0]
        self.image_width = self.shape[1]
        
    def newFileName(self, newFilePath):
        """
        This funcion will replace the fileName
        
        newFilePath = a full path: if None it will remain unchanged
        """
        
        self.filePathComplete = newFilePath
        self.filePathBase = os.path.split(newFilePath)[0]
        self.fileName = os.path.split(newFilePath)[1]
        self.fileExtension = os.path.splitext(self.fileName)[1]
    
    
    def cropOutOfRange(self):
        if ('uint16' in str(self.image.dtype)) == True:
            self.image[self.image < 0] = 0
            self.image[self.image > 65535] = 65535
        
        if ('float' in str(self.image.dtype)) == True:
            self.image[self.image < 0] = 0
            self.image[self.image > 1] = 1
            
        if ('uint8' in str(self.image.dtype)) == True:
            self.image[self.image < 0] = 0
            self.image[self.image > 255] = 255
    
    
    def newResolution(self, resolution, unit='microns'):
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
            self.res_y_microns = yres
            self.res_x_microns = xres
            
            self.y_resolution = (yres/10000).as_integer_ratio() #divide by 10000 to convert to centimeters
            self.x_resolution = (xres/10000).as_integer_ratio()
            
            if hasattr(self,'tags'):
                self.tags['YResolution'] = self.y_resolution
                self.tags['XResolution'] = self.x_resolution
        
        
        self.resolution_unit = 3
        if hasattr(self,'tags'):
            self.tags['ResolutionUnit'] = 3
    
    
    
    
    def bigTiffRequired(self):
        """
        TiffClass with .image array
        Returns True if the size and data type of the array and bit type form >= 2GB and 
        requires a BifTiff format
        
        Else returns False
        """
        bigTiffCutoff = (2**32 - 2**25)/1024/1024/1024/2  ##Converted to GB (/1024/1024/1024) '/2' required to bring below 2GB or tiff fails to write
        # fileSize = self.image.shape[0]*self.image.shape[1]
        
        for num, ii in enumerate(self.image.shape):
            if num==0:
                fileSize = ii
            else:
                fileSize *= ii
            
        if str(self.image.dtype) == 'uint16':
            fileSize = fileSize*16-1
        elif str(self.image.dtype) == 'uint8' or str(self.image.dtype) == 'ubyte':
            fileSize = fileSize*8-1
        elif str(self.image.dtype) == 'float32':
            fileSize = fileSize*32-1
        elif str(self.image.dtype) == 'float' or str(self.image.dtype) == 'float64':
            fileSize = fileSize*64-1
        
        fileSize = fileSize/8/1024/1024/1024
        
        if fileSize < bigTiffCutoff:
            return False
        else:
            return True
    
    
    
    def write(self,compression='zlib', tile=(512,512)):
        ## NOTE: This version of tifffile requires all lowercase
        ## and does not allow export of metadata
        ## Does not allow specification of compression other than lzma
        ## Newer version of skimage may require edits 
        
        bigTiff = self.bigTiffRequired()
            
        with tifffile.TiffWriter(self.filePathComplete,bigtiff=bigTiff) as tiffout: ###############Change True to bigTiff
            
        
            if hasattr(self,'y_resolution') == False:
                # Default to resolution of 1 micron
                res_x_microns, res_y_microns = 1,1
            else:
                res_x_microns, res_y_microns = self.res_x_microns, self.res_y_microns
            
            ## Round is used in resolution to limit the size of the numbers passed
            ## to tiffout.save.  If the number is too big, it throws an exception
            resolution=(round(10000/res_x_microns,4),
                        round(10000/res_y_microns,4),
                        'CENTIMETER')
        
            if tile is None:
                if len(self.image.shape) == 3 and self.image.shape[-1] == 3:
                    tiffout.save(
                        self.image,
                        photometric='rgb',
                        compression=compression,
                        resolution=resolution
                        )
                else:
                    tiffout.save(
                        self.image,
                        photometric='minisblack',
                        compression=compression,
                        resolution=resolution
                        )
            
            else:
                if len(self.image.shape) == 3 and self.image.shape[-1] == 3:
                    tiffout.save(
                        self.image,
                        photometric='rgb',
                        tile=tile,
                        compression=compression,
                        resolution=resolution
                        )
                else:
                    tiffout.save(
                        self.image,
                        photometric='minisblack',
                        tile=tile,
                        compression=compression,
                        resolution=resolution
                        )
    
    
    
    def clone(self, newFilePath=None, array=None, newResolutionMicrons=None):
        """
        This funcion will clone a tiff class to a new fileName and array
        
        newFilePath = a full path: if None it will remain unchanged
        array = a numpy array: if None it will remain unchanged
        newResolutionMicrons = is the resolution as specified in function tiffNewResolution
        """
        
        newClass = copy.deepcopy(self)
        if array is None:
            pass
        else:
            newClass.image = array
            newClass.shape = newClass.image.shape
            newClass.image_length = newClass.shape[0]
            newClass.image_width = newClass.shape[1]
            if hasattr(self,'tags'):
                newClass.tags['image_length'] = newClass.shape[0]
                newClass.tags['image_width'] = newClass.shape[1]
            
        if newFilePath is None:
            pass
        else:
            newClass.newFileName(newFilePath)
            
        if newResolutionMicrons is None:
            pass
        else:
            newClass.newResolution(newResolutionMicrons, unit='microns')
            
        return newClass
    
    
    
    def resizeImage(self,resolution,unit='microns'):
        
        """
        This funcion will resize the image to the specified resolution
        
        resolution = a float or int in the units specified, it can also be a tuple (yres,xres)
        unit = microns - this is the only option currently - it assumes that all units will be converted to metric (centimeters is what goes into tags)
        
        returns a tiffClass without a filename as a safety to be sure that the origional 
        file is not accidently overwritten.
        """
        
        
        if isinstance(resolution, tuple) == True:
            yres, xres = resolution
            
        else:
            yres = xres = resolution
        yres = float(yres)
        xres = float(xres)
        
        yResizeFactor = self.res_y_microns / yres
        xResizeFactor = self.res_x_microns / xres
        
        if yResizeFactor < 1 or xResizeFactor < 1:
            newImage = tiff(file=None, array=rescale(self.image,(yResizeFactor,xResizeFactor),anti_aliasing=True))
        else:
            newImage = tiff(file=None, array=rescale(self.image,(yResizeFactor,xResizeFactor),anti_aliasing=False))
        
        newImage.newResolution((yres,xres), unit=unit)
        newImage.toDtype(self.image.dtype)
        
        return newImage

    







