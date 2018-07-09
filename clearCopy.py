#!/usr/bin/env python
import os
import sys
import uuid
import argparse
import re
import logging

def override(s,l):
    bb = re.split("/", s)
    if bb == []:
        return s
    i = 0
    for c in bb:
        for d in l.keys():
            if d in c:
                bb[i] = l.get(d)
        i = i + 1
    return '\\'.join(bb)

def build_path(p, gp):
    return (gp.strip().strip("\\").strip("/") + "\\" + p.strip().strip("\\").strip("/")).replace("/","\\").strip("\\")

def gen_path(dd, list):
    newl = {}
    aa = dd
    newlist = []
    for key in dd.keys():
        newl[key] = override(dd.get(key),aa)

    for l in list:
        #print l
        aa = re.split(" *# *",l)
        aaa = re.split(" ",aa[0])
        if aaa != []:
            for aaaa in aaa:
                if re.search(" *\\S*.inf *\S*", aaaa):
                    newlist.append(override(aaaa, newl))
        continue
        newlist.append(override(aa[0], newl))
    #print "============================================"
    #for l in newlist:
        #print l
    return newlist

def gen_path_(dd, list):
    newl = {}
    aa = dd
    newlist = []
    for key in dd.keys():
        newl[key] = override(dd.get(key),aa)

    for l in list:
        #print l
        if re.match(" *# *",l):
            continue

        aaa = re.split(" *# *",l)
        if aaa != []:
            for aaaa in aaa:
                if re.search(" *\\S*.dec *\S*", aaaa):
                    newlist.append(override(aaaa, newl))
        continue
        newlist.append(override(l, newl))
    #print "============================================"
    #for l in newlist:
        #print l
    return newlist



def prasesection(path):
    fileLinesList = []
    userExtFind = False
    findEnd = True
    fileLastLine = False
    sectionLine = ''
    sectionData = []
    section = {}
    """
    read line and prase [xxxx] section data
    """
    fileLinesList = open(path, "r+").readlines()
    for index in range(0, len(fileLinesList)):
        line = str(fileLinesList[index]).strip()
        if index + 1 == len(fileLinesList):
            fileLastLine = True
            nextLine = ''
        else:
            nextLine = str(fileLinesList[index + 1]).strip()

        if userExtFind and findEnd == False:
            if line:
                sectionData.append(line)
        """if line contian [], assume this as a section"""
        if line.lower().startswith("[") and line.lower().endswith("]"):
            sectionLine = line
            userExtFind = True
            findEnd = False
        """if next line is end with []"""
        if (nextLine != '' and nextLine[0] == "[" and \
            nextLine[-1] == "]") or fileLastLine:
            userExtFind = False
            findEnd = True
            #print sectionLine
            # self.infSectionDataList.append({sectionLine: sectionData[:]})
            if section.has_key(sectionLine):
                data = section.get(sectionLine)
                for a in sectionData:
                    data.append(a)
                section[sectionLine] = data
            else :
                section[sectionLine] = sectionData[:]
            sectionData = []
            sectionLine = ''
            data = []
    #print "aaaa", section
    return section

def replacedefine(s, d):

    a = ""
    b = ""
    found = False
    end = False
    '''if string not have "$()", just return'''
    if s.find("$(") == -1:
        return s
    '''dispatch string'''
    for index in xrange(0,len(s)):
        if s[index] == "$" or s[index] == "(": #skip $(
            found = True
            continue
        if s[index] == ")": #skip )
            end = True
            continue
        if found == True and end != True: #find xxxx in $(xxxx)
            a = a + s[index]
        if found == True and end == True:
            found = False
            end = False
            if a in d.keys(): #find string in define list
                b = b + d.get(a).strip().strip("\\") #replace string
            a = ""
        if found == False and end == False:
            b = b + s[index]
    return b

def filterMark(s):
    '''if  string begin with #, we assume this as marked string'''
    b = ""
    '''check whether frist c is not "#", if True, just return NULL'''
    if s.strip().strip(" ").find("#") == 0:
        return ""
    '''found if there have # and then spilt it and assume the string after # is not useful'''
    if s.find("#") != -1:
        return s.split("#")[0]
    return s

"""
find the who path to search the matched fileNames
input: file name / code path
output: whole file path
"""
def found_path(fileName, path):
    for root, dirs, files in os.walk(path,True):
        for file in files:
            if file == fileName:
                return  root + "\\" + file
    return ""


class IniFile:
    def __init__(self, path):
        self.path = ""
        self.exist = True
        self.section = {}
        self.workPath = ""
        self.testPath = ""
        self.used = []
        self.dscList = []
        self.fdfList = []
        self.fileList = []
        if not os.path.isfile(path):
            self.exist = False
        self.path = path
        pass

    def prase_section(self):
        self.section = prasesection(self.path)
        pass

    def prase_path(self):
        section = self.section
        if "[PATHS]" not in section.keys():
            return
        paths = section.get("[PATHS]")
        for path in paths:
            if re.match(" *# *", path) is None and path.find("=") > -1:
                path_ = re.split(" *= *", path.replace("#", " "))
                if "WorkPath" in path_:
                    self.workPath = path_[1]
                if "TestPath" in path_:
                    self.testPath = path_[1]
        pass

    def prase_used(self):
        section = self.section
        dirList = []
        fileList = []
        if "[USED]" not in section.keys():
            return
        lines = section.get("[USED]")
        for line in lines:
            if re.match(" *# *", line) is None:
                line_ = re.split(" *", line.replace("#", " "))
                if line_[0] != "":
                    self.used.append(line_[0])

        pass

    def prase_fdf(self):
        section = self.section
        if "[FDFS]" not in section.keys():
            return
        paths = section.get("[FDFS]")
        for path in paths:
            if re.match(" *# *", path) is None:
                self.fdfList.append(re.split(" ",path.replace("=", " ").replace("#", " "))[0])
        pass

    def prase_dsc(self):
        section = self.section
        if "[DSCS]" not in section.keys():
            return
        paths = section.get("[DSCS]")
        for path in paths:
            if re.match(" *# *", path) is None:
                self.dscList.append(re.split(" ",path.replace("=", " ").replace("#", " "))[0])
        pass

    def prase_file(self):
        extension = []
        section = self.section
        if "[FILES]" not in section.keys():
            return
        files = section.get("[FILES]")
        for file in files:
            if file.find("*") == 0:
                ext = file.strip().strip("*").strip(" ")
                for root, dirs, files in os.walk(self.workPath, True):
                    for file in files:
                        if ext in file:
                            self.fileList.append(root+"\\"+file)

        pass
    def process(self):
        if not self.exist:
            return
        self.prase_section()
        self.prase_dsc()
        self.prase_fdf()
        self.prase_path()
        self.prase_used()
        self.prase_file()
        pass

class DebugMessage:
    def __init__(self, path):
        self.path = path
        logger = logging.getLogger()
        formatter1 = logging.Formatter('[line:%(lineno)d] %(message)s')
        formatter = logging.Formatter('%(message)s')
        file_handler = logging.FileHandler(path)
        file_handler.setFormatter(formatter1)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = formatter
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        self.log = logger
        pass

    def messageDebug(self,level,message):
        if level == "INFO":
            self.log.info(message)
        if level == "DEBUG":
            self.log.debug(message)
        if level == "ERROR":
            self.log.error(message)
        if level == "ALWAYS":
            self.log.critical(message)
        pass
LOG_L ={    0:"INFO",
            1:"DEBUG",
            2:"ERROR"}

log = DebugMessage(os.path.join(os.getcwd(),"log.txt"))


class DscFile:
    DEF_STRING = "DEFINE"
    def __init__(self, path, workPath):

        self.path = ""
        self.workPath = workPath
        self.define = {}
        self.infList = []
        self.dscList = []
        self.section = {}
        self.exist = True
        """check the inf file exist or not"""
        if os.path.isfile(path) is not True:
            self.exist = False
            return
        self.path = path
        pass

    def prase_section(self):
        self.section = prasesection(self.path)
        pass

    def prase_lib(self):
        section = self.section
        for key in section.keys():
            librarys = []
            libraysTemp = []
            '''get line from [LibraryClasses.XXXX] and [Components.XXXXX] section'''
            if "LibraryClasses" not in key and "Components" not in key:
                continue
            librarys = section.get(key)   # get seciton data libary lines
            libraysTemp = librarys
            '''check if there have a dsc file in this'''
            for line in libraysTemp:
                lineTemp = self.prasedsc(line, [])
                if lineTemp != []:
                    for lineTempLine in lineTemp:
                        librarys.append(lineTempLine)
            '''dispatch all line and library line'''
            for line in librarys:
                # ".inf" and not marked with # and "|" means this is lib line
                # such as xxxLib|xxxxxxx/xxxxxx/xxxx.inf
                if line.find(".inf")>-1 and re.match(" *# *", line) is None and line.find("|")>-1:
                    #replace "|" and "#" and "{" in driver override library
                    lineReplace = line.replace("|", " ").replace("#", " ").replace("{", " ")
                    if lineReplace.find(" ") > -1:
                        # split xxxLib|xxxxxxx/xxxxxx/xxxx.inf #aaaaa ===> xxxLib xxxxxxx/xxxxxx/xxxx.inf aaaaa
                        # ===> [xxxLib, xxxxxxx/xxxxxx/xxxx.inf, aaaaa]
                        infLibraryFiles = re.split(" ", lineReplace)
                        for infLibraryFile in infLibraryFiles:
                            #check str in [xxxLib, xxxxxxx/xxxxxx/xxxx.inf, aaaaa] which have a ",inf"
                            if infLibraryFile.find(".inf") > -1 and infLibraryFile not in self.infList:
                                self.infList.append(infLibraryFile)
        pass

    def prase_dsc(self):
        fileLinesList = open(self.path, "r+").readlines()
        dscFileList = []
        for line in fileLinesList:
            #check ".dsc" and not marked as "#"
            #such as  xxxxx xxxxx/xxxxx/xxxx.dsc #aaa
            if ".dsc" in line and re.match(" *# *", line) is  None:
                if line.find(" ") > -1:
                    dscFileStrings = re.split(" *",line.replace("#"," "))
                    for dscFileString in dscFileStrings:
                        #check str in [xxxx, xxx/xxxx/xxxx.dsc, aaa] which have a ".dsc"
                        if ".dsc" in dscFileString and dscFileString not in self.dscList:
                            self.dscList.append(dscFileString)
        pass

    def prasedsc(self,dscLine,dscLines):
        # check dscLine [xxxx xxxx/xxxx/xxxx.dsc #aaaa] and not marked with "#"
        if ".dsc" in dscLine and re.match(" *# *", dscLine) is None:
            dscReplaceLine = dscLine.replace("#"," ")
            #find if there have a " "
            if dscReplaceLine.find(" ") > -1:
                dscFileStrings = re.split(" ", dscReplaceLine)
                for dscFileString in dscFileStrings:
                    if ".dsc" in dscFileString and dscFileString not in self.dscList:
                        self.dscList.append(dscFileString)
                        # find the real dsc path with defines in [Defines]
                        dscFileReplaceString = replacedefine(dscFileString, self.define)
                        dscFilePath = build_path(dscFileReplaceString, self.workPath)
                        #print dsc_,dsc__
                        #check whether have a true path
                        if os.path.isfile(dscFilePath):
                            #open new dsc file
                            lines = open(dscFilePath, "r+").readlines()
                            for line in lines:
                                #dispathc lines
                                dscLines.append(line)
                                self.prasedsc(line,dscLines)
        return dscLines


    def prase_driver(self):
        section = self.section
        for key in section.keys():
            if "Components" not in key:
                continue
            #dispatch line and find if there a dsc file
            driverLines = []
            driverLinesTemp = []
            driverLinesTemp = section.get(key)
            driverLines = driverLinesTemp
            for driverLine in driverLinesTemp:
                newDriverLines = self.prasedsc(driverLine,[])
                if newDriverLines != []:
                    for newDriverLine in newDriverLines:
                        driverLines.append(newDriverLine)
            #dispatch all line in this section
            for driverline in driverLines:
                #check if there have [INF XXXX/XXXX/XXXX.INF #AAAA] and not marked with "#" and library override
                if driverline.find(".inf") > -1 and re.match(" *# *", driverline) is None and driverline.find("|") == -1 :
                    #replace [XXXX/XXXX/XXXX.INF #AAAA] == [XXXX/XXXX/XXXX.INF AAAA]
                    # replace [XXXX/XXXX/XXXX.INF { #AAAA] == [XXXX/XXXX/XXXX.INF   AAAA]
                    driverReplaceLine = driverline.replace("#", " ").replace("{", " ")
                    if driverReplaceLine.find(" ")>-1:
                        driverFileStrings = re.split(" ",driverReplaceLine)
                        for driverFileString in driverFileStrings:
                            if driverFileString.find(".inf") > -1 and driverFileString not in self.infList :
                                self.infList.append(driverFileString)
                                break
                    else:
                        #append [XXXX/XXXX/XXXX.INF]
                        self.infList.append(driverReplaceLine.strip(" "))
        pass

    def prase_define(self):
        '''check wheather there have a [Defines] section'''
        define = {}
        defineTemp = {}
        defineLines = []
        defineLinesTemp = []
        if self.section.has_key('[Defines]'):
            defineLinesTemp = self.section.get('[Defines]')
        '''prase lines which contian "DEFINE" and build a define dict'''
        defineLines = defineLinesTemp
        #1.dispatch and find the defines
        for defineLine in defineLines:
            if (self.DEF_STRING in defineLine) and re.match(" *# *", defineLine) is None:
                defineReplaceLine = defineLine.replace("DEFINE", "").replace(" ","")
                defineLineFindMark = defineReplaceLine.find("#")
                if defineLineFindMark > -1:
                    defineTemp[defineReplaceLine[:defineReplaceLine.find("=")]] = defineReplaceLine[defineReplaceLine.find("=")+1:defineLineFindMark]
                    continue
                defineTemp[defineReplaceLine[:defineReplaceLine.find("=")]] = defineReplaceLine[defineReplaceLine.find("=") + 1:]
            dscDefinesLines = self.prasedsc(defineLine, [])
            if dscDefinesLines != []:
                for dscDefineLine in dscDefinesLines:
                    defineLines.append(dscDefineLine)
        #2.replace the define value in self.defines
        temp = defineTemp
        for key in defineTemp.keys():
            self.define[key] = replacedefine(defineTemp.get(key),temp)
        pass

    def process(self):
        if not self.exist:
            return
        self.prase_section()
        self.prase_define()
        self.prase_driver()
        self.prase_lib()
        self.prase_dsc()
        pass



class FdfFile:
    USED_FILES = [".efi",".EFI",".BIN",".Bin",".bin",".dat",".Dat",".pdb",".rom",".depex",".bmp",".JPG",".crt",".der",".txt"]
    def __init__(self, path, workPath):
        self.path = ""
        self.binList = []
        self.definelist = {}
        self.section = {}
        self.exist = True
        """check the inf file exist or not"""
        self.fdfList = []
        if os.path.isfile(path) is not True:
            self.exist = False
            return
        self.path = path
        self.workPath = workPath
        self.dir = os.path.dirname(self.path).replace(self.workPath,"").strip().strip("\\")
        pass

    def prase_section(self):
        self.section = prasesection(self.path)
        pass

    def prase_define(self):
        pass

    def prase_fdf(self):
        for data in self.section.keys():
            fvLines = self.section.get(data)
            for fvline in fvLines:
                # found the fdf file such as [xxxx XXXX/XXXX/XXXX.fdf #aaaa] and not marked
                if re.match(" *# *", fvline) is None and fvline.find(".fdf"):
                    if fvline.find(" ") > -1:
                        fdfLineStrings = re.split(" ", fvline.replace("#", " "))
                        for fdfLineString in fdfLineStrings:
                            if ".fdf" in fdfLineString:
                                self.fdfList.append(os.path.join(self.dir,fdfLineString))
        pass
    def prase_bin(self):
        binarylist = []
        for key in self.section.keys():
            #check [FV.xxxx] section
            if "FV." not in key:
                continue
            fvLines = self.section.get(key)
            for fvLine in fvLines:
                # bypass marked line
                if re.match(" *# *", fvLine) is None:
                    #found the binrary file such as [xxxx  =  XXXX/XXXX/XXXX.efi #aaaa] ==> [xxxx   XXXX/XXXX/XXXX.efi  aaaa]
                    fvLineReplace = fvLine.replace("INF","").replace("#"," ").replace("="," ")
                    for fileSuffix in self.USED_FILES:
                        # check whether the line have the current Suffix String
                        if fvLineReplace.find(fileSuffix) > -1:
                            if fvLineReplace.find(" ") > -1:
                                # split the line as [xxxx XXXX/XXXX/XXXX.efi aaaa]
                                fvLineReplaceStrings = re.split(" ", fvLineReplace)
                                for fvLineReplaceString in fvLineReplaceStrings:
                                    if fileSuffix in fvLineReplaceString:
                                        binarylist.append(fvLineReplaceString)
                            else:
                                binarylist.append(fvLineReplace)
        self.binList = binarylist

        pass

    def process(self):
        if not self.exist:
            return
        self.prase_section()
        self.prase_bin()
        self.prase_fdf()
        pass



class InfFile:
    SECTION = {
                "def":"[Defines]",
                "dec":"[Packages]"
               }
    DEF_STRING = "DEFINE"
    def __init__(self, path, workPath):
        self.path = ""
        self.section = {}
        self.define = {}
        self.decList = []
        self.workPath = workPath
        self.exist = True
        """check the inf file exist or not"""
        if os.path.isfile(path) is not True:
            self.exist = False
            return
        self.path = path

    def prase_section(self):
        self.section = prasesection(self.path)
        pass

    def prase_defines(self):
        '''check wheather there have a [Defines] section'''
        define = {}
        defineLines = []
        if self.section.has_key('[Defines]'):
            defineLines = self.section.get('[Defines]')
        '''prase lines which contian "DEFINE" and build a define dict'''
        for defineLine in defineLines:
            #found line [DEFINE XXXXX = XXXXX] and not marked with #
            if self.DEF_STRING in defineLine and re.match(" *# *",defineLine) is None:
                defineLineReplace = defineLine.strip().strip("\n").strip(" ").replace("DEFINE", "").replace(" ","")
                defineLineMarked = defineLineReplace.find("#")
                if defineLineMarked > -1:
                    define[defineLineReplace[:defineLineReplace.find("=")]] = defineLineReplace[defineLineReplace.find("=")+1:defineLineMarked]
                    continue
                define[defineLineReplace[:defineLineReplace.find("=")]] = defineLineReplace[defineLineReplace.find("=") + 1:]
        self.define = define

    def prase_dec(self):
        decLines = []
        decList = []
        if self.section.has_key('[Packages]'):
            decLines = self.section.get('[Packages]')
        if decLines == []:
            return
        for decLine in decLines:
            decLineFiltred = filterMark(replacedefine(decLine, self.define))
            if decLineFiltred != "" and decLineFiltred not in decList:
                decList.append(decLineFiltred)
        self.decList = decList
        pass

    def process(self):
        if not self.exist:
            return
        self.prase_section()
        self.prase_defines()
        self.prase_dec()
        pass

class DecFile:
    def __init__(self, path, workPath):
        """
            section[] --- section data in dec
            inlcude[] --- include file path list
        """

        self.section = {}
        self.includeList = []
        self.path = ""
        self.workPath = workPath
        self.exist = True
        """check the inf file exist or not"""
        if os.path.isfile(path) is not True:
            self.exist = False
            return
        self.exist = True
        self.path = path
        self.dir = os.path.dirname(self.path).replace(self.workPath,"").strip().strip("\\")
        pass

    def prase_section(self):
        self.section = prasesection(self.path)
        pass

    def prase_include(self):
        includeList = []
        includeLines = []
        for key in self.section.keys():
            if "[Includes" not in key:
                continue
            includeLines = self.section.get(key)
            if includeLines == []:
                return
            for includeLine in includeLines:
                if re.match(" *# *",includeLine) is not None:
                    continue
                includeLineFilter = filterMark(includeLine)
                if includeLineFilter != "" and includeLineFilter.strip(" ") != "" and includeLineFilter not in includeList:
                    includeList.append(self.dir+ "/" + includeLineFilter.strip())
        self.includeList = includeList

    def process(self):
        if not self.exist:
            return
        self.prase_section()
        self.prase_include()

def copyfolder(sourceDir,targetDir):
    for file in os.listdir(sourceDir):
        sourceFile = os.path.join(sourceDir, file)
        targetFile = os.path.join(targetDir, file)
        log.messageDebug(LOG_L[0], "  [" + sourceDir + "===>" + targetDir + "]")
        if os.path.isfile(sourceFile):
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)
            if not os.path.exists(targetFile):
                log.messageDebug(LOG_L[0], "    -" + file + "===>" + file)
                open(targetFile, "wb").write(open(sourceFile, "rb").read())
        if os.path.isdir(sourceFile):
            copyfolder(sourceFile, targetFile)

class CopyUsed:

    def __init__(self, work, test, pathList,  buildType):
        self.type = "none"
        self.source = ""
        self.target = ""
        self.work = work
        self.test = test
        self.buildType = buildType
        self.pathList = pathList
        pass

    def copy_folders(self):
        sourceDir = self.source
        targetDir = self.target
        if not os.path.exists(sourceDir):
            return
        log.messageDebug(LOG_L[0], "[" + sourceDir + "===>" + targetDir + "]")
        copyfolder(sourceDir, targetDir)
        pass

    def copy_files(self):
        sourceFile = self.source
        targetFile = self.target
        if not os.path.exists(sourceFile):
            return
        if os.path.isfile(sourceFile):
            log.messageDebug(LOG_L[0], "   " + sourceFile + "===>" + targetFile)
        if not os.path.exists(os.path.dirname(targetFile)):
            os.makedirs(os.path.dirname(targetFile))
        if not os.path.exists(targetFile):
            open(targetFile, "wb").write(open(sourceFile, "rb").read())

    def processDebug(self):
        for pathList in self.pathList:
            sourceDir = buildpaths(self.work, pathList, self.buildType)
            targetDir = buildpaths(self.test, pathList, self.buildType)
            if sourceDir == "" or targetDir == "":
                continue
            self.source = sourceDir
            self.target = targetDir
            if not os.path.exists(self.source):
                self.type = "none"
            if os.path.isdir(self.source):
                self.type = "dir"
            if os.path.isfile(self.source):
                self.type = "file"
            self.debug()

    def process(self):
        for pathList in self.pathList:
            sourceDir = buildpaths(self.work, pathList, self.buildType)
            targetDir = buildpaths(self.test, pathList, self.buildType)
            if sourceDir == "" or targetDir == "":
                continue
            self.source = sourceDir
            self.target = targetDir
            if not os.path.exists(self.source):
                self.type = "none"
                continue
            if os.path.isdir(self.source):
                self.copy_folders()
            if os.path.isfile(self.source):
                self.copy_files()

    def debug(self):
        if self.type == "none":
            print "[None]:", self.source, "==>", self.target
        if self.type == "dir":
            print "[dir]:",self.source,"==>",self.target
        if self.type == "file":
            print "[file]:", self.source, "==>", self.target


def buildpaths(fp, sp, type):
    fristPath = fp.strip().strip("\\").strip("/").replace("/","\\")
    secondPath = sp.strip().strip("\\").strip("/").replace("/","\\")
    if sp == "" or fp == "":
        return fp
    if type == "none":
        return os.path.join(fristPath, secondPath)
    if type == "dirname":
        return os.path.dirname(os.path.join(fristPath, secondPath))
    if type == "replace":
        fristPaths = fristPath.split("\\")
        secondPaths = secondPath.split("\\")
        for index in xrange(0,len(fristPaths),1):
            if fristPaths[index] == secondPaths[index]:
                continue
            secondPaths[index] = fristPaths[index]
        return "\\".join(secondPaths).strip().strip("\\").strip("/").replace("/","\\")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='ini', type=str, help='ini file path', required=True)
    args = parser.parse_args()

    '''process the ini file, get the information'''
    ini = IniFile(args.ini)
    #print args.ini
    ini.process()
    #print ini.workPath,ini.used
    log.messageDebug(LOG_L[0], " ======================Get ini file information Start==========================")
    log.messageDebug(LOG_L[0], "WorkPath: %s" % ini.workPath)
    log.messageDebug(LOG_L[0], "TestPath: %s" % ini.testPath)
    log.messageDebug(LOG_L[0], ("Fdf file: %s" % " ".join(ini.fdfList)))
    log.messageDebug(LOG_L[0], ("dsc file: %s" % " ".join(ini.dscList)))
    log.messageDebug(LOG_L[0], ("used dir: %s" % "\n          ".join(ini.used)))

    log.messageDebug(LOG_L[0], "  ======================Get ini file information End ==========================")

    '''walk through the work dir and  get dsc and fdf file path'''
    fdfFilePathsList = []
    dscFilePathsList = []
    for fdfFile in ini.fdfList:
        fdfFilePathsList.append(found_path(fdfFile, ini.workPath))
    for fdfFile in ini.dscList:
        dscFilePathsList.append(found_path(fdfFile, ini.workPath))
    #print fdfFilePathsList,dscFilePathsList

    '''prase dsc file'''
    log.messageDebug(LOG_L[0], " ======================Get dsc file information Start==========================")
    log.messageDebug(LOG_L[0], " [Dsc File Name]: %s" % " ".join(dscFilePathsList))
    infFilesList = []
    dscFilesList = []
    dscDefine = {}
    for dscFilePath in dscFilePathsList:
        dscFile = DscFile(dscFilePath, ini.workPath)
        dscFile.process()
        for infFile in dscFile.infList:
            temp = replacedefine(infFile.strip("").strip("\n"),dscFile.define)
            if temp not in infFilesList:
                infFilesList.append(temp)
        for dsc_File in dscFile.dscList:
            temp = replacedefine(dsc_File.strip("").strip("\n"), dscFile.define)
            if temp not in dscFilesList:
                dscFilesList.append(temp)
        for key in dscFile.define.keys():
            dscDefine[key] = dscFile.define.get(key)
    log.messageDebug(LOG_L[0], "   -Inf File-")
    log.messageDebug(LOG_L[0], " \n".join(infFilesList))
    log.messageDebug(LOG_L[0], "   -Dsc File-")
    log.messageDebug(LOG_L[0], " \n".join(dscFilesList))
    log.messageDebug(LOG_L[0], " ======================Get dsc file information End==========================")

    '''prase inf file'''
    log.messageDebug(LOG_L[0], " ======================Get inf file information Start==========================")
    decFilesList = []
    for inf_File in infFilesList:
        infFilePath = os.path.join(ini.workPath,inf_File.replace("/","\\"))
        #print infFilePath, os.path.isfile(infFilePath)
        infFile = InfFile(infFilePath, ini.workPath)
        infFile.process()
        #print infFile.decList
        for decFile in infFile.decList:
            temp = replacedefine(decFile, infFile.define).strip().strip(" ").strip("\n")
            if temp not in decFilesList:
                decFilesList.append(temp)
    log.messageDebug(LOG_L[0], "   -dec File-")
    log.messageDebug(LOG_L[0], " \n".join(decFilesList))
    log.messageDebug(LOG_L[0], " ======================Get inf file information End==========================")

    '''prase dec file'''
    log.messageDebug(LOG_L[0], " ======================Get dec file information Start==========================")
    includePathsList = []
    for decFilePath in decFilesList:
        decFilePath_Path = os.path.join(ini.workPath, decFilePath.replace("/","\\"))
        #print infFilePath, os.path.isfile(infFilePath)
        decFile = DecFile(decFilePath_Path, ini.workPath)
        decFile.process()
        #print infFile.decList
        for includePath in decFile.includeList:
            temp = includePath.strip().strip(" ").strip("\n")
            if temp not in includePathsList:
                includePathsList.append(includePath)
    log.messageDebug(LOG_L[0], "   -include  File-")
    log.messageDebug(LOG_L[0], " \n".join(includePathsList))
    log.messageDebug(LOG_L[0], " ======================Get inf file information End==========================")

    '''prase fdf file'''
    log.messageDebug(LOG_L[0], " ======================Get fdf file information Start==========================")
    log.messageDebug(LOG_L[0], " [fdf File Name]: %s" % " ".join(fdfFilePathsList))
    binFilesList = []
    fdfFilesList = []
    for fdfFilePath in fdfFilePathsList:
        fdfFile = FdfFile(fdfFilePath, ini.workPath)
        fdfFile.process()
        for binFile in fdfFile.binList:
            temp = replacedefine(binFile.strip("").strip("\n"), dscDefine)
            if temp not in binFilesList:
                binFilesList.append(temp)
        for fdf_File in fdfFile.fdfList:
            temp = replacedefine(fdf_File.strip("").strip("\n"), dscDefine)
            if temp not in fdfFilesList:
                fdfFilesList.append(temp)
    log.messageDebug(LOG_L[0], "   -bin File-")
    log.messageDebug(LOG_L[0], " \n".join(binFilesList))
    log.messageDebug(LOG_L[0], "   -fdf File-")
    log.messageDebug(LOG_L[0], " \n".join(fdfFilesList))
    log.messageDebug(LOG_L[0], " ======================Get fdf file information End==========================")

    """start copy used files"""
    log.messageDebug(LOG_L[0], " ======================START COPY FILES==========================")
    log.messageDebug(LOG_L[0], " [Inlcude folders]:")
    CopyUsed(ini.workPath, ini.testPath, includePathsList, "none").process()

    log.messageDebug(LOG_L[0], " [INF FILE folders]:")
    CopyUsed(ini.workPath, ini.testPath, infFilesList, "dirname").process()

    log.messageDebug(LOG_L[0], " [DEC FILE ]:\n %s" % '\n'.join(decFilesList))
    CopyUsed(ini.workPath, ini.testPath, decFilesList, "none").process()

    log.messageDebug(LOG_L[0], " [bin FILE ]:")
    CopyUsed(ini.workPath, ini.testPath, binFilesList, "none").process()

    log.messageDebug(LOG_L[0], " [dsc FILE ]:")
    CopyUsed(ini.workPath, ini.testPath, dscFilesList, "none").process()
    CopyUsed(ini.workPath, ini.testPath, dscFilePathsList, "replace").process()

    log.messageDebug(LOG_L[0], " [Fdf FILE ]:")
    CopyUsed(ini.workPath, ini.testPath, fdfFilesList, "none").process()
    CopyUsed(ini.workPath, ini.testPath, fdfFilePathsList, "replace").process()

    log.messageDebug(LOG_L[0], " [Used in Ini]:")
    CopyUsed(ini.workPath, ini.testPath, ini.used, "none").process()

    log.messageDebug(LOG_L[0], " [File in Ini]:")
    CopyUsed(ini.workPath, ini.testPath, ini.fileList, "replace").process()
    #print '\n'.join(ini.fileList)

    return



if __name__ == '__main__':
    main()