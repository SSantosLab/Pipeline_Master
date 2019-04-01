#!/usr/bin/env python

import time
from time import strftime
import numpy as np
import os
from glob import glob
import checkStatusFunctions
import ImgProc_statusPage
import sys
import argparse


#parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
#parser.add_argument('--season', help='Season number', type=int)
#args = parser.parse_args()
#season=str(args.season)

import make_Mastermaster

def checker(season, expnum):
    thisTime = strftime("%Y%m%d.%H%M")
    thisTime=thisTime.replace('.','_')
    seasonTime=open('seasonTime'+str(season)+'_'+str(expnum)+'.txt','w+')
    seasonTime.write(str(season))
    seasonTime.write('\n')
    seasonTime.write(thisTime)
    seasonTime.close()
    print('seasonTime'+str(season)+'_'+str(expnum)+'.txt was made.')


    seaTim=open('seasonTime'+str(season)+'_'+str(expnum)+'.txt','r')
    seTi=seaTim.readlines()
    print(seTi)
    seaTim.close()
    season=seTi[0].split('\n')[0]
    time=seTi[1]
    print(season)
    print(time)
    #print('./forcephoto/output/dp'+season+'/'+time+'_DESY'+season)

    #statusList=checkStatusFunctions.checkStatus('ImgProcStatus'+str(season)+'.txt',season,time)
    #statusPage.statusPage(statusList,season)
    
    statusList = []
    txtfile = open('ImgProcStatus'+str(season)+'_'+str(expnum)+'.txt', 'r')
    lines = txtfile.read().split('\n')
    txtfile.close()
    for line in lines:
        statusList.append(line)
    
    print(statusList)
    ImgProc_statusPage.statusPage(statusList,season, expnum)
    if not os.path.isdir('./html_files'):
        os.makedirs('./html_files')

    os.system('mv ImgProc_statusPage'+str(season)+'_'+str(expnum)+'.html html_files/')
    os.system('scp html_files/ImgProc_statusPage'+str(season)+'_'+str(expnum)+'.html codemanager@desweb.fnal.gov:/des_web/www/html/desgw/post-processing-all/')
    print("copied html to codemanager")

    make_Mastermaster.mastermaster('ImgProc_statusPage'+str(season)+'_'+str(expnum)+'.html', 'Img Proc', season)

    return("Run chcecker done")
