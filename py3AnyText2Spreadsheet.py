#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Concept art:
import resources.py3Any2Spreadsheet
chocolateStrawberry = resources.py3Any2Spreadsheet('resources\py3Any2Spreadsheet\resources\KAG3.PrincessBritania.py')

The above line should work. The idea is for py3Any2Spreadsheet to act as a proxy to call upon various types of parsing scripts but always return a chocolate strawberry.
If imported as a library, then it should just act as a proxy for the parsing script.
But if called directly as 'python py3Any2Spreadsheet.py --file input', then it should output .csv and .xlsx files instead.

# Update: This should probably be moved to an external program that is dedicated to parsing input and supports conversion to .xlsx or .csv. Update: Moved.

# That seperate program should probably support something like: https://github.com/Distributive-Network/PythonMonkey
# For cross language support of parsing files. Then again, Python is very easy to use.

Credit: gdiaz384
License: APGLv3 
"""
__version__='2024Feb29'


# Set defaults.
verbose=False
debug=False

consoleEncoding='utf-8'
defaultTextFileEncoding='utf-8'                     # Settings that should not be left as a default setting should have default prepended to them.
defaultTextEncodingForKSFiles='shift-jis'

supportedExtensions=[ '.csv' , '.xlsx' , '.xls' , '.ods' ]
defaultSpreadsheetExtension='.xlsx'
parseSettingsExtension='.ini'
tempParseScriptPathAndName='scratchpad/temp.py'

inputErrorHandling='strict'
#outputErrorHandling='namereplace'        #This is set dynamically below.

metadataDelimiter='_'
linesThatBeginWithThisAreComments='#'
assignmentOperatorInSettingsFile='='
ignoreWhitespace=False

unspecifiedError='Unspecified error in py3Any2Spreadsheet.py.'
usageHelp=' Usage: python py3Any2Spreadsheet.py --help  Example: py3Any2Spreadsheet input myInputFile.ks parsingScript.py --rawFileEncoding shift-jis'


# import stuff.
import argparse                                                 # For command line options. Import conditionally later.
import sys                                                           # For sys.exit()
import os                                                            # Check if file exists.
import pathlib                                                     # Sane path handling.
import resources.chocolate as chocolate       # Main wrapper for openpyxl library.
import csv                                                           # Used to read character dictionary.
import shutil                                                        # Supports high-level copy operations. Used to copy script file to scratchpad temporary directory for importing.


#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
sysVersion=int(sys.version_info[1])
if sysVersion >= 5:
    outputErrorHandling='namereplace'
elif sysVersion < 5:
    outputErrorHandling='backslashreplace'    
else:
    sys.exit( unspecifiedError.encode(consoleEncoding) )


def createCommandLineOptions():
    # Add command line options.
    commandLineParser=argparse.ArgumentParser(description='Description: Turns text files into spreadsheets using user-defined scripts. If mode is set to input, then parsingScript.input() will be called. If mode is set to output, then parsingScript.output() will be called.' + usageHelp)
    commandLineParser.add_argument('mode', help='Must be input or output.', type=str)

    commandLineParser.add_argument('rawFile', help='Specify the text file to parse.', type=str)
    commandLineParser.add_argument('-e','--rawFileEncoding', help='Specify the encoding of the rawFile.', default=None, type=str)

    commandLineParser.add_argument('parsingScript', help='Specify the .py script that will be used to parse rawFile.', type=str)
    commandLineParser.add_argument('-', '--parsingScriptEncoding', help='Specify the encoding of the parsingScript.', default=None,type=str)

    commandLineParser.add_argument('--parseSettingsFile', help='Optional .ini or .txt file to read settings file to convert to a settings dictionary.', default=None,type=str)
    commandLineParser.add_argument('-pfe','--parseSettingsFileEncoding', help='Specify the encoding of parseSettingsFile.', default=None, type=str)

    commandLineParser.add_argument('-s','--spreadsheet', help='Specify the spreadsheet file to use. For mode=input, this is the file name that will contain the extracted strings. For mode=output, this is used to insert translated entries back into the original file. Must be .csv .xlsx .xls .ods', default=None, type=str)
    commandLineParser.add_argument('-se','--spreadsheetEncoding', help='Only valid for .csv files. Specify the encoding of the spreadsheet file.', default=None, type=str)

    commandLineParser.add_argument('-cn','--characterNamesDictionary', help='Optional character dictionary containing the names of the characters. Using aliases is likely better than the actual translated names because entries will be reverted during translation.', default=None, type=str)
    commandLineParser.add_argument('-cne','--characterNamesDictionaryEncoding', help='Specify the encoding of the character dictionary file.', default=None, type=str)

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

    userInput[ 'parsingScript' ] = commandLineArguments.parsingScript
    userInput[ 'parsingScriptEncoding' ] = commandLineArguments.parsingScriptEncoding

    userInput[ 'parseSettingsFile' ] = commandLineArguments.parseSettingsFile
    userInput[ 'parseSettingsFileEncoding' ] = commandLineArguments.parseSettingsFileEncoding

    userInput['spreadsheet' ] = commandLineArguments.spreadsheet
    userInput['spreadsheetEncoding' ] = commandLineArguments.spreadsheetEncoding

    userInput[ 'characterDictionaryFileName' ] = commandLineArguments.characterNamesDictionary
    userInput[ 'characterDictionaryEncoding' ] = commandLineArguments.characterNamesDictionaryEncoding

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
    if fileNameWithPath == None:
        print( ('Cannot read settings from None entry: '+fileNameWithPath ).encode(consoleEncoding) )
        return None

    if os.path.isfile(fileNameWithPath) != True:
        sys.exit( ('\n Error: Unable to find input file \''+ fileNameWithPath + '\'' + usageHelp).encode(consoleEncoding) )

    #then read entire file into memory
    #If there is an error reading the contents into memory, just close it.
#    try:
#        inputFileHandle = open(fileNameWithPath,'r',encoding=fileNameEncoding, errors=inputErrorHandling) #open in read only text mode #Will error out if file does not exist.
        #open() works with both \ and / to traverse folders.
#        inputFileContents=inputFileHandle.read()
#    finally:
#        inputFileHandle.close()#Always executes, probably.

    #Newer, simplier syntax.
    with open( fileNameWithPath, 'r', encoding=fileNameEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read()

    if (not isinstance(inputFileContents, str) ) or (inputFileContents == ''):
        sys.exit( ( 'Error: Unable to read from file: ' + fileNameWithPath ).encode(consoleEncoding) )

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


# This returns either None or a dictionary of the contents of parsingScript.ini.
def checkIfParseSettingsFileExists(parsingScript,parseSettingsFileEncoding):
    parsingScriptObject=pathlib.Path(parsingScript).absolute()

    iniNameAndPath=None
    #check to see if settings file exists.
    if os.path.isfile( str(parsingScriptObject.parent) + '/' + parsingScriptObject.stem + parseSettingsExtension ):
        iniNameAndPath=str(parsingScriptObject.parent) + '/' + parsingScriptObject.stem + parseSettingsExtension
    elif os.path.isfile( str(parsingScriptObject) + parseSettingsExtension ):
        iniNameAndPath=str(parsingScriptObject) + parseSettingsExtension

    if debug==True:
        print('iniName1=' + str(parsingScriptObject.parent) + parsingScriptObject.stem + parseSettingsExtension)
        print('iniName2=' + str(parsingScriptObject) + parseSettingsExtension)

    if iniNameAndPath != None:
        print( 'Info: Using the following file as parseSettingsDictionary:')
        print( iniNameAndPath.encode(consoleEncoding) )
    else:
        print( 'Info: parseSettingsDictionary was not found.')
        return None

    parseSettingsDictionary = readSettingsFromTextFile( iniNameAndPath, parseSettingsFileEncoding)

    if debug==True:
        print(str(parseSettingsDictionary))

    if parseSettingsDictionary != None:
        return parseSettingsDictionary
    else:
        return None


def validateUserInput(userInput):
    if userInput['mode'].lower() == 'input':
        userInput['mode']='input'
    elif userInput['mode'].lower() == 'output':
        userInput['mode']='output'
    else:
        print( ('Error: Mode must be input or output. Mode=' + userInput['mode']).encode(consoleEncoding) )

    verifyThisFileExists(userInput['rawFileName'])
    verifyThisFileExists(userInput['parsingScript'])

    if userInput['rawFileEncoding'] == None:
        userInput['rawFileEncoding']=defaultTextFileEncoding
        print( ('Warning: rawFileEncoding was not specified. Setting to \'' + defaultTextFileEncoding +'\' This is probably incorrect.' ).encode(consoleEncoding) )

    if userInput['parseSettingsFile'] != None:
        if checkIfThisFileExists(userInput['parseSettingsFile']) == True:
            pass
        else:
            print( 'Warning: The following parseSettingsFile was specified but does not exist:' )
            print( (userInput['parseSettingsFile']).encode(consoleEncoding) )
            userInput['parseSettingsFile']=None

    if userInput['parseSettingsFileEncoding']==None:
        userInput['parseSettingsFileEncoding']=defaultTextFileEncoding


    #if userInput[ 'spreadsheet' ] != None:
    if userInput[ 'mode' ] == 'input':
        if userInput[ 'spreadsheet' ] == None:
            print( 'Info: Spreadsheet file was not specified. Will create as: '+ defaultSpreadsheetExtension )
            userInput[ 'spreadsheet' ] = userInput['rawFileName'] + defaultSpreadsheetExtension
            userInput[ 'spreadsheetExtension'] = defaultSpreadsheetExtension
        else:
            userInput[ 'spreadsheetExtension'] = pathlib.Path( userInput[ 'spreadsheet' ] ).suffix

        if checkIfThisFileExists( userInput[ 'spreadsheet' ] ) == True:
            # Rename to .backup because it will be replaced.
            pathlib.Path( userInput[ 'spreadsheet' ] ).replace( userInput[ 'spreadsheet' ] + '.backup' )
            print ( ('Info: '+ userInput[ 'spreadsheet' ] + ' moved to ' + userInput[ 'spreadsheet' ] + '.backup').encode(consoleEncoding) )

        #elif checkIfThisFileExists( userInput[ 'spreadsheet' ] ) != True:
        #else:
        #    Update: Then user specified an output file that does not exist yet. That makes sense. All is well.
        #    However, still need to verify the extension is correct: .csv .xlsx .xls .ods
            # It is not entirely correct to call this userInput, but whatever.
        if userInput[ 'spreadsheetExtension'] in supportedExtensions:
            pass
        else:
            print( (' Error: Unsupported extension for spreadsheet: \'' + userInput[ 'spreadsheetExtension'] + '\'' ).encode(consoleEncoding) )
            print( 'Supported extensions: ' + str(supportedExtensions) )
            sys.exit(1)

        #    print( 'Warning: The following spreadsheet file was specified but does not exist:' )
        #    print( ( userInput[ 'spreadsheet' ] ).encode(consoleEncoding) )
        #    userInput[ 'parseSettingsFile' ] = None

    #elif userInput[ 'mode' ] == 'output':
    else:
        if userInput[ 'spreadsheet' ] == None:
            print( 'Error: Please specify a valid spreadsheet from which to read translations.' )
            sys.exit(1)

        if checkIfThisFileExists( userInput[ 'spreadsheet' ] ) != True:
            print( 'Error: The following spreadsheet file was specified but does not exist:' )
            print( ( userInput[ 'spreadsheet' ] ).encode(consoleEncoding) )
            sys.exit(1)            
#        elif checkIfThisFileExists( userInput[ 'spreadsheet' ] ) == True:
#        else:
                #Then user specified an output file, and it exists. All is well. Do nothing here.


    if userInput[ 'spreadsheetEncoding' ] == None:
        userInput[ 'spreadsheetEncoding' ] = defaultTextFileEncoding

    if userInput[ 'characterDictionaryEncoding' ] == None:
        userInput[ 'characterDictionaryEncoding' ] = defaultTextFileEncoding

    userInput[ 'characterDictionary' ]=None
    if userInput[ 'characterDictionaryFileName' ] != None:
        if checkIfThisFileExists( userInput[ 'characterDictionaryFileName' ] ) == True:
            #Read in character dictionary
            tempDict={}
            tempKey=''
            tempValue=''
            index=0
            #'with' is correct. Do not use 'while'.
            with open(userInput[ 'characterDictionaryFileName' ], 'r', newline='', encoding=userInput[ 'characterDictionaryEncoding' ], errors=inputErrorHandling) as myFileHandle:
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
                        tempDict[line[0]]=line[1]
                userInput[ 'characterDictionary' ]=tempDict
        else:
            print( 'Warning: characterDictionary file was specified but does not exist:' )
            print( ( userInput[ 'characterDictionaryFileName' ] ).encode(consoleEncoding) )
            userInput[ 'characterDictionaryFileName' ] = None

    if userInput[ 'debug' ] == True:
        userInput[ 'verbose' ] = True
        for key, value in userInput.items():
            print( str(key) + '=' + str(value) )

    global verbose
    verbose=userInput[ 'verbose' ]
    global debug
    debug=userInput[ 'debug' ]

    if debug == True:
        print( 'userInput[characterDictionary]=' + str( userInput[ 'characterDictionary' ] ) )

    return userInput


def parse(rawFileNameAndPath, parsingScript, rawFileEncoding=defaultTextFileEncoding, parsingScriptEncoding=defaultTextFileEncoding, parseSettingsFile=None, parseSettingsFileEncoding=defaultTextFileEncoding, characterDictionary=None):
    #parsingScript='templates\KAG3.py'
    #parsingScript='templates\KAG3.PrincessBritania.py'

    # import parsingScript  # With fancier import syntax where the parent directory is added to sys.path first:
    #parsingScriptObject=pathlib.Path(parsingScript).absolute() #According to the docs, this should not work, but it does. There is no absolute() method.

    # This takes the parsingScript.py, gets the absolute path, adds the parent directory to sys.path so Python can import it, fixes the name to not contain reserved characters, and then imports it as a temporary file.
    parsingScriptObject=pathlib.Path(parsingScript).resolve()
    # sys.path.append(str(parsingScriptObject.parent))
    # importlib.import_module(parsingScriptObject.stem)
    
    # Alternative, more flexible method.
    # Algorithm: Create scratchpad directory, copy target script to scratchpad directory, import as: import scratchpad.temp as customParser
    # This is ideal because: 
    # 1. Weird file system names that are not valid module names are then no longer an issue,
    # 2. Trying to resolve paths and importing above parent directory from __main__ is no longer an issue,
    # 3. The importlib library to handle special import handling is no longer necessary. However, shutil.copy2 becomes necessary to copy the code. The alternative to shutil is platform specific code with the os module, or opening the file and copying the contents manually.
    # 4. scratchpad is already labeled as a temporary directory in git.
    pathlib.Path( str(pathlib.Path(tempParseScriptPathAndName).resolve().parent) ).mkdir( parents = True, exist_ok = True )

    if debug == True:
        print( 'copyFrom=' + str(parsingScriptObject) )
        print( 'copyTo=' + str( pathlib.Path(tempParseScriptPathAndName).resolve()) )

    # Minor issue still: No way to avoid hardcoding this unless using the importlib module.
    #shutil.copy( str(parsingScriptObject) , str( pathlib.Path(tempParseScriptPathAndName).resolve() ) )
    shutil.copy( str(parsingScriptObject) , 'scratchpad/temp.py' )
    import scratchpad.temp as customParser
    # importlib.import_module( tempParseScriptPathAndName) #This still requires fixing the \\ and / in the path.

    # Now that customParser exists, the internal variable names can be updated.

    #customParser='resources.' + parsingScriptObject.name
    #import customParser
    #import resources.templates.KAG3_PrincessBritania as customParser
    #import parsingScript
    #from 'resources.' + customParser import input
#    print('parsingScriptObject=' + str(parsingScriptObject))
#    print('parsingScriptObject.name=' + parsingScriptObject.name)

    #customParser = importlib.import_module('resources.templates.KAG3_PrincessBritania')
    #fixedName=str(parsingScriptObject).replace('\\','.')
    #print( 'fixedName=' + fixedName )
    #customParser = importlib.import_module(fixedName)
    #customParser = importlib.import_module('...KAG3_PrincessBritania',package='.')

#    currentScriptPathObject=pathlib.Path('.').absolute()
#    print( 'currentScriptPathObject=' + str(currentScriptPathObject) )

#    relativePath=parsingScriptObject.relative_to(currentScriptPathObject)
#    print( 'relativePath=' + str(relativePath) )
#    print( 'relativePath.exists()=' + str(relativePath.exists()) )

#    fixedRelativePath=str(relativePath).replace('\\','.').replace('/','.')
#    print( 'fixedRelativePath=' + fixedRelativePath)

    #print( 'customParser.__version__=' + str(customParser.__version__) )
    #print(str(dir(customParser) ))

    parseSettingsDictionary=checkIfParseSettingsFileExists(parsingScript,parseSettingsFileEncoding)

    spreadsheet=None
    if parseSettingsDictionary != None:
        # Usage: customParser.input('A01.ks', ...)
                                                #def input( fileNameWithPath, parseSettingsDictionary, fileEncoding=defaultTextEncoding, charaNamesDict=None):
        spreadsheet = customParser.input(rawFileNameAndPath, parseSettingsDictionary, fileEncoding=rawFileEncoding, charaNamesDict=characterDictionary)
    #elif parseSettingsDictionary == None:
    else:
        # This syntax assumes there is no parseSettings.ini since that is defined within the file. If parseSettings.ini is required, then this syntax will fail.
        spreadsheet = customParser.input(rawFileNameAndPath, fileEncoding=rawFileEncoding, charaNamesDict=characterDictionary)

    if (debug == True) and (spreadsheet != None):
        spreadsheet.printAllTheThings()
    return spreadsheet


def insertTranslatedText():
    pass


def main():

    # Define command line options.
    # userInput is a dictionary.
    userInput=createCommandLineOptions()

    # Verify input.
    userInput=validateUserInput(userInput)

    if userInput['mode'] == 'input':
        #parseInput()
        #parser.importFromTextFile('A01.ks',)
        #def parse(rawFileNameAndPath, parsingScript, rawFileEncoding=defaultTextFileEncoding, parseSettingsFile=None, parseSettingsFileEncoding=defaultTextFileEncoding, characterDictionary=None):
        spreadsheet=parse(
                userInput['rawFileName'], 
                userInput['parsingScript'], 
                rawFileEncoding=userInput['rawFileEncoding'],
                parsingScriptEncoding=userInput['parsingScriptEncoding'],
                parseSettingsFile=userInput[ 'parseSettingsFile' ],
                parseSettingsFileEncoding=userInput[ 'parseSettingsFileEncoding' ],
                characterDictionary=userInput[ 'characterDictionary' ]
        )

        assert( isinstance( spreadsheet, chocolate.Strawberry )  )

        # Export to .xlsx
        outputPathObject=pathlib.Path( userInput[ 'spreadsheet' ] )
        #outputPathObject.extension # This does not work. What an odd design choice.


        if ( userInput['spreadsheetExtension'] == '.csv' ):
            spreadsheet.exportToCSV( userInput[ 'spreadsheet' ], fileEncoding=userInput[ 'spreadsheetEncoding' ], errors=outputErrorHandling )
        elif ( userInput['spreadsheetExtension'] == '.xlsx' ):
            spreadsheet.exportToXLSX( userInput['spreadsheet' ] )
        elif ( userInput['spreadsheetExtension'] == '.xls' ):
            spreadsheet.exportToXLS( userInput['spreadsheet' ] )
        elif ( userInput['spreadsheetExtension'] == '.ods' ):
            spreadsheet.exportToODS( userInput[ 'spreadsheet' ] )
        else:
            print( unspecifiedError )
            sys.exit(1)
        # Writing operations are always scary, so spreadsheet.exportTo() should always print when it is writing output internally. No need to do it again here.

    elif userInput['mode'] == output:
        # parseOutput()
        #parser.output('A01.ks',)
        print('Hello, world!')


if __name__ == '__main__':
    main()
    sys.exit(0)

# Print success message.
print('pie10')

