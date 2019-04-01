#!/bin/bash

season=`cat oldseason.txt`
timenow=```date +"%s"```

exposures=```awk '{print $1}' exposures_$season.txt```
nite=```awk 'NF{print $2}' exposures_$season.txt | tail -1 ```

if [ -f exposures_$season.txt ]; then
    for exp in $exposures; do
	path="/pnfs/des/persistent/gw/forcephoto/images/dp$season/$nite/$exp"
#	echo $path 
	if [ -d $path ]; then
#	    echo path exists
	    lastmod=`date -r $path +"%s"`
	    diff=`expr $timenow - $lastmod`
#	    echo $diff
	    if [ $diff -lt 1800 ]; then #has the path been updated in 30min?
#		echo path less than
		numfiles=`ls $path | wc -l`  
		if [ $numfiles -gt 2 ]; then 
#		    echo more than two files 
   		    echo $exp >> SEdiffdoneexps_$season.list
		    awk '$1=='$exp' {print $0}' exposures_$season.txt >> SEdiffdoneexps_$season.txt
		fi
	    fi
	fi
    done
    time=```date +'%y%m%d-%H%M'```
    count=```cat SEdiffdoneexps_$season.list | wc -l```
    finished=```cat SEdiffdoneexps_$season.list```
    
    bands=```awk -vORS=, '!a[$6]++ {print $6}' SEdiffdoneexps_$season.txt | sed 's/,$/\n/'```
    echo bands $bands
    
    if [ ! -f ppcounts_$season.txt ]; then
	echo i dont exits
	echo 0 >> ppcounts_$season.txt
    fi	
    ppcounts=```cat ppcounts_$season.txt```
    a=0
    count=6
    check=`expr $count / 5`
#    echo check $check
    for line in $ppcounts; do
#	echo line $line
	if [ $line == $check ]; then
#	    echo test
	    a=$(($a+1))
	fi
    done
    if [ $a == 0 ]; then
#	echo im here
	sed -i -e "/^season/s/=.*$/= $season/" Post-Processing/postproc.ini
	sed -i -e "/^exposures_listfile/s/=.*$/= $explist/" Post-Processing/postproc.ini
	sed -i -e "/^bands/s/=.*$/= $bands/" Post-Processing/postproc.ini
	cp Post-Processing/postproc.ini Post-Processing/postproc_$season.ini

	source Post-Processing/diffimg_setup.sh
#	nohup python Post-Processing/run_postproc.py --season $season --outputdir ./PostProc_$season\_$time/ &> postproc_$season\_$time.log &
#	echo $! > PP_pid_$season\_$time.out

	expr $count / 5 >> ppcounts_$season.txt
    fi


fi





