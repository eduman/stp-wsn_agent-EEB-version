import ConfigParser
import os


def getCommonSettingsSection():
	return "common_settings"

def getCOMPort():
	return "com_port"

def getGatewayID():
	return "gateway_id"

def getMessageBroker():
	return "message_broker"


def getCOMPortValue(configPath):
	try:
		return getConfigurator(configPath).get(getCommonSettingsSection(), getCOMPort())
	except Exception, e:
		raise Exception(e)

def getGatewayIDValue(configPath):
	try:
		return getConfigurator(configPath).get(getCommonSettingsSection(), getGatewayID())
	except Exception, e:
		raise Exception(e)

def getMessageBrokerValue(configPath):
	try:
		return getConfigurator(configPath).get(getCommonSettingsSection(), getMessageBroker())
	except Exception, e:
		raise Exception(e)



def makeDefaultConfigFile(configPath):
	try:
		os.makedirs(os.path.dirname(configPath))
	except Exception, e:
		pass

	f = open(configPath, "w+")

	#ConfigParser.SafeConfigParser.add_comment = lambda self, section, option, value: self.set(section, '\n; '+option, value)

	config = ConfigParser.SafeConfigParser()
	
	section = getCommonSettingsSection()
	config.add_section(section)
	config.set(section, getCOMPort(), "/dev/ttyACM0")
	config.set(section, getGatewayID(), "EEB-gateway-name")
	config.set(section, getMessageBroker(), "seemp.polito.it:1883")

	config.write(f)


def getConfigurator (configPath):
	config = ConfigParser.SafeConfigParser()
	try: 
		if not os.path.exists(configPath):
			makeDefaultConfigFile(configPath)

		config.read(configPath)
		return config
	except Exception, e:
		raise Exception("Error on CommonConfigurator.getConfigurator(): %s" % (e))


