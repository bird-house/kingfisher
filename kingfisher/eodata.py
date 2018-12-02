from tempfile import mkstemp
from osgeo import gdal, osr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from eggshell.visual import visualisation as vs
import io
from PIL import Image
import rasterio
import numpy as np
from os import path, listdir
import glob
import subprocess

import logging
LOGGER = logging.getLogger("PYWPS")

def get_bai(basedir, product='Sentinel2'):
    """
    :param basedir: path of basedir for EO data
    :param product: EO product e.g. "Sentinel2" (default)

    :retrun: bai file
    """

    LOGGER.debug("Start calculating BAI")

    prefix = path.basename(path.normpath(basedir)).split('.')[0]

    jps = []
    fname = basedir.split('/')[-1]
    ID = fname.replace('.SAFE','')

    LOGGER.debug("Start calculating BAI for %s " % ID)

    for filename in glob.glob(basedir + '/GRANULE/*/IMG_DATA/*jp2'):
        jps.append(filename)

    jp_B04 = [jp for jp in jps if '_B04.jp2' in jp][0]
    jp_B08 = [jp for jp in jps if '_B08.jp2' in jp][0]

    with rasterio.open(jp_B04) as red:
        RED = red.read()
    with rasterio.open(jp_B08) as nir:
        NIR = nir.read()

    try:
        #compute the BAI burned area index
        # 1 / ((0.1 - RED)^2 + (0.06 -NIR)^2)
        bai = 1 / (np.power((0.1 - RED) ,2) + np.power((0.06 - NIR) ,2))

        LOGGER.debug("BAI values are calculated")

        profile = red.meta
        profile.update(driver='GTiff')
        profile.update(dtype=rasterio.float32)

        _, bai_file = mkstemp(dir='.', prefix=prefix, suffix='.tif')
        with rasterio.open(bai_file, 'w', **profile) as dst:
            dst.write(bai.astype(rasterio.float32))
    except:
        LOGGER.exception("Failed to Calculate BAI for %s " % prefix)
    return bai_file


def get_timestamp(tile):
    """
    returns the creation timestamp of a tile image as datetime.

    :param tile: path to geotiff confom to gdal metadata http://www.gdal.org/gdal_datamodel.html

    :return datetime: timestamp
    """

    from datetime import datetime as dt
    try:
        ds = gdal.Open(tile, 0)
        ts = ds.GetMetadataItem("TIFFTAG_DATETIME")

        LOGGER.debug("timestamp: %s " % ts)
        ds = None  # to close the dataset

        timestamp = dt.strptime(ts, '%Y:%m:%d %H:%M:%S')
    except:
        LOGGER.exception('failed to get timestamp for: %s' % tile)

    return timestamp


def resample(DIR, band, resolution):
    """
    resamples a band of a SENTINEL product to a given target resolution

    :param DIR: base directory of Sentinel2 directory tree
    :param band: band name (e.g. B4)
    :param resolution: target resolution in meter (e.g 10)

    :return: resampled band
    """

    from snappy import GPF

    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    HashMap = jpy.get_type('java.util.HashMap')
    BandDescriptor = jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')

    parameters = HashMap()
    parameters.put('targetResolution', resolution)
    parameters.put('upsampling','Bicubic')
    parameters.put('downsampling','Mean')
    parameters.put('flagDownsampling','FlagMedianAnd')
    parameters.put('resampleOnPyramidLevels',True)

    product = ProductIO.readProduct(DIR)
    product=GPF.createProduct('Resample', parameters, product)

    rsp_band = product.getBand(band)

    return rsp_band



def merge(tiles, prefix="mosaic_"):
    """
    merging a given list of files with gdal_merge.py

    :param tiles: list of geotiffs to be merged_tiles

    :return geotiff: mosaic of merged files
    """

    from eggshell.eo import gdal_merge as gm
    from os.path import join, basename
    import subprocess
    from subprocess import CalledProcessError
    from eggshell.config import _PATH

    try:
        LOGGER.debug('start merging of %s files' % len(tiles))
        # prefix = dt.strftime(date, "%Y%m%d")
        _, filename = mkstemp(dir='.', prefix=prefix, suffix='.tif')
        gdal_merge = '%s/gdal_merge.py' % _PATH
        cmd = ['python', gdal_merge, '-o', filename, '-of', 'GTiff', '-v']
        for tile in tiles:
            LOGGER.debug('extent tile %s ', tile)
            cmd.append(tile)

        LOGGER.debug('cmd: %s' % cmd)
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        LOGGER.debug('gdal_merge log: \n %s', output)

    except CalledProcessError as e:
        LOGGER.exception('failed to merge tiles:\n{0}'.format(e.output))

    # import sys
    # try:
    #     LOGGER.debug('start merging')
    #     # prefix = dt.strftime(date, "%Y%m%d")
    #     _, filename = mkstemp(dir='.', prefix=prefix, suffix='.tif')
    #     call = ['-o',  "%s" % filename, '-of', 'GTiff', '-v']
    #     #
    #     # tiles_day = [tile for tile in tiles if date.date() == get_timestamp(tile).date()]
    #
    #     for tile in tiles:
    #         call.extend([tile])
    #     sys.argv[1:] = call
    #     gm.main()
    #
    #     LOGGER.debug("files merged for %s tiles " % len(tiles))
    # except:
    #     LOGGER.exception("failed to merge tiles")

    return filename


def get_ndvi(basedir, product='Sentinel2'):
    """
    :param basedir: path of basedir for EO data
    :param product: EO product e.g. "Sentinel2" (default)

    :retrun files, plots : list of calculated files and plots
    """
    import rasterio
    import numpy as np
    from os import path, listdir
    from tempfile import mkstemp
    from osgeo import gdal
    # import os, rasterio
    import glob
    import subprocess

    prefix = path.basename(path.normpath(basedir)).split('.')[0]

    jps = []
    fname = basedir.split('/')[-1]
    ID = fname.replace('.SAFE','')

    for filename in glob.glob(basedir + '/GRANULE/*/IMG_DATA/*jp2'):
        jps.append(filename)

    jp_B04 = [jp for jp in jps if '_B04.jp2' in jp][0]
    jp_B08 = [jp for jp in jps if '_B08.jp2' in jp][0]

    with rasterio.open(jp_B04) as red:
        RED = red.read()
    with rasterio.open(jp_B08) as nir:
        NIR = nir.read()

    try:
        # compute the ndvi
        ndvi = (NIR.astype(float) - RED.astype(float)) / (NIR + RED )

        profile = red.meta
        profile.update(driver='GTiff')
        profile.update(dtype=rasterio.float32)

        _, ndvifile = mkstemp(dir='.', prefix=prefix, suffix='.tif')
        with rasterio.open(ndvifile, 'w', **profile) as dst:
            dst.write(ndvi.astype(rasterio.float32))
    except:
        LOGGER.exception("Failed to Calculate NDVI for %s " % prefix)
    return ndvifile


# def plot_RGB(DIR, colorscheem='natural_color'):
#     """
#     Extracts the files for RGB bands of Sentinel2 directory tree, scales and merge the values.
#     Output is a merged tif including 3 bands.
#
#     :param DIR: base directory of Sentinel2 directory tree
#     :param colorscheem: usage of bands (default=natural_color will use B4,B3,B2 for red,green,blue)
#
#     :returns: png image
#     """
#     from snappy import ProductIO
#     from snappy import ProductUtils
#     from snappy import ProgressMonitor
#     from snappy import jpy
#
#     from os.path import join
#
#     mtd = 'MTD_MSIL1C.xml'
#     fname = DIR.split('/')[-1]
#     ID = fname.replace('.SAFE','')
#
#     # _, rgb_image = mkstemp(dir='.', prefix=prefix , suffix='.png')
#     source = join(DIR, mtd)
#
#     sourceProduct = ProductIO.readProduct(source)
#
#     if colorscheem == 'naturalcolors':
#         red = sourceProduct.getBand('B4')
#         green = sourceProduct.getBand('B3')
#         blue = sourceProduct.getBand('B2')
#
#     elif colorscheem == 'falsecolors-vegetation':
#         red = sourceProduct.getBand('B8')
#         green = sourceProduct.getBand('B4')
#         blue = sourceProduct.getBand('B3')
#
#     elif colorscheem == 'falsecolors-urban':
#         red = sourceProduct.getBand('B12')
#         green = sourceProduct.getBand('B11')
#         blue = resample(source, 'B4', 20)  # sourceProduct.getBand('B4')
#
#     elif colorscheem == 'athmospheric-penetration':
#         red = sourceProduct.getBand('B12')
#         green = sourceProduct.getBand('B11')
#         blue = sourceProduct.getBand('B8a')
#
#     elif colorscheem == 'agriculture':
#         red = sourceProduct.getBand('B11')
#         green = resample(source, 'B8', 20)
#         blue = resample(source, 'B2', 20)
#
#     elif colorscheem == 'healthy-vegetation':
#         red = sourceProduct.getBand('B8')
#         green = resample(source, 'B11', 10)
#         blue = sourceProduct.getBand('B2')
#
#     elif colorscheem == 'land-water':
#         red =  resample(source, 'B8', 20)
#         green = sourceProduct.getBand('B11')
#         blue = resample(source, 'B4', 20 )
#
#     elif colorscheem == 'naturalcolors-athmosphericremoval':
#         red = sourceProduct.getBand('B12')
#         green = resample(source, 'B8', 20)
#         blue = resample(source, 'B3', 20)
#
#     elif colorscheem == 'shortwave-infrared':
#         red = sourceProduct.getBand('B12')
#         green = resample(source, 'B8', 20)
#         blue = resample(source, 'B4',20)
#
#     elif colorscheem == 'vegetation-analyses':
#         red = sourceProduct.getBand('B11')
#         green = resample(source, 'B8', 20)
#         blue = resample(source, 'B4',20)
#
#     else:
#         LOGGER.debug('colorscheem %s not found ' % colorscheem)
#
#     Color = jpy.get_type('java.awt.Color')
#     ColorPoint = jpy.get_type('org.esa.snap.core.datamodel.ColorPaletteDef$Point')
#     ColorPaletteDef = jpy.get_type('org.esa.snap.core.datamodel.ColorPaletteDef')
#     ImageInfo = jpy.get_type('org.esa.snap.core.datamodel.ImageInfo')
#     ImageLegend = jpy.get_type('org.esa.snap.core.datamodel.ImageLegend')
#     ImageManager = jpy.get_type('org.esa.snap.core.image.ImageManager')
#     JAI = jpy.get_type('javax.media.jai.JAI')
#     RenderedImage = jpy.get_type('java.awt.image.RenderedImage')
#
#     # Disable JAI native MediaLib extensions
#     System = jpy.get_type('java.lang.System')
#     System.setProperty('com.sun.media.jai.disableMediaLib', 'true')
#
#     #
#     legend = ImageLegend(blue.getImageInfo(), blue)
#     legend.setHeaderText(blue.getName())
#
#     # red = product.getBand('B4')
#     # green = product.getBand('B3')
#     # blue = product.getBand('B2')
#     # from tempfile import mkstemp
#     # from PIL import Image
#     #
#     # _ , snapfile = mkstemp(dir='.', prefix='RGB_', suffix='.png')
#
#     imagefile = '%s_%s.png' % (colorscheem, ID)
#
#     image_info = ProductUtils.createImageInfo([red, green, blue], True, ProgressMonitor.NULL)
#     im = ImageManager.getInstance().createColoredBandImage([red, green, blue], image_info, 0)
#     JAI.create("filestore", im, imagefile, 'PNG')
#
#     #
#     # basewidth = 600
#     # img = Image.open(snapfile)
#     # wpercent = (basewidth / float(img.size[0]))
#     # hsize = int((float(img.size[1]) * float(wpercent)))
#     # img = img.resize((basewidth, hsize), Image.ANTIALIAS)
#     # img.save(imagefile)
#
#     return imagefile

# def plot_band(source, file_extension='PNG', colorscheem=None):
#     """
#     plots the first band of a geotif file
#
#     :param source: geotif file containning one band with NDVI values
#     :param file_extension: format of the output graphic. default='png'
#     :param colorscheem: predifined colorscheem
#                         allowed values: "NDVI", "BAI"
#                         if None (default), plot will given as grayscale
#
#     :result str: path to graphic file
#     """
#
#     from snappy import ProductIO
#     from snappy import ProductUtils
#     # from snappy import ProgressMonitor
#     from snappy import jpy
#
#     from os.path import splitext, basename
#
#     try:
#         LOGGER.debug('Start plotting Band')
#         sourceProduct = ProductIO.readProduct(source)
#         # bandname = list(sourceProduct.getBandNames())[0]
#         # LOGGER.debug('bandname found: %s ' % bandname)
#         ndvi = sourceProduct.getBand("band_1")
#     except:
#         LOGGER.exception("failed to read ndvi values")
#     try:
#         LOGGER.debug('read in org.esa information')
#         # More Java type definitions required for image generation
#         Color = jpy.get_type('java.awt.Color')
#         ColorPoint = jpy.get_type('org.esa.snap.core.datamodel.ColorPaletteDef$Point')
#         ColorPaletteDef = jpy.get_type('org.esa.snap.core.datamodel.ColorPaletteDef')
#         ImageInfo = jpy.get_type('org.esa.snap.core.datamodel.ImageInfo')
#         ImageLegend = jpy.get_type('org.esa.snap.core.datamodel.ImageLegend')
#         ImageManager = jpy.get_type('org.esa.snap.core.image.ImageManager')
#         JAI = jpy.get_type('javax.media.jai.JAI')
#         RenderedImage = jpy.get_type('java.awt.image.RenderedImage')
#
#         # Disable JAI native MediaLib extensions
#         System = jpy.get_type('java.lang.System')
#         System.setProperty('com.sun.media.jai.disableMediaLib', 'true')
#     except:
#         LOGGER.exception('failed to read in org.esa information')
#
#     # points = [ColorPoint(-1.0, Color.WHITE),
#     #           # ColorPoint(50.0, Color.RED),
#     #           ColorPoint(1.0, Color.GREEN)]
#     # cpd = ColorPaletteDef(points)
#     # ii = ImageInfo(cpd)
#     # ndvi.setImageInfo(ii)
#
#     try:
#         LOGGER.debug('write image')
#         img_name = 'INDICE_%s.png' % (splitext(basename(source))[0])
#
#         image_format = 'PNG'
#
#         im = ImageManager.getInstance().createColoredBandImage([ndvi], ndvi.getImageInfo(), 0)
#         JAI.create("filestore", im, img_name, image_format)
#     except:
#         LOGGER.exception('failed to write image')
#     return img_name
