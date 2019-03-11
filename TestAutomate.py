import subprocess, os
from threading import Thread
import make_recycler_config
import make_postproc_ini
import argparse
import numpy as np
import smtplib
from email.mime.text import MIMEText
import datetime

cwd = os.getcwd()
parser = argparse.ArgumentParser()
parser.add_argument('--rootdir',
                    default = cwd,
                    help="Directory where the Main-Injector, gw_workflow, and PostProcessing directories live.")
args=parser.parse_args()

DIR_SOURCE = args.rootdir

############# Send emails to appropriate people when things fail #############

def send_email(error, where):
    
    text = 'There was an error with the GW pipeline during %s, with message %s ' % (where, error)
    msg = MIMEText(text)
    # me == the sender's email address
    # you == the recipient's email address
    me = 'alyssag94@brandeis.edu'
    you = 'alyssag94@brandeis.edu'
    msg['Subject'] = 'GW pipeline error'
    msg['From'] = me            
    msg['To'] = you
    s = smtplib.SMTP('localhost')
    s.sendmail(me, [you], msg.as_string())
    print('There was an error. An email was sent to %s' % you)
    s.quit()


########### Use to update current environment because subprocess is doesn't handle it well #############

def source(script, update=1):
    pipe = subprocess.Popen(". %s > /dev/null; env" % script, stdout=subprocess.PIPE, shell=True)
    data = pipe.communicate()[0]
    env={}
    for line in data.splitlines():
        #print(line)
        splt1=line.split('=',1)
        if splt1[0] == 'BASH_FUNC_setup()':
            splt1[1] = '() {  eval `$EUPS_DIR/bin/eups_setup           "$@"`  \n}'
            #print(splt1[1])
        if splt1[0] == 'BASH_FUNC_unsetup()':
            splt1[1] = '() {  eval `$EUPS_DIR/bin/eups_setup --unsetup "$@"`  \n}'
            #print(splt1[1])
        if splt1[0] == 'BASH_FUNC_module()':
            splt1[1]='() {  eval `/usr/bin/modulecmd bash $*`   \n}'
            #print(splt1[1])
        if splt1[0] =='}':
            continue

        #print(splt1)
        env[splt1[0]]=splt1[1]
        
    if update:
        os.environ.update(env)

    return env


############# Image Processing ################ 

############ create new season number ###########
### Y6 will start with 600 (use 417 for mock runs) #####
import easyaccess
import fitsio

query = 'SELECT max(SEASON) from marcelle.SNFAKEIMG where SEASON < 800;'
connection=easyaccess.connect('destest')
connection.query_and_save(query,'testfile.fits')
data = fitsio.read('testfile.fits')
print(data[0][0])

newseason = (int(data[0][0]/100) + 1)*100
newseason = 519
print("the season number for this event is "+str(newseason))
print('')

#Update season number in dagmaker.rc
os.system("sed -i -e '/^SEASON/s/=.*$/="+str(newseason)+"/' "+DIR_SOURCE+"/gw_workflow/dagmaker.rc")

#Make curatedExposure.list
os.system("bash "+DIR_SOURCE+"/make_curatedlist.sh")

print("Setting up environment for image processing")
source('gw_workflow/setup_img_proc.sh')
print("Done.")
print('')

#explist = np.genfromtxt(DIR_SOURCE+'/curatedExposure.list', delimiter=' ', usecols=0) #this will just be curatedExposure.list for production. new_curated.list, bns_nite1_first10exposures.list are test lists
EXPLIST = os.popen('''awk '{print $1}' curatedExposure.list''').read().splitlines() #curatedExposure.list
EXPS = filter(None,set(EXPLIST)) #remove repeats and empty entries

dagmakerout = open('imgproc_dagmaker_'+str(newseason)+'.out', 'w')
dagmakererr = open('imgproc_dagmaker_'+str(newseason)+'.err', 'w')
jobsubout = open("imgproc_jobsub_"+str(newseason)+".out", 'w')
jobsuberr = open('imgproc_jobsub_'+str(newseason)+'.err', 'w')

for i in EXPS: #explist:
    EXPNUM = int(i)
    check = os.path.isdir(DIR_SOURCE+'/gw_workflow/mytemp_'+str(EXPNUM))

    check = False #only for test runs
    if check == False:
        print("mytemp_"+str(EXPNUM)+" does not exist, running DAGMaker.sh")

        img1 = subprocess.Popen(['time','bash','-c', DIR_SOURCE+'/gw_workflow/DAGMaker.sh '+str(EXPNUM)] ,
                                stdout = subprocess.PIPE, stderr=subprocess.PIPE, cwd='gw_workflow/') 
        
        im1out, im1err = img1.communicate()
        dagmakerout.write(im1out)
        dagmakererr.write(im1err)


        rc1 = img1.returncode
        print('The return code for DAGMaker is '+str(rc1))
        
        if rc1 != 0:
            err_msg = "DAGMaker failed."
            where = "Image Processing ("+DIR_SOURCE+"/"+dagmakererr.name+")"
            send_email(err_msg, where)
        else:
            print('Finished ./DAGMaker for exposure '+str(EXPNUM)+'. Submitting jobs.')

        print('')
        

        img2 = subprocess.Popen(['jobsub_submit_dag','--role=DESGW', '-G', 'des','file://desgw_pipeline_'+str(EXPNUM)+'.dag'], 
                                stdout = subprocess.PIPE, stderr=subprocess.PIPE, cwd='gw_workflow/')        

        im2out, im2err = img2.communicate()
        jobsuberr.write("Errors for jobsub_submit_dag:\n")
        jobsubout.write("Output for jobsub_submit_dag:\n")
        jobsubout.write(im2out)
        jobsuberr.write(im2err)

        rc2 = img2.returncode
        print('The return code for this jobsub is '+str(rc2))
        if rc2 != 0:
            err_msg = "Image processing job sub failed."
            where = "Image Processing ("+DIR_SOURCE+"/"+jobsuberr.name+")"
            send_email(err_msg, where)

        else:
            print('Finished jobsub_submit_dag for exposure '+str(EXPNUM))
            print('Look at test_imgproc_jobsub.out for the jobid')
            print('')
    else:
        print('Already processed exposure number '+str(EXPNUM))

dagmakerout.close()
dagmakererr.close()
jobsuberr.close()
jobsubout.close()

print("Finished image processing! Moving on to post processing...")
print('')
print('')

#### check if Image processing jobs finised 
#if at least 2 files of nonzero size exisit in /pnfs/des/persistent/gw/forcephoto/images/dpSEASON/DATE/EXP/ then move on to Post Processing

print("Waiting 20min, then we will check if SEdiff finished.")
import time
import glob

time.sleep(1200) #wait 20min before checking if file exisits 
print("Checking if SEdiff finsihed...")

#get and date of exposure 
#DATELIST = os.popen('''awk '{print $2}' curatedExposure.list''').read().splitlines()
DATELIST = os.popen('''awk '{print $2}' bns_nite1_first3exposures.list''').read().splitlines()
DATES = filter(None,set(DATELIST))

for EXP in EXPS:
    for DATE in DATES:
        path = '/pnfs/des/persistent/gw/forcephoto/images/dp'+str(newseason)+'/'+str(DATE)+'/'+str(EXP)+'/'
        while not os.path.exists(path):
            time.sleep(120)
            print("No fits files yet, checking again in 2 min.")
            
        fitspath = glob.glob(path+'*.fits') 
        if len(fitspath) >= 2:
            for i in range(len(fitspath)):
                if os.path.getsize(fitspath[i]) == 0:
                    continue
        else:
            print("less than 2 fits files, waiting 1min")
            time.sleep(60)
            continue

############# Run Post Processing #############

postprocout = open(DIR_SOURCE+'/postproc_'+str(newseason)+'.out', 'w')
postprocerr = open(DIR_SOURCE+'/postproc_'+str(newseason)+'.err', 'w')

#load recycler.yaml for some info
import yaml
with open(DIR_SOURCE+'/Main-Injector/recycler.yaml') as f:
    var=yaml.load(f.read())
f.close()

band_array = var['exposure_filter_NS']
band_list = (', '.join(band_array))

#Hack - make ligo id
today = datetime.datetime.today().strftime('%y%m%d') #YYMMDD
ligo_id = 'GW'+today

make_postproc_ini.makeini(season=newseason, ligoid=ligo_id, triggerid=var['trigger_id'], propid="2018B-0942", recycler_mjd=var['recycler_mjd'], bands=band_list)

os.system("mv postproc.ini "+DIR_SOURCE+"/Post-Processing/postproc_"+str(newseason)+".ini")

start_pp = ['bash','-c', DIR_SOURCE+'/Post-Processing/seasonCycler.sh']
postproc = subprocess.Popen(start_pp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='Post-Processing/')

while postproc.poll() is None:
    l = postproc.stdout.readline()
    print l

postproc_out, postproc_err = postproc.communicate()
rc3 = postproc.returncode

postprocout.write(postproc_out)
postprocerr.write(postproc_err)

postprocout.close()
postprocerr.close()

print('the return code for post processing is '+str(rc3))
print('')

if rc3 != 0: 
    error = os.popen('tail -10 '+postprocerr.name).read()
    where = "Post Processing ("+DIR_SOURCE+"/"+postprocerr.name+")"
    send_email(error, where)
    
print("Finished Post-Processing! Visit website for more information")





