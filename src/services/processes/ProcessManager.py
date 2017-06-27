import threading

from multiprocessing import Event

from MyTestProcess import MyTestProcess


class ProcessManager:
    __processes = []

    def __init__(self, data, logQueue):
        self.__logQueue = logQueue
        self.__dataProcesses = data
        self.__isRunning = True
        self.__event = Event()

    def startProcesses(self):
        for process in self.__dataProcesses:
            self.__createProcess(process)

        self.processThread = threading.Thread(target=self.__checkProcesses, name="checkerProcess")
        self.processThread.start()

    def __checkProcesses(self):
        while self.__isRunning:
            for proc in self.__processes:
                if proc.is_alive() == False:
                    self.__logQueue.put("Process " + str(proc.name) + " is stopped, restart now")

                    proc.join()

                    self.__processes.remove(proc)
                    self.__createProcess(proc.name)

                    break

    def __createProcess(self, name):
        try:
            process = MyTestProcess(name, self.__logQueue, self.__event)
            self.__processes.append(process)
            process.start()
        except Exception as e:
            self.toError("error create process" + name + " error:" + str(e))

    def stopProcess(self):
        self.__isRunning = False
        self.__event.set()
        for proc in self.__processes:
            proc.join()

        if self.processThread.is_alive():
            self.processThread.join()

    def toError(self, value):
        self.toLog("ERROR:: " + value)

    def toLog(self, value):
        if self.__logQueue is not None:
            self.__logQueue.put(value)

    def getStatus(self):
        return sum(map(lambda x: 1 if x.is_alive() == True else 0, self.__processes)), len(self.__processes)