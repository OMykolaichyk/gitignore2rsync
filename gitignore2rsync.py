#!/usr/bin/env python
"""
My awesome script to convert gitignore files to rsync exclude rules
"""

import io
import os
import os.path
import string
import sys


def usage():
    print "Too many arguments!"
    print "Usage:"
    print "\tpython gitignore2rsync.py [PATH]"
    print "\t\t[PATH] - path to ROOT project dir"
    print "\tIn case when PATH not received - current dir will be the ROOT project dir"

def globalGitPaths():

    globalGitPaths = []
    envString = os.environ.get("HOME")
    if envString != None:
        globalGitPaths.append(os.path.join(envString, ".config", "git", "ignore"))

    envString = os.environ.get("XDG_CONFIG_HOME")
    if envString != None:
        globalGitPaths.append(os.path.join(envString, "git", "ignore"))

    globalGitPaths.append(os.path.join(rootProjectPath, ".git", "info", "exclude"))

    return globalGitPaths

def readFile(path):
    gitignoreParams = []
    try:
        f = io.open(path)
        if f.readable():
            for line in f:
                gitignoreParams.append(line)
    except IOError as e:
        print "I/O error({0}): {1} ({2})".format(e.errno, e.strerror, path)
    return gitignoreParams


def readGlobalGitignoreFiles(globalGitignorePaths):
    ignoreParams = []
    for el in globalGitignorePaths:
        ignoreParams.extend(readFile(el))
    return ignoreParams

def readRootGitignoreFile(projectRoot):
    return readFile(os.path.join(projectRoot, ".gitignore"))

def convert(params):
    #del comments
    rsyncExcludeParams = []
    for el in params:
        if el[0] == "#":
            params.remove(el)
    #del end lines
    for el in params:
        found = string.find(el, "\n" )
        if found != -1:
            if len(el[:found]) != 0:
                rsyncExcludeParams.append(os.path.join(el[:found]))
    #convert "**" rule
    for el in rsyncExcludeParams:
        found = string.find(el, "**")
        if found != -1:
            rsyncExcludeParams.append(el[:found] + el[found+3:])
    return rsyncExcludeParams

def writeRsyncRulesToFile(rules, path=None):
    if path is None:
        path = os.path.join(rootProjectPath, "root.rsyncignore")
    else:
        path = os.path.join(path, "other.rsyncignore")
    if len(rules) != 0:
        f = open(path, "w+")
        for el in rules:
            f.write(el + "\n")

def writeMergeRulesToFile(mergeRule):
    path = os.path.join(rootProjectPath, ".rsyncignore")
    f = open(path, "w+")
    f.write(mergeRule + "\n")

def genMergeRules():
    rule = "dir-merge,n- other.rsyncignore"
    return rule
    pass


#we need to go deeper (-_-)
def readDeeper():
    ignoreList = []
    ignoreDict = dict() #key - dirpath, value - list of gitignore params
    for dirpath, dirnames, filenames in os.walk(rootProjectPath):
        if ".gitignore" in filenames and dirpath != rootProjectPath:
            f = io.open(os.path.join(dirpath, ".gitignore"), "r")
            for line in f:
                ignoreList.append(line)
            ignoreDict[dirpath] = ignoreList
            ignoreList = []
    return ignoreDict

# Python script entry point
if __name__ == '__main__':
    rootProjectPath = os.path.curdir
    if len(sys.argv) == 2:
        if os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]) \
                and os.access(sys.argv, os.W_OK ) and os.access(sys.argv[1], os.R_OK): #check is dir and permission
            rootProjectPath = sys.argv[1]
        else:
            print "Failed check for (Is path exists, is directory, access for reading or writing)"
    elif len(sys.argv) > 2:
        usage()
        exit(-1)
    paths = globalGitPaths()
    globalGitignoreParams = readGlobalGitignoreFiles(paths)
    globalGitignoreParams.extend(readRootGitignoreFile(rootProjectPath))
    rootRsyncRules = convert(globalGitignoreParams)
    writeRsyncRulesToFile(rootRsyncRules)

    mergeRule = genMergeRules()
    writeMergeRulesToFile(mergeRule)

    otherGitignoreFiles = readDeeper()
    otherRsyncRules = dict()
    for key, value in otherGitignoreFiles.iteritems():
        writeRsyncRulesToFile(convert(value), key)


