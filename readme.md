## Global forest carbon flux model

### Purpose and scope
This model maps gross annual greenhouse gas emissions from forests, 
gross carbon removals (sequestration) by forests, and the difference between them 
(net flux), all between 2001 and 2019. 
Gross emissions includes CO2, NH4, and N20 and all carbon pools, and gross removals includes removals into aboveground and belowground biomass carbon. 
Although the model is run for all tree canopy densities (per Hansen et al. 2013), it is most relevant to
pixels with canopy density >30% in 2000 or pixels which subsequently had tree cover gain (per Hansen et al. 2013).
It covers planted forests in most of the world, mangroves, and non-mangrove natural forests, and excludes palm oil plantations that existed more than 20 years ago.
It essentially spatially applies IPCC national greenhouse gas inventory rules (2016 guidelines) for forests.
It covers only forests converting to non-forests, non-forests converted to forests and forests remaining forests (no other land 
use transitions). The model is described and published in Harris et al. (2021) Nature Climate Change
"Global maps of twenty-first century forest carbon fluxes" (https://www.nature.com/articles/s41558-020-00976-6).

### Inputs
Well over twenty inputs are needed to run this model. Most are spatial, but some are tabular.
All spatial data are converted to 10 x 10 degree raster tiles at 0.00025 x 0.00025 degree resolution 
(approximately 30 x 30 m at the equator). The tabular data are generally annual biomass removal (i.e. 
sequestration) factors (e.g., mangroves, planted forests, natural forests), which are then applied to spatial data. 
Spatial data include annual tree cover loss, biomass densities in 2000, drivers of tree cover loss, 
ecozones, tree cover extent in 2000, elevation, etc. Different inputs are needed for different
steps in the model. This repository includes scripts for processing all of the needed inputs. 
Many inputs can be processed the same way (e.g., many rasters can be processed using the same gdal function) but some need special treatment.
The input processing scripts are scattered among almost all the folders, unfortunately, a historical legacy of how I built this out
which I haven't fixed yet. The data prep scripts are generally in the folder for which their outputs are most relevant.

### Outputs
There are three key outputs produced: gross GHG emissions, gross removals, and net flux, all for 2001-2019. 
These are produced at two resolutions: 0.00025 x 0.00025 degrees 
(approximately 30 x 30 m at the equator) in 10 x 10 degree rasters (to make outputs a 
manageable size), and 0.04 x 0.04 degrees (approximately 4 x 4 km at the equator) as global rasters.

#### 30-m outputs

The 30-m outputs are used for zonal statistics analyses (i.e. emissions, removals, or net in polygons of interest)
and mapping on the Global Forest Watch web platform or at small scales (where 30-m pixels can be distinguished). 
Individual emissions can be assigned years based on Hansen loss during further analyses 
but removals and net flux are cumulative over the entire model run and cannot be assigned specific years. 
This 30-m output is in megagrams CO2e/ha 2001-2019 (i.e. densities) and includes all tree cover densities ("full extent")
`(((TCD2000>0 AND WHRC AGB2000>0) OR Hansen gain=1 OR mangrove AGB2000>0) NOT IN pre-2000 plantations)`.
However, the model is designed to be used specifically for forests, so the model creates three derivative 30-m
outputs for each key output (gross emissions, gross removals, net flux) as well 
(only for the standard model, not for sensitivity analyses):

1) Per pixel values for the full model extent (all tree cover densities) 
   `(((TCD2000>0 AND WHRC AGB2000>0) OR Hansen gain=1 OR mangrove AGB2000>0) NOT IN pre-2000 plantations)`
2) Per hectare values for forest pixels only 
   `(((TCD2000>30 AND WHRC AGB2000>0) OR Hansen gain=1 OR mangrove AGB2000>0) NOT IN pre-2000 plantations)`
3) Per pixel values for forest pixels only  
   `(((TCD2000>30 AND WHRC AGB2000>0) OR Hansen gain=1 OR mangrove AGB2000>0) NOT IN pre-2000 plantations)`

The per hectare outputs are used for making maps, while the per pixel outputs are used for analyses because the values
of those pixels can be summed within areas of interest. 
(The pixels of the per hectare outputs should not be summed but they can be averaged.)
Statistics from this model are always based on the "forest extent" rasters, not the "full extent" rasters.
The full model extent outputs should generally not be used but are created by the model in case they are needed.

#### 4-km outputs

The 4-km outputs are used for static large-scale maps, like in publications and presentations. 
The units are Mt CO2e/pixel/year (in order to show absolute values). They are created using the "forest extent" 
per pixel 30-m rasters, not the "full extent" 30-m rasters. 

Although gross emissions are traditionally given positive (+) values and
gross removals are traditionally given negative (-) values, the 30-m gross removals rasters are positive, while the 4-km gross removals rasters are negative. 
Net flux at both scales can be positive or negative depending on the balance of emissions and removals in the area of interest.

In addition to these three key outputs, there are many intermediate output rasters from the model,
some of which may be useful for QC, analyses by area of interest, or something else. 
All of these are at 0.00025 x 0.00025 degree resolution and reported as per hectare values (as opposed to per pixel values), if applicable. 
Intermediate outputs include the annual aboveground and belowground biomass removal rates
for all kinds of forests, the type of removal factor applied to each pixel, the carbon pool densities in 2000, 
carbon pool densities in the year of tree cover loss, and the number of years in which removals occurred. 

Almost all model output have metadata associated with them, viewable using the `gdalinfo` command line utility (https://gdal.org/programs/gdalinfo.html). 
Metadata includes units, date created, model version, geographic extent, and more. Unfortunately, the metadata are not viewable in ArcMap.

Model runs also automatically generate a txt log that is saved to s3. This log includes nearly everything that is output in the console.
This log is useful for documenting model runs and checking for mistakes/errors in retrospect, although it does not capture errors that terminate the model.
For example, users can examine it to see if the correct input tiles were downloaded or if the intended tiles were used during the model run.  

### Running the model
There are two ways to run the model: as a series of individual scripts, or from a master script, which runs the individual scripts sequentially.
Which one to use depends on what you are trying to do. Generally, the individual scripts (which correspond to model stages) are
more appropriate for development and testing, while the master script is better for running
the main part of the model from start to finish in one go. In either case, the code must be cloned from this repository.
Run at scale, both options iterate through a list of ~275 10x10 degree tiles. (Different model stages have different numbers of tiles.)
Run all tiles in the model extent fully through one model stage before starting on the next stage. 
(The master script does this automatically.) If a user wants to run the model on just one or a few tiles, 
that can be done through a command line argument (`--tile-id-list` or `-l`). 
If individual tiles are listed, only those will be downloaded and run. This is a natural system for testing. 

The model runs inside a Docker container. Once you have Docker configured on your system, have cloned this repository, 
and have configured access to Amazon Web Services, you can do the following on the command line in the same folder as the repository on your system.
This will enter the command line in the Docker container. 

For runs on my local computer, I use `docker-compose` so that the Docker is mapped to my computer's drives. 
I do this for development and testing. If running on another computer, you will need to change the local 
folder being mapped in `docker-compose.yaml` to fit your computer's directory structure.
`docker-compose build`
`docker-compose run --rm -e AWS_SECRET_ACCESS_KEY=... -e AWS_ACCESS_KEY_ID=... carbon-budget`

For runs on an AWS r5d spot machine (for full model runs), I use `docker build`.
`docker build . -t gfw/carbon-budget`
`docker run --rm -it -e AWS_SECRET_ACCESS_KEY=... -e AWS_ACCESS_KEY_ID=... gfw/carbon-budget`

Before doing a model run, confirm that the dates of the relevant input and output s3 folders are correct in `constants_and_names.py`. 
Depending on what exactly the user is running, the user may have to change lots of dates in the s3 folders or change none.
Unfortunately, I can't really give better guidance than that; it really depends on what part of the model is being run and how.
(I want to make the situations under which users change folder dates more consistent eventually.)

The model can be run either using multiple processors or one processor. The former is for full model runs,
while the latter is for model development. The user can switch between these two versions by commenting out
the appropriate code chunks in each script. The single-processor option is commented out by default. 
One important thing to note is that if a user tries to use too many processors, the system will run out of memory and
can crash (particularly on AWS EC2 instances). Thus, it is important not to use too many processors at once.
Generally, the limitation in running the model is the amount of memory available on the system rather than the number of processors.
Each script has been somewhat calibrated to use a safe number of processors for an r5d.24xlarge EC2 instance,
and often the number of processors being used is 1/2 or 1/3 of the actual number available.
If the tiles were smaller (e.g., 1x1 degree), more processors could be used but then there'd also be more tiles to process, so I'm not sure that would be any faster.
Users can track memory usage in realtime using the `htop` command line utility in the Docker container. 


#### Individual scripts
The flux model is comprised of many separate scripts (or stages), each of which can be run separately and
has its own inputs and output(s). Combined, these comprise the flux model. There are several data preparation
scripts, several for the removals (sequestration/gain) model, a few to generate carbon pools, one for calculating
gross emissions, one for calculating net flux, and one for aggregating key results into coarser 
resolution rasters for mapping. 
Each script really has two parts: its `mp_` (multiprocessing) part and the part that actually does the calculations
on each 10x10 degree tile.
The `mp_` scripts (e.g., `mp_create_model_extent.py`) are the ones that are run. They download input files,
do any needed preprocessing, change output folder names as needed, list the tiles that are going to be run, etc.,
then initiate the actual work done on each tile in the script without the `mp_` prefix.
The order in which the individual stages must be run is very specific; many scripts depend on
the outputs of other scripts. Looking at the files that must be downloaded for the 
script to run will show what files must already be created and therefore what scripts must have already been
run. Alternatively, you can look at `run_full_model.py` to see the order in which model stages are run. 
The date component of the output directory on s3 generally must be changed in `constants_and_names.py`
for each output file unless a date argument is provided on the command line. 

Each script can be run either using multiple processors or one processor. The former is for full model runs,
while the latter is for model development. The user can switch between these two versions by commenting out
the appropriate code chunks. 

#### Master script 
The master script runs through all of the non-preparatory scripts in the model: some removal factor creation, gross removals, carbon
pool generation, gross emissions, net flux, and aggregation. It includes all the arguments needed to run
every script. The user can control what model components are run to some extent and set the date part of 
the output directories. The emissions C++ code has to be be compiled before running the master script (see below).
Preparatory scripts like creating soil carbon tiles or mangrove tiles are not included in the master script because
they are run very infrequently.

`python run_full_model.py -t std -s all -r true -d 20200822 -l all -ce loss -p biomass_soil -tcd 30 -ma true -us true -ln "This will run the entire standard model, including creating mangrove and US removal factor tiles, on all tiles and output everything in s3 folders with the date 20200822."`

| Argument | Required/Optional | Description | 
| -------- | ----------- | ------ |
| `model-type` | Required | Standard model (`std`) or a sensitivity analysis. Refer to `constants_and_names.py` for valid list of sensitivity analyses. |
| `stages` | Required | The model stage at which the model should start. `all` will run the following stages in this order: model_extent, forest_age_category_IPCC, annual_removals_IPCC, annual_removals_all_forest_types, gain_year_count, gross_removals_all_forest_types, carbon_pools, gross_emissions, net_flux, aggregate, create_supplementary_outputs |
| `run-through` | Required | Options: true or false. true: run stage provided in `stages` argument and all following stages. false: run only stage in `stages` argument. |
| `run-date` | Required | Date of run. Must be format YYYYMMDD. This sets the output folder in s3. |
| `tile-id-list` | Required | List of tile ids to use in the model. Should be of form 00N_110E or 00N_110E,00N_120E or all |
| `carbon-pool-extent` | Optional | Extent over which carbon pools should be calculated: loss or 2000 or loss,2000 or 2000,loss |
| `pools-to-use` | Optional | Options are soil_only or biomass_soil. Former only considers emissions from soil. Latter considers emissions from biomass and soil. |
| `tcd-threshold` | Optional | Tree cover density threshold above which pixels will be included in the aggregation. |
| `std-net-flux-aggreg` | Optional | The s3 standard model net flux aggregated tif, for comparison with the sensitivity analysis map. |
| `mangroves` | Optional | Create mangrove removal factor tiles as the first stage. true or false |
| `us-rates` | Optional | Create US-specific removal factor tiles as the first stage (or second stage, if mangroves are enabled). true or false |
| `log-note` | Optional | Adds text to the beginning of the log |

##### Running the emissions model
The gross emissions script is the only part of the model that uses C++. Thus, it must be manually compiled before running.
There are a few different versions of the emissions script: one for the standard model and a few other for
sensitivitity analyses.
The command for compiling the C++ script is (subbing in the actual file name): 

`c++ /usr/local/app/emissions/cpp_util/calc_gross_emissions_[VERSION].cpp -o /usr/local/app/emissions/cpp_util/calc_gross_emissions_[VERSION].exe -lgdal`

### Sensitivity analysis
Several variations of the model are included; these are the sensitivity variants, as they use different inputs or parameters. 
They can be run by changing the `model-type` argument from `std` to an option found in `constants_and_names.py`. 
Each sensitivity analysis variant starts at a different stage in the model and runs to the final stage,
except that sensitivity analyses do not include the creation of the supplementary outputs (per pixel tiles, forest extent tiles).
Some use all tiles and some use a smaller extent.

| Sensitivity analysis | Description | Extent | Starting stage | 
| -------- | ----------- | ------ | ------ |
| `std` | Standard model | Global | `mp_model_extent.py` |
| `maxgain` | Maximum number of years of gain (removals) for gain-only and loss-and-gain pixels | Global | `gain_year_count_all_forest_types.py` |
| `no_shifting_ag` | Shifting agriculture driver is replaced with commodity-driven deforestation driver | Global | `mp_calculate_gross_emissions.py` |
| `convert_to_grassland` | Forest is assumed to be converted to grassland instead of cropland in the emissions model| Global | `mp_calculate_gross_emissions.py` |
| `biomass_swap` | Uses Saatchi 1-km AGB map instead of Baccini 30-m map for starting carbon densities | Extent of Saatchi map, which is generally the tropics| `mp_model_extent.py` |
| `US_removals` | Uses IPCC default removal factors for the US instead of US-specific removal factors from USFS FIA | Continental US | `mp_annual_gain_rate_AGC_BGC_all_forest_types.py` |
| `no_primary_gain` | Primary forests and IFLs are assumed to not have any removals| Global | `mp_forest_age_category_IPCC.py` |
| `legal_Amazon_loss` | Uses Brazil's PRODES annual deforestation system instead of Hansen loss | Legal Amazon| `mp_model_extent.py` |
| `Mekong_loss` | Uses Hansen loss v2.0 (multiple loss in same pixel). NOTE: Not used for flux model v1.2.0, so this is not currently supported. | Mekong region | N/A |

### Modifying the model
It is recommended that any changes to the model be tested in a local Docker instance before running on an EC2 instance.
A standard development route is: 

1) make changes to a single model script and run using the single processor option on a single tile (easiest for debugging) in local Docker,

2) run single script on a few representative tiles using a single processor in local Docker,

3) run single script on a few representative tiles using multiple processor option,

4) run the single script from the master script on a few representative tiles using multiple processor option to confirm that changes work when using master script,

5) run single script on a few representative tiles using multiple processors on EC2 instance (need to commit and push changes to GitHub first),

6) run master script on all tiles using multiple processors on EC2 instance. If the changes likely affected memory usage, make sure to watch memory with `htop` to make sure that too much memory isn't required. If too much memory is needed, reduce the number of processors being called in the script. 

Obviously, depending on the changes being made, some of these steps can be ommitted. 

### Dependencies
Theoretically, this model should run anywhere that the correct Docker container can be started and there is access to the AWS s3 bucket. 
The Docker container should be self-sufficient in that it is configured to include the right Python packages, C++ compiler, GDAL, etc.
It is described in `Dockerfile`, with Python requirements (installed during Docker creation) in `requirements.txt`.
On an AWS EC2 instance, I have only run it on r5d instance types but it might be able to run on others.
At the least, it needs a certain type of memory configuration on the EC2 instance (at least one large SSD volume, I believe). 
Otherwise, I do not know the limitations and constraints on running this model. 

### Contact information
David Gibbs

Global Forest Watch, World Resources Institute, Washington, D.C.

david.gibbs@wri.org
