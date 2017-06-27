# -*- coding: utf-8 -*-
# ! /usr/bin/env python
import os
from time import sleep, time

import signal
import win32serviceutil
import win32service
import win32event
import win32api

import servicemanager

from os.path import splitext, abspath
import sys
import stat
from multiprocessing import Queue

import winerror
import wmi as wmi

from com.LogService import initLogger, removeLogger, toLog, toErrorLog, getQueue
from settings import Config
from settings import Settings
from processes.ProcessManager import ProcessManager



class TestServiceSvc(win32serviceutil.ServiceFramework):
    __processes = []
    _svc_name_ = Settings.SERVICE_NAME
    _svc_display_name_ = Settings.SERVICE_DISPLAY_NAME
    _svc_reg_class_ = ""
    _svc_is_auto_start_ = False
    def __init__(self, args):
        # global logQueue, logger

        self.__isRunning = True
        # if logger is None:
        initLogger()
        #
        toLog("--test service svc--")
        # if logQueue is not None:
        #     self.__logQueue = logQueue
        # else:
        #     self.__logQueue = Queue()
        # if logger is not None:
        #     self.__logger = logger;
        # else:
        #     self.__logger = Logger(self.__logQueue)
        #     self.__logger.start()

        self.timeout = 10000
        self._paused = False

        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        toLog("Get message about stop service, send signal 'stop'")

        self.__processManager.stopProcess()

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STOPPED,
                              (self._svc_name_, '')
                              )
        self.logInfo("Service stopped")
        # self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        removeLogger()

    def SvcDoRun(self):
        toLog("--svc do run--")
        # self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            # self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  servicemanager.PYS_SERVICE_STARTED,
                                  (self._svc_name_, ''))
            self.__startService()
        except Exception as e:
            toErrorLog("Run error " + str(e))

    def __startService(self):
        self.logInfo("Start service")

        self.loadConfig()
        self.__startProcesses()
        while True:
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            if rc == win32event.WAIT_OBJECT_0:
                break
            active, total = self.__processManager.getStatus()
            toLog("Service is active, work " + str(active) + "/" + str(total) + " processes")

    def __startProcesses(self):
        self.__processManager = ProcessManager(Config.getData(), getQueue())
        self.__processManager.startProcesses()

    def loadConfig(self):
        Config.loadConfig()

    def logInfo(self, value):
        print(value)
        toLog(value)
        servicemanager.LogInfoMsg(value)


SUCCESS = winerror.ERROR_SUCCESS
FAILURE = -1
MAX_STATUS_CHANGE_CHECKS = 3
STATUS_CHANGE_CHECK_DELAY = 3

serviceClass_ = None

def init( serviceClass ):
    global serviceClass_
    serviceClass_ = serviceClass
    initLogger()

def isStandAloneContext() :
    return sys.argv[0].endswith( ".exe" )

def dispatch(  ):
    result = verifyInstall()
    if result == FAILURE:
        install()
        return

    if sys.argv[0].endswith( ".exe" ) :

        toLog("--start dispatch--" + sys.argv[0])
        servicemanager.Initialize()
        toLog("Initialize")
        servicemanager.PrepareToHostSingle( serviceClass_ )
        toLog("PrepareToHostSingle")
        servicemanager.Initialize( serviceClass_._svc_name_,
                                   os.path.abspath( servicemanager.__file__ ) )
        toLog("Initialize with __file__")
        try:
            # servicemanager.StartServiceCtrlDispatcher()
            # win32serviceutil.HandleCommandLine(serviceClass_, argv=[os.path.abspath( servicemanager.__file__ ), "start"])
            win32serviceutil.StartService(
                serviceClass_._svc_name_
            )
            pass
        except Exception as e:
            toErrorLog("start servcie ctrl dispatcher " + str(e))
            removeLogger()
            win32serviceutil.HandleCommandLine(serviceClass_, argv=[__file__, "stop"])
            # sys.exit(1)
        # try:
        #     win32serviceutil.StartService(
        #         serviceClass_._svc_name_
        #     )
        # except Exception as e:
        #     toErrorLog("start servcie ctrl dispatcher " + str(e))
        #     removeLogger()
        #     win32serviceutil.HandleCommandLine(serviceClass_, argv=[__file__, "stop"])
        #     sys.exit(1)
            # win32serviceutil.HandleCommandLine(self.serviceClass_, argv=[ servicemanager.__file__ , "start"])
    else :
        removeLogger()
        win32serviceutil.HandleCommandLine(serviceClass_, argv=[__file__, "restart"])

def install(  ):
    toLog("Installation start")
    win32api.SetConsoleCtrlHandler(lambda x: True, True)
    result = verifyInstall()

    thisExePath = os.path.realpath( sys.argv[0] )
    thisExeDir  = os.path.dirname( thisExePath )
    serviceModPath = sys.modules[ serviceClass_.__module__ ].__file__
    serviceModPath = os.path.splitext(os.path.abspath( serviceModPath ))[0]
    serviceClassPath = "%s.%s" % ( serviceModPath, serviceClass_.__name__ )
    serviceClass_._svc_reg_class_ = serviceClassPath

    serviceExePath = (serviceModPath + ".exe") if isStandAloneContext() else None
    isAutoStart = serviceClass_._svc_is_auto_start_
    startOpt = (win32service.SERVICE_AUTO_START if isAutoStart else
                win32service.SERVICE_DEMAND_START)


    if result == SUCCESS or result != FAILURE:
        removeLogger()
        return result
    try :

        win32serviceutil.InstallService(
            pythonClassString = serviceClass_._svc_reg_class_,
            serviceName       = serviceClass_._svc_name_,
            displayName       = serviceClass_._svc_display_name_,
            description       = serviceClass_._svc_description_,
            exeName           = serviceExePath,
            startType         = startOpt,
        )
    except win32service.error as e:
        toErrorLog("installation error" + str(e))
        return e[0]

    except Exception as e: raise e

    win32serviceutil.SetServiceCustomOption(
        serviceClass_._svc_name_, thisExePath, thisExeDir )

    for i in range( 0, MAX_STATUS_CHANGE_CHECKS ) :
        result = verifyInstall()
        if result == SUCCESS:
            toLog("Install complete")
            removeLogger()
            return SUCCESS
        sleep( STATUS_CHANGE_CHECK_DELAY )
    removeLogger()
    return result

def removeService():
    win32serviceutil.HandleCommandLine(serviceClass_, argv=[__file__, "stop"])
    win32serviceutil.HandleCommandLine(serviceClass_, argv=[__file__, "remove"])
    removeLogger()

def verifyInstall():
    c = wmi.WMI ()
    srv = c.Win32_Service(name=serviceClass_._svc_name_)
    if srv != []:
        toLog(str(srv))
        return 0
    return -1

def killProcess(idProcess_ = None):
    try:
        os.system("taskkill /fi TestService_3.exe")
        os.system("taskkill /fi _A")
        print("--killed process--")
    except:
        pass
        print("--not found process--")
    try:
        p = "M:\\work\\freelance\\test\\testServiceTask\\dist\\TestService_3.exe"
        p2 = "M:\\work\\freelance\\test\\testServiceTask\\dist"
        # os.rmdir(p2)
        # os.chmod(p, stat.S_IWUSR)
        # os.unlink(p)
        # os.chmod(p, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.chmod(p, 0777)
        os.remove(p)
    except Exception as e:
        print("error remove file", e)

def tryInstall():

    dispatch()
    # WinServiceManager(TestServiceSvc).dispatch()


def removeInstall():
    removeService()
    # WinServiceManager(TestServiceSvc).removeService()


# 1053  --->   error
if __name__ == '__main__':
    init(TestServiceSvc)
    isDel = False
    # isDel = True
    isRun = True
    # win32serviceutil.StartService(
    #     TestServiceSvc._svc_name_
    # )
    # WinServiceManager(TestServiceSvc).dispatch()
    if isRun:
        if isDel:
            killProcess()
            removeInstall()
        else:
            tryInstall()