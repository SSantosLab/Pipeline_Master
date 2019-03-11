# Pipeline_Master
All scripts needed to run search and discovery pipeline automatically 

## 03-11-2018 ##
Currently everything assumes you are running as the desgw user. You may not be able to run otherwise - updates coming soon possibly.

Before you run:
check to make sure the season number is what you want. This script will automatically assign a season number for corresponding with the des-gw project (starting at 600). For testing, manually go in and assign a test season number. 

In addition to changing the season number, you will also want to make sure you feed it an exposures.list file that is not empty. bns_nite1_first3exposures.list is provided to test with - make sure this is being called in the script. 

To run:
> conda activate des18a
> python TestAutomate.py

Outputs will be saved in the cwd
Outputs:
test_imgproc_dagmaker.err
test_imgproc_dagmaker.out
test_imgproc_jobsub.err
test_imgproc_jobsub.out
