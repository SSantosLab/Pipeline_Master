#!/bin/bash

## Workflow:
### check if exposure has been processed before, if yes - skip
### if no, then check the nite - if this is a new night, use new season number, else use same season
### run TestAutomate.py

cd /data/des41.a/data/desgw/O3FULL/
source gw_workflow/setup_img_proc.sh
nohup python checkDB.py &> checkdb.log &
echo $! > checkdb_pid.txt 

new_season=`cat newseason.txt`
old_season=`cat oldseason.txt`

new_exps=```awk '{print $1}' newexps.list```
used_exps=```awk '{print $1}' used_exp.txt``` #NR>1 avoids parsing the header 

new_nite=```awk '{print $2}' newexps.list```
old_nite=```awk 'NF{print $2}' used_exp.txt | tail -1``` #get nite for last entry

if [ -f newexps.list ]; then
    bla=$(cat newexps.list | wc -l)
    if [ $bla -gt 0 ]; then #if this file is not empty 
	a=0
	for j in $used_exps; do
	    for x in $new_exps; do
		if [ $j == $x ]; then #if this is not a new exposure
		    a=$(($a+1))
		fi
	    done
	done
	if [ $a == 0 ]; then #if there is a new exposure
	    if [ $new_nite == $old_nite ]; then #use same season number for exps taken in one nite
		#exposures_$season.txt for reference later
		awk '$1=='$new_exps' {print $0}' newexps.list >> exposures_$old_season.txt
		
		timenow=```date +'%y%m%d-%H%M%S'```
		nohup python TestAutomate_v2.py --season $old_season --testExps newexps.list &> automate$old_season-$timenow.out &
		echo $! > automate_pid_$old_season-$timenow.txt
		
		#add expsure to used exposures list -- the ultimate reference file
		awk '$1=='$new_exps' {print $0}' newexps.list >> used_exp.txt 

	    else #this might be a diff thing, use new seaon number
		awk '$1=='$new_exps' {print $0}' newexps.list >> exposures_$new_season.txt
		timenow=```date +'%y%m%d-%H%M%S'```
		nohup python TestAutomate_v2.py --season $new_season --testExps newexps.list &> automate$new_season-$timenow.out &
		echo $! > automate_pid_$new_season-$timenow.txt
		
		echo $new_season > oldseason.txt #update old season   
		awk '$1=='$new_exps' {print $0}' newexps.list >> used_exp.txt
	    fi
	fi
    fi
fi





