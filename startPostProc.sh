#!/bin/bash

cd /data/des41.a/data/desgw/O3FULL
season=`cat oldseason.txt`
timenow=```date +"%s"```

if [ -f exposures_$season.txt ]; then
    exposures=```awk '{print $1}' exposures_$season.txt```
    nite=```awk 'NF{print $2}' exposures_$season.txt | tail -1 ```
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
		if [ $numfiles -gt 5 ]; then 
#		    echo more than two files 
   		    echo $exp >> SEdiffdone_$season.list #exp list for postproc is just exps
		    awk '$1=='$exp' {print $0}' exposures_$season.txt >> SEdiffdone_$season.txt
		    cp SEdiffdone_$season* Post-Processing/
		
		    awk '!a[$0]++' SEdiffdone_$season.list > SEdiffdoneexps_$season.list #remove repeates from list
		    awk '!a[$0]++' SEdiffdone_$season.txt > SEdiffdoneexps_$season.txt
		
		fi
		time=```date +'%y%m%d-%H%M'```
		count=```cat SEdiffdoneexps_$season.list | wc -l```
		
		#get bands as comma seperated list (-vORS makes comma sep, !a[$6] removes repeats
		bands=```awk -vORS=, '!a[$6]++ {print $6}' SEdiffdoneexps_$season.txt | sed 's/,$/\n/'```

		if [ ! -f ppcounts_$season.txt ]; then
		    echo 0 >> ppcounts_$season.txt
		fi
		ppcounts=```cat ppcounts_$season.txt```
		a=0
		check=`expr $count / 5` #rounds to nearest integer
		for line in $ppcounts; do
		    if [ $line == $check ]; then 
			#echo test                                                                                                   
			a=$(($a+1))
		    fi
		done
		if [ $a == 0 ]; then #once there are at least 5, 10, 15, ... exposures done, run post proc       
		    sed -i -e "/^season/s/=.*$/= $season/" Post-Processing/postproc.ini
		    sed -i -e "/^exposures_listfile/s/=.*$/= SEdiffdoneexps_$season.list/" Post-Processing/postproc.ini
		    sed -i -e "/^bands/s/=.*$/= $bands/" Post-Processing/postproc.ini
		    cp Post-Processing/postproc.ini Post-Processing/postproc_$season.ini

		    cd Post-Processing
		    source diffimg_setup.sh
		    bash update_forcephoto_links.sh
		    nohup python run_postproc.py --season $season --outputdir ./PostProc_$season\_$time/ &> postproc_$season\_$time.log &
		    echo $! > PP_pid_$season\_$time.out

		    expr $count / 5 >> ppcounts_$season.txt
		fi
	    fi
	fi
    done

fi





