#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
This script parses substation alpha (.ssa), advanced substation alpha (.ass) subtitle, https://wiki.videolan.org/SubStation_Alpha , and SubRip, http://en.wikipedia.org/wiki/SubRip , files and returns a spreadsheet.
There is also support for subrip, microdvd, and the other formats that are supported by the pysubs2 library.
It also takes a spreadsheet and outputs the hopefully translated contents back into the file.
That spreadsheet is implemented as a Strawberry() class found in the chocolate.py library. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

API concept art:
input() processes raw data and converts it to a spreadsheet for further processing.
output() takes data from a processed spreadsheet and inserts it back into the original file.

CLI Usage:
python py3Any2Spreadsheet.py --help
python py3Any2Spreadsheet.py input subtitles.ass ass.parsingTemplate.py
python py3Any2Spreadsheet.py output subtitles.ass ass.parsingTemplate.py --spreadsheet subtitles.ass.xlsx

py3Any2Spreadsheet.py Usage:
import 'resources\templates\ass.parsingTemplate.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Algorithim:
.ssa/.ass files do not usually have speakers, so just extract contents and the entry # as metadata.
.ssa/.ass files have extensive support for formatting, so use ass-tag-parser library to handle it.

External Dependencies:
This file uses the pysubs2 library: https://pypi.org/project/pysubs2/
It must be installed using pip as: pip install pysubs2
Developed using pip install pysubs2==1.6.1
Source code: https://github.com/tkarabela/pysubs2
This file uses the escapeStuff library: https://github.com/gdiaz384/py3AnyText2Spreadsheet/tree/main/resources
Developed using escapeStuff.py==2024.06.20

Licenses:
pysubs2: https://github.com/tkarabela/pysubs2
License for this file: See main program.
"""
__version__ = '2024.06.21'


# Set program defaults.
verbose=False
debug=False
consoleEncoding='utf-8'
defaultTextEncoding='utf-8'
defaultOutputColumn=4
metadataDelimiter='_'

#https://docs.python.org/3.7/library/codecs.html#standard-encodings
inputErrorHandling='strict'
#inputErrorHandling='backslashreplace'
#outputErrorHandling='namereplace'  #This is set dynamically below.


# Import stuff.
import sys                                                         # Used to sys.exit() in case of an error and to check system version.
import pathlib
# import os
# import pathlib
# import json

import resources.chocolate as chocolate            # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.
# To import directly:
# import sys
# import pathlib
# sys.path.append( str( pathlib.Path('C:/resources/chocolate.py').resolve().parent) )
# import chocolate

import resources.escapeText as escapeText     # Handles removing and reinserting tags, [], <>, {}, and one off escape sequences into strings.
# To import directly:
# import sys
# import pathlib
# sys.path.append( str( pathlib.Path('C:\\resources\\escapeText.py').resolve().parent) )
# import escapeText

import pysubs2

#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
sysVersion=int(sys.version_info[1])
if sysVersion >= 5:
    outputErrorHandling='namereplace'
elif sysVersion < 5:
    outputErrorHandling='backslashreplace'
else:
    sys.exit('Unspecified error.'.encode(consoleEncoding))


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
[ '「勉強ねぇ」', None, 'p-009_body p_288' ]  # .ebook ; Column C is the filename_css search tag_entry number, with _ being used as a delimter.
"""


def input( fileNameWithPath, characterDictionary=None, settings={} ):

    if debug == True:
        print( ( 'characterDictionary=' + str(characterDictionary) ).encode(consoleEncoding) )

    # Unpack some variables.
    if 'fileEncoding' in settings:
        fileEncoding=settings['fileEncoding']
    else:
        fileEncoding=defaultTextEncoding

    if 'parseSettingsDictionary' in settings:
        parseSettingsDictionary=settings['parseSettingsDictionary']
    else:
        parseSettingsDictionary=None

    # The input file is an .srt txt file. Instead of converting it into a list of strings, use pysubs2.load().
#    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
#        inputFileContents = myFileHandle.read() #.splitlines()
    # Update: pysubs2 has a convinence function.
    subtitles = pysubs2.load(fileNameWithPath, encoding=fileEncoding, errors=inputErrorHandling)

    #doesNotStartWith=[r'm ', r'b ']

    subtitlesList=[]
    for lineNumber,line in enumerate(subtitles):
        tempString=line.text.strip()
        if (tempString != '') and ( line.is_comment == False ) and ( line.is_drawing == False ):
            #print(tempString)
            tempLine=escapeText.EscapeText( tempString.strip(), escapeSequences=[ r'\N', '\u200a' ] ).text
            #print(type(tempLine))
            #escapedString=escapeText.EscapeText( tempString.strip(), escapeSequences=[ r'\N' ] ).text
            #subtitlesList.append( [ tempString.strip(), None, lineNumber ] )
            #validSubtitle=True
            #for item in doesNotStartWith:
            #    if tempLine.startswith( item ):
            #        validSubtitle=False
            #if ( validSubtitle == True ): # and ( len(tempLine) > 2):
            subtitlesList.append( [ tempLine , None, lineNumber ] )
        #else:
            #print(line.effect)
            #print(line.style)# .name .layer .type

        # Debug code.
        #if lineNumber > 20:
            #pass
            #sys.exit(1)
            #break

    # Debug code.
    #print(subtitlesList)
    #print(len(subtitlesList))
    #sys.exit(1)

    # Create a chocolate.Strawberry().
    mySpreadsheet=chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker', 'metadata' ] )

    # Add data entries and format metadata column appropriately.
    for entry in subtitlesList:
        # list.append([ string, speakerName, currentSubEntry_formattingRemovedOrNot ])
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
                # Then search for the string to see if it is the name of a header.
                # This sets outputColumn to a string like 'A' based upon the search value in settings['outputColumn']. Or if the search string was not found, then the function returns None.
                outputColumn = mySpreadsheet.searchHeaders( settings[ 'outputColumn' ] )
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
    translatedLines = mySpreadsheet.getColumn( outputColumn )
    speakerList = mySpreadsheet.getColumn( 'B' )
    metadataColumn = mySpreadsheet.getColumn( 'C' )

    # Remove header.
    # https://www.w3schools.com/python/ref_list_pop.asp
    untranslatedLines.pop( 0 )
    translatedLines.pop( 0 )
    speakerList.pop( 0 )
    metadataColumn.pop( 0 )

    # The input file is an .srt txt file. Instead of converting it into a list of strings, use pysubs2.load().
#    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
#        inputFileContents = myFileHandle.read().splitlines()
    subtitles = pysubs2.load( fileNameWithPath, encoding=fileEncoding, errors=inputErrorHandling )

    currentSpreadsheetRow = 0
    nextTranslatedLine = int( metadataColumn[ currentSpreadsheetRow ] )
    for subtitleCounter,line in enumerate( subtitles ):
        # if every entry from the spreadsheet has been processed and the only entries left are ones without translations, then stop processing the file.
        if subtitleCounter > nextTranslatedLine:
            break

        if subtitleCounter < nextTranslatedLine:
            continue

        tempLine = escapeText.EscapeText( line.text.strip(), escapeSequences=[ r'\N', '\u200a' ] )
        assert( untranslatedLines[ currentSpreadsheetRow ] == tempLine.text )

        escapedTranslatedLine = tempLine.getTranslatedStringWithEscapesInserted( translatedLines[currentSpreadsheetRow].strip() )

        if ( debug == True ) and ( nextTranslatedLine == 3477 ):
            print( 'nextTranslatedLine=', nextTranslatedLine )
            print( 'line.text=', line.text )
            print( 'tempLine.text=', tempLine.text )
            print( 'translatedline=', translatedLines[currentSpreadsheetRow] )
            print( 'escapedTranslatedLine=', escapedTranslatedLine )

        if translatedLines[currentSpreadsheetRow].strip() != tempLine.text:
            line.text=escapedTranslatedLine

        print( line.text )

        currentSpreadsheetRow += 1
        if currentSpreadsheetRow > len(translatedLines) -1:
            break
        nextTranslatedLine = int( metadataColumn[ currentSpreadsheetRow ] )

        # Debug code.
        #if subtitleCounter > 100:
        #    sys.exit(0)

    if translatedRawFileName in settings:
        outputFileName=settings['translatedRawFileName']
    else:
        outputFileName=fileNameWithPath + '.translated' + pathlib.Path(fileToTranslateFileName).suffix

    # Write out the subtitles natively.
    subtitles.save(outputFileName, encoding=fileEncoding)

    # The code that calls this function will check if the return type is a chocolate.Strawberry(), a string, or a list and handle writing out the file appropriately, so there is no need to do anything more here.
    # Since the file was saved already, just return none.
    return None
    #return tempString

