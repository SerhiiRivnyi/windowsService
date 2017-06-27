# -*- coding: utf-8 -*-
# ! /usr/bin/env python
from time import sleep

import win32serviceutil
import win32service
import win32event
import win32api

import servicemanager

from os.path import splitext, abspath
import sys
from multiprocessing import Queue

from com.LogService import Logger
from settings import Config
from settings import Settings
from processes.ProcessManager import ProcessManager

logQueue = None
logger = None


class TestServiceSvc(win32serviceutil.ServiceFramework):
    __processes = []
    _svc_name_ = Settings.SERVICE_NAME
    _svc_display_name_ = Settings.SERVICE_DISPLAY_NAME
    _svc_reg_class_ = ""
    def __init__(self, args):
        global logQueue, logger

        self.__isRunning = True

        if logQueue is not None:
            self.__logQueue = logQueue
        else:
            self.__logQueue = Queue()
        if logger is not None:
            self.__logger = logger;
        else:
            self.__logger = Logger(self.__logQueue)
            self.__logger.start()
        self.__logQueue.put("---test---1")
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.__logQueue.put("---test---2")

        self.timeout = 60000
        self._paused = False

    def SvcStop(self):
        self.__logQueue.put("Get message about stop service, send signal 'stop'")

        self.__processManager.stopProcess()

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STOPPED,
                              (self._svc_name_, '')
                              )
        self.logInfo("Service stopped")
        # self.__logQueue.put("stopLogger")

    def SvcDoRun(self):
        self.__logQueue.put("---test---3")
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.__logQueue.put("---test---4")
        self.__startService()

    def __startService(self):
        self.logInfo("Start service")

        self.loadConfig()
        self.__logQueue.put("---test---5")
        self.__startProcesses()
        self.__logQueue.put("---test---6")
        while True:
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            if rc == win32event.WAIT_OBJECT_0:
                break
            active, total = self.__processManager.getStatus()
            active, total = 0,0
            self.__logQueue.put("Service is active, work " + str(active) + "/" + str(total) + " processes")
        self.__logQueue.put("---test---7")

    def __startProcesses(self):
        self.__logQueue.put("---test---8")
        self.__processManager = ProcessManager(Config.getData(), self.__logQueue)
        self.__processManager.startProcesses()
        self.__logQueue.put("---test---9")

    def loadConfig(self):
        Config.loadConfig()

    def logInfo(self, value):
        self.__logQueue.put(value)
        servicemanager.LogInfoMsg(value)


def instart(cls, name, display_name=None, stay_alive=True):
    ''' Install and  Start (auto) a Service

        cls : the class (derived from Service) that implement the Service
        name : Service name
        display_name : the name displayed in the service manager
        stay_alive : Service will stop on logout if False
    '''
    cls._svc_name_ = name
    cls._svc_display_name_ = display_name or name

    try:
        module_path = sys.modules[cls.__module__].__file__
    except AttributeError:
        from sys import executable
        module_path = executable
    module_file = splitext(abspath(module_path))[0]
    cls._svc_reg_class_ = '%s.%s' % (module_file, cls.__name__)

    if stay_alive: win32api.SetConsoleCtrlHandler(lambda x: True, True)

    try:
        win32serviceutil.InstallService(
            cls._svc_reg_class_,
            cls._svc_name_,
            cls._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=Settings.SERVICE_DESCRIPTION
        )
        toLog("INSTALL OK")
        # win32serviceutil.StartService(
        #     cls._svc_name_
        # )


    except Exception, x:
        toLog(str(x))
        win32serviceutil.HandleCommandLine(cls, argv=[__file__, "remove"])
        toLog("RUN OK")


        # win32serviceutil.HandleCommandLine(cls, argv=[__file__, "start"])
        # win32serviceutil.HandleCommandLine(cls, argv=[__file__, "restart"])


        # win32serviceutil.HandleCommandLine(TestServiceSvc)  41


def initLogger():
    global logger, logQueue
    logQueue = Queue()

    logger = Logger(logQueue)
    logger.start()


def toLog(value):
    global logger, logQueue
    if logger is not None:
        logQueue.put(value)
    else:
        print(value)

def removeLogger():
    global  logQueue;
    if logQueue is not None:
        logQueue.put("stopLogger")


if __name__ == '__main__':
    # logQueue.put("--main--")

    # if called without argvs, let's run !
    try:
        # initLogger()
        instart(TestServiceSvc, Settings.SERVICE_NAME, Settings.SERVICE_DISPLAY_NAME, )
        # servicemanager.Initialize('backup service', None)
        # servicemanager.PrepareToHostSingle(TestServiceSvc)
    except Exception as e:
        toLog(str(e))
    # sleep(1)
    # removeLogger()