#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Concept art:
import resources.py3Any2Spreadsheet
chocolateStrawberry = resources.py3Any2Spreadsheet('resources\py3Any2Spreadsheet\resources\ks.kag3.kirikiri.parsingTemplate.py')

The above line should work. The idea is for py3Any2Spreadsheet to act as a proxy to call upon various types of parsing scripts but always return a chocolate strawberry.
If imported as a library, then it should just act as a proxy for the parsing script.
But if called directly as 'python py3Any2Spreadsheet.py --file input', then it should output .csv and .xlsx files instead.

# Update: This should probably be moved to an external program that is dedicated to parsing input and supports conversion to .xlsx or .csv. Update: Moved.

# That seperate program should probably support something like: https://github.com/Distributive-Network/PythonMonkey
# For cross language support of parsing files. Then again, Python is very easy to use.

TODO: Alternatively, create a lot of Python specific parse files or engines that can do .srt, .epub, .ass, and so forth to and from spreadsheet formats.
Is it even possible to parse XML and HTML without knowing the structure in advance? Well, web browsers do it, right? So it should be possible. Just blacklist everything in headers, all script tags, and keep track of the current cursor position or run the files through a normalizer first so each entry is on its own line to make it easier to parse.

Copyright (c) 2024 gdiaz384 ; License: GNU Affero GPL v3. https://www.gnu.org/licenses/agpl-3.0.html
"""
__version__='2024.06.06 alpha'


# Set defaults.
verbose=False
debug=False

consoleEncoding='utf-8'
defaultTextFileEncoding='utf-8'                     # Settings that should not be left as a default setting should have default prepended to them.
defaultTextEncodingForKSFiles='shift-jis'   # UCS2 BOM LE (aka UTF-16 LE) might also work. Need to test.

supportedExtensions=[ '.csv' , '.xlsx' , '.xls' , '.ods' ]
defaultSpreadsheetExtension='.xlsx'
defaultOutputColumn=4
parseSettingsExtension='.ini'
tempParseScriptPathAndName='scratchpad/temp.py'   # This is associated with a hardcoded import statment to as scratchpad\temp.py It is not possible to make this dynamic without importing an additional library.

inputErrorHandling='strict'
#outputErrorHandling='namereplace'        #This is set dynamically below.

metadataDelimiter='_'
linesThatBeginWithThisAreComments='#'
assignmentOperatorInSettingsFile='='
ignoreWhitespaceForCSVFiles=False

unspecifiedError='Unspecified error in py3Any2Spreadsheet.py.'
usageHelp=' Usage: python py3Any2Spreadsheet.py --help  Example: py3Any2Spreadsheet input myInputFile.ks parsingProgram.py --rawFileEncoding shift-jis'


# import stuff.
import argparse                                                 # For command line options.
import sys                                                           # For sys.exit() and add library locations dynamically with sys.path.append().
import os                                                            # Check if files and folders exist.
import pathlib                                                     # Sane path handling.
import csv                                                           # Used to read character dictionary.
import shutil                                                        # Supports high-level copy operations. Used to copy script file to scratchpad temporary directory for importing.
import resources.chocolate as chocolate       # Main wrapper for openpyxl library. Used as core data structure.
import resources.dealWithEncoding as dealWithEncoding # Handles text encoding and implements optional chardet library.

#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
sysVersion=int(sys.version_info[1])
if sysVersion >= 5:
    outputErrorHandling='namereplace'
elif sysVersion < 5:
    outputErrorHandling='backslashreplace'    
else:
    sys.exit( unspecifiedError.encode(consoleEncoding) )


def createCommandLineOptions():
    commandLineParser=argparse.ArgumentParser(description='Description: Turns text files into spreadsheets using user-defined scripts. If mode is set to input, then parsingProgram.input() will be called. If mode is set to output, then parsingProgram.output() will be called.' + usageHelp)
    commandLineParser.add_argument('mode', help='Must be input or output.', type=str)

    commandLineParser.add_argument('rawFile', help='Specify the text file to parse.', type=str)
    commandLineParser.add_argument('-e','--rawFileEncoding', help='Specify the encoding of the rawFile.', default=None, type=str)

    commandLineParser.add_argument('parsingProgram', help='Specify the .py script that will be used to parse rawFile.', type=str)
    commandLineParser.add_argument('-pse', '--parsingScriptEncoding', help='Specify the encoding of the parsingProgram.', default=None,type=str)

    commandLineParser.add_argument('-psf','--parseSettingsFile', help='Optional .ini or .txt file to read settings file to convert to a settings dictionary.', default=None,type=str)
    commandLineParser.add_argument('-psfe','--parseSettingsFileEncoding', help='Specify the encoding of parseSettingsFile.', default=None, type=str)

    commandLineParser.add_argument('-s','--spreadsheet', help='Specify the spreadsheet file to use. For mode=input, this is the file name that will contain the extracted strings. For mode=output, this is used to insert translated entries back into the original file. Must be .csv .xlsx .xls .ods', default=None, type=str)
    commandLineParser.add_argument('-se','--spreadsheetEncoding', help='Only valid for .csv files. Specify the encoding of the spreadsheet file.', default=None, type=str)

    commandLineParser.add_argument('-cn','--characterNamesDictionary', help='Optional character dictionary containing the names of the characters. Using aliases is likely better than the actual translated names because entries will be reverted during translation.', default=None, type=str)
    commandLineParser.add_argument('-cne','--characterNamesDictionaryEncoding', help='Specify the encoding of the character dictionary file.', default=None, type=str)

    commandLineParser.add_argument('-trf','--translatedRawFile', help='Specify the output file name and path for the translatedRawFile. Only valid for mode=output.', default=None, type=str)
    commandLineParser.add_argument('-trfe','--translatedRawFileEncoding', help='Specify the encoding of translatedRawFile.', default=None, type=str)

    commandLineParser.add_argument('-c', '--columnToUseForReplacements', help='Specify the column in the spreadsheet to use for replacements. Can be an integer starting with 1 or the name of the column header. Case sensitive. Only valid for mode=output.', default=None, type=str) # This lacks a type= declaration. Is that needed? #Update: If no type declaration is used, then str is assumed. Just make it explicit then.

    commandLineParser.add_argument('-t', '--testRun', help='Parse stuff, but do not write any output files.', action='store_true')
    commandLineParser.add_argument('-vb', '--verbose', help='Print more information.', action='store_true')
    commandLineParser.add_argument('-d', '--debug', help='Print too much information.', action='store_true')
    commandLineParser.add_argument('-v', '--version', help='Print version information and exit.', action='store_true')    

    commandLineArguments=commandLineParser.parse_args()

    if commandLineArguments.version == True:
        print( __version__.encode(consoleEncoding) )
        sys.exit(0)

    userInput={}
    userInput[ 'mode' ] = commandLineArguments.mode

    userInput[ 'rawFileName' ] = commandLineArguments.rawFile
    userInput[ 'rawFileEncoding' ] = commandLineArguments.rawFileEncoding

    userInput[ 'parsingProgram' ] = commandLineArguments.parsingProgram
    userInput[ 'parsingScriptEncoding' ] = commandLineArguments.parsingScriptEncoding # This should always be utf-8. Can Python even execute non-utf-8 and non-ascii?

    userInput[ 'parseSettingsFile' ] = commandLineArguments.parseSettingsFile
    userInput[ 'parseSettingsFileEncoding' ] = commandLineArguments.parseSettingsFileEncoding

    userInput[ 'spreadsheetFileName' ] = commandLineArguments.spreadsheet
    userInput[ 'spreadsheetFileEncoding' ] = commandLineArguments.spreadsheetEncoding

    userInput[ 'characterDictionaryFileName' ] = commandLineArguments.characterNamesDictionary
    userInput[ 'characterDictionaryEncoding' ] = commandLineArguments.characterNamesDictionaryEncoding

    userInput[ 'translatedRawFileName' ] = commandLineArguments.translatedRawFile
    userInput[ 'translatedRawFileEncoding' ] = commandLineArguments.translatedRawFileEncoding

    userInput[ 'columnToUseForReplacements' ] = commandLineArguments.columnToUseForReplacements

    userInput[ 'testRun' ] = commandLineArguments.testRun
    userInput[ 'verbose' ] = commandLineArguments.verbose
    userInput[ 'debug' ] = commandLineArguments.debug

    return userInput


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

def checkIfThisFileExists(myFile):
    if (myFile == None) or (os.path.isfile(str(myFile)) != True):
        return False
    return True

def checkIfThisFolderExists(myFolder):
    if (myFolder == None) or (os.path.isdir(str(myFolder)) != True):
        return False
    return True


#This function reads program settings from text files using a predetermined list of rules.
#The text file uses the syntax: setting=value, # are comments, empty/whitespace lines ignored.
#This function builds a dictionary and then returns it to the caller.
def readSettingsFromTextFile(fileNameWithPath, fileNameEncoding):

    #Has already been verified to not be None.
    #if fileNameWithPath == None:
    #    print( ('Cannot read settings from None entry: '+ str(fileNameWithPath) ).encode(consoleEncoding) )
    #    return None

    #Has already been verified to exist.
    #if checkIfThisFileExists(fileNameWithPath) != True:
    #    return None

    #Newer, simplier syntax.
    #open() works with both \ and / to traverse folders.
    with open( fileNameWithPath, 'r', encoding=fileNameEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read()

    if ( not isinstance(inputFileContents, str) ) or ( inputFileContents == '' ):
        print( ( 'Error: Unable to read from file: ' + fileNameWithPath ).encode(consoleEncoding) )
        return None

    #Okay, so the file was specified, it exists, and it was read from successfully. The contents are in inputFileContents.
    #Now turn inputFileContents into a dictionary.
    tempDictionary={}
    # Update: This is very old code. A simpler way to read plaintext files is to do fileContentsAsAListofStrings = myFileHandle.read().splitlines() and then just interate over the list where each entry in the list is a string that represents a different line.
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
                print( ('Warning: Error reading key\'s value \''  + key + '\' in file: ' + str(fileNameWithPath) + ' Using None as fallback.').encode(consoleEncoding) )
                value = None
            elif value.lower() == 'none':
                value = None
            elif key.lower() == 'ignorelinesthatstartwith':#ignoreLinesThatStartWith
                # Then every item that is not blank space is a valid list value.
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


# This returns either None or a dictionary of the contents of parsingProgram.ini.
def getParseSettingsDictionary(parsingProgram,parseSettingsFile=None,parseSettingsFileEncoding=defaultTextFileEncoding):
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

    parseSettingsDictionary = readSettingsFromTextFile( parseSettingsFile, parseSettingsFileEncoding)

    if debug==True:
        print( ( 'parseSettingsDictionary=' + str(parseSettingsDictionary) ).encode(consoleEncoding) )

    return parseSettingsDictionary


# This should also read in all of the input files.
def validateUserInput(userInput):
    global verbose
    verbose=userInput[ 'verbose' ]
    global debug
    debug=userInput[ 'debug' ]

    # TODO: Update debug setting in all imported libraries, chocolate, dealWithEncoding, and the parsingProgram.
    # The first two are doable but the parsingProgram does not get imported here. Should it be?

    if userInput[ 'mode' ].lower() == 'input':
        userInput[ 'mode' ] = 'input'
    elif userInput[ 'mode' ].lower() == 'in':
        userInput[ 'mode' ] = 'input'
    elif userInput[ 'mode' ].lower() == 'output':
        userInput[ 'mode' ] = 'output'
    elif userInput[ 'mode' ].lower() == 'out':
        userInput[ 'mode' ] = 'output'
    else:
        print( ('Error: Mode must be input or output. Mode=' + userInput['mode']).encode(consoleEncoding) )
        sys.exit(1)

    verifyThisFileExists( userInput[ 'rawFileName' ] )
    verifyThisFileExists( userInput[ 'parsingProgram' ] )

    if userInput[ 'parseSettingsFile' ] != None:
        if checkIfThisFileExists( userInput[ 'parseSettingsFile' ] ) == True:
            pass
        else:
            print( 'Warning: The following parseSettingsFile was specified but does not exist:' )
            print( ( userInput[ 'parseSettingsFile' ] ).encode(consoleEncoding) )
            userInput[ 'parseSettingsFile' ]=None

    if userInput[ 'mode' ] == 'input':
        if userInput[ 'spreadsheetFileName' ] == None:
            print( 'Info: Spreadsheet file was not specified. Will create as: '+ defaultSpreadsheetExtension )
            userInput[ 'spreadsheetFileName' ] = userInput['rawFileName'] + defaultSpreadsheetExtension
            userInput[ 'spreadsheetExtension'] = defaultSpreadsheetExtension
        #if userInput[ 'spreadsheetFileName' ] != None:
        else:
            userInput[ 'spreadsheetExtension'] = pathlib.Path( userInput[ 'spreadsheetFileName' ] ).suffix

        if checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) == True:
            # Rename to .backup because it will be replaced.
            pathlib.Path( userInput[ 'spreadsheetFileName' ] ).replace( userInput[ 'spreadsheetFileName' ] + '.backup' )
            print ( ('Info: '+ userInput[ 'spreadsheetFileName' ] + ' moved to ' + userInput[ 'spreadsheetFileName' ] + '.backup').encode(consoleEncoding) )
        #elif checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) != True:
        #else:
        #    Update: Then user specified an output file that does not exist yet. That makes sense. All is well.

        #    However, still need to verify the extension is correct: .csv .xlsx .xls .ods
            # It is not entirely correct to call this userInput, but whatever.
        if userInput[ 'spreadsheetExtension'] in supportedExtensions:
            pass
        else:
            print( ('Error: Unsupported extension for spreadsheet: \'' + userInput[ 'spreadsheetExtension' ] + '\'' ).encode(consoleEncoding) )
            print( 'Supported extensions: ' + str(supportedExtensions) )
            sys.exit(1)

    #elif userInput[ 'mode' ] == 'output':
    else:
        if userInput[ 'spreadsheetFileName' ] == None:
            print( 'Error: Please specify a valid spreadsheet from which to read translations.' )
            sys.exit(1)

        if checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) != True:
            print( 'Error: The following spreadsheet file was specified but does not exist:' )
            print( ( userInput[ 'spreadsheetFileName' ] ).encode(consoleEncoding) )
            sys.exit(1)            
#        elif checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) == True:
#        else:
                # Then user specified an input file, and it exists. All is well. Do nothing here.
#                pass

        if userInput[ 'translatedRawFileName' ] == None:
            # Then the user did not specify an output file.
            # What would be sane behavior here?

            # maybe just append translated.extension?
            userInput[ 'translatedRawFileName' ] = userInput[ 'rawFileName' ] + '.translated' + pathlib.Path( userInput[ 'rawFileName'] ).suffix
            print( 'Warning: No output file name was specified for the translated file. Using:')
            print( userInput[ 'translatedRawFileName'].encode(consoleEncoding) )

    # This is about to be used, so map it now.
    if userInput[ 'characterDictionaryEncoding' ] == None:
        userInput[ 'characterDictionaryEncoding' ] = defaultTextFileEncoding

    if userInput[ 'characterDictionaryFileName' ] != None:
        if checkIfThisFileExists( userInput[ 'characterDictionaryFileName' ] ) == True:
            # Read in characterDictionary.csv
            tempDict={}
            tempKey=''
            tempValue=''
            index=0
            # 'with' is correct. Do not use 'while'.
            with open(userInput[ 'characterDictionaryFileName' ], 'r', newline='', encoding=userInput[ 'characterDictionaryEncoding' ], errors=inputErrorHandling) as myFileHandle:
                csvReader = csv.reader(myFileHandle)
                currentLine=0
                for line in csvReader:
                    # Skip first line.
                    if currentLine == 0:
                        currentLine+=1
                    elif currentLine != 0:
                        if ignoreWhitespaceForCSVFiles == True:
                            for i in range(len(line)):
                                line[i]=line[i].strip()
                        if line[1] == '':
                            line[1] = None
                        tempDict[line[0]]=line[1]
            userInput[ 'characterDictionary' ]=tempDict

            if debug == True:
                print( ( 'userInput[characterDictionary]=' + str( userInput[ 'characterDictionary' ] ) ).encode(consoleEncoding) )

        #elif checkIfThisFileExists( userInput[ 'characterDictionaryFileName' ] ) != True:
        else:
            print( 'Warning: characterDictionary file was specified but does not exist:' )
            print( ( userInput[ 'characterDictionaryFileName' ] ).encode(consoleEncoding) )
            userInput[ 'characterDictionaryFileName' ] = None
            userInput[ 'characterDictionary' ] = None

    #elif userInput[ 'characterDictionaryFileName' ] == None
    else:
        userInput[ 'characterDictionary' ] = None

    # This cannot be fully validated, checked to see if it exists, because the spreadsheet needs to be parsed first. So far, only the file name has been validated, so only setting a default value can be done at this point.
    if userInput[ 'columnToUseForReplacements' ] == None:
        userInput[ 'columnToUseForReplacements' ] = defaultOutputColumn
        userInput[ 'outputColumnIsDefault' ]=True
    else:
        userInput[ 'outputColumnIsDefault' ]=False

    if userInput[ 'debug' ] == True:
        userInput[ 'verbose' ] = True
        for key, value in userInput.items():
            print( str(key) + '=' + str(value) )

    # Handle encoding options here.
    # TODO: update with dealWithEncoding.ofThisFile() logic for chardet library implementation.
    if userInput[ 'rawFileEncoding' ] == None:
        # Update rawFileEncoding for kirikiri .ks files to different default.
        if pathlib.Path( userInput[ 'rawFileName'] ).suffix == '.ks':
            userInput[ 'rawFileEncoding' ] = defaultTextEncodingForKSFiles
        else:
            userInput[ 'rawFileEncoding' ] = defaultTextFileEncoding
        print( ('Warning: rawFileEncoding was not specified. Setting to \'' + userInput[ 'rawFileEncoding' ] +'\' This is probably incorrect.' ).encode(consoleEncoding) )

    if userInput[ 'parseSettingsFileEncoding' ] == None:
        userInput[ 'parseSettingsFileEncoding' ] = defaultTextFileEncoding

    if userInput[ 'spreadsheetFileEncoding' ] == None:
        userInput[ 'spreadsheetFileEncoding' ] = defaultTextFileEncoding

    if userInput[ 'translatedRawFileEncoding' ] == None:
        userInput[ 'translatedRawFileEncoding' ] = userInput[ 'rawFileEncoding' ]

    if debug == True:
        print( 'userInput[characterDictionary]=' + str( userInput[ 'characterDictionary' ] ) )

    return userInput


# This should probably be moved into main() for simplicity's sake. Having an extra function passing around so many paramaters just makes things more confusing and only being invoked once instead of reused sort-of implies that it is part of the same logic anyway.
def parseRawFile(
            rawFileNameAndPath,
            parsingProgram,
            rawFileEncoding=defaultTextFileEncoding,
            parsingScriptEncoding=defaultTextFileEncoding,
            parseSettingsFile=None,
            parseSettingsFileEncoding=defaultTextFileEncoding,
            characterDictionary=None
            ):

    # parsingProgram='templates\KAG3.py'

    # import parsingProgram  # With fancier import syntax where the parent directory is added to sys.path first:
    #parsingScriptObject=pathlib.Path(parsingProgram).absolute() #According to the docs, this should not work, but it does. There is no absolute() method.

    # This takes the parsingProgram.py, gets the absolute path, adds the parent directory to sys.path so Python can import it, fixes the name to not contain reserved characters, and then imports it as a temporary file.
    parsingScriptObject=pathlib.Path(parsingProgram).resolve()
    # sys.path.append(str(parsingScriptObject.parent))
    # importlib.import_module(parsingScriptObject.stem)

    # Alternative, more flexible method.
    # Algorithm: Create scratchpad directory, copy target script to scratchpad directory, import as: import scratchpad.temp as customParser
    # This is ideal because: 
    # 1. Weird file system names that are not valid module names are then no longer an issue,
    # 2. Trying to resolve paths and importing above parent directory from __main__ is no longer an issue,
    # 3. The importlib library to handle special import handling is no longer necessary. However, shutil.copy becomes necessary to copy the code. The alternative to shutil is platform specific code with the os module, or opening the file and copying the contents manually.
    # 4. scratchpad is already labeled as a temporary directory in git.
    global tempParseScriptPathAndName
    tempParseScriptPathAndName = str( pathlib.Path(__file__).resolve().parent ) + '/' + tempParseScriptPathAndName
    #print( 'tempParseScriptPathAndName=' + tempParseScriptPathAndName)

    pathlib.Path( tempParseScriptPathAndName ).resolve().parent.mkdir( parents = True, exist_ok = True )

    if debug == True:
        print( 'copyFrom=' + str(parsingScriptObject) )
        print( 'copyTo=' + str( pathlib.Path(tempParseScriptPathAndName).resolve()) )

    # TODO: before copying, if the target exists, then read both files and compare their hash. Do not copy if their hashes match.
    # import hashlib

    # Minor issue still: No way to avoid hardcoding this unless using the importlib module.
    #shutil.copy( str(parsingScriptObject) , str( pathlib.Path(tempParseScriptPathAndName).resolve() ) )
    shutil.copy( str(parsingScriptObject) , tempParseScriptPathAndName )
    sys.path.append( str( pathlib.Path(__file__).resolve().parent) )
    import scratchpad.temp as customParser # Hardcoded to import as scratchpad\temp.py
    # importlib.import_module( tempParseScriptPathAndName) #This still requires fixing the \\ and / in the path.

    # Now that customParser exists, the internal variable names can be updated.

    #customParser='resources.' + parsingScriptObject.name
    #import customParser
    #import resources.templates.KAG3 as customParser
    #import parsingProgram
    #from 'resources.' + customParser import input
#    print('parsingScriptObject=' + str(parsingScriptObject))
#    print('parsingScriptObject.name=' + parsingScriptObject.name)

    #fixedName=str(parsingScriptObject).replace('\\','.')
    #print( 'fixedName=' + fixedName )
    #customParser = importlib.import_module(fixedName)

#    currentScriptPathObject=pathlib.Path('.').absolute()
#    print( 'currentScriptPathObject=' + str(currentScriptPathObject) )

#    relativePath=parsingScriptObject.relative_to(currentScriptPathObject)
#    print( 'relativePath=' + str(relativePath) )
#    print( 'relativePath.exists()=' + str(relativePath.exists()) )

#    fixedRelativePath=str(relativePath).replace('\\','.').replace('/','.')
#    print( 'fixedRelativePath=' + fixedRelativePath)

    #print( 'customParser.__version__=' + str(customParser.__version__) )
    #print(str(dir(customParser) ))

    parseSettingsDictionary=getParseSettingsDictionary(parsingProgram, parseSettingsFile=parseSettingsFile, parseSettingsFileEncoding=parseSettingsFileEncoding)

    settings={}
    settings[ 'fileEncoding' ]=rawFileEncoding
    settings[ 'parseSettingsDictionary' ] = parseSettingsDictionary

    mySpreadsheet=None
#    if parseSettingsDictionary != None:
        # Usage: customParser.input('A01.ks', ...)
                                                #def input( fileNameWithPath, parseSettingsDictionary, fileEncoding=defaultTextEncoding, characterDictionary=None):
        # This could be updated to put fileEncoding into a settings {} dictionary, but like... why? There needs to be more variables handed in for it to be worth it. What more variables should be handed in? #Update: Just dump it in there in order to present a uniform API for user experience reasons.
#        mySpreadsheet = customParser.input(rawFileNameAndPath, parseSettingsDictionary, fileEncoding=rawFileEncoding, characterDictionary=characterDictionary)
    #elif parseSettingsDictionary == None:
#    else:
        # This syntax assumes there is no parseSettings.ini since that is defined within the file. If parseSettings.ini is required, then this syntax will fail.
#        mySpreadsheet = customParser.input(rawFileNameAndPath, parseSettingsDictionary, fileEncoding=rawFileEncoding, characterDictionary=characterDictionary)
    # New API.
    mySpreadsheet=customParser.input( rawFileNameAndPath, characterDictionary=characterDictionary, settings=settings )

    if (debug == True) and (mySpreadsheet != None):
        mySpreadsheet.printAllTheThings()
    return mySpreadsheet


# This takes the translated spreadsheet and returns a string that represents the translated version of file rawFileName.
# This should probably be moved into main() for simplicity's sake. Having an extra function passing around so many paramaters just makes things more confusing and only being invoked once instead of reused sort-of implies that it is part of the same logic anyway.
def insertTranslatedText(
            rawFileName,
            spreadsheetFileName,
            parsingProgram,
            rawFileEncoding=defaultTextFileEncoding,
            spreadsheetFileEncoding=defaultTextFileEncoding,
            parsingScriptEncoding=defaultTextFileEncoding,
            parseSettingsFile=None, 
            parseSettingsFileEncoding=defaultTextFileEncoding,
            characterDictionary=None,
            outputColumn=defaultOutputColumn,
            outputColumnIsDefault=None
            ):

    global tempParseScriptPathAndName

    #print( 'tempParseScriptPathAndName=' + tempParseScriptPathAndName)
    tempParseScriptPathAndName = str( pathlib.Path( __file__ ).resolve().parent ) + '/' + tempParseScriptPathAndName
    #print( 'tempParseScriptPathAndName=' + tempParseScriptPathAndName)

    pathlib.Path( tempParseScriptPathAndName ).resolve().parent.mkdir( parents = True, exist_ok = True )

    parsingProgramObject=pathlib.Path(parsingProgram).resolve()
    shutil.copy( str(parsingProgramObject) , tempParseScriptPathAndName )
    sys.path.append( str( pathlib.Path( __file__ ).resolve().parent) )
    import scratchpad.temp as customParser # Hardcoded to import as scratchpad\temp.py

    # Need to pass in rawFileName as-is.
    # Need to pass parsingProgram as-is.
    # Need to convert spreadsheet to a chocolate.Strawberry(), using rawFileEncoding
    # Need to convert parseSettingsFile to parseSettingsDictionary using parseSettingsFileEncoding
    # Support direct passthrough for characterDictionary

    mySpreadsheet=chocolate.Strawberry( myFileName=spreadsheetFileName, fileEncoding=spreadsheetFileEncoding)

    parseSettingsDictionary=getParseSettingsDictionary( parsingProgram, parseSettingsFile=parseSettingsFile, parseSettingsFileEncoding=parseSettingsFileEncoding )

    # Dump everything into a 'settings' dictionary so the API does not have to change as often.
    settingsDictionary={}
    settingsDictionary[ 'fileEncoding' ]=rawFileEncoding
    settingsDictionary[ 'parseSettingsDictionary'] = parseSettingsDictionary
    #settingsDictionary[ 'characterDictionary'] = characterDictionary # This should be passed directly.
    settingsDictionary[ 'outputColumn' ] = outputColumn
    #settingsDictionary[ 'outputColumnIsDefault' ] = userInput[ 'outputColumnIsDefault' ]
    #Workaround
    if outputColumnIsDefault != None:
        settingsDictionary[ 'outputColumnIsDefault' ]=outputColumnIsDefault

    #def output(fileNameWithPath, mySpreadsheet, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, characterDictionary=None):
#    myString=customParser.output(
#            rawFileName,
#            mySpreadsheet=mySpreadsheet,
#            parseSettingsDictionary=parseSettingsDictionary,
#            fileEncoding=rawFileEncoding,
#            characterDictionary=characterDictionary
#            )

    #def output( fileNameWithPath, mySpreadsheet, characterDictionary=None, settings={} ): # mySpreadsheet is a chocolate Strawberry.
    myString=customParser.output(
            rawFileName,
            mySpreadsheet=mySpreadsheet,
            characterDictionary=characterDictionary,
            settings=settingsDictionary
            )

    #if debug == True:
    #print( myString.encode(consoleEncoding) )

    return myString


def main():

    # Define command line options.
    # userInput is a dictionary.
    userInput = createCommandLineOptions()

    # Verify input.
    userInput = validateUserInput( userInput ) # This should also read in all of the input files except for the parseScript.py.

    if debug==True:
        print( ( 'userInput=' + str(userInput) ).encode(consoleEncoding) )

    if userInput['mode'] == 'input':
        #parseInput()
        #parser.importFromTextFile('A01.ks',)
        #def parse(rawFileNameAndPath, parsingProgram, rawFileEncoding=defaultTextFileEncoding, parseSettingsFile=None, parseSettingsFileEncoding=defaultTextFileEncoding, characterDictionary=None):
        mySpreadsheet=parseRawFile(
                userInput['rawFileName'], 
                userInput['parsingProgram'], 
                rawFileEncoding=userInput['rawFileEncoding'],
                parsingScriptEncoding=userInput['parsingScriptEncoding'],
                parseSettingsFile=userInput[ 'parseSettingsFile' ],
                parseSettingsFileEncoding=userInput[ 'parseSettingsFileEncoding' ],
                characterDictionary=userInput[ 'characterDictionary' ]
        )

        if mySpreadsheet == None:
            print('Empty file.')
            sys.exit(1)
        else:
            assert( isinstance( mySpreadsheet, chocolate.Strawberry )  )

        # Export to .xlsx
        #outputPathObject=pathlib.Path( userInput[ 'spreadsheetFileName' ] )
        #outputPathObject.extension # This does not work. What an odd design choice.

        if userInput[ 'testRun' ] != True:
            # Writing operations are always scary, so mySpreadsheet.export() should always print when it is writing output internally. No need to do it again here.
            mySpreadsheet.export( userInput[ 'spreadsheetFileName' ], fileEncoding=userInput[ 'spreadsheetFileEncoding' ] )


    elif userInput[ 'mode' ] == 'output':
        # parseOutput()
        #parser.output('A01.ks',)
        translatedTextFile=insertTranslatedText(
                userInput['rawFileName'],
                userInput['spreadsheetFileName'], 
                userInput['parsingProgram'],
                rawFileEncoding=userInput['rawFileEncoding'],
                spreadsheetFileEncoding=userInput['spreadsheetFileEncoding'], 
                parsingScriptEncoding=userInput['parsingScriptEncoding'],
                parseSettingsFile=userInput[ 'parseSettingsFile' ],
                parseSettingsFileEncoding=userInput[ 'parseSettingsFileEncoding' ],
                characterDictionary=userInput[ 'characterDictionary' ],
                outputColumn=userInput[ 'columnToUseForReplacements' ],
                outputColumnIsDefault=userInput[ 'outputColumnIsDefault' ]
        )

        if debug == True:
            print( ( 'translatedTextFile=' + str(translatedTextFile) ).encode(consoleEncoding) )

        if userInput[ 'testRun' ] == True:
            return

        if isinstance( translatedTextFile, chocolate.Strawberry) == True:
            translatedTextFile.export( userInput[ 'translatedRawFileName' ], fileEncoding=userInput[ 'translatedRawFileEncoding' ] )
        elif isinstance( translatedTextFile, str ) == True:
            #userInput exists
            with open( userInput[ 'translatedRawFileName' ], 'w', encoding=userInput[ 'translatedRawFileEncoding' ], errors=outputErrorHandling ) as myFileHandle:
                myFileHandle.write(translatedTextFile)
        elif isinstance( translatedTextFile, list ) == True:
            with open( userInput[ 'translatedRawFileName' ], 'w', encoding=userInput[ 'translatedRawFileEncoding' ], errors=outputErrorHandling ) as myFileHandle:
                for entry in translatedTextFile:
                    # This might corrupt the output on Linux/Unix or vica-versa on Windows if the software is expecting and requires a specific type of newline \r\n or \n.
                    # By default, Python will translate \n based upon the host OS, not what the software that will actually read the file is expecting because it cannot possibly know that, therefore this is a potential source of corruption.
                    # A sane way of handling this is to maybe determine the line ending of the original file and use that line ending schema here. How are line endings determined? Huristics? How does Python determine line endings correctly when the platform does not match the source file?
                    myFileHandle.write(entry + '\n')
        elif translatedTextFile == None:
            print('Empty file.')
        else:
            print( 'Error: Unknown type of return value from parsing script. Must be a chocolate.Strawberry() or string.')
            print( 'type=' +  str( type(translatedTextFile) ) )

        # chocolate.Strawberry() will print out its own confirmation of writing out the file on its own, so do not duplicate that message here.
        if ( checkIfThisFileExists( userInput[ 'translatedRawFileName' ] ) == True ) and ( isinstance( translatedTextFile, chocolate.Strawberry ) == False ):
            print( ('Wrote: '+ userInput[ 'translatedRawFileName' ]).encode(consoleEncoding) )


if __name__ == '__main__':
    main()
    sys.exit(0)

