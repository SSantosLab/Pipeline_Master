# Pipeline_Master
All scripts needed to run search and discovery pipeline automatically 

### 03-11-2018
<p>Currently everything assumes you are running as the desgw user. You may not be able to run otherwise - updates coming soon possibly. <br>
Before you run:<br>
check to make sure the season number is what you want. This script will automatically assign a season number for corresponding with the des-gw project (starting at 600). For testing, manually go in and assign a test season number. <br>

In addition to changing the season number, you will also want to make sure you feed it an exposures.list file that is not empty. bns_nite1_first3exposures.list is provided to test with - make sure this is being called in the script. </p>

<p>To run:<br>
> conda activate des18a
>
> python TestAutomate.py
</p>
<p>Outputs will be saved in the cwd
<br>
Outputs:
<br>
test_imgproc_dagmaker.err <br>
test_imgproc_dagmaker.out <br>
test_imgproc_jobsub.err <br>
test_imgproc_jobsub.out <br>
