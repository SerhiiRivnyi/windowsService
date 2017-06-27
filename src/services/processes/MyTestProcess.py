# -*- coding: utf-8 -*-

import multiprocessing
from time import sleep

class MyTestProcess(multiprocessing.Process):
    def __init__(self, name, queue, event = None):
        super(MyTestProcess, self).__init__(name=str(name))
        self.__queue = queue
        self.__event = event

    def run(self):
        self.__queue.put("Run process " + self.name)
        a = 10
        while not self.__event.is_set():
            sleep(1)
            a -= 1
            if a < 0:
                raise Exception(" a < 0 ")


        self.__queue.put("Exit from process " + self.name + " succesfull")