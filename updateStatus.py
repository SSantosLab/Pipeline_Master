def updateStatus(statuslist,season,expnum):
    stat=open('ImgProcStatus'+str(season)+'_'+str(expnum)+'.txt','w+')
    for status in statuslist:
        if status == False:
            stat.write('False \n')
        elif status == True:
            stat.write('True \n')
        elif status == 'Waiting':
            stat.write('Waiting\n')
        elif status == 'Running':
            stat.write('Running\n')
        else:
            stat.write(str(status))
    stat.close()
    return 'Status updated!'
