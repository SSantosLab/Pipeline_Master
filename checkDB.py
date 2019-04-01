#!/usr/bin/env python

import os
import pandas
import psycopg2
import argparse
import subprocess
import easyaccess
import fitsio

with open('/data/des41.a/data/desgw/O3MarchER/Post-Processing/lastExp.txt', "r") as f:
    lastExp = f.read()
f.close()

query = """SELECT id as EXPNUM,
       TO_CHAR(date - '12 hours'::INTERVAL, 'YYYYMMDD') AS NITE,
       EXTRACT(EPOCH FROM date - '1858-11-17T00:00:00Z')/(24*60*60) AS MJD_OBS,
       ra AS RADEG,
       declination AS DECDEG,
       filter AS BAND,
       exptime AS EXPTIME,
       propid AS PROPID,
       flavor AS OBSTYPE,
       qc_teff as TEFF,
       object as OBJECT
FROM exposure.exposure
WHERE flavor='object' and exptime>29.999 and RA is not NULL and id>"""+str(lastExp)+"""
ORDER BY id DESC LIMIT 2"""
#NULL and id>=182809 and expnum

conn =  psycopg2.connect(database='decam_prd',
                           user='decam_reader',
                           host='des61.fnal.gov',
                           port=5443) 
some_exposures = pandas.read_sql(query, conn)
conn.close()
#print some_exposures.keys()
 

mystrings=''
mystrings=some_exposures.to_string(index_names=False,index=False,justify="left")
myout=open('checknewexposures.dat','w')


myout.write(mystrings)
myout.write('\n')
myout.close()

#pull exposures with the correct propid, save file with exp num and nite
#propid= "2018B-0942"
propid1=2019A-0205 #(BNS)
propid2=2019A-0235 #(BBH)

os.system('''awk '$8=="%s" {print $0}' checknewexposures.dat > newexps.list''' %propid1)
os.system('''awk '$8=="%s" {print $0}' checknewexposures.dat > newexps.list''' %propid2)


##get new season number
season_query = 'SELECT max(SEASON) from marcelle.SNFAKEIMG where SEASON < 800;'
connection=easyaccess.connect('destest')
connection.query_and_save(season_query,'testfile.fits')
data = fitsio.read('testfile.fits')
newseason = (int(data[0][0]/100) + 1)*100
current = open('newseason.txt', 'w')
current.write(str(newseason))
current.close()




