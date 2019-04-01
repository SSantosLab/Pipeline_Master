#!/usr/bin/env python
import os

def mastermaster(statushtml, section, season):
    f = open('Master-master.html', 'r')
    contents = f.readlines()
    f.close()

    newline = '<p><a id="status" href="'+str(statushtml)+'"><font size="6">'+str(section)+' Status Page '+str(season)+'</font></a></body></p>\n'
#    contents.insert(2, newline) #insert new line at line 2

    a=0
    for line in contents:
        if line == newline:
            a = a + 1

    if a == 0:
        contents.insert(2, newline)
        f = open('Master-master.html', 'w')
        contents = ''.join(contents)
        f.write(contents)
        f.close()

    os.system('scp Master-master.html codemanager@desweb.fnal.gov:/des_web/www/html/desgw/post-processing-all/')

    
