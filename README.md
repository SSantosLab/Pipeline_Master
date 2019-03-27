# Pipeline_Master
All scripts needed to run search and discovery pipeline automatically 

# 03-27-2018 #
Currently everything assumes you are running as the desgw user. You may not be able to run otherwise - updates coming soon possibly.

Before you run:
check to make sure the season number is what you want. This script will automatically assign a season number for corresponding with the des-gw project (starting at 600). For testing, manually go in and assign a test season number. 

In addition to changing the season number, you will also want to make sure you feed it an exposures.list file that is not empty. bns_nite1_first3exposures.list is provided to test with - make sure this is being called in the script. 

To run:
> conda activate des18a

> python TestAutomate_v2.py

Optional arguments: 

--rootdir: directory where Main-Injector, gw_workflow, and Post-Processing live. Use this if that is not your cwd

--season: what season number to use for the exposures

--tesExps: a .list file with the exposures you want to run with

-C : for DAGMaker to run even if that exposure has already been run. 

Outputs will be saved in the cwd

Outputs:

test_imgproc_dagmaker.err

test_imgproc_dagmaker.out

test_imgproc_jobsub.err

test_imgproc_jobsub.out
