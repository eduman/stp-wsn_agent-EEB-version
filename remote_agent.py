#!/usr/bin/python

#DEPENDENCIES: pyserial
import serial
import sys
import time
import signal
import thread
import logging


COM_PORT = '/dev/ttyACM0' 
#COM_PORT = 'COM5'
GATEWAY_NAME = 'colombo_36'
ERROR_MSG = "ST-P Device Angent error, %s: %s\n"

logging.basicConfig(filename=GATEWAY_NAME+str(".log"),format='%(message)s',level=logging.DEBUG)
logger=logging.getLogger()
#myJsonSample = '{"n":"%s","u":"%s","v":%s}'
myJsonSample = "{'u':'%s','v':'%s'}"
loop = True
input = sys.stdin
out = sys.stdout
err = sys.stderr

def signal_handler(signal, frame):
    close()


def close():
    global loop 
    loop = False

def main():
    # The main thread reads data from the serial port.
    try:
        thread.start_new_thread(readInput, ())
        ser = serial.Serial(COM_PORT,9600)
        if not ser.isOpen():
            ser.open()
        signal.signal(signal.SIGINT, signal_handler)
        while(loop):
            try:
                line = ser.readline()
                line = line.strip().replace('\r', '').replace('\n', '')
                if line:
                    fields = line.split(';')
                    isToBeSent = False
                    sample = {"data":{}}
                    nodeID = "Unknown"
                    for field in fields:
                        if field:
                            keyVal = field.split("=")
                            if len(keyVal) == 2 and keyVal[0].lower() == "id":
                                nodeID = keyVal[1]
                                isToBeSent = True    
                            elif len (keyVal) == 2 and keyVal[0].lower() == "t":
                                val = keyVal[1]
                                sample = makeSample(sample, "Temperature", "Celsius", val)
                            elif len(keyVal) == 2 and keyVal[0].lower() == "h":
                                val = keyVal[1]
                                sample = makeSample(sample, "Humidity", "Percent", val)
                    
                    if isToBeSent:
                        unixTimeStamp = int(time.time())
                        payload={ "location":str(GATEWAY_NAME),"node":str(nodeID), "time_stamp":str(unixTimeStamp),"data":sample['data']}
                        print payload
                        logger.debug(str(payload))

            except serial.serialutil.SerialException, e:
                err.write(ERROR_MSG % ("SerialException", str(e)))
                err.flush()
            except IOError, e:
                err.write(ERROR_MSG % ("IOError", str(e)))
                err.flush()
            except Exception, e:
                err.write(ERROR_MSG % ("Exception", str(e)))
                err.flush()

        if ser.isOpen():
            ser.close()
        sys.exit(0)
    except Exception, e:
        err.write(ERROR_MSG %("Exception", str(e)))
        err.flush()    

def makeSample (outString, name ,unit, value):
    try:
        value = float(value)
        #outString["data"][name] = myJsonSample % ( unit, str(value))
        outString["data"][name] = {"u":str(unit),"v":str(value)}
    except ValueError, e:
        err.write(ERROR_MSG % ("ValueError", str(e)))
        err.flush()
    
    return outString
    
def readInput():
    # It is the core for a second thread. It reads data from the stdin and 
    # forward them to the stp coordinator via the serial port.
    # TODO: to be implemented
    try:
        while loop:
            line = input.readline()
            line = line.strip().replace('\r', '').replace('\n', '')
            if line:
                if line.lower() == "stp-stop":
                    close()
                else:
                    err.write(ERROR_MSG % ("Incoming input", "TODO " + line))
                    err.flush()
    except Exception, e:
        err.write(ERROR_MSG % ("Exception", str(e)))
        err.flush()
    

if __name__ == '__main__':
    main()
