#!/usr/bin/python

#DEPENDENCIES: pyserial, paho
import serial
import sys
import time
import signal
from threading import Thread
from commons.myMqtt.MQTTClient import MyMQTTClass
import logging
import os
import json
from commons.myConfigurator import CommonConfigurator
import ConfigParser

#logLevel = logging.DEBUG 
logLevel = logging.INFO
TOPIC = "/EEB/%s/%s"

class STPAgent(object):
	def __init__(self, gatewayName):
		#self.brokerUri = "seemp.polito.it"
		#self.brokerPort = 1883
		#self.comport = '/dev/ttyACM0' 
		self.gatewayName = gatewayName
		self.configPath = "conf/STPAgent.conf"
		logPath = "log/STPAgent.log"
		backupPath = "log/backup_data.log"
		self.loop = True

		if not os.path.exists(logPath):
			try:
				os.makedirs(os.path.dirname(logPath))
			except Exception, e:
				pass

		if not os.path.exists(backupPath):
			try:
				os.makedirs(os.path.dirname(backupPath))
			except Exception, e:
				pass

		if not os.path.exists(self.configPath):
			try:
				CommonConfigurator.makeDefaultConfigFile(self.configPath)
			except Exception, e:
				pass

		self.logger = logging.getLogger(self.gatewayName)
		self.logger.setLevel(logLevel)
		hdlr = logging.FileHandler(logPath)
		formatter = logging.Formatter(self.gatewayName + ": " + "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
		hdlr.setFormatter(formatter)
		self.logger.addHandler(hdlr)
		
		consoleHandler = logging.StreamHandler()
		consoleHandler.setFormatter(formatter)
		self.logger.addHandler(consoleHandler)

		# using a logger to backup json strings with sampled values
		self.backupLogger = logging.getLogger(self.gatewayName + "_backup")
		self.backupLogger.setLevel(logging.INFO)
		backupHdlr = logging.FileHandler(backupPath)
		backupFormatter = logging.Formatter("")
		backupHdlr.setFormatter(backupFormatter)
		self.backupLogger.addHandler(backupHdlr)

		for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
			signal.signal(sig, self.signal_handler)

		try:
			self.brokerUri, self.brokerPort = ''.join(CommonConfigurator.getMessageBrokerValue(self.configPath ).split()).split(':')
			self.comport = CommonConfigurator.getCOMPortValue(self.configPath )
			self.gatewayID = CommonConfigurator.getGatewayIDValue(self.configPath )
		except Exception, e:
			self.logger.error("Unable to run the agent due to: % s" % (e))
			self.stop()

		try: 
			self.serial = serial.Serial(COM_PORT,9600)
			if not self.serial.isOpen():
				self.serial.open()
			signal.signal(signal.SIGINT, signal_handler)
		except Exception, e:
			self.logger.error("Unable to run the agent due to serial port issues: % s" % (e))
			self.stop()

		try:
			self.mqtt = MyMQTTClass(self.gatewayID, self.logger, None)
			self.mqtt.connect(self.brokerUri, self.brokerPort)
		except Exception, e:
			self.logger.error("Unable to run the agent due to mqtt issues: % s" % (e))
			self.stop()



	def signal_handler(self, signal, frame):
		self.stop()

	def stop (self):
		self.logger.info("Stopping %s" % (self.gatewayName))

		if hasattr (self, "mqtt"):
			try:
				self.mqtt.disconnect()
			except Exception, e:
				self.logger.error("Error on stop(): unable to disconnect from the broker due to %s" % (e))


		if hasattr (self, "serial"): 
			try: 
				if self.serial.isOpen():
					self.serial.close()
			except:
				pass

		self.loop = False
		sys.exit(0)

	def start (self):
		# The main thread reads data from serial port.
		try:
			while(self.loop):
				try:
					line = self.serial.readline()
					line = line.strip().replace('\r', '').replace('\n', '').replace(" ", "")
					# sometime strip() does not work... 
					line = line.replace(" ", "")

					if line:
						sendingThread = Thread (target = self.send, args=(line,))
						sendingThread.start()

					time.sleep(0.1)
				except serial.serialutil.SerialException, e:
					self.logger.error("SerialException: %s" % e)
				except IOError, e:
					self.logger.error("IOError: %s" % e)
				except Exception, e:
					self.logger.error("Exception: %s" % e)

			
		except Exception, e:
			self.logger.error("Exception: %s" % e)

	def send(self, line):
		try:
			fields = line.split(';')
			isToBeSent = False
			samples = []
			nodeID = "Unknown"
			for field in fields:
				if field:
					keyVal = field.split("=")
					if len(keyVal) == 2 and keyVal[0].lower() == "id":
						nodeID = keyVal[1]
						isToBeSent = True	
					elif len (keyVal) == 2 and keyVal[0].lower() == "t":
						val = keyVal[1]
						samp = {"n": "Temperature" ,"u": "Cel" ,"v": float(val)}
						samples.append(samp)
					elif len(keyVal) == 2 and keyVal[0].lower() == "h":
						val = keyVal[1]
						samp = {"n": "Humidity" ,"u": "Percent" ,"v": float(val)}
						samples.append(samp)

			
			if isToBeSent:
				unixTimeStamp = int(time.time())
				bn = "EEB/%s/%s" % (self.gatewayID, nodeID)
				payload = json.dumps({"bn": bn, "bt": str(unixTimeStamp), "e": samples})
				self.backupLogger.info(payload)
				self.mqtt.publish( (TOPIC % (self.gatewayID, nodeID)) , payload)


		except Exception, e:
			self.logger.error("Unable to publish a paylod due to: %s" % e)

	

if __name__ == '__main__':
	agent = STPAgent("STPAgent")
	agent.start()

