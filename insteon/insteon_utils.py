#!/usr/bin/env python2
import os, urllib, urllib2, json, pickle, logging, pprint, re, sys, time, traceback
from secrets import *

account_filename = os.environ["HOME"]+ "/.insteon_hub/" + account_name + ".pickle"
server = "https://connect.insteon.com"
pp = pprint.PrettyPrinter(indent=21)

account_houses = {}
account_authorization = ""
account_houses = {}
house_data = {}
devices = {}
devices_dict = {}
devices_byid = {}
devices_byname = {}
scenes = {}
rooms = {}
dev_categories = []


def create_logger():
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create file handler which logs even debug messages
    #fh = logging.FileHandler('/var/log/insteon_hub.log', mode='a')
    #fh.setLevel(logging.INFO)

    # create console handler with a higher log level
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.WARN)

    # create formatter and add it to the handlers
    #formatter_fh = logging.Formatter('[%(asctime)s] ' +
    #                              '(%(filename)s:%(lineno)s) ' +
    #				  '%(message)s',
    #				datefmt='%Y-%m-%d %H:%M:%S')
    formatter_ch = logging.Formatter('(%(filename)s:%(lineno)s) ' +
    				  '%(message)s')
    # fh.setFormatter(formatter_fh)
    ch.setFormatter(formatter_ch)

    # add the handlers to the logger
    logger.addHandler(ch)
    # logger.addHandler(fh)

    return logger

logger = create_logger()

def token_request(data_list):
        global pp
	#Authorization Grant
	#Retrieve an access token using user credentials or an authorization_code, or refresh an expired access token. Response 'expires_in' value is in seconds.

	#Password Grant Type POST Parameters

	#NameTypeDescription
	#usernamestringThe username of the Insteon account
	#passwordstringThe password of the Insteon account
	#client_idstringValid API Key
	#grant_typestringMust be "password"

	opener = urllib2.build_opener()
	request = {'client_id' : API_Key,
                   'username' : account_name,
                   'password' : account_password,
                   'grant_type' : 'password'}
	data_list.update(request)
	logger = logging.getLogger(__name__)
	logger.debug(pp.pformat(data_list))
	data_encoded = urllib.urlencode(data_list)	
	logger.debug(pp.pformat(data_encoded))
        logger.info(server + "/api/v2/oath2/token")
	response = opener.open(server + "/api/v2/oauth2/token", data_encoded)
	content = response.read()
	dict_return = json.loads(content)
        logger.debug(pp.pformat(response))
        logger.debug(pp.pformat(dict_return))
	return dict_return

def refresh_bearer(): 
	global account_authorization
	data_list = {
		'refresh_token' : Refresh_Token,
		'grant_type' : 'refresh_token'}
	response = token_request(data_list)
	account_authorization = response["access_token"]
	logger = logging.getLogger(__name__)
	logger.debug("refresh_bearer " + pp.pformat(account_authorization))
	save_account()

def general_get_request(endpoint):
	logger = logging.getLogger(__name__)
	while True:
		#opener = urllib2.build_opener()
		if account_authorization == "":
			refresh_bearer()
		#for item in headers:
			#opener.addheaders.append((item , headers[item]))
		try:
			headers = { 
				"Content-Type" : "application/json",
				"Authentication" : "APIKey " + API_Key,
				"Authorization" : "Bearer " + account_authorization
				}
			url = server + "/api/v2/" + endpoint
			request = urllib2.Request(url,  headers = headers)
			#logger.info(url + " " + pp.pformat(headers))
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			logger.error("general_get_request: " + str(e.code))
			if e.code == 403 or e.code == 401:
                                r = e.read()
				logger.error( r)
				refresh_bearer()
                                sys.exit("Fatal Error: " + str(r))
			elif e.code == 500:
				break
		else:
			content_raw = response.read()
                        #logger.debug("content_raw")
                        #print(content_raw)
                        # Hack to fix a bug in the Insteon API
                        content = re.sub(r'(\d\d\d\d-\d\d-\d\d),',lambda m: '"' + m.group(1) + '",',content_raw)
                        #logger.debug(pp.pformat(content))
                        
			dict_return = json.loads(content)
			return dict_return
			break

#I think their accounts endpoint is extra broke
def account_list():
	return_dict = general_get_request("accounts")
	return return_dict

#Houses Endpoint	
def get_house(house_id1):
        global rooms, devices, scenes
        house_id = str(house_id1)
	basic_info = general_get_request("houses/" + house_id)
	rooms = general_get_request("houses/" + house_id + "/rooms")
	devices = general_get_request("houses/" + house_id + "/devices")
	scenes = general_get_request("houses/" + house_id + "/scenes")
	new_dict = { 
		"basic" : basic_info,
		"rooms" : rooms,
		"devices" : devices,
		"scenes" : scenes
		}
	return new_dict
	
def get_houses():
	return_dict = general_get_request("houses")
	return return_dict
	
def house_check():
	global account_houses
	account_houses = get_houses()
	save_account()

def populate_houses():
	global house_data
	if account_houses == {}:
		house_check()
	for item in account_houses['HouseList']:
		house_id = str(item['HouseID'])
		house_data[house_id] = get_house(house_id)
		house_data[house_id]['Name'] = item['HouseName']
	save_account()

def populate_all():
        if len(account_houses['HouseList']) == 1:
            get_house(account_houses['HouseList'][0]['HouseID'])
	populate_rooms()
	populate_devices()

#Devices Endpoint
def populate_devices():
	global devices,pp
	logger = logging.getLogger(__name__)
	devices = general_get_request("devices?properties=all")
	#pp.pprint(devices)
	for index,device in enumerate(devices["DeviceList"]):
		devices_byname[device["DeviceName"]] = device["DeviceID"]
		devices_byid[device["DeviceID"]] = device["DeviceName"]

                logger.debug(str(device["DeviceID"]) + " " + device["DeviceName"])
                dev = general_get_request("devices/" + str(device["DeviceID"]))
                # logger.debug(pp.pformat(dev))
		devices_dict[device["DeviceID"]] = dev
                #logger.debug("dev_categories")
                #logger.debug(pp.pformat(dev_categories))
		for category in dev_categories:
			logger.debug("category" + category["Name"])
			#logger.debug(pp.pformat(category))
			#logger.debug("device")
			#logger.debug(pp.pformat(device))
			if dev["DevCat"] == int(category["Device Category"],16) and dev["SubCat"] == int(category["Device Sub-Category"],16):
				devices["DeviceList"][index]["DeviceTypeName"]=category["Name"]
				devices["DeviceList"][index]["SKU"]=category["SKU"]
				break
	logger.debug(pp.pformat(devices_byid))
	logger.debug(pp.pformat(devices_byname))
	logger.debug(pp.pformat(devices_dict))
	save_account()

def device_command(device_id, command_string, data_list={}):
	# command_string: on, off, get_status
        global pp,devices_byid,devices_dict
	logger = logging.getLogger(__name__)
	#opener = urllib2.build_opener()
	logger.debug(str(device_id) + " " + command_string)
	response = False	
	if account_authorization == "":
		refresh_bearer()
	headers = { 
		"Content-Type" : "application/json",
		"Authentication" : "APIKey " + API_Key,
		"Authorization" : "Bearer " + account_authorization
		}
	#for item in headers:
	#	opener.addheaders.append((item , headers[item]))
	request = {
		'device_id' : device_id,
		'command': command_string
		  }
	data_list.update(request)
	data_encoded = urllib.urlencode(data_list)	
	loop = True
	while True:
		try:
			urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
			logger.debug( json.dumps(data_list))
			if "level" in data_list: 
				request = urllib2.Request(server + "/api/v2/commands?device_id=" + str(data_list["device_id"]) + "&command=" + data_list["command"] + "&level=" + str(data_list["level"]), headers = headers)
			else:
				request = urllib2.Request(server + "/api/v2/commands", data = json.dumps(data_list), headers = headers)
			logger.debug( request.get_full_url())
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			response = False
			#logger.error( e.code)
			#logger.error( e.reason)
			error_info = e.read()
			#logger.error( error_info)
			logger.error( e.reason + ": " + error_info)
			#logger.error( headers)
			logger.error( request.get_full_url())
			#logger.error( json.dumps(data_list))
			if e.code == 403 or e.code == 401:
				logger.debug(e.read())
				refresh_bearer()
                                exit
				continue
			break
		break
	if response:
		content = response.read()
		logger.debug(pp.pformat(content))
		dict_return = json.loads(content)
		command_id = dict_return["id"]
	else:
		#logger.error(response)
		command_id = "???"
		return "???"
	count = 1
	while count < 10:
		command_return = general_get_request("commands/" + str(command_id))
		logger.debug("Try #" + str(count) + " " + pp.pformat(command_return))
		status = command_return["status"]
		if not "pending" in status:
			break
		count = count + 1
		time.sleep(1)

	# Need to special case devices that don't return status
	if "X10_0" in devices_dict[device_id]["SerialNumber"]:
		return command_return
	
	if not "succeeded" in status:
		logger.warn ("After " + str(count) + " tries '" + command_string + "' for device_id " + str(device_id) + 
					" [" + devices_byid[device_id] + "] '" + status + "'!!!!!")
	else:
		logger.debug("Success after " + str(count) + " checks: " + pp.pformat(command_return))
	return command_return

def do_dev_status(device_id):
	#
	# Get the status of a device
	#  1) Some devices (X10) don't return a status
	#  2) Sometimes this just fails
	#

        global pp,devices_byid,devices_dict
	logger = logging.getLogger(__name__)

	dev = devices_dict[device_id]
	if "X10_0" in dev["SerialNumber"]:
		# logger.warn("Cannot get device status for X10 device " + str(device_id) + " " + dev["DeviceName"])
		return "X10"

	logger.debug("dev_status(" + str(device_id) + ")")
	dict_return = device_command(device_id, "get_status")
	logger.debug(pp.pformat(dict_return))

        device_status = dict_return["status"]
	try:
	        if dict_return["status"] == "pending":
	                device_status = "PENDING"
	        elif dict_return["status"] == "failed":
	                device_status = "FAILED"
	        elif dict_return["response"]["level"] == 100:
			logger.debug(pp.pformat(dict_return["response"]))
			device_status = "On"
		elif dict_return["response"]["level"] == 0:
			logger.debug(pp.pformat(dict_return["response"]))
			device_status = "Off"
		else:
			device_status = str(dict_return["response"]["level"]) + "% On"
		logger.debug(str(device_id) + " " + device_status)
	except:
		print(pp.pformat(dict_return))
		traceback.print_exc()
	return device_status

def dev_status(device_id):
	# For PENDING or FAILED, try up to 3 times
	logger = logging.getLogger(__name__)
	for trynum in range(1, 3): 
		status = do_dev_status(device_id) 
		if (not re.match('failed|pending',status,re.I)):
			return status
		# logger.warn(str(trynum) + "/3) Could not retrieve status for device " + str(device_id) + " [" + devices_byid[device_id] + "] '" + status + "'!!!")

	return status

##Test thing to see about the status of each device:
def list_device_status():
	logger = logging.getLogger(__name__)
	if devices == {}:
		populate_devices()
	for item in devices["DeviceList"]:
		#Check if it's a multi-device device (like keypads and outlets)
		name = item["DeviceName"]
		device_id = item["DeviceID"]
		#if item["GroupList"] == []:
		logger.debug("Checking device status for '" + name + "'")
		dev_status(device_id)
			#logger.debug("balls")
			
	#	else:
	#		#device is not that, the ones i know about are keypads and outlets
	#		logger.debug(name + " is not a device we are checking"
	#		device_item = ""
	#		category = hex(item["DevCat"])
	#		subcategory = hex(item["SubCat"])
	#		for device_item in dev_categories: 
	#			if category in device_item['Device Sub-Category'] and subcategory in device_item['Device Sub-Category']:
	#				device = device_item
	#		if device_item['SKU'] == "2663-222": #On Off Outlet
	#			logger.debug("on/off outlet")

def device_off(device_id):
	device_command(device_id, "off")

def device_on(device_id, level=0):
	logger = logging.getLogger(__name__)
	logger.debug(str(device_id) + " " + str(level))
	if level == 0:
		for device in devices["DeviceList"]:
			if device_id == device["DeviceID"]:
				#logger.debug("Finding level")
				if "DimLevel" in device:
					prelevel = device["DimLevel"]
					level  = (( prelevel + 1) * 100 )/ 255
				else:
					level = 100
	if level < 10: #It doesn't work correctly under 10. Who knows why....
		level = 10
	device_command(device_id, "on", {"level": level })

def dev_search_id(device_id):
	for device in devices["DeviceList"]:
		if device_id == device["DeviceID"]:
			return device
#Room Endpoint
def populate_rooms():
	global rooms
	rooms = general_get_request("rooms?properties=all")
	save_account()

def room_listing():
	logger = logging.getLogger(__name__)
	for item in rooms["RoomList"]:
		logger.debug(item["RoomName"])
		for item2 in item["DeviceList"]:
			device = dev_search_id(item2["DeviceID"])
			logger.debug("\t" + device["DeviceName"])

#def room_off(room_id):
#	for item in rooms["RoomList"]:
#		if item["RoomID"] == room_id:
#			for device in item["DeviceList"]:
#				device_off(device["DeviceID"])
#

#def room_on(room_id):
#	for item in rooms["RoomList"]:
#		if item["RoomID"] == room_id:
#			for device in item["DeviceList"]:
#				device_on(device["DeviceID"])
	
#Scenes Endpoint
def populate_scenes():
	global scenes,pp
	scenes = general_get_request("scenes?properties=all")
	save_account()

def scene_listing():
	logger = logging.getLogger(__name__)
        #logger.debug("scenes")
	#logger.debug(pp.pformat(scenes))
	for item in scenes["SceneList"]:
                logger.debug("item")
                logger.debug(pp.pformat(item))
		logger.debug(item["SceneName"])
		#for item2 in item["SceneID"]:
			#device = dev_search_id(item2["DeviceID"])
			#logger.debug("\t" + device["DeviceName"]

def scene_command(scene_id, command_string, data_list={}):
	logger = logging.getLogger(__name__)
	#opener = urllib2.build_opener()
	if account_authorization == "":
		refresh_bearer()
	headers = { 
		"Content-Type" : "application/json",
		"Authentication" : "APIKey " + API_Key,
		"Authorization" : "Bearer " + account_authorization
		}
	#for item in headers:
	#	opener.addheaders.append((item , headers[item]))
	request = {
		'scene_id' : scene_id,
		'command': command_string
		  }
	data_list.update(request)
	data_encoded = urllib.urlencode(data_list)	
	loop = True
	while True:
		try:
			request = urllib2.Request("https://connect.insteon.com/api/v2/commands", data = json.dumps(data_list), headers = headers)
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			logger.error( e.code)
			logger.error( e.read())
			if e.code == 403 or e.code == 401:
				logger.debug(e.read())
				refresh_bearer()
                                exit
			continue
		break
	content = response.read()
	dict_return = json.loads(content)
	command_id = dict_return["id"]
	while True:
		command_return = general_get_request("commands/" + str(command_id))
		status = command_return["status"]
		if "succeeded" in status:
			break
		logger.error("WHY DIDN'T IT SUCCEED: " + status + "!!!!!")
		#sys.exit(1)

	logger.debug(command_return)
	return command_return["status"]

def scene_off(scene_id):
	scene_command(scene_id, "off")

def scene_on(scene_id, level=0):
	scene_command(scene_id, "on")


##Dealing with the files
def save_account():
	with open(account_filename, 'w') as f:
		pickle.dump([account_authorization, account_houses, house_data, devices, rooms, scenes], f)
