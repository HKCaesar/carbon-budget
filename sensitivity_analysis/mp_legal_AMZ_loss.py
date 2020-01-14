

import multiprocessing
from functools import partial
import glob
import argparse
from osgeo import gdal
import legal_AMZ_loss
import pandas as pd
import subprocess
import os
import sys
sys.path.append('../')
import constants_and_names as cn
import universal_util as uu

def main ():

    # Files to download for this script.
    download_dict = {cn.loss_dir: [''],
                     cn.WHRC_biomass_2000_unmasked_dir: [cn.pattern_WHRC_biomass_2000_unmasked]
    }


    Brazil_stages = ['all', 'create_forest_extent', 'create_loss',
                     'forest_age_category', 'gain_year_count', 'annual_removals', 'cumulative_removals']


    # The argument for what kind of model run is being done: standard conditions or a sensitivity analysis run
    parser = argparse.ArgumentParser(description='Create tiles of the number of years of carbon gain for mangrove forests')
    parser.add_argument('--stages', '-s', required=True,
                        help='Stages of creating Brazil legal Amazon-specific gross cumulative removals. Options are {}'.format(Brazil_stages))
    parser.add_argument('--run_through', '-r', required=True,
                        help='Options: true or false. true: run named stage and following stages. false: run only named stage.')
    args = parser.parse_args()
    stage_input = args.stages
    run_through = args.run_through


    # Checks the validity of the two arguments. If either one is invalid, the script ends.
    if (stage_input not in Brazil_stages):
        raise Exception('Invalid stage selection. Please provide a stage from {}.'.format(Brazil_stages))
    else:
        pass
    if (run_through not in ['true', 'false']):
        raise Exception('Invalid run through option. Please enter true or false.')
    else:
        pass

    actual_stages = uu.analysis_stages(Brazil_stages, stage_input, run_through)
    print actual_stages


    # By definition, this script is for US-specific removals
    sensit_type = 'Brazil_loss'

    # List of output directories and output file name patterns
    output_dir_list = [cn.Brazil_forest_extent_2000_processed_dir, cn.Brazil_annual_loss_processed_dir,
                       cn.age_cat_natrl_forest_dir, cn.gain_year_count_natrl_forest_dir,
                       # cn.Brazil_annual_gain_AGB_natrl_forest_dir, cn.Brazil_annual_gain_BGB_natrl_forest_dir,
                       # cn.Brazil_cumul_gain_AGCO2_natrl_forest_dir, cn.Brazil_cumul_gain_BGCO2_natrl_forest_dir
                       ]
    output_pattern_list = [cn.pattern_Brazil_forest_extent_2000_processed, cn.pattern_Brazil_annual_loss_processed,
                           cn.pattern_age_cat_natrl_forest, cn.pattern_gain_year_count_natrl_forest,
                           # cn.pattern_Brazil_annual_gain_AGB_natrl_forest, cn.pattern_Brazil_annual_gain_BGB_natrl_forest,
                           # cn.pattern_Brazil_cumul_gain_AGCO2_natrl_forest, cn.pattern_Brazil_cumul_gain_BGCO2_natrl_forest
                           ]


    count = multiprocessing.cpu_count()

    # Creates forest extent 2000 raster from multiple PRODES forest extent rasters
    if 'create_forest_extent' in actual_stages:

        print 'Creating forest extent tiles'

        # List of tiles that could be run. This list is only used to create the FIA region tiles if they don't already exist.
        tile_id_list = uu.tile_list_s3(cn.WHRC_biomass_2000_unmasked_dir)
        # tile_id_list = ["00N_000E", "00N_050W", "00N_060W", "00N_010E", "00N_020E", "00N_030E", "00N_040E", "10N_000E", "10N_010E", "10N_010W", "10N_020E", "10N_020W"] # test tiles
        # tile_id_list = ['50N_130W'] # test tiles
        print tile_id_list
        print "There are {} tiles to process".format(str(len(tile_id_list))) + "\n"

        # Downloads input rasters and lists them
        uu.s3_folder_download(cn.Brazil_forest_extent_2000_raw_dir, '.', sensit_type)
        raw_forest_extent_inputs = glob.glob('*_AMZ_warped_*tif')   # The list of tiles to merge

        # Gets the resolution of a more recent PRODES raster, which has a higher resolution. The merged output matches that.
        raw_forest_extent_input_2019 = glob.glob('*2019_AMZ_warped_*tif')
        prodes_2019 = gdal.Open(raw_forest_extent_input_2019[0])
        transform_2019 = prodes_2019.GetGeoTransform()
        pixelSizeX = transform_2019[1]
        pixelSizeY = -transform_2019[5]
        print pixelSizeX
        print pixelSizeY

        # This merges all six rasters together, so it takes a lot of memory and time. It seems to repeatedly max out
        # at about 300 GB as it progresses abot 15% each time; then the memory drops back to 0 and slowly increases.
        cmd = ['gdal_merge.py', '-o', '{}.tif'.format(cn.pattern_Brazil_forest_extent_2000_merged),
               '-co', 'COMPRESS=LZW', '-a_nodata', '0', '-n', '0', '-ot', 'Byte', '-ps', '{}'.format(pixelSizeX), '{}'.format(pixelSizeY),
               raw_forest_extent_inputs[0], raw_forest_extent_inputs[1], raw_forest_extent_inputs[2],
               raw_forest_extent_inputs[3], raw_forest_extent_inputs[4], raw_forest_extent_inputs[5]]
        subprocess.check_call(cmd)

        # Uploads the merged forest extent raster to s3 for future reference
        uu.upload_final_set(cn.Brazil_forest_extent_2000_merged_dir, cn.pattern_Brazil_forest_extent_2000_merged)

        # Creates legal Amazon extent 2000 tiles
        source_raster = '{}.tif'.format(cn.pattern_Brazil_forest_extent_2000_merged)
        out_pattern = cn.pattern_Brazil_forest_extent_2000_processed
        dt = 'Byte'
        pool = multiprocessing.Pool(count/2)
        pool.map(partial(uu.mp_warp_to_Hansen, source_raster=source_raster, out_pattern=out_pattern, dt=dt), tile_id_list)

        # Checks if each tile has data in it. Only tiles with data are uploaded.
        upload_dir = output_dir_list[0]
        pattern = output_pattern_list[0]
        pool = multiprocessing.Pool(count - 5)
        pool.map(partial(uu.check_and_upload, upload_dir=upload_dir, pattern=pattern), tile_id_list)


    # Creates annual loss raster for 2001-2015 from multiples PRODES rasters
    if 'create_loss' in actual_stages:

        print 'Creating annual loss tiles'

        tile_id_list = uu.tile_list_s3(cn.Brazil_forest_extent_2000_processed_dir)
        print tile_id_list
        print "There are {} tiles to process".format(str(len(tile_id_list))) + "\n"

        # Downloads input rasters and lists them
        uu.s3_folder_download(cn.Brazil_annual_loss_raw_dir, '.', sensit_type)

        # Gets the resolution of the more recent PRODES raster, which has a higher resolution. The merged output matches that.
        raw_forest_extent_input_2017 = glob.glob('Prodes2017_*tif')
        prodes_2017 = gdal.Open(raw_forest_extent_input_2017[0])
        transform_2017 = prodes_2017.GetGeoTransform()
        pixelSizeX = transform_2017[1]
        pixelSizeY = -transform_2017[5]

        # This merges both loss rasters together, so it takes a lot of memory and time. It seems to max out
        # at about 150 GB. Loss from PRODES2014 needs to go second so that its loss years get priority over PRODES2017,
        # which seems to have a preponderance of 2007 loss that appears to often be earlier loss years.
        cmd = ['gdal_merge.py', '-o', '{}.tif'.format(cn.pattern_Brazil_annual_loss_merged),
               '-co', 'COMPRESS=LZW', '-a_nodata', '0', '-n', '0', '-ot', 'Byte', '-ps', '{}'.format(pixelSizeX), '{}'.format(pixelSizeY),
               'Prodes2017_annual_loss_2007_2015.tif', 'Prodes2014_annual_loss_2001_2006.tif']
        subprocess.check_call(cmd)

        # Uploads the merged loss raster to s3 for future reference
        uu.upload_final_set(cn.Brazil_annual_loss_merged_dir, cn.pattern_Brazil_annual_loss_merged)

        # Creates annual loss 2001-2015 tiles
        source_raster = '{}.tif'.format(cn.pattern_Brazil_annual_loss_merged)
        out_pattern = cn.pattern_Brazil_annual_loss_processed
        dt = 'Byte'
        pool = multiprocessing.Pool(count/2)
        pool.map(partial(uu.mp_warp_to_Hansen, source_raster=source_raster, out_pattern=out_pattern, dt=dt), tile_id_list)

        # Checks if each tile has data in it. Only tiles with data are uploaded.
        # In practice, every Amazon tile has loss in it but I figured I'd do this just to be thorough.
        upload_dir = output_dir_list[1]
        pattern = output_pattern_list[1]
        pool = multiprocessing.Pool(count - 5)
        pool.map(partial(uu.check_and_upload, upload_dir=upload_dir, pattern=pattern), tile_id_list)


    # Creates forest age category tiles
    if 'forest_age_category' in actual_stages:

        print 'Creating forest age category tiles'

        # Files to download for this script.
        download_dict = {cn.loss_dir: [''],
                         cn.gain_dir: [cn.pattern_gain],
                         cn.WHRC_biomass_2000_non_mang_non_planted_dir: [
                             cn.pattern_WHRC_biomass_2000_non_mang_non_planted],
                         cn.planted_forest_type_unmasked_dir: [cn.pattern_planted_forest_type_unmasked],
                         cn.mangrove_biomass_2000_dir: [cn.pattern_mangrove_biomass_2000],
                         cn.Brazil_forest_extent_2000_processed_dir: [cn.pattern_Brazil_forest_extent_2000_processed]
                         }


        tile_id_list = uu.tile_list_s3(cn.Brazil_forest_extent_2000_processed_dir)
        print tile_id_list
        print "There are {} tiles to process".format(str(len(tile_id_list))) + "\n"


        # Downloads input files or entire directories, depending on how many tiles are in the tile_id_list
        for key, values in download_dict.iteritems():
            dir = key
            pattern = values[0]
            uu.s3_flexible_download(dir, pattern, '.', sensit_type, tile_id_list)


        # If the model run isn't the standard one, the output directory and file names are changed
        if sensit_type != 'std':
            print "Changing output directory and file name pattern based on sensitivity analysis"
            output_dir_list = uu.alter_dirs(sensit_type, output_dir_list)
            output_pattern_list = uu.alter_patterns(sensit_type, output_pattern_list)


        output_pattern = output_pattern_list[2]

        # This configuration of the multiprocessing call is necessary for passing multiple arguments to the main function
        # It is based on the example here: http://spencerimp.blogspot.com/2015/12/python-multiprocess-with-multiple.html
        # With processes=30, peak usage was about 350 GB using WHRC AGB.
        # processes=26 maxes out above 480 GB for biomass_swap, so better to use fewer than that.
        pool = multiprocessing.Pool(count/2)
        pool.map(partial(legal_AMZ_loss.legal_Amazon_forest_age_category,
                         sensit_type=sensit_type, output_pattern=output_pattern), tile_id_list)
        pool.close()
        pool.join()

        # # For single processor use
        # for tile_id in tile_id_list:
        #
        #     legal_AMZ_loss.legal_Amazon_forest_age_category(tile_id, sensit_type, output_pattern)

        # Uploads output tiles to s3
        uu.upload_final_set(output_dir_list[2], output_pattern_list[2])




















    # # Counts how many processed FIA region tiles there are on s3 already. 16 tiles cover the continental US.
    # FIA_regions_tile_count = uu.count_tiles_s3(cn.FIA_regions_processed_dir)
    #
    # # Only creates FIA region tiles if they don't already exist on s3.
    # if FIA_regions_tile_count == 16:
    #     print "FIA region tiles already created. Copying to s3 now..."
    #     uu.s3_flexible_download(cn.FIA_regions_processed_dir, cn.pattern_FIA_regions_processed, '.', 'std', 'all')
    #
    # else:
    #     print "FIA region tiles do not exist. Creating tiles, then copying to s3 for future use..."
    #     uu.s3_file_download(os.path.join(cn.FIA_regions_raw_dir, cn.name_FIA_regions_raw), '.', 'std')
    #
    #     cmd = ['unzip', '-o', '-j', cn.name_FIA_regions_raw]
    #     subprocess.check_call(cmd)
    #
    #     # Converts the region shapefile to Hansen tiles
    #     pool = multiprocessing.Pool(count/2)
    #     pool.map(US_removal_rates.prep_FIA_regions, tile_id_list)
    #
    #
    # # List of FIA region tiles on the spot machine. Only this list is used for the rest of the script.
    # US_tile_list = uu.tile_list_spot_machine('.', '{}.tif'.format(cn.pattern_FIA_regions_processed))
    # US_tile_id_list = [i[0:8] for i in US_tile_list]
    # # US_tile_id_list = ['50N_130W']    # For testing
    # print US_tile_id_list
    # print "There are {} tiles to process".format(str(len(US_tile_id_list))) + "\n"
    #
    #
    # # Counts how many processed forest age category tiles there are on s3 already. 16 tiles cover the continental US.
    # US_age_tile_count = uu.count_tiles_s3(cn.US_forest_age_cat_processed_dir)
    #
    # # Only creates FIA forest age category tiles if they don't already exist on s3.
    # if US_age_tile_count == 16:
    #     print "Forest age category tiles already created. Copying to spot machine now..."
    #     uu.s3_flexible_download(cn.US_forest_age_cat_processed_dir, cn.pattern_US_forest_age_cat_processed,
    #                             '', 'std', US_tile_id_list)
    #
    # else:
    #     print "Southern forest age category tiles do not exist. Creating tiles, then copying to s3 for future use..."
    #     uu.s3_file_download(os.path.join(cn.US_forest_age_cat_raw_dir, cn.name_US_forest_age_cat_raw), '.', 'std')
    #
    #     # Converts the national forest age category raster to Hansen tiles
    #     source_raster = cn.name_US_forest_age_cat_raw
    #     out_pattern = cn.pattern_US_forest_age_cat_processed
    #     dt = 'Int16'
    #     pool = multiprocessing.Pool(count/2)
    #     pool.map(partial(uu.mp_warp_to_Hansen, source_raster=source_raster, out_pattern=out_pattern, dt=dt), US_tile_id_list)
    #
    #     uu.upload_final_set(cn.US_forest_age_cat_processed_dir, cn.pattern_US_forest_age_cat_processed)
    #
    #
    # # Counts how many processed FIA forest group tiles there are on s3 already. 16 tiles cover the continental US.
    # FIA_forest_group_tile_count = uu.count_tiles_s3(cn.FIA_forest_group_processed_dir)
    #
    # # Only creates FIA forest group tiles if they don't already exist on s3.
    # if FIA_forest_group_tile_count == 16:
    #     print "FIA forest group tiles already created. Copying to spot machine now..."
    #     uu.s3_flexible_download(cn.FIA_forest_group_processed_dir, cn.pattern_FIA_forest_group_processed, '', 'std', US_tile_id_list)
    #
    # else:
    #     print "FIA forest group tiles do not exist. Creating tiles, then copying to s3 for future use..."
    #     uu.s3_file_download(os.path.join(cn.FIA_forest_group_raw_dir, cn.name_FIA_forest_group_raw), '.', 'std')
    #
    #     # Converts the national forest group raster to Hansen forest group tiles
    #     source_raster = cn.name_FIA_forest_group_raw
    #     out_pattern = cn.pattern_FIA_forest_group_processed
    #     dt = 'Byte'
    #     pool = multiprocessing.Pool(count/2)
    #     pool.map(partial(uu.mp_warp_to_Hansen, source_raster=source_raster, out_pattern=out_pattern, dt=dt), US_tile_id_list)
    #
    #     uu.upload_final_set(cn.FIA_forest_group_processed_dir, cn.pattern_FIA_forest_group_processed)
    #
    #
    # # Downloads input files or entire directories, depending on how many tiles are in the tile_id_list
    # for key, values in download_dict.iteritems():
    #     dir = key
    #     pattern = values[0]
    #     uu.s3_flexible_download(dir, pattern, '.', sensit_type, US_tile_id_list)
    #
    #
    #
    # # Table with US-specific removal rates
    # cmd = ['aws', 's3', 'cp', os.path.join(cn.gain_spreadsheet_dir, cn.table_US_removal_rate), '.']
    # subprocess.check_call(cmd)
    #
    # # Imports the table with the region-group-age AGB removal rates
    # gain_table = pd.read_excel("{}".format(cn.table_US_removal_rate),
    #                            sheet_name="US_rates_for_model")
    #
    # # Converts gain table from wide to long, so each region-group-age category has its own row
    # gain_table_group_region_by_age = pd.melt(gain_table, id_vars=['FIA_region_code', 'forest_group_code'],
    #                                   value_vars=['growth_young', 'growth_middle',
    #                                               'growth_old'])
    # gain_table_group_region_by_age = gain_table_group_region_by_age.dropna()
    #
    # # In the forest age category raster, each category has this value
    # age_dict = {'growth_young': 1000, 'growth_middle': 2000, 'growth_old': 3000}
    #
    # # Creates a unique value for each forest group-region-age category in the table.
    # # Although these rates are applied to all standard gain model pixels at first, they are not ultimately used for
    # # pixels that have Hansen gain (see below).
    # gain_table_group_region_age = gain_table_group_region_by_age.replace({"variable": age_dict})
    # gain_table_group_region_age['age_cat'] = gain_table_group_region_age['variable']*10
    # gain_table_group_region_age['group_region_age_combined'] = gain_table_group_region_age['age_cat'] + \
    #                                           gain_table_group_region_age['forest_group_code']*100 + \
    #                                           gain_table_group_region_age['FIA_region_code']
    # # Converts the forest group-region-age codes and corresponding gain rates to a dictionary,
    # # where the key is the unique group-region-age code and the value is the AGB removal rate.
    # gain_table_group_region_age_dict = pd.Series(gain_table_group_region_age.value.values, index=gain_table_group_region_age.group_region_age_combined).to_dict()
    # print gain_table_group_region_age_dict
    #
    #
    # # Creates a unique value for each forest group-region category using just young forest rates.
    # # These are assigned to Hansen gain pixels, which automatically get the young forest rate, regardless of the
    # # forest age category raster.
    # gain_table_group_region = gain_table_group_region_age.drop(gain_table_group_region_age[gain_table_group_region_age.age_cat != 10000].index)
    # gain_table_group_region['group_region_combined'] = gain_table_group_region['forest_group_code']*100 + \
    #                                                    gain_table_group_region['FIA_region_code']
    # # Converts the forest group-region codes and corresponding gain rates to a dictionary,
    # # where the key is the unique group-region code (youngest age category) and the value is the AGB removal rate.
    # gain_table_group_region_dict = pd.Series(gain_table_group_region.value.values, index=gain_table_group_region.group_region_combined).to_dict()
    # print gain_table_group_region_dict
    #
    #
    # # count/2 on a m4.16xlarge maxes out at about 230 GB of memory (processing 16 tiles at once), so it's okay on an m4.16xlarge
    # pool = multiprocessing.Pool(count/2)
    # pool.map(partial(US_removal_rates.US_removal_rate_calc, gain_table_group_region_age_dict=gain_table_group_region_age_dict,
    #                  gain_table_group_region_dict=gain_table_group_region_dict,
    #                  output_pattern_list=output_pattern_list, sensit_type=sensit_type), US_tile_id_list)
    # pool.close()
    # pool.join()
    #
    # # # For single processor use
    # # for tile_id in US_tile_id_list:
    # #
    # #     US_removal_rates.US_removal_rate_calc(tile_id, gain_table_group_region_age_dict, gain_table_group_region_dict,
    # #                                           output_pattern_list, sensit_type)
    #
    #
    # # Uploads output tiles to s3
    # for i in range(0, len(output_dir_list)):
    #     uu.upload_final_set(output_dir_list[i], output_pattern_list[i])


if __name__ == '__main__':
    main()