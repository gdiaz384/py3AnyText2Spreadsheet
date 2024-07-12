#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
py3AnyText2Spreadsheet supports Python parsing scripts that can convert various formats, like .epub, .srt, .ass, .ks, .json, and so forth to and from spreadsheet formats, .csv, .xlsx, .xls, .ods. 

Concept art:
The idea is if py3AnyText2Spreadsheet called directly as 'python py3AnyText2Spreadsheet.py --file input', then it should output .csv and .xlsx files instead.
for py3AnyText2Spreadsheet to act as a proxy to call upon various types of parsing scripts that always returns and accepts a chocolate.Strawberry().
If imported as a library, then it should just act as a proxy for the parsing script.

import resources.py3AnyText2Spreadsheet
spreadsheet = resources.py3AnyText2Spreadsheet('resources\py3AnyText2Spreadsheet\resources\ks.kag3.kirikiri.parsingTemplate.py')

For cross language support of parsing files, this program should probably support something like: https://github.com/Distributive-Network/PythonMonkey
Then again, Python is very easy to use.

Copyright (c) 2024 gdiaz384 ; License: GNU Affero GPL v3. https://www.gnu.org/licenses/agpl-3.0.html

"""
__version__='2024.06.21 alpha'


# Set defaults.
verbose = False
debug = False

consoleEncoding = 'utf-8'
defaultTextFileEncoding = 'utf-8'                     # Settings that should not be left as a default setting should have default prepended to them.
defaultTextEncodingForKSFiles = 'shift-jis'      # UCS2 BOM LE (aka UTF-16 LE) might also work. Need to test.
# shift-jis is a text encoding. In terms of ANSI code pages, it maps to cp932.
 
supportedSpreadsheetExtensions = [ '.csv' , '.xlsx' , '.xls' , '.ods', '.tsv' ]
defaultSpreadsheetExtension = '.xlsx'
defaultOutputColumn = 4
tempParseScriptPathAndName = 'scratchpad/temp.py'   # Do not change this. This is associated with a hardcoded import statement pointing to scratchpad\temp.py It is not possible to make tempParseScriptPathAndName dynamic without importing an additional library which is more complicated to manage than just hardcoding this.

inputErrorHandling = 'strict'
#outputErrorHandling = 'namereplace'        #This is set dynamically below.

unspecifiedError = 'Unspecified error in py3AnyText2Spreadsheet.py.'
usageHelp = ' Usage: python py3AnyText2Spreadsheet.py --help  Example: py3AnyText2Spreadsheet input myInputFile.ks parsingProgram.py --rawFileEncoding shift-jis'


# import stuff.
import argparse                                                 # For command line options.
import sys                                                           # For sys.exit() and add library locations dynamically with sys.path.append().
import os                                                            # Check if files and folders exist.
import pathlib                                                     # Sane path handling.
import csv                                                           # Used to read character dictionary.
import shutil                                                        # Supports high-level copy operations. Used to copy script file to scratchpad temporary directory for importing.
#import hashlib                                                      # TODO: Before copying, if the target exists, then read both files and compare their hash. Do not copy if their hashes match.

import resources.chocolate as chocolate             # Main wrapper for openpyxl library. Used as core data structure.
import resources.dealWithEncoding as dealWithEncoding # Handles text encoding and implements optional chardet library.
import resources.functions as functions               # Has a lot of helper functions not directly related to this program's core logic.

#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
if sys.version_info.minor >= 5:
    outputErrorHandling = 'namereplace'
elif sys.version_info.minor < 5:
    outputErrorHandling = 'backslashreplace'    


def createCommandLineOptions():
    commandLineParser=argparse.ArgumentParser( description='Description: Turns text files into spreadsheets using user-defined scripts. If mode is set to input, then parsingProgram.input() will be called. If mode is set to output, then parsingProgram.output() will be called.' + usageHelp)
    commandLineParser.add_argument( 'mode', help='Must be input or output.', type=str)

    commandLineParser.add_argument( 'rawFile', help='Specify the text file to parse.', type=str)
    commandLineParser.add_argument( '-e','--rawFileEncoding', help='Specify the encoding of the rawFile.', default=None, type=str)

    commandLineParser.add_argument( 'parsingProgram', help='Specify the .py script that will be used to parse rawFile.', type=str)
    commandLineParser.add_argument( '-pse', '--parsingProgramEncoding', help='Specify the encoding of the parsingProgram.', default=None,type=str)

    commandLineParser.add_argument( '-psf', '--parseSettingsFile', help='Optional parsingProgram.ini to convert to a settings dictionary.', default=None,type=str)
    commandLineParser.add_argument( '-psfe', '--parseSettingsFileEncoding', help='Specify the encoding of parseSettingsFile.', default=None, type=str)

    commandLineParser.add_argument( '-s', '--spreadsheet', help='Specify the spreadsheet file to use. For mode=input, this is the file name that will contain the extracted strings. For mode=output, this is used to insert translated entries back into the original file. Must be .csv .xlsx .xls .ods', default=None, type=str)
    commandLineParser.add_argument( '-se', '--spreadsheetEncoding', help='Only valid for .csv files. Specify the encoding of the spreadsheet file.', default=None, type=str)

    commandLineParser.add_argument( '-cn', '--characterNamesDictionary', help='Optional character dictionary containing the names of the characters. Using aliases is likely better than the actual translated names because entries will be reverted during translation.', default=None, type=str)
    commandLineParser.add_argument( '-cne', '--characterNamesDictionaryEncoding', help='Specify the encoding of the character dictionary file.', default=None, type=str)

    commandLineParser.add_argument( '-trf', '--translatedRawFile', help='Specify the output file name and path for the translatedRawFile. Only valid for mode=output.', default=None, type=str)
    commandLineParser.add_argument( '-trfe', '--translatedRawFileEncoding', help='Specify the encoding of translatedRawFile.', default=None, type=str)

    commandLineParser.add_argument( '-c', '--columnToUseForReplacements', help='Specify the column in the spreadsheet to use for replacements. Can be an integer starting with 1 or the name of the column header. Case sensitive. Only valid for mode=output.', default=None, type=str) # This lacks a type= declaration. Is that needed? #Update: If no type declaration is used, then str is assumed. Just make it explicit then.

    commandLineParser.add_argument( '-t', '--testRun', help='Parse stuff, but do not write any output files.', action='store_true')
    commandLineParser.add_argument( '-vb', '--verbose', help='Print more information.', action='store_true')
    commandLineParser.add_argument( '-d', '--debug', help='Print too much information.', action='store_true')
    commandLineParser.add_argument( '-v', '--version', help='Print version information and exit.', action='store_true')    

    commandLineArguments=commandLineParser.parse_args()

    if commandLineArguments.version == True:
        print( __version__.encode(consoleEncoding) )
        sys.exit( 0 )

    userInput={}
    userInput[ 'mode' ] = commandLineArguments.mode

    userInput[ 'rawFileName' ] = commandLineArguments.rawFile
    userInput[ 'rawFileEncoding' ] = commandLineArguments.rawFileEncoding

    userInput[ 'parsingProgram' ] = commandLineArguments.parsingProgram
    userInput[ 'parsingProgramEncoding' ] = commandLineArguments.parsingProgramEncoding # This should always be utf-8. Can Python even execute non-utf-8 and non-ascii?

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


# This should also read in all of the input files.
def validateUserInput(userInput):
    global verbose
    verbose=userInput[ 'verbose' ]
    global debug
    debug=userInput[ 'debug' ]

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

    functions.verifyThisFileExists( userInput[ 'rawFileName' ] )
    functions.verifyThisFileExists( userInput[ 'parsingProgram' ] )

    if userInput[ 'parseSettingsFile' ] != None:
        if functions.checkIfThisFileExists( userInput[ 'parseSettingsFile' ] ) == True:
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

        if functions.checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) == True:
            # Rename to .backup because it will be replaced.
            pathlib.Path( userInput[ 'spreadsheetFileName' ] ).replace( userInput[ 'spreadsheetFileName' ] + '.backup' )
            print ( ('Info: '+ userInput[ 'spreadsheetFileName' ] + ' moved to ' + userInput[ 'spreadsheetFileName' ] + '.backup').encode(consoleEncoding) )
        #elif functions.checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) != True:
        #else:
        #    Update: Then user specified an output file that does not exist yet. That makes sense. All is well.

        #    However, still need to verify the extension is correct: .csv .xlsx .xls .ods
            # It is not entirely correct to call this userInput, but whatever.
        if userInput[ 'spreadsheetExtension'] in supportedSpreadsheetExtensions:
            pass
        else:
            print( ('Error: Unsupported extension for spreadsheet: \'' + userInput[ 'spreadsheetExtension' ] + '\'' ).encode(consoleEncoding) )
            print( 'Supported extensions: ' + str(supportedSpreadsheetExtensions) )
            sys.exit(1)

    #elif userInput[ 'mode' ] == 'output':
    else:
        if userInput[ 'spreadsheetFileName' ] == None:
            print( 'Error: Please specify a valid spreadsheet from which to read translations.' )
            sys.exit(1)

        if functions.checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) != True:
            print( 'Error: The following spreadsheet file was specified but does not exist:' )
            print( ( userInput[ 'spreadsheetFileName' ] ).encode(consoleEncoding) )
            sys.exit(1)            
#        elif functions.checkIfThisFileExists( userInput[ 'spreadsheetFileName' ] ) == True:
#        else:
                # Then user specified an input file, and it exists. All is well. Do nothing here.
#                pass

        if userInput[ 'translatedRawFileName' ] == None:
            # Then the user did not specify an output file.
            # What would be sane behavior here? Maybe just append translated.extension?
            userInput[ 'translatedRawFileName' ] = userInput[ 'rawFileName' ] + '.translated' + pathlib.Path( userInput[ 'rawFileName'] ).suffix
            print( 'Warning: No output file name was specified for the translated file. Using:')
            print( userInput[ 'translatedRawFileName'].encode(consoleEncoding) )

    # This is about to be used, so map it now.
    if userInput[ 'characterDictionaryEncoding' ] == None:
        userInput[ 'characterDictionaryEncoding' ] = defaultTextFileEncoding

    if userInput[ 'characterDictionaryFileName' ] != None:
        if functions.checkIfThisFileExists( userInput[ 'characterDictionaryFileName' ] ) == True:
            # Read in characterDictionary.csv
            userInput[ 'characterDictionary' ]=functions.importDictionaryFromFile( userInput[ 'characterDictionaryFileName' ], encoding=userInput[ 'characterDictionaryEncoding' ] )
            if debug == True:
                print( ( 'userInput[characterDictionary]=' + str( userInput[ 'characterDictionary' ] ) ).encode(consoleEncoding) )

        #elif functions.checkIfThisFileExists( userInput[ 'characterDictionaryFileName' ] ) != True:
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
    # TODO: update with dealWithEncoding.ofThisFile() logic for implementation of chardet library or alternatives.
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

    # Try to detect line endings from the original file so it can be used for output.
    # dealWithEncoding.detectLineEndingsFromFile() returns a tuple like ( 'windows', '\r\n' ) or ( 'unix', '\n' ) .
    detectedLineEndings=dealWithEncoding.detectLineEndingsFromFile( userInput[ 'rawFileName' ], userInput[ 'rawFileEncoding' ] )
    #print( 'detectedLineEndings=' + detectedLineEndings[0] )
    userInput[ 'rawFileLineEndings' ] = detectedLineEndings[1]

    if debug == True:
        print( 'userInput[characterDictionary]=' + str( userInput[ 'characterDictionary' ] ) )

    return userInput


def main( userInput=None ):

    if not isinstance( userInput, dict ):
        # Define command line options.
        # userInput is a dictionary.
        userInput = createCommandLineOptions()
        # Verify input.
        userInput = validateUserInput( userInput ) # This should also read in all of the input files into dictionaries except for the parseScript.py.

    if debug == True:
        print( ( 'userInput=' + str(userInput) ).encode(consoleEncoding) )

    # Import algorithm: Create scratchpad directory, copy target script to scratchpad directory, import as: import scratchpad.temp as customParser
    # This is ideal because: 
    # 1. Weird file system names that are not valid module names are then no longer an issue.
    # 2. Trying to resolve paths and importing above parent directory from __main__ is no longer an issue.
    # 3. The importlib library to handle special import handling is no longer necessary. However, shutil.copy becomes necessary to copy the code. The alternative to shutil is platform specific code with the os module, or opening the file and copying the contents manually.
    # 4. scratchpad is already labeled as a temporary directory in git.
    # The best alternative is sys.path.append(/path/to/library.py) but there is no way of knowing if 'library' has forbidden characters for library names like -, so renaming would be necessary. However, that would alter the file name the user specified, so that is absolutely not allowed which makes copying the file to a temporary location unavoidable.

    parsingScriptObject=pathlib.Path(userInput['parsingProgram']).resolve()
    global tempParseScriptPathAndName
    tempParseScriptPathAndName = str( pathlib.Path(__file__).resolve().parent ) + '/' + tempParseScriptPathAndName
    #print( 'tempParseScriptPathAndName=' + tempParseScriptPathAndName)

    pathlib.Path( tempParseScriptPathAndName ).resolve().parent.mkdir( parents = True, exist_ok = True )

    if debug == True:
        print( 'copyFrom=' + str(parsingScriptObject) )
        print( 'copyTo=' + str( pathlib.Path(tempParseScriptPathAndName).resolve()) )

    # TODO: before copying, if the target exists, then read both files and compare their hash. Do not copy if their hashes match.
    # Minor issue still: No way to avoid hardcoding this unless using the importlib module.
    shutil.copy( str(parsingScriptObject) , tempParseScriptPathAndName )

    sys.path.append( str( pathlib.Path(__file__).resolve().parent) )
    import scratchpad.temp as customParser          # Hardcoded to import as scratchpad\temp.py

    # TODO: Now that customParser exists, the internal variable names can be updated.
    # Update debug setting in all imported libraries, chocolate, functions, dealWithEncoding, and the parsingProgram.
    #customParser.consoleEncoding=...
    #customParser.verbose=...
    #customParser.debug=...

    parseSettingsDictionary=functions.getParseSettingsDictionary( userInput['parsingProgram'], parseSettingsFile=userInput[ 'parseSettingsFile' ], parseSettingsFileEncoding=userInput[ 'parseSettingsFileEncoding' ])

    # Just dump everything into a 'settings' dictionary {} so the API does not have to change as often, to present a uniform API over all the parsers, and improve user experience.
    settings = userInput.copy()
    settings[ 'fileEncoding' ] = userInput[ 'rawFileEncoding' ]
    settings[ 'parseSettingsDictionary' ] = parseSettingsDictionary
    settings[ 'outputColumn'] = userInput[ 'columnToUseForReplacements' ]
    settings[ 'rawFileLineEndings' ] = userInput[ 'rawFileLineEndings' ] 

    if userInput[ 'mode' ] == 'input':
        # def input( fileNameWithPath, characterDictionary=None, settings={} ):
        mySpreadsheet=customParser.input( userInput['rawFileName'], characterDictionary=userInput[ 'characterDictionary' ], settings=settings )
 
        if mySpreadsheet == None:
            print( 'Empty file.' )
            sys.exit( 1 )
        else:
            assert( isinstance( mySpreadsheet, chocolate.Strawberry )  )

        if debug == True:
            mySpreadsheet.printAllTheThings()

        # Export to .xlsx
        if userInput[ 'testRun' ] != True:
            # Writing operations are always scary, so mySpreadsheet.export() should always print when it is writing output internally. No need to do it again here.
            mySpreadsheet.export( userInput[ 'spreadsheetFileName' ], fileEncoding=userInput[ 'spreadsheetFileEncoding' ] )

    elif userInput[ 'mode' ] == 'output':

        mySpreadsheet=chocolate.Strawberry( myFileName=userInput[ 'spreadsheetFileName'], fileEncoding=userInput[ 'spreadsheetFileEncoding' ], removeWhitespaceForCSV=True, csvDialect=None)

        #def output( fileNameWithPath, mySpreadsheet, characterDictionary=None, settings={} ): # mySpreadsheet is a chocolate Strawberry.
        translatedTextFile=customParser.output( userInput['rawFileName'], mySpreadsheet=mySpreadsheet, characterDictionary=userInput[ 'characterDictionary' ], settings=settings )

        if debug == True:
            print( ( 'translatedTextFile=' + str(translatedTextFile) ).encode(consoleEncoding) )

        if userInput[ 'testRun' ] == True:
            return

        wroteFile=False
        if isinstance( translatedTextFile, chocolate.Strawberry) == True:
            translatedTextFile.export( userInput[ 'translatedRawFileName' ], fileEncoding=userInput[ 'translatedRawFileEncoding' ] )
            wroteFile = True
        elif isinstance( translatedTextFile, str ) == True:
            #userInput exists
            with open( userInput[ 'translatedRawFileName' ], 'w', encoding=userInput[ 'translatedRawFileEncoding' ], errors=outputErrorHandling, newline=userInput[ 'rawFileLineEndings' ] ) as myFileHandle:
                myFileHandle.write(translatedTextFile)
            wroteFile = True
        elif isinstance( translatedTextFile, list ) == True:
            with open( userInput[ 'translatedRawFileName' ], 'w', encoding=userInput[ 'translatedRawFileEncoding' ], errors=outputErrorHandling, newline=userInput[ 'rawFileLineEndings' ] ) as myFileHandle:
                for entry in translatedTextFile:
                    # This might corrupt the output on Linux/Unix or vica-versa on Windows if the software is expecting and requires a specific type of newline \r\n or \n.
                    # By default, Python will translate \n based upon the host OS, not what the software that will actually read the file is expecting because it cannot possibly know that, therefore this is a potential source of corruption.
                    # A sane way of handling this is to maybe determine the line ending of the original file and use that line ending schema here. How are line endings determined? Huristics? How does Python determine line endings correctly when the platform does not match the source file?
                    myFileHandle.write(entry + '\n')
            wroteFile = True
        elif translatedTextFile == None:
            print('Empty file.')
        else:
            print( 'Error: Unknown type of return value from parsing script. Must be a chocolate.Strawberry(), list, or string.')
            print( 'type=' +  str( type(translatedTextFile) ) )

        if wroteFile == True:
            # chocolate.Strawberry() will print out its own confirmation of writing out the file on its own, so do not duplicate that message here.
            if ( checkIfThisFileExists( userInput[ 'translatedRawFileName' ] ) == True ) and ( isinstance( translatedTextFile, chocolate.Strawberry ) == False ):
                print( ('Wrote: '+ userInput[ 'translatedRawFileName' ]).encode(consoleEncoding) )


if __name__ == '__main__':
    main()
    sys.exit(0)

