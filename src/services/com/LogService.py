import logging
import os
from threading import Thread

from multiprocessing import Queue

from settings import Settings

class Logger(Thread):

    def __init__(self, queue):
        super(Logger, self).__init__()
        self.__queue = queue

        self.__logger = logging.getLogger("testLogger")
        try:
            self.__hdlr = logging.FileHandler(Settings.LOG_FILE_NAME)
        except:
            if not os.path.isdir(Settings.FOLER_LOG_FILE):
                os.makedirs(Settings.FOLER_LOG_FILE)
            self.__hdlr = logging.FileHandler(Settings.LOG_FILE_NAME)


        formatter = logging.Formatter('%(asctime)s %(message)s')

        self.__hdlr.setFormatter(formatter)
        self.__logger.addHandler(self.__hdlr)
        self.__logger.setLevel(logging.INFO)

    def run(self):
        while True:
            m = self.__queue.get()
            if m == "stopLogger":
                break
            self.__logger.info(m)

logQueue = None
logger = None

def initLogger():
    global logger, logQueue
    logQueue = Queue()

    logger = Logger(logQueue)
    logger.start()


def toLog(value):
    global logger, logQueue
    if logQueue is not None:
        logQueue.put(value)
    else:
        print(value)

def toErrorLog(value):
    toLog("ERROR::" + value)

def getQueue():
    return logQueue

def removeLogger():
    global  logQueue;
    if logQueue is not None:
        logQueue.put("stopLogger")