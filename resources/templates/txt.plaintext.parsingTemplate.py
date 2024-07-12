#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
This script parses plaintext files line by line as input and returns a spreadsheet.
It also takes a spreadsheet and outputs the hopefully translated contents back into the file.
That spreadsheet is implemented as a Strawberry() class found in the chocolate.py library. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

API concept art:
input() processes raw data and converts it to a spreadsheet for further processing.
output() takes data from a processed spreadsheet and inserts it back into the original file.

CLI Usage:
python py3Any2Spreadsheet.py --help
python py3Any2Spreadsheet.py input plaintext.txt txt.plaintext.parsingTemplate.py
python py3Any2Spreadsheet.py output plaintext.txt txt.plaintext.parsingTemplate.py --spreadsheet plaintext.txt.xlsx

py3Any2Spreadsheet.py Usage:
import 'resources\templates\txt.plaintext.parsingTemplate.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Algorithim:
Skip empty lines.
Skip linest that start with predefined list of ignore characters. See skipLinesStartingWith

License: See main program.
"""
__version__ = '2024.07.11'


# Set program defaults.
verbose = False
debug = False
consoleEncoding = 'utf-8'
defaultTextEncoding = 'utf-8'
defaultOutputColumn = 4
metadataDelimiter = '_'
defaultTargetEncoding='cp932'

#https://docs.python.org/3.7/library/codecs.html#standard-encodings
inputErrorHandling = 'strict'
#inputErrorHandling = 'backslashreplace'
#outputErrorHandling = 'namereplace'  #This is set dynamically below.

# If a line should be ignored, add an appropriate character here to skip parsing it. Adjust as needed for each dataset.
skipLinesStartingWith = [
'#',
'@',
]

# import stuff
import sys                                                         # Used to sys.exit() in case of an error and to check system version.

import resources.chocolate as chocolate            # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.
# To import directly:
# import sys
# import pathlib
# sys.path.append( str( pathlib.Path( 'C:/resources/chocolate.py' ).resolve().parent ) )
# import chocolate

import resources.functions as functions              # A helper library that has many functions.
# To import directly:
# import sys
# import pathlib
# sys.path.append( str( pathlib.Path( 'C:\\resources\\functions.py' ).resolve().parent ) )
# import functions

#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
if sys.version_info.minor >= 5:
    outputErrorHandling = 'namereplace'
elif sys.version_info.minor < 5:
    outputErrorHandling = 'backslashreplace'    


"""
Development Guide:
input() is called with the following parameters:
1) fileNameWithPath ; This is rawFile as it was passed to py3AnyText2Spreadsheet at the CLI. It still needs to be opened and read into memory.
2) characterDictionary {} ; This is optional, but if characterDictionary.csv was specified at the CLI, then it will be available here as a Python dictionary. The first row is always reserved for headers and so is ignored when going from characterDictionary.csv->Python dictionary.
3) settings {} ; This is a dictionary that has all of the settings passed to py3AnyText2Spreadsheet at the command line interface and a few extra values.
input() is responsible for returning a completed chocolate.Strawberry() spreadsheet back to py3AnyText2Spreadsheet so it can be written out to disk.

output() is called with the following parameters:
1) fileNameWithPath ; This is rawFile as it was passed to py3AnyText2Spreadsheet at the CLI. It still needs to be opened and read into memory.
2) spreadsheet ; The chocolate.Strawberry() that was created using the input() function and specified at the CLI using the --spreadsheet option will be available here.
3) characterDictionary {} ; This is optional, but if characterDictionary.csv was specified at the CLI, then it will be available here as a Python dictionary. The first row is always reserved for headers and so is ignored when going from characterDictionary.csv->Python dictionary.
4) settings {} ; This is a dictionary that has all of the settings passed to py3AnyText2Spreadsheet at the command line interface and a few extra values.
output() is responsible inserting the translated/completed contents in chocolate.Strawberry() spreadsheet back into fileNameWithPath. Once fileNameWithPath has been updated, it should be sent back as a string, a list of strings, or a chocolate.Strawberry() to be written out to disk.

The settings {} dictionary has all of the parameters passed at the CLI and a few others. These in particular are useful:
settings[ 'fileEncoding' ] - The encoding of rawFile as a string.
settings[ 'parseSettingsDictionary' ] - The parsingTemplate.ini file as a Python dictionary.
settings[ 'outputColumn' ] - The columnToUseForReplacements from the CLI as a string. If a number was specified, it can be converted back using int( settings[ 'outputColumn' ] ) . If one was not specified, then settings[ 'outputColumnIsDefault' ] == True.
settings[ 'translatedRawFileName' ] - The filename and path of the file to use when writing the translated file as output.

Spreadsheet formatting suggestion: https://github.com/gdiaz384/py3TranslateLLM#regarding-the-spreadsheet-formats
The format is based on the format used by VNT, T++, and common sense.
Summary:
Column A should be the extracted rawText.
Column B should be the speaker (if any). If there is none, then leave this column blank. If possible, use the characterDictionary to translate any raw names into their translated forms as this is more convenient to translate + edit.
Column C should be any metadata required to validate and reinsert the contents of Column A and B back into the source text.
As a suggestion for Column C, use the line numbers the input is taken from or the order the input is parsed in, and any other data that is unique to that entry.
Example lists that represent a row for different types of data:
[ 'It is all I can do to hold them off!', None, 15 ]  # .ssa subtitles ; Column C is the entry number. 
[ 'Yes, sir!', 'speaker1', '19_True' ]     # srt subtitles ; Column C is the entry number and if the original entry was split for translation due to multiple speakers appearing in the same entry.
[ '「勉強ねぇ」', None, 'p-009_body p_288' ]  # .ebook ; .ebook ; Column C is the filename_css search tag_entry number, with _ being used as a delimter.
"""


def input( fileNameWithPath, characterDictionary=None, settings={} ):

    if debug == True:
        print( ( 'characterDictionary=' + str(characterDictionary) ).encode(consoleEncoding) )
        print( ( 'settings=' + str(settings) ).encode(consoleEncoding) )

    # Unpack some variables.
    if 'fileEncoding' in settings:
        fileEncoding = settings[ 'fileEncoding' ]
    else:
        fileEncoding=defaultTextEncoding

    if 'parseSettingsDictionary' in settings:
        parseSettingsDictionary = settings[ 'parseSettingsDictionary' ]
    else:
        parseSettingsDictionary = None

    # The input file is actually a .txt file so read it in and convert it into a list of strings.
    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read().splitlines()

    temporaryList = []
    for currentLineNumber,line in enumerate( inputFileContents ):
        # Skip empty lines.
        if line.strip () == '':
            continue
        line = line.strip()
        tempSpeaker = None

        skipTheCurrentLine = False
        for entry in skipLinesStartingWith:
            if line.startswith( entry):
                skipTheCurrentLine = True

        if skipTheCurrentLine != True:
            if ( tempSpeaker != None ) and ( characterDictionary != None ):
                if tempSpeaker in characterDictionary:
                    tempSpeaker = characterDictionary[ tempSpeaker ]
                else:
                    print( 'Warning: Speaker encountered that was not in character dictionary at line', currentLineNumber)

            # Whatever is left is the contents of the line. Append everything found so far to temporaryList.
            temporaryList.append( [ line, tempSpeaker, currentLineNumber ] )

    # Create a new spreadsheet using chocolate.Strawberry().
    mySpreadsheet = chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker','metadata' ] )

    # Add data entries and format metadata column appropriately.
    for entry in temporaryList:
        mySpreadsheet.appendRow( [ entry[0], entry[1], str( entry[2] ) ])

    if debug == True:
        mySpreadsheet.printAllTheThings()

    return mySpreadsheet


# This function takes mySpreadsheet as a chocolate.Strawberry() and inserts the contents back to fileNameWithPath.
def output( fileNameWithPath, mySpreadsheet, characterDictionary=None, settings={} ):

    assert isinstance(mySpreadsheet, chocolate.Strawberry)

    # Unpack some variables.
    if 'fileEncoding' in settings:
        fileEncoding=settings['fileEncoding']
    else:
        fileEncoding=defaultTextEncoding

    if 'parseSettingsDictionary' in settings:
        parseSettingsDictionary=settings['parseSettingsDictionary']
    else:
        parseSettingsDictionary=None

    #outputColumn=None
    if ( not 'outputColumn' in settings ):
        #outputColumn=defaultOutputColumn
        outputColumn=len( mySpreadsheet.getRow(1) )
    #elif 'outputColumn' in settings:
    else:
        if ( 'outputColumnIsDefault' in settings ):
            if ( settings[ 'outputColumnIsDefault' ] == True ):
                # User did not choose it, so disregard default value.
                settings[ 'outputColumn' ]=None

        if isinstance( settings[ 'outputColumn' ], int ) == True:
            # This sets outputColumn to an integer like 4.
            outputColumn = settings[ 'outputColumn' ]
        elif isinstance( settings[ 'outputColumn' ], str ) == True:
            if len(settings[ 'outputColumn' ]) == 1:
                try:
                    outputColumn = int(settings[ 'outputColumn' ])
                except:
                    # Then assume it is already valid as-is.
                    outputColumn=settings[ 'outputColumn' ]
            else:
                # This sets outputColumn to a string like 'A' based upon the search value in settings['outputColumn']. Or if the search string was not found, then the function returns None.
                outputColumn=mySpreadsheet.searchHeaders( settings[ 'outputColumn' ] )
                if outputColumn == None:
                    #settings[ 'outputColumn' ] = None
                    # Then the string does not appear in the headers, so revert to using the furthest right value.
                    try:
                        outputColumn = int(settings[ 'outputColumn' ])
                    except:
                        outputColumn = len( mySpreadsheet.getRow(1) )
                        print( ('Warning: Could not find column \'' + settings[ 'outputColumn' ] + '\' in spreadsheet. Using furthest right column value \'' + str(outputColumn) + ':'+ str( mySpreadsheet.getColumn(outputColumn)[0] ) + '\'' ).encode(consoleEncoding) )
        # if settings[ 'outputColumn' ] is not an integer or string, then give up and use a default value.
        else:
            #outputColumn=defaultOutputColumn
            outputColumn = len( mySpreadsheet.getRow(1) )

    # Get the untranslated lines, the translated lines, and related metadata.
    untranslatedLines = mySpreadsheet.getColumn( 'A' )
    speakerList = mySpreadsheet.getColumn( 'B' )
    metadataColumn = mySpreadsheet.getColumn( 'C' )
    translatedLines = mySpreadsheet.getColumn( outputColumn )

    # Remove headers.
    # https://www.w3schools.com/python/ref_list_pop.asp
    untranslatedLines.pop( 0 )
    speakerList.pop( 0 )
    metadataColumn.pop( 0 )
    translatedLines.pop( 0 )

    # The input file is actually a .txt file so read it in and convert it into a list of strings.
    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read().splitlines()

    # Spreadsheets start with row 1 but row 1 contains headers. Therefore, row 2 is the first row with valid data normally. However, the 'correct' row number has all the data put into a series lists for processing. Lists begin their indexes at 0, so decrement 1 in order to get the correct 2nd item in the spreadsheet. Decrement by 1 again since the headers were removed.
    currentRowInSpreadsheet = 2 - 1 - 1
    nextTranslatedLine = None

    for currentLineNumber,currentLine in enumerate( inputFileContents ):
        if nextTranslatedLine == None: 
            if currentRowInSpreadsheet >= len( untranslatedLines ):
                break
            nextTranslatedLine = metadataColumn[currentRowInSpreadsheet]

        # Keep going until the next line that has a translation in the spreadsheet.
        if currentLineNumber < int( nextTranslatedLine ):
            continue

        # Do some sanity checks now.
        try:
            assert( currentLineNumber == nextTranslatedLine )
            # Sanity check that the line has the untranslated contents.
            assert( currentLine.find( untranslatedLines[ currentRowInSpreadsheet ] ) != -1 )
        except:
            print( 'currentLine=', currentLine)
            print( 'currentLineNumber=', currentLineNumber)
            print( 'currentRowInSpreadsheet=', currentRowInSpreadsheet)
            print( 'nextTranslatedLine=', nextTranslatedLine)
            print( 'metadataFromFile=', metadataFromFile )
            raise

        currentSpeakerForLineFromFile = None

        # Sanity check the speaker name, if any. The only way to do this is to use the characterDictionary for the mapping of untranslated to translated names.
        if currentSpeakerForLineFromFile != None:
            # then assert that the speaker from the spreadsheet is not None.
            assert( speakerList[ currentRowInSpreadsheet ] != None )
            if isinstance( characterDictionary, dict) == True:
                if speakerList[ currentRowInSpreadsheet ].strip() in characterDictionary.values():
                    untranslatedSpeakerName=None
                    for key,value in characterDictionary.items():
                        # Retrieve the speaker name from the current row in the spreadsheet and reverse translate it back to the untranslated name
                        if speakerList[currentRowInSpreadsheet].strip() == value:
                            untranslatedSpeakerName = key
                            break
                    # assert the un-translated name from speakerList[currentRowInSpreadsheet] is the same as the currentSpeaker for the current line from the input file in order to validate the translated speaker entry: speakerList[currentRowInSpreadsheet] 
                    # assert ( currentSpeakerForLineFromFile.find( untranslatedSpeakerName )  != -1 ) # Which of these are better logic?
                    #assert( untranslatedSpeakerName == currentSpeakerForLineFromFile.strip() ) # The intent is more clear here.
                    try:
                        assert( untranslatedSpeakerName == currentSpeakerForLineFromFile.strip() ) # The intent is more clear here.
                    except:
                        #Sometimes, a certain name or phrase will be translated from the source language into the target language as a duplicate. Like 少年 and 男の子 both getting translated to "Boy". When sanity checking that, the source will not match since 男の子 will be checked against 少年. When that happens, if the first entry in the character dictionary failed, then try to validate that by using the last name that appears in the dictionary. Lazy, but should work as long as there is no more than one duplicate entry. The proper way is to check if any entry matches, which is more complicated than copy/pasting existing code.
                        try:
                            for key,value in characterDictionary.items():
                                # Retrieve the speaker name from the current row in the spreadsheet and reverse translate it back to the untranslated name
                                if speakerList[currentRowInSpreadsheet].strip() == value:
                                    untranslatedSpeakerName=key
                            assert( untranslatedSpeakerName == currentSpeakerForLineFromFile.strip() ) # The intent is more clear here.
                        except:
                            # if that still does not work, then print debug information and quit.
                            print( 'nextTranslatedLine=', nextTranslatedLine)
                            print( 'currentLine=', currentLine)
                            print( 'currentLineNumber=', currentLineNumber)
                            print( 'metadataFromFile=', metadataFromFile )
                            print( 'metadataFromSpreadsheet=', metadataFromSpreadsheet)
                            print( 'untranslatedSpeakerName=', untranslatedSpeakerName)
                            print( 'currentSpeakerForLineFromFile.strip()=', currentSpeakerForLineFromFile.strip())
                            raise
                #elif currentSpeakerForLineFromFile not in characterDictionary.values():
                else:
                    print( ( 'Warning: The character dictionary does not have the name \''+ speakerList[currentRowInSpreadsheet] + '\' at row number '+ str(currentRowInSpreadsheet+1) + '.' ).encode(consoleEncoding) )

        # Fix a few more one off things in the post-translated data. Sort of like post-processing? Word wrap, if any, should be done here.
        # Word wrap should remove any '\n', characters and insert r'\n' where needed. For some engines, literal newlines are written as r'\r\n', r'\N', <br> or similar dataset specific escape characters.
        # This replaces all non-valid cp932 characters with empty strings. There is a warning printed about this if it happens.
        #tempTranslatedData = functions.normalizeEncoding( translatedLines[ currentRowInSpreadsheet ], defaultTargetEncoding )

        # The line number was validated. The metadata was validated. The speaker, if any, was validated. The translated value is in the spreadsheet exists, probably. Now it is time to replace the line in the file with the translated contents.

        inputFileContents[currentLineNumber] = inputFileContents[currentLineNumber].replace(untranslatedLines[ currentRowInSpreadsheet ], translatedLines[currentRowInSpreadsheet])

        # Clear variables.
        nextTranslatedLine = None
        currentSpeakerForLineFromFile = None

        # Move on to next entry.
        currentRowInSpreadsheet+=1

    # Once inputFileContents is fully updated, just send it back to the calling function so it can be written out to disk.
    # The code that calls this function will check if the return type is a chocolate.Strawberry(), a string, or a list and handle writing out the file appropriately, so there is no need to do anything more here.
    return inputFileContents

