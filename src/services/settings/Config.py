from Settings import *

__defaultData = ["[processes]"]
__data = []

def parseData(data):
    __data.append(data)

def addData(data):
    __data.append(data)

def loadConfig():
    try:
        f = open(CONFIG_FILE_NAME, "r")
        isAdd = False
        for line in f:
            line = line.strip()
            if line[0] + line[-1:] == "[]":
                isAdd = line[1:-1] == "processes"
                continue

            if isAdd:
                addData(str(line))
        f.close()
    except Exception as e:
        __data = __defaultData
        __saveDefaultConfig()

def __saveDefaultConfig():
    try:
        f = open(CONFIG_FILE_NAME, "w")
        for value in __defaultData:
            f.writelines(value)
        f.close()
    except Exception as e:
        pass

def getData():
    return __data