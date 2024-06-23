#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description: A helper library that has many functions that py3AnyText2Spreadsheet relies on. This library can also be used by parsing templates.

Library Usage: 
import resources.functions as functions
# Or to import directly:
# import sys
# import pathlib
# sys.path.append( str( pathlib.Path('C:\\resources\\functions.py').resolve().parent) )
# import functions
functions.verifyThisFileExists()

Function Usage: See each function for usage instructions.

Notes: Only functions that do not use module-wide variables and have return values are listed here. Functions without return values and those that rely on module specific variables that would be cumbersome to pass around should still be in the main program.

Copyright (c) 2024 gdiaz384; License: See main program.

"""
__version__='2024.06.21'


# Set defaults.
#printStuff=True
verbose=False
debug=False

consoleEncoding='utf-8'
defaultTextFileEncoding='utf-8'   # Settings that should not be left as a default setting should have default prepended to them.

linesThatBeginWithThisAreComments='#'
assignmentOperatorInSettingsFile='='
inputErrorHandling='strict'
#outputErrorHandling='namereplace'  # This gets set dynamically below.

parseSettingsExtension='.ini'

usageHelp='\n Usage: python py3AnyText2Spreadsheet --help'


# Import stuff. These must be here or the library will crash even if these modules have already been imported by main program.
import sys                                   # End program on fail condition.
import os, os.path                      # Extract extension from filename, and test if file exists.
import pathlib                            # For pathlib.Path Override file in file system with another and create subfolders. Sane path handling.
#import requests                          # Check if internet exists. # Update: Changed to socket library instead, so this is not needed anymore.
import socket
#import io                                      # Manipulate files (open/read/write/close).
import datetime                          # Used to get current date and time.
import csv                                    # Read and write to csv files. Example: Read in 'resources/languageCodes.csv'
import openpyxl                          # Used as the core internal data structure and to read/write xlsx files. Must be installed using pip.
try:
    import odfpy                           #Provides interoperability for Open Document Spreadsheet (.ods).
    odfpyLibraryIsAvailable=True
except:
    odfpyLibraryIsAvailable=False
try:
    import xlrd                              #Provides reading from Microsoft Excel Document (.xls).
    xlrdLibraryIsAvailable=True
except:
    xlrdLibraryIsAvailable=False

#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
sysVersion=int(sys.version_info[1])
if sysVersion >= 5:
    outputErrorHandling='namereplace'
elif sysVersion < 5:
    outputErrorHandling='backslashreplace'    
else:
    sys.exit( 'Unspecified error.'.encode(consoleEncoding) )


def checkEncoding(string, encoding):
    try:
        string.encode(encoding)
        return True
    except UnicodeEncodeError:
        return False

def normalizeEncoding(string, encoding):
    if checkEncoding(string, encoding) == True:
        return string
    # Okay, so, something messed up. What was it? Check character by character and klobber the offender.
    tempString=''
    for i in range( len(string) ):
        if checkEncoding( string[ i : i+1 ], encoding) == True:
            tempString=tempString+string[ i : i+1 ]
        else:
            print( ('Warning: ' + string[ i : i+1 ] + ' cannot be encoded to valid ' + encoding + '.' ).encode(consoleEncoding) )
    print( ('Warning: Output changed from to: \'' + tempString + '\'').encode(consoleEncoding) )
    return tempString


#Errors out if myFile or myFolder does not exist.
def verifyThisFileExists(myFile,nameOfFileToOutputInCaseOfError=None):
    if myFile == None:
        sys.exit( ('Error: Please specify a valid file for: ' + str(nameOfFileToOutputInCaseOfError) + usageHelp).encode(consoleEncoding))
    if os.path.isfile(myFile) != True:
        sys.exit( (' Error: Unable to find file \'' + str(nameOfFileToOutputInCaseOfError) + '\' ' + usageHelp).encode(consoleEncoding) )

def verifyThisFolderExists(myFolder, nameOfFileToOutputInCaseOfError=None):
    if myFolder == None:
        sys.exit( ('Error: Please specify a valid folder for: ' + str(nameOfFileToOutputInCaseOfError) + usageHelp).encode(consoleEncoding))
    if os.path.isdir(myFolder) != True:
        sys.exit( (' Error: Unable to find folder \'' + str(nameOfFileToOutputInCaseOfError) + '\' ' + usageHelp).encode(consoleEncoding) )

#Usage:
#verifyThisFileExists('myfile.csv','myfile.csv')
#verifyThisFileExists(myVar, 'myVar')


# Returns True or False depending upon if myFile, myFolder exists or not.
def checkIfThisFileExists(myFile):
    if (myFile == None) or (os.path.isfile(str(myFile)) != True):
        return False
    return True

def checkIfThisFolderExists(myFolder):
    if (myFolder == None) or (os.path.isdir(str(myFolder)) != True):
        return False
    return True

#Usage:
#checkIfThisFileExists('myfile.csv')
#checkIfThisFileExists(myVar)


# This function builds a Python dictionary from a text file and then returns it to the caller.
# The idea is to read program settings from text files using a predetermined list of rules.
# The text file uses the syntax: setting=value, # are comments, empty/whitespace lines ignored.
def getDictionaryFromTextFile(fileNameWithPath, fileNameEncoding, consoleEncoding=consoleEncoding, errorHandlingType=inputErrorHandling,debug=debug):
    if fileNameWithPath == None:
        print( ('Warning: Cannot read settings from None entry: ' + str(fileNameWithPath) ).encode(consoleEncoding) )
        return None

    #check if file exists   'scratchpad/ks_testFiles/A01.ks'
    #if os.path.isfile(fileNameWithPath) != True:
    #    sys.exit( ('\n Error: Unable to find input file \''+ fileNameWithPath + '\'' + usageHelp).encode(consoleEncoding) )
    verifyThisFileExists(fileNameWithPath, fileNameWithPath)

    #Newer, simplier syntax.
    with open( fileNameWithPath, 'rt', encoding=fileNameEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read()

    if not isinstance(inputFileContents, str):
        sys.exit( ('Error: Unable to read from file: '+fileNameWithPath).encode(consoleEncoding) )

    #Okay, so the file was specified, it exists, and it was read from successfully. The contents are in inputFileContents.
    #Now turn inputFileContents into a dictionary.
    tempDictionary={}
    #while line is not empty (at least \n is present)
    while inputFileContents != '' :
        #returns the current line that will be processed
        myLine=inputFileContents.partition('\n')[0] #returns first line of string to process in the current loop

        #The line should be ignored if the first character is a comment character (after removing whitespace) or if there is only whitespace
        ignoreCurrentLine = False
        if (myLine.strip() == '') or ( myLine.strip()[:1] == linesThatBeginWithThisAreComments.strip()[:1] )  :
            ignoreCurrentLine = True

        tempList=[]
        if ignoreCurrentLine == False:
            #If line should not be ignored, then = must exist to use it as a delimitor. exit due to malformed data if not found.
            if myLine.find(assignmentOperatorInSettingsFile) == -1:
                sys.exit( ('Error: Malformed data was found processing file: '+ fileNameWithPath + ' Missing: \''+assignmentOperatorInSettingsFile+'\'').encode(consoleEncoding) )
            #If the line should not be ignored, then use = as a delimiter set each side as key = value in a temporaryDictionary
            #Example:  paragraphDelimiter=emptyLine   #ignoreLinesThatStartWith=[ * ; 【     #wordWrap=45   #alwaysAddAfterTranslationEndOfLine=None
            key, value = myLine.split(assignmentOperatorInSettingsFile,1)
            key=key.strip()
            value=value.strip()
            if value.lower() == '':
                print( ('Warning: Error reading key\'s value \'' +key+ '\' in file: '+str(fileNameWithPath)+' Using None as fallback.').encode(consoleEncoding) )
                value = None
            elif value.lower() == 'none':
                value = None
            elif key.lower() == 'ignorelinesthatstartwith':#ignoreLinesThatStartWith
                #then every item that is not blank space is a valid list value
                tempList = value.split(' ')
                value=[]
                #Extra whitespace between entries is hard to spot in the file and can produce malformed list entries, so parse each entry individually.
                for i in tempList:
                    if i != '':
                        value.append(i.strip())
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            tempDictionary[key]=value

        #Finished processing line, so remove current line from string to prepare to process next line.
        inputFileContents=inputFileContents.partition('\n')[2] 

    #Finished reading entire file, so return resulting dictionary.
    if debug == True:
        print( (fileNameWithPath+' was turned into this dictionary='+str(tempDictionary)).encode(consoleEncoding) )
    return tempDictionary

# This returns either None or a dictionary of the contents of parsingProgram.ini.  It will try to infer thename
def getParseSettingsDictionary(parsingProgram, parseSettingsFile=None, parseSettingsFileEncoding=defaultTextFileEncoding):
    parsingScriptObject=pathlib.Path(parsingProgram).absolute()

    if parseSettingsFile == None:
        #check to see if settings file exists.
        if checkIfThisFileExists( str(parsingScriptObject.parent) + '/' + parsingScriptObject.stem + parseSettingsExtension ) == True:
            parseSettingsFile=str(parsingScriptObject.parent) + '/' + parsingScriptObject.stem + parseSettingsExtension
        elif checkIfThisFileExists( str(parsingScriptObject) + parseSettingsExtension ) == True:
            parseSettingsFile=str(parsingScriptObject) + parseSettingsExtension

    if debug==True:
        print('iniName1=' + str(parsingScriptObject.parent) + parsingScriptObject.stem + parseSettingsExtension)
        print('iniName2=' + str(parsingScriptObject) + parseSettingsExtension)

    if parseSettingsFile != None:
        print( 'Info: Using the following file as parseSettingsDictionary:')
        print( parseSettingsFile.encode(consoleEncoding) )
    #elif parseSettingsFile == None:
    else:
        print( 'Info: parseSettingsDictionary was not found.')
        return None

    parseSettingsDictionary = getDictionaryFromTextFile( parseSettingsFile, parseSettingsFileEncoding )

    if debug==True:
        print( ( 'parseSettingsDictionary=' + str(parseSettingsDictionary) ).encode(consoleEncoding) )

    return parseSettingsDictionary


def getCurrentMonthFromNumbers(x):
    x = str(x)
    if (x == '1') or (x == '01'):
        return 'Jan'
    elif (x == '2') or (x == '02'):
        return 'Feb'
    elif (x == '3') or (x == '03'):
        return 'Mar'
    elif (x == '4') or (x == '04'):
        return 'April'
    elif (x == '5') or (x == '05'):
        return 'May'
    elif (x == '6') or (x == '06'):
        return 'June'
    elif (x == '7') or (x == '07'):
        return 'July'
    elif (x == '8') or (x == '08'):
        return 'Aug'
    elif (x == '9') or (x == '09'):
        return 'Sept'
    elif (x == '10'):
        return 'Oct'
    elif (x == '11'):
        return 'Nov'
    elif (x == '12'):
        return 'Dec'
    else:
          sys.exit('Unspecified error.'.encode(consoleEncoding))


# These functions return the current date, time, yesterday's date, and full (day+time)
def getYearMonthAndDay():
    today = datetime.datetime.today()

    #debug code
    #print(datetime.today().strftime('%Y-%m-%d'))
    #print(today.strftime("%d/%m/%Y %H:%M:%S"))

    currentYear = str( today.strftime('%Y') )
#    currentMonth = getCurrentMonthFromNumbers(today.strftime('%m'))
    currentMonth = str( today.strftime('%m') )
    currentDay = str( today.strftime('%d') )
    return( currentYear + '-' + currentMonth + '-' + currentDay )


def getYesterdaysDate():
    yesterday = datetime.datetime.today() - datetime.timedelta(1)

    #debug code
    #print(datetime.yesterday().strftime('%Y-%m-%d'))
    #print(yesterday.strftime("%d/%m/%Y %H:%M:%S"))

    currentYear = str( yesterday.strftime('%Y') )
    currentMonth = getCurrentMonthFromNumbers(yesterday.strftime('%m'))
    currentMonth = str( yesterday.strftime('%m') )
    currentDay = str( yesterday.strftime('%d') )
    return( currentYear + '-' + currentMonth + '-' + currentDay )


def getCurrentTime():
    today = datetime.datetime.today()

    currentHour=today.strftime('%H')
    currentMinutes=today.strftime('%M')
    currentSeconds=today.strftime('%S')
    return( currentHour + '-' + currentMinutes + '-' + currentSeconds )


def getDateAndTimeFull():
    #currentDateAndTimeFull=currentDateFull+'-'+currentTimeFull
    return getYearMonthAndDay() + '.' + getCurrentTime()

#if (verbose == True) or (debug == True):
#    print(currentDateAndTimeFull.encode(consoleEncoding))


# Returns True if internet is available. Returns false otherwise.
def checkIfInternetIsAvailable():
    try:
        myRequest = socket.getaddrinfo('lumen.com',443)
        return True
    except:
        return False


def importDictionaryFromFile( myFile, encoding=None ):
    if checkIfThisFileExists(myFile) != True:
        return None
    #else it exists, so find the extension and call the appropriate import function for that fileType
    myFileNameOnly, myFileExtensionOnly = os.path.splitext(myFile)
    if myFileExtensionOnly == None:
        return None
    if myFileExtensionOnly == '':
        return None
    elif myFileExtensionOnly == '.csv':
        return importDictionaryFromCSV( myFile, encoding, ignoreWhitespace=False)
    elif myFileExtensionOnly == '.xlsx':
        return importDictionaryFromXLSX( myFile,encoding )
    elif myFileExtensionOnly == '.xls':
        return importDictionaryFromXLS( myFile, encoding )
    elif myFileExtensionOnly == '.ods':
        return importDictionaryFromODS( myFile, encoding )
    else:
        print( ('Warning: Unrecognized extension for file: '+str(myFile)).encode(consoleEncoding) )
        return None


#Even if importing to dictionary from .csv/.xlsx/.xls/.ods to a dictionary instead of an openpyxl data structure, the rule is that the first entry is headers, so the first key=value entry must be skipped regardless.
def importDictionaryFromCSV( myFile, myFileEncoding, ignoreWhitespace=False ):
    tempDict={}

    #'with' is correct. Do not use 'while'.
    with open(myFile, 'rt', newline='', encoding=myFileEncoding, errors=inputErrorHandling) as myFileHandle:
        csvReader = csv.reader(myFileHandle)
        currentLine=0
        for line in csvReader:
            #skip first line
            if currentLine == 0:
                currentLine+=1
            elif currentLine != 0:
                if ignoreWhitespace == True:
                    for i in range(len(line)):
                        line[i]=line[i].strip()
                if line[1] == '':
                    line[1] = None
                elif line[1].lower() == 'true':
                    line[1] = True
                elif line[1].lower() == 'false':
                    line[1] = False
                tempDict[line[0]]=line[1]

    # if the contents of item are '' or 'none', then change to None
    for key,item in tempDict.items():
        if item != None:
            if ( item == '' ) or ( item.lower() == 'none' ):
                tempDict[key]=None

    return tempDict


def importDictionaryFromXLSX(myFile, myFileEncoding):
    print('Hello World'.encode(consoleEncoding))
    workbook = openpyxl.load_workbook(filename=myFile) #, data_only=)
    spreadsheet=workbook.active
    # TODO: Put stuff here.


def importDictionaryFromXLS(myFile, myFileEncoding):
    print('Hello World'.encode(consoleEncoding))


def importDictionaryFromODS(myFile, myFileEncoding):
    print('Hello World'.encode(consoleEncoding))


