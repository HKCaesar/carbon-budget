from subprocess import Popen, PIPE, STDOUT, check_call
import datetime
import rasterio
import sys
sys.path.append('../')
import constants_and_names as cn
import universal_util as uu

# Gets the names of the input tiles
def tile_names(tile_id):

    # Names of the loss, gain, tree cover density, intact forest landscape, mangrove biomass and planted forest tiles
    loss = '{0}_{1}.tif'.format(cn.pattern_loss, tile_id)
    gain = '{0}_{1}.tif'.format(cn.pattern_gain, tile_id)
    model_extent = '{0}_{1}.tif'.format(tile_id, cn.pattern_model_extent)

    return loss, gain, model_extent


# Creates gain year count tiles for pixels that only had loss
def create_gain_year_count_loss_only(tile_id):

    uu.print_log("Gain year count for loss only pixels:", tile_id)

    # start time
    start = datetime.datetime.now()

    # Names of the loss, gain and tree cover density tiles
    loss, gain, model_extent = tile_names(tile_id)

    # Pixels with loss only
    loss_calc = '--calc=(A>0)*(B==0)*(C>0)*(A-1)'
    loss_outfilename = '{}_growth_years_loss_only.tif'.format(tile_id)
    loss_outfilearg = '--outfile={}'.format(loss_outfilename)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, '-C', model_extent, loss_calc, loss_outfilearg,
           '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW', '--type', 'Byte', '--quiet']
    uu.log_subprocess_output_full(cmd)

    # Prints information about the tile that was just processed
    uu.end_of_fx_summary(start, tile_id, 'growth_years_loss_only')


# Creates gain year count tiles for pixels that only had gain
def create_gain_year_count_gain_only_standard(tile_id):

    uu.print_log("Gain year count for gain only pixels using standard function:", tile_id)

    # start time
    start = datetime.datetime.now()

    # Names of the loss, gain and tree cover density tiles
    loss, gain, model_extent = tile_names(tile_id)

    # Pixels with gain only
    gain_calc = '--calc=(A==0)*(B==1)*(C>0)*({}/2)'.format(cn.gain_years)
    gain_outfilename = '{}_growth_years_gain_only.tif'.format(tile_id)
    gain_outfilearg = '--outfile={}'.format(gain_outfilename)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, '-C', model_extent, gain_calc, gain_outfilearg,
           '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW', '--type', 'Byte', '--quiet']
    uu.log_subprocess_output_full(cmd)

    # Prints information about the tile that was just processed
    uu.end_of_fx_summary(start, tile_id, 'growth_years_gain_only')


# Creates gain year count tiles for pixels that only had gain
def create_gain_year_count_gain_only_maxgain(tile_id):

    uu.print_log("Gain year count for gain only pixels using maxgain function:", tile_id)

    # Names of the loss, gain and tree cover density tiles
    loss, gain, model_extent = tile_names(tile_id)

    # start time
    start = datetime.datetime.now()

    # Pixels with gain only
    gain_calc = '--calc=(A==0)*(B==1)*(C>0)*({})'.format(cn.loss_years)
    gain_outfilename = '{}_growth_years_gain_only.tif'.format(tile_id)
    gain_outfilearg = '--outfile={}'.format(gain_outfilename)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, '-C', model_extent, gain_calc, gain_outfilearg,
           '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW', '--type', 'Byte', '--quiet']
    uu.log_subprocess_output_full(cmd)

    # Prints information about the tile that was just processed
    uu.end_of_fx_summary(start, tile_id, 'growth_years_gain_only')


# Creates gain year count tiles for pixels that had neither loss not gain
def create_gain_year_count_no_change(tile_id):

    uu.print_log("Gain year count for pixels with neither loss nor gain:", tile_id)

    # Names of the loss, gain and tree cover density tiles
    loss, gain, model_extent = tile_names(tile_id)

    # start time
    start = datetime.datetime.now()

    # Pixels with neither loss nor gain
    no_change_calc = '--calc=(A==0)*(B==0)*(C>0)*{}'.format(cn.loss_years)
    no_change_outfilename = '{}_growth_years_no_change.tif'.format(tile_id)
    no_change_outfilearg = '--outfile={}'.format(no_change_outfilename)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, '-C', model_extent, no_change_calc,
           no_change_outfilearg, '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW', '--type', 'Byte', '--quiet']
    uu.log_subprocess_output_full(cmd)

    # Prints information about the tile that was just processed
    uu.end_of_fx_summary(start, tile_id, 'growth_years_no_change')


# Creates gain year count tiles for pixels that had both loss and gain
def create_gain_year_count_loss_and_gain_standard(tile_id):

    uu.print_log("Loss and gain pixel processing using standard function:", tile_id)

    # Names of the loss, gain and tree cover density tiles
    loss, gain, model_extent = tile_names(tile_id)

    # start time
    start = datetime.datetime.now()

    # Pixels with both loss and gain
    loss_and_gain_calc = '--calc=((A>0)*(B==1)*(C>0)*((A-1)+floor(({}+1-A)/2)))'.format(cn.loss_years)
    loss_and_gain_outfilename = '{}_growth_years_loss_and_gain.tif'.format(tile_id)
    loss_and_gain_outfilearg = '--outfile={}'.format(loss_and_gain_outfilename)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, '-C', model_extent, loss_and_gain_calc,
           loss_and_gain_outfilearg, '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW', '--type', 'Byte', '--quiet']
    uu.log_subprocess_output_full(cmd)

    # Prints information about the tile that was just processed
    uu.end_of_fx_summary(start, tile_id, 'growth_years_loss_and_gain')


# Creates gain year count tiles for pixels that had both loss and gain
def create_gain_year_count_loss_and_gain_maxgain(tile_id):

    uu.print_log("Loss and gain pixel processing using maxgain function:", tile_id)

    # Names of the loss, gain and tree cover density tiles
    loss, gain, model_extent = tile_names(tile_id)

    # start time
    start = datetime.datetime.now()

    # Pixels with both loss and gain
    loss_and_gain_calc = '--calc=((A>0)*(B==1)*(C>0)*({}-1))'.format(cn.loss_years)
    loss_and_gain_outfilename = '{}_growth_years_loss_and_gain.tif'.format(tile_id)
    loss_and_gain_outfilearg = '--outfile={}'.format(loss_and_gain_outfilename)
    cmd = ['gdal_calc.py', '-A', loss, '-B', gain, '-C', model_extent, loss_and_gain_calc,
           loss_and_gain_outfilearg, '--NoDataValue=0', '--overwrite', '--co', 'COMPRESS=LZW', '--type', 'Byte', '--quiet']
    uu.log_subprocess_output_full(cmd)

    # Prints information about the tile that was just processed
    uu.end_of_fx_summary(start, tile_id, 'growth_years_loss_and_gain')


# Merges the four gain year count tiles above to create a single gain year count tile
def create_gain_year_count_merge(tile_id, pattern, sensit_type):

    uu.print_log("Merging loss, gain, no change, and loss/gain pixels into single raster for {}".format(tile_id))

    # start time
    start = datetime.datetime.now()

    # The four rasters from above that are to be merged
    loss_only_gain_years = '{}_growth_years_loss_only.tif'.format(tile_id)
    gain_only_gain_years = '{}_growth_years_gain_only.tif'.format(tile_id)
    no_change_gain_years = '{}_growth_years_no_change.tif'.format(tile_id)
    loss_and_gain_gain_years = '{}_growth_years_loss_and_gain.tif'.format(tile_id)

    # Names of the output tiles
    gain_year_count_merged = '{0}_{1}.tif'.format(tile_id, pattern)

    # Opens biomass tile
    with rasterio.open(loss_only_gain_years) as loss_only_gain_years_src:

        # Grabs metadata about the tif, like its location/projection/cellsize
        kwargs = loss_only_gain_years_src.meta

        # Grabs the windows of the tile (stripes) so we can iterate over the entire tif without running out of memory
        windows = loss_only_gain_years_src.block_windows(1)

        # Updates kwargs for the output dataset
        kwargs.update(
            driver='GTiff',
            count=1,
            compress='lzw',
            nodata=0
        )

        gain_only_gain_years_src = rasterio.open(gain_only_gain_years)
        no_change_gain_years_src = rasterio.open(no_change_gain_years)
        loss_and_gain_gain_years_src = rasterio.open(loss_and_gain_gain_years)

        # Opens the output tile, giving it the arguments of the input tiles
        gain_year_count_merged_dst = rasterio.open(gain_year_count_merged, 'w', **kwargs)

        # Adds metadata tags to the output raster
        uu.add_rasterio_tags(gain_year_count_merged_dst, sensit_type)
        gain_year_count_merged_dst.update_tags(
            units='years')
        gain_year_count_merged_dst.update_tags(
            min_possible_value='0')
        gain_year_count_merged_dst.update_tags(
            max_possible_value=cn.loss_years)
        gain_year_count_merged_dst.update_tags(
            source='Gain years are assigned based on the combination of Hansen loss and gain in each pixel. There are four combinations: neither loss nor gain, loss only, gain only, loss and gain.')
        gain_year_count_merged_dst.update_tags(
            extent='Full model extent')

        # Iterates across the windows (1 pixel strips) of the input tile
        for idx, window in windows:

            loss_only_gain_years_window = loss_only_gain_years_src.read(1, window=window)
            gain_only_gain_years_window = gain_only_gain_years_src.read(1, window=window)
            no_change_gain_years_window = no_change_gain_years_src.read(1, window=window)
            loss_and_gain_gain_years_window = loss_and_gain_gain_years_src.read(1, window=window)

            gain_year_count_merged_window = loss_only_gain_years_window + gain_only_gain_years_window + \
                                            no_change_gain_years_window + loss_and_gain_gain_years_window

            gain_year_count_merged_dst.write_band(1, gain_year_count_merged_window, window=window)

    # Prints information about the tile that was just processed
    uu.end_of_fx_summary(start, tile_id, pattern)