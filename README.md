# tiff_utils

## This class is a simple way of working with tiff files



-During reads, all tags are collected and resolutions are extracted in microns
    a) by default, specifying a file name loads the image, tags and resolution information: 

​		`myImage = tiff_utils.tiff(fileName.tiff)` 

​	b) loadImage=False can be specified when instantiating the class to load only tags and resolution information
​    c) image can be loaded manually by calling class method: .loadImage()

-During writes, the class.write() method will automatically:
    a) determine if BigTiff is required (files >= 2GB)
    b) Manage compression (currently defaults to 'zlib')
    c) Manage tiled-tiff writes (currently defaults to (512,512))

​    CAUTION: be careful when calling .write() because it will overwrite the origional image
​        if the file name was not changed.

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