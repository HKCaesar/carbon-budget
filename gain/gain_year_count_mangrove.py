### Creates tiles in which each mangrove pixel is the number of years that trees are believed to have been growing there between 2001 and 2015.
### It is based on the annual Hansen loss data and the 2000-2012 Hansen gain data (as well as the 2000 tree cover density data).
### First it calculates rasters of gain years for mangrove pixels that had loss only, gain only, neither loss nor gain, and both loss and gain.
### The gain years for each of these conditions are calculated according to rules that are found in the function called by the multiprocessor command.
### At this point, those rules are the same as for non-mangrove natural forests.
### Then it combines those four rasters into a single gain year raster for each tile.
### This is one of the mangrove inputs for the carbon gain model.
### If different input rasters for loss (e.g., 2001-2017) and gain (e.g., 2000-2018) are used, the constants in create_gain_year_count_mangrove.py must be changed.

import utilities
import subprocess
import datetime

def create_gain_year_count(tile_id):

    print "Processing:", tile_id

    # start time
    start = datetime.datetime.now()

    # Names of the loss, gain and tree cover density tiles
    loss = '{}.tif'.format(tile_id)
    gain = '{}_{}.tif'.format(utilities.pattern_gain, tile_id)
    tcd = '{}_{}.tif'.format(utilities.pattern_tcd, tile_id)

    # Number of years covered by loss and gain input rasters. If the input rasters are changed, these must be changed, too.
    loss_years = 15  # currently, loss raster for carbon model is 2001-2015
    gain_years = 12  # currently, gain raster is 2000-2012

    print '  Loss tile is', loss
    print '  Gain tile is', gain
    print '  tcd tile is', tcd

    # Creates four separate rasters for the four tree cover loss/gain combinations for pixels. Then merges the rasters.
    # In all rasters, 0 is NoData value.
    # Pixels with loss only
    print "  Creating raster of growth years for loss-only pixels"
    #gdal_calc.py -A 00N_050W.tif -B Hansen_GFC2015_gain_00N_050W.tif --calc="(A>0)*(B==0)*(A-1)" --outfile=loss_only.tif --NoDataValue=0 --overwrite
    loss_calc = '--calc=(A>0)*(B==0)*(A-1)'
    loss_outfile1 = 'growth_years_loss_only_{}.tif'.format(tile_id)
    loss_outfile2 = '--outfile={}'.format(loss_outfile1)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, loss_calc, loss_outfile2, '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW']
    subprocess.check_call(cmd)

    # Pixels with gain only
    print "  Creating raster of growth years for gain-only pixels"
    #gdal_calc.py -A 00N_050W.tif -B Hansen_GFC2015_gain_00N_050W.tif --calc="(A==0)*(B==1)*6" --outfile=gain_only.tif --NoDataValue=0 --overwrite
    gain_calc = '--calc=(A==0)*(B==1)*({}/2)'.format(gain_years)
    gain_outfile1 = 'growth_years_gain_only_{}.tif'.format(tile_id)
    gain_outfile2 = '--outfile={}'.format(gain_outfile1)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, gain_calc, gain_outfile2, '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW']
    subprocess.check_call(cmd)

    # Pixels with neither loss nor gain but in areas with tree cover density >0
    print "  Creating raster of growth years for no change pixels"
    # gdal_calc.py -A 00N_050W.tif -B Hansen_GFC2015_gain_00N_050W.tif -C Hansen_GFC2014_treecover2000_00N_050W.tif --calc "(A==0)*(B==0)*(C>0)*15" --outfile=no_change.tif --NoDataValue=0 --overwrite
    no_change_calc = '--calc=(A==0)*(B==0)*(C>0)*{}'.format(loss_years)
    no_change_outfile1 = 'growth_years_no_change_{}.tif'.format(tile_id)
    no_change_outfile2 = '--outfile={}'.format(no_change_outfile1)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, '-C', tcd,  no_change_calc, no_change_outfile2, '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW']
    subprocess.check_call(cmd)

    # Pixels with both loss and gain
    print "  Creating raster of growth years for loss and gain pixels"
    # gdal_calc.py -A 00N_050W.tif -B Hansen_GFC2015_gain_00N_050W.tif --calc="((A>0)*(B==1)*((A-1)+(16-A)/2))" --outfile=gain_and_loss.tif --NoDataValue=0 --overwrite
    loss_and_gain_calc = '--calc=((A>0)*(B==1)*((A-1)+({}+1-A)/2))'.format(loss_years)
    loss_and_gain_outfile1 = 'growth_years_loss_and_gain_{}.tif'.format(tile_id)
    loss_and_gain_outfile2 = '--outfile={}'.format(loss_and_gain_outfile1)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, loss_and_gain_calc, loss_and_gain_outfile2, '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW']
    subprocess.check_call(cmd)

    print "  Merging loss, gain, no change, and loss/gain pixels into single raster"
    age_outfile = '{}_{}.tif'.format(utilities.pattern_gain_year_count_mangrove, tile_id)
    cmd = ['gdal_merge.py', '-o', age_outfile, loss_outfile1, gain_outfile1, no_change_outfile1, loss_and_gain_outfile1, '-co', 'COMPRESS=LZW', '-a_nodata', '0']
    subprocess.check_call(cmd)

    utilities.upload_final("growth_years_loss_only", utilities.gain_year_count_mangrove_dir, tile_id)
    utilities.upload_final("growth_years_gain_only", utilities.gain_year_count_mangrove_dir, tile_id)
    utilities.upload_final("growth_years_no_change", utilities.gain_year_count_mangrove_dir, tile_id)
    utilities.upload_final("growth_years_loss_and_gain", utilities.gain_year_count_mangrove_dir, tile_id)
    utilities.upload_final(utilities.pattern_gain_year_count_mangrove, utilities.gain_year_count_mangrove_dir, tile_id)

    end = datetime.datetime.now()
    elapsed_time = end-start

    print "Processing time for tile", tile_id, ":", elapsed_time




