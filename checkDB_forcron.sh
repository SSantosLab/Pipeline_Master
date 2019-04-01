#!/bin/bash

## Workflow:
### check if exposure has been processed before, if yes - skip
### if no, then check the nite - if this is a new night, use new season number, else use same season
### run TestAutomate.py

source gw_workflow/setup_img_proc.sh
#nohup python checkDB.py &> checkdb.log &
#echo $! > checkdb_pid.txt 

new_season=`cat newseason.txt`
old_season=`cat oldseason.txt`

new_exps=```awk '{print $1}' newexps.list```
used_exps=```awk '{print $1}' used_exp.txt``` #NR>1 avoids parsing the header 

new_nite=```awk '{print $2}' newexposures.txt```
old_nite=```awk 'NF{print $2}' used_exp.txt | tail -1``` #get nite for last entry

if [ -f newexposures.txt ]; then
    if cat newexposures.txt | wc > 0; then #if this file is not empty 
	a=0
	for j in $used_exps; do
	    for x in $new_exps; do
		if [ $j == $x ]; then #if this is a new exposure
		    a=$(($a+1))
		fi
	    done
	done
    fi
fi

if [ $a == 0 ]; then
    if [ $new_nite == $old_nite ]; then
	#echo new is old
	awk '$1=='$new_exps' {print $0}' newexps.list >> exposures_$old_season.txt #to keep track of season
	timenow=```date +'%y%m%d-%H%M%S'```

	nohup python TestAutomate.py --season $old_season --testExps newexps.list &> automate$old_season-$timenow.out &
	echo $! > automate_pid_$old_season-$timenow.txt

	#add expsure to used exposures list                                           
	awk '$1=='$new_exps' {print $0}' newexps.list >> used_exp.txt #ultimate reference file
    else
	awk '$1=='$new_exps' {print $0}' newexps.list >> exposures_$new_season.txt
	timenow=```date +'%y%m%d-%H%M%S'```
                      
	nohup python TestAutomate.py --season $new_season --testExps newexps.list &> automate$new_season-$timenow.out &
        echo $! > automate_pid_$new_season-$timenow.txt 

        echo $new_season > oldseason.txt #update old season 
        awk '$1=='$new_exps' {print $0}' newexps.list >> used_exp.txt
    fi
else
    echo $new_exps has already been processed. 
fi










#		    for n in $new_nite; do
#			echo $n
#			for i in $old_nite; do
#			    echo $i
#			    if [ $n == $i ]; then #use same season for exps taken on same nite
#				echo same nite
#				echo $x $n >> exposures_$old_season.txt
#				timenow=```date +'%y%m%d-%H%M%S'```

				#nohup python TestAutomate.py --season $old_season --testExps &> automate.out &
				#echo $! > automate_pid_$old_season-$timenow.txt

				#add expsure to used exposures list
#				echo "awk '$1==$x {print $0}' newexposures.txt" >> used_exp.txt  
#			    else
#				echo $x $n >> exposures_$new_season.txt
#				timenow=```date +'%y%m%d-%H%M%S'```

				#nohup python TestAutomate.py --season $new_season &> automate.out &
				#echo $! > automate_pid_$new_season-$timenow.txt
##
#				echo $new_season > oldseason.txt #update old season
#				echo ```awk '$1==```$x``` {print $0}' newexposures.txt``` >> used_exp.txt
#			    fi #if same nite
#			done #old nite list
#		    done #new nite list
#		else
#		    echo exposure $x already processed 
#		fi
#	    done #new exp list
#	done #used exp list
 #   fi #is new exp list empty
#fi #does file exist 

