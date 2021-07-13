Github Self-Hosted Runner Agent  
Author: Demian Ginther (st.diluted@gmail.com)  

Github self-hosted runners don't have a way to easily kill them off if you are worried about losing in-progress jobs. We run multiple runner processes on each AWS instance to allow for multiple threads of CI execution, and finding a time when _all_ the runner processes are not busy is nigh-impossible. 

This tool runs as root on a self-hosted runner, and will check once a minute (by default) to see if there is a 'kill file' in the runner home directory. If there is, it will loop through the configured runners on the system, determine if each runner is busy with a job, and if it is not, it will stop the runner process for that particular runner, and deregister the runner from the repository. If it is busy, it will wait 60 seconds and try again. Once all the runners have been removed, you can safely terminate the instance and assuming you have an ASG, you will get a new instance.

TO_DO: 
- Add some way of terminating instance when all processes have exited
- Add some other kind of trigger besides a kill file


Required env vars:
- RUNNERS_HOMES=/home/runner/runner1,/home/runner/runner2,...
- RUNNER_HOME=/home/runner
- KILL_FILE=marked_for_death.txt
