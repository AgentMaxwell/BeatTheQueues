# BeatTheQueues
Beat The Queues with notifications about your favourite rides (or Rita) 
# Beat The Q

HEY THERE! If you’re here then that probably means you like rides. Me too. I was bored and was wondering what I could do. I remembered the countless hours staring at the queue time apps working out the best plan of action, with things such as recent openings and low queues something I was looking out for. So… that’s what i’ve done. Or at least, started to do. It is definitely not in a finished state, but with the start of the season fast approaching (it has already started at BPB/PBR/PBL/PB (iykyk)) I wanted to get this out there and see the reception to see if it’s something I develop purely for myself or with a wider audience in mind. 

For full setup instructions please scroll to the bottom. 

IT DOES NOT LOOK PRETTY AT THE MOMENT AND IS FAR FROM WHERE I WANT IT. 

# features

- see all queue times, split up by ride type
- set push notifications for the following (note through email at the moment, email can be set using “settings” button
    - When a ride opens/closes
    - When a ride wait time goes below a certain threshold
        - A second push notification will not be sent unless the wait time has increased above the threshold first
- swap between (to begin) merlin parks within the UK (AT and TP to begin, others coming soon)

## intended features in the future

be able to interface into the system to be able to change settings whilst on park

run the system from a server to remove the need for individual devices running python

be able to see a rolling “trend in last hour” symbol - green (down), grey (steady), red (up) 

## known bugs/unintended features

- after a checkbox is checked, it will send an email with the current status. i know the cause of this but am trying to work out the best way to not break the rest of the system
- the countdown at the bottom of the page does not seem count down at the moment. it does work though, i promise :)

# setup

You will need to do the following:

1. Install python 3.12 from the microsoft store 
2. Go to command Prompt (type cmd in start)
    1. type “pip install requests” and hit enter - wait for this to finish installing and restart your system. You only need to do this once. 
3. Open [main.py](http://main.py) in your python instance
4. Run
5. Pray for no errors
6. input your email into the settings

The system is now “initialised”. For day to day use:

1. Open and run [main.py](http://main.py)
2. Select the rides you want to receive notifications for and set thresholds if required
3. Have a fun day!
