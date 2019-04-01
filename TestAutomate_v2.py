#!/usr/bin/env python

import subprocess, os
from threading import Thread
#import make_recycler_config
import make_postproc_ini
import argparse
import numpy as np
import smtplib
from email.mime.text import MIMEText
import datetime
import updateStatus
import ImgProc_run_checker
import make_Mastermaster

cwd = os.getcwd()
parser = argparse.ArgumentParser()
parser.add_argument('--rootdir',
                    default = cwd,
                    help="Directory where the Main-Injector, gw_workflow, and PostProcessing directories live.")
parser.add_argument('--season', type=int, help='season number for the event. GW events start with season 600.')
parser.add_argument('--testExps', help="a .list file with the exposures you want to test with")
parser.add_argument('-C', action='store_true', help='For testing, force run DAGMaker.') 
args=parser.parse_args()


DIR_SOURCE = args.rootdir
if args.testExps == None:
    explistfile = 'curatedExposure.list'
else:
    explistfile = args.testExps

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

#[dagmaker, jobsub, starting imgproc]
statusList=['Waiting','Waiting','Waiting','incomplete']

#---------------------------------------------------------------
############ create new season number ###########
############ Y6 will start with 600   ###########
import easyaccess
import fitsio

if args.season == None:
    query = 'SELECT max(SEASON) from marcelle.SNFAKEIMG where SEASON < 800;'
    connection=easyaccess.connect('destest')
    connection.query_and_save(query,'testfile.fits')
    data = fitsio.read('testfile.fits')
    print(data[0][0])
    newseason = (int(data[0][0]/100) + 1)*100
else:
    newseason = args.season
print("the season number for this event is "+str(newseason))
print('')

##---------------------------------------------------

#Update season number in dagmaker.rc
os.system("sed -i -e '/^SEASON/s/=.*$/="+str(newseason)+"/' "+DIR_SOURCE+"/gw_workflow/dagmaker.rc")

print("Setting up environment for image processing")
source('gw_workflow/setup_img_proc.sh')
print("Done.")
print('')

#Make curatedExposure.list

if args.testExps == None:
    os.system("bash "+DIR_SOURCE+"/make_curatedlist.sh")

EXPLIST = os.popen('''awk '{print $1}' '''+explistfile).read().splitlines()
EXPS = filter(None,set(EXPLIST)) #remove repeats and empty entries


############# Image Processing ################

for i in EXPS: #explist:
    EXPNUM = int(i)
    #check = os.path.isdir(DIR_SOURCE+'/gw_workflow/mytemp_'+str(EXPNUM))
    
    dagmakerout = open('imgproc_dagmaker_'+str(newseason)+'_'+str(EXPNUM)+'.out', 'w')
    dagmakererr = open('imgproc_dagmaker_'+str(newseason)+'_'+str(EXPNUM)+'.err', 'w')
    jobsubout = open("imgproc_jobsub_"+str(newseason)+"_"+str(EXPNUM)+".out", 'w')
    jobsuberr = open('imgproc_jobsub_'+str(newseason)+'_'+str(EXPNUM)+'.err', 'w')

    runpath = DIR_SOURCE+'/gw_workflow/dp'+str(newseason)+'/'+str(EXPNUM)
    check = os.path.isdir(runpath)
    
    #make dir structure if it doesnt exist already
    # doing this outside of the if check==false loop so we don't constantly rewrite this when using -C option
    if not os.path.isdir(runpath):
        os.makedirs(runpath)
    
    if args.C:
        check = False #only for test runs
        print("path "+str(runpath)+" exists, running dagmaker anyways")
    if check == False:
        print("mytemp_"+str(EXPNUM)+" does not exist, running DAGMaker.sh")
        
        statusList[0]='Running'
        update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
        ImgProc_run_checker.checker(newseason,EXPNUM)
        
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

            statusList[0]=False
            update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
            print("status updated")

        else:
            print('Finished ./DAGMaker for exposure '+str(EXPNUM)+'. Submitting jobs.')
            statusList[0]=True
            update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
            print("status updated")

        ImgProc_run_checker.checker(newseason,EXPNUM)
        print('')
        
        #copy the .dag file and the dagmaker.rc to the run path
        os.system('cp '+DIR_SOURCE+'/gw_workflow/desgw_pipeline_'+str(EXPNUM)+'.dag '+str(runpath))
        os.system('cp '+DIR_SOURCE+'/gw_workflow/dagmaker.rc '+str(runpath))

        #submit dag
        statusList[1]='Running'
        update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
        ImgProc_run_checker.checker(newseason,EXPNUM)

        os.system('export X509_USER_PROXY=/opt/desgw/desgw.DESGW.proxy')
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

            statusList[1]=False
            update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
            print("status updated")

        else:
            print('Finished jobsub_submit_dag for exposure '+str(EXPNUM))
            print('Look at test_imgproc_jobsub.out for the jobid')
            
            statusList[1]=True
            update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
            print("status updated")

        ImgProc_run_checker.checker(newseason,EXPNUM)
    else:
        print('Already processed exposure number '+str(EXPNUM))
        statusList[0]=True #dagmaker
        statusList[1]=True #jobsub
        update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
        ImgProc_run_checker.checker(newseason,EXPNUM)
        print("status updated")

    dagmakerout.close()
    dagmakererr.close()
    jobsuberr.close()
    jobsubout.close()
    
    #move all log files to the appropriate directories
    os.system('mv imgproc_dagmaker_'+str(newseason)+'_'+str(EXPNUM)+'.out '+runpath)
    os.system('mv imgproc_dagmaker_'+str(newseason)+'_'+str(EXPNUM)+'.err '+runpath)
    os.system('mv imgproc_jobsub_'+str(newseason)+'_'+str(EXPNUM)+'.out '+runpath)
    os.system('mv imgproc_jobsub_'+str(newseason)+'_'+str(EXPNUM)+'.err '+runpath)

    ImgProc_run_checker.checker(newseason, EXPNUM)

#save the dagmaker that was used
os.system("cp "+DIR_SOURCE+"/gw_workflow/dagmaker.rc dagmaker"+str(newseason)+".rc")

print("Finished image processing! Moving on to post processing...")
print('')
print('')


#------------------------------------------------------------------------------------

#### check if Image processing jobs finised 
#if at least 2 files of nonzero size exisit in /pnfs/des/persistent/gw/forcephoto/images/dpSEASON/DATE/EXP/ then move on to Post Processing

print("Waiting 20min, then we will check if SEdiff finished.")
import time
import glob


def send_email2(season):

    text = 'Checking if we can start postproc in 20min! Check forcephoto dir for season %s' % (season)
    msg = MIMEText(text)
    # me == the sender's email address
    # you == the recipient's email address
    me = 'alyssag94@brandeis.edu'
    you = 'alyssag94@brandeis.edu'
    msg['Subject'] = 'Starting PostProc in 20'
    msg['From'] = me
    msg['To'] = you
    s = smtplib.SMTP('localhost')
    s.sendmail(me, [you], msg.as_string())
    print('A notification email was sent to %s' % you)
    s.quit()

send_email2(str(newseason))

#time.sleep(1200) #wait 20min before checking if file exisits 
print("Checking if SEdiff finsihed...")

statusList[2]=True
for i in EXPS: #explist       
    EXPNUM = int(i)
    print('check1',statusList)
    update=updateStatus.updateStatus(statusList,newseason,EXPNUM)
    print("status updated")

    ImgProc_run_checker.checker(newseason, EXPNUM)

"""
#get and date of exposure 
DATELIST = os.popen('''awk '{print $2}' '''+explistfile).read().splitlines()
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
#------------------------------------------------------------------------------------

############# Run Post Processing #############

postprocout = open(DIR_SOURCE+'/postproc_'+str(newseason)+'.out', 'w')
postprocerr = open(DIR_SOURCE+'/postproc_'+str(newseason)+'.err', 'w')

#load recycler.yaml for some info
import yaml
with open(DIR_SOURCE+'/Main-Injector/recycler.yaml') as f:
    var=yaml.load(f.read())
f.close()

#band_array = var['exposure_filter_NS']
#band_list = (','.join(band_array))
bands=subprocess.check_output(['awk', '{print $6}', 'checknewexposures.dat'])
bandarray=bands.split('\n')
band_list=','.join(bandlist[1:-1]) #0th index is the word "band" and the last index is just \n


#Hack - make ligo id
today = datetime.datetime.today().strftime('%y%m%d') #YYMMDD
ligo_id = 'GW'+today

#Make a base postproc ini file
make_postproc_ini.makeini(season=newseason, ligoid=ligo_id, triggerid=var['trigger_id'], propid="2018B-0942", recycler_mjd=var['recycler_mjd'], bands=band_list)

#change the name to be in the style postproc_{season}.ini
os.system("mv postproc.ini "+DIR_SOURCE+"/Post-Processing/postproc_"+str(newseason)+".ini")

#run postproc
source(DIR_SOURCE+'/Post-Processing/diffimg_setup.sh')

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

"""



