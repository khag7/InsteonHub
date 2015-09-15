#!/usr/bin/env python2

print ("Loading insteon_hub.py")

import os, urllib, urllib2, json, pickle, logging, logging.handlers, pprint, re, sys, traceback, insteon_utils
from secrets import API_Key, Client_Secret, Refresh_Token, account_name, account_password
from insteon_utils import token_request, refresh_bearer, general_get_request, account_list, \
	get_house, get_houses, house_check, populate_houses, populate_all, populate_devices, \
	device_command, dev_status, list_device_status, device_off, device_on, \
	dev_search_id, room_listing, populate_scenes,scene_listing,scene_command, scene_off, scene_on, save_account, \
	devices, pp, server

def logger_dir():
	candidates = { "/var/log" , "/usr/local/log" , "/tmp" , os.environ["HOME"] }
	for logdir in candidates:
		# W_OK is for writing, R_OK for reading, etc.
		if (os.access(logdir, os.W_OK)):
			return logdir

def create_logger():
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(logger_dir() + '/insteon_hub.log', mode='a')
    fh.setLevel(logging.INFO)

    # create console handler with a higher log level
    # ch = logging.StreamHandler(stream=sys.stdout)
    # ch.setLevel(logging.WARN)

    # create formatter and add it to the handlers
    formatter_fh = logging.Formatter('[%(asctime)s] ' +
                                  '(%(filename)s:%(lineno)s) ' +
				  '%(message)s',
				datefmt='%Y-%m-%d %H:%M:%S')
    # formatter_ch = logging.Formatter('(%(filename)s:%(lineno)s) ' +
    #				  '%(message)s')
    fh.setFormatter(formatter_fh)
    # ch.setFormatter(formatter_ch)

    # add the handlers to the logger
    # logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

def devlist():
	sys.stderr.write ("Valid devices:")
	for name,id in sorted(insteon_utils.devices_byname.items()):
		print ("\t" +  str(name))

def status_all():
	global logger
	for devname in insteon_utils.devices_byname:
		devnum = insteon_utils.devices_byname[devname]
		status = dev_status(devnum)
		logger.info("Status check - '" + devname + "' (" + str(devnum) + ") - " + status)


def turn_on(devnum,devname,ON_OFF_STATUS,status):
	# Don't turn it on if it's already on!
	global logger
	logger.debug("[" + ON_OFF_STATUS + "][" + status + "]")
	if (not re.match('.*On.*',status,re.I)):
		logger.info("device_on(" + str(devnum) + ", 5) # " + devname)
		device_on(devnum, 5)
		# Check that it's actually on now
		status = dev_status(devnum)
		if (status == "Off"):
			logger.error(devname + "(" + str(devnum) + ") did not turn on - Current status = " + status)
		else:
			logger.info("Do Nothing - " + devname + " is already ON")
	return status

def turn_off(devnum,devname,status):
	# Don't turn it off if it's already off!
	global logger
	if (status != "Off"):
		logger.info ("device_off(" + str(devnum) + ") # " + devname)
		device_off(devnum)
		status = dev_status(devnum)
		if (status == "On"):
			logger.error(devname + "(" + str(devnum) + ") did not turn off - Current status = " + status)
	else:
		logger.info("Do Nothing - " + devname + " is already OFF")
	return status


def get_status(devnum):
	global logger
	status = dev_status(devnum)
	# no logging needed here. "dev_status" already logs
	# logger.info("Status check - '" + devname + "' (" + str(devnum) + ") - " + status)
	return status

def process_request(devname,ON_OFF_STATUS):
	global logger
	devnum = insteon_utils.devices_byname[devname]

	# Check current device status
	status = dev_status(devnum)
	# logger.info("[" + ON_OFF_STATUS + "][" + status + "]")
	if (re.match( ON_OFF_STATUS, status , re.I)):
		logger.info(devname + " is already " + status)
	else:
		logger.info(devname + " is currently " + status)

	# Asked to turn on
	if re.match( 'on|100', ON_OFF_STATUS, re.I):
		status = turn_on(devnum,devname,ON_OFF_STATUS,status)
	# Asked to turn off
	elif re.match( 'off|0', ON_OFF_STATUS , re.I):
		status = turn_off(devnum,devname,status)
	elif re.match( 'status', ON_OFF_STATUS , re.I):
		status = get_status(devnum)
	else:
		print("ERROR - " +  str(ON_OFF_STATUS) + " " + devname) 
	return status

#
##############
# Main
#

def main():
	global logger
	print ("insteon_hub.main()")
	logger = create_logger()

	try:
		with open(account_filename) as f:
			account_authorization, account_houses, house_data, devices, rooms, scenes = pickle.load(f)
			logging.debug(pp.pformat(account_authorization, account_houses));
	except:
	        populate_houses()
	        populate_all()
	        save_account()
	
	try: 
		with open('device_categories.json') as data_file:
			data = json.load(data_file)
			dev_categories = data['Device Category List']
	except:
		with open(os.environ["HOME"] + '/.local/insteon-python/device_categories.json') as data_file:
			data = json.load(data_file)
			dev_categories = data['Device Category List']
	
	if len(sys.argv) < 3:
		print( sys.argv[0] + " [On/Off/Status] [device name 1] [device name 2] ...")
		devlist()
		sys.exit(0)
	
	try:
		ON_OFF_STATUS = sys.argv[1]
	 
		for devidx in range (2, len(sys.argv)):
			devname = sys.argv[devidx]
			process_request(devname,ON_OFF_STATUS)
	except:
		traceback.print_exc()
		#print("Unknown command: " + ON_OFF_STATUS + " '" + str(sys.argv) + "'") 
		#devlist()
		sys.exit(1)

###

main()
																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																		