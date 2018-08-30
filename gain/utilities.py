import subprocess
import glob


def s3_download(source, dest):

    cmd = ['aws', 's3', 'cp', source, dest, '-r']
    subprocess.check_call(cmd)

# Lists the tiles in a folder in s3
def tile_list(source):

    ## For an s3 folder in a bucket using AWSCLI
    # Captures the list of the files in the folder
    out = subprocess.Popen(['aws', 's3', 'ls', source], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    # Writes the output string to a text file for easier interpretation
    aboveground_c_tiles = open("aboveground_c_tiles.txt", "w")
    aboveground_c_tiles.write(stdout)
    aboveground_c_tiles.close()

    file_list = []

    # Iterates through the text file to get the names of the tiles and appends them to list
    with open("aboveground_c_tiles.txt", 'r') as tile:
        for line in tile:
            num = len(line.strip('\n').split(" "))
            tile_name = line.strip('\n').split(" ")[num - 1]
            tile_short_name = tile_name.replace('_carbon.tif', '')
            file_list.append(tile_short_name)

    return file_list

def upload_final(upload_dir, tile_id):

    files = glob.glob('growth_years_*{}.tif'.format(tile_id))

    print files

    for f in files:

        print "uploading {}".format(f)
        cmd = ['aws', 's3', 'cp', f, upload_dir]
        print cmd

        try:
            subprocess.check_call(cmd)
        except:
            print "Error uploading output tile"



##### Not currently using the below functions


def coords(tile_id):
    NS = tile_id.split("_")[0][-1:]
    EW = tile_id.split("_")[1][-1:]

    if NS == 'S':
        ymax =-1*int(tile_id.split("_")[0][:2])
    else:
        ymax = int(str(tile_id.split("_")[0][:2]))

    if EW == 'W':
        xmin = -1*int(str(tile_id.split("_")[1][:3]))
    else:
        xmin = int(str(tile_id.split("_")[1][:3]))


    ymin = str(int(ymax) - 10)
    xmax = str(int(xmin) + 10)

    return ymax, xmin, ymin, xmax


def wgetloss(tile_id):
    print "download hansen loss tile"
    loss_tile = '{}_loss.tif'.format(tile_id)
    cmd = ['wget', r'http://glad.geog.umd.edu/Potapov/GFW_2015/tiles/{}.tif'.format(tile_id),
           '-O', loss_tile]

    subprocess.check_call(cmd)

    return loss_tile

def wget2015data(tile_id, filetype):

    outfile = '{0}_{1}_h.tif'.format(tile_id, filetype)

    website = 'https://storage.googleapis.com/earthenginepartners-hansen/GFC-2015-v1.3/Hansen_GFC-2015-v1.3_{0}_{1}.tif'.format(filetype, tile_id)
    cmd = ['wget', website, '-O', outfile]
    print cmd

    subprocess.check_call(cmd)

    return outfile


def rasterize_shapefile(xmin, ymax, xmax, ymin, shapefile, output_tif, attribute_field):
    layer = shapefile.replace(".shp", "")
    # attribute_field = 'old_100'
    cmd= ['gdal_rasterize', '-te', str(xmin), str(ymin), str(xmax), str(ymax), '-a', attribute_field, '-co', 'COMPRESS=LZW', '-tr', '.00025', '.00025', '-tap', '-a_nodata', '0', '-l', layer, shapefile, output_tif]

    subprocess.check_call(cmd)

    return output_tif


def resample_00025(input_tif, resampled_tif):
    # resample to .00025
    cmd = ['gdal_translate', input_tif, resampled_tif, '-tr', '.00025', '.00025', '-co', 'COMPRESS=LZW']
    subprocess.check_call(cmd)


