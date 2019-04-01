import time

def statusPage(ListStatuses,season, expnum):
    Header=['<!DOCTYPE HTML>\n','<html>\n','<head>','<link rel="stylesheet" type="text/css" href="statusPageCss.css">','<title> Status </title>\n','</head>\n','<body>','<table align="center">','<th bgcolor="#bfbfbf">Step</th>','<th bgcolor = "#bfbfbf">Status</th>']
    stepList=['dagmaker', 'jobsub', 'starting post proc']
    Date=time.strftime("%Y-%m-%d-%H-%M")
    moreInfo=['<div id="info">','<p>Last Run:     '+Date+'</p>','<div id="info">','<p>Exposure Number:     '+str(expnum)+'</p>','<p><a id="status" href="output'+season+'.txt">Log</a></p>','</div>']
    
    statusPage=open('ImgProc_statusPage'+season+'_'+str(expnum)+'.html','w+')
    for line in Header:
        statusPage.write(line)
    statusPage.close()

    statusPage=open('ImgProc_statusPage'+season+'_'+str(expnum)+'.html','a')
    for x in moreInfo:
        statusPage.write(x)
    statusPage.close()

    ListStatuses=ListStatuses[:-1]

    statusPage=open('ImgProc_statusPage'+season+'_'+str(expnum)+'.html','a')
    for i in range(len(ListStatuses)):
        status=ListStatuses[i]
        step=stepList[i]
        if status=='True ':
            stat="Success"
            color="#00FF00"
        elif status=='Waiting':
            stat="Waiting"
            color="#FFFF00"
        elif status=='Running':
            stat='Running'
            color="#FFFF00"
        else:
            stat="Failed"
            color="#FF0000"
        data=["<tr>","<th>"+step+"</th>","<td bgcolor="+color+"><font color='#000000'>"+stat+"</font></td>","</tr>"]
        for line in data:
            statusPage.write(line)
    statusPage.close()
    closingLines=['</tr>']
    statlins=['</body>','</html>']
    stausPage=open('ImgProc_statusPage'+season+'_'+str(expnum)+'.html','a')
    for lin in statlins:
        stausPage.write(lin)
    statusPage.close()
    

