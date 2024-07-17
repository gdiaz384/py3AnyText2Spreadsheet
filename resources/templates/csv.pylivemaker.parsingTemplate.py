#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
This script parses livemaker.csv, https://pypi.org/project/pylivemaker/ , files and returns a spreadsheet.
It also takes a spreadsheet and outputs the hopefully translated contents back into the file.
That spreadsheet is implemented as a Strawberry() class found in the chocolate.py library. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

API concept art:
input() processes raw data and converts it to a spreadsheet for further processing.
output() takes data from a processed spreadsheet and inserts it back into the original file.

CLI Usage:
python py3Any2Spreadsheet.py --help
python py3Any2Spreadsheet.py input livemaker.csv csv.pylivemaker.parsingTemplate.py
python py3Any2Spreadsheet.py output livemaker.csv csv.pylivemaker.parsingTemplate.py --spreadsheet pylivemaker.csv.extracted.xlsx

py3Any2Spreadsheet.py Usage:
import 'resources\templates\csv.pylivemaker.parsingTemplate.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Links:
https://pylivemaker.readthedocs.io/en/latest/

Algorithim:
Take the 4th column and extract it into data/speaker pairs, or speaker if not available. Skip the header. Reinsert the same way.

License: See main program.
"""
__version__ = '2024.06.21'


# Set program defaults.
verbose = False
debug = False
consoleEncoding = 'utf-8'
defaultTextEncoding = 'utf-8'
defaultOutputColumn = 4
metadataDelimiter = '_'
defaultTargetEncoding = 'cp932'

#https://docs.python.org/3.7/library/codecs.html#standard-encodings
inputErrorHandling = 'strict'
#inputErrorHandling = 'backslashreplace'
#outputErrorHandling = 'namereplace'  #This is set dynamically below.


# import stuff.
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

    # Unpack some variables.
    if 'fileEncoding' in settings:
        fileEncoding = settings['fileEncoding']
    else:
        fileEncoding = defaultTextEncoding

    if 'parseSettingsDictionary' in settings:
        parseSettingsDictionary = settings['parseSettingsDictionary']
    else:
        parseSettingsDictionary = None

    # The input file is actually a .csv which is a type of spreadsheet already, so do the lazy thing and convert it into a chocolate.Strawberry()
    tempSpreadsheet = chocolate.Strawberry( fileNameWithPath, fileEncoding=fileEncoding, removeWhitespaceForCSV=True )

    rawDataColumn = tempSpreadsheet.getColumn( 'D' )
    metadataColumn = tempSpreadsheet.getColumn( 'A' )

    temporaryList = []
    for counter,cell in enumerate( rawDataColumn ):
        if counter == 0:
            continue

        tempData = None
        tempSpeaker = None

        if cell.find('「') == -1:
            tempData=cell.strip()
        elif cell.find('「') == 0:
            tempData=cell.strip()
        else:
            # Then assume a speaker is in the cell and try to extract it.
            tempSpeaker = cell.partition( '「' )[ 0 ].strip()
            tempData = '「' + cell.partition( '「' )[ 2 ].strip()

        if tempSpeaker == '':
            tempSpeaker = None

        # Fix characterName.
        if ( tempSpeaker != None ) and ( characterDictionary != None ):
            if tempSpeaker in characterDictionary:
                tempSpeaker = characterDictionary[ tempSpeaker ]
            else:
                print( 'Warning: Speaker not in characterDictionary was found at line', counter ) 

        temporaryList.append( [ tempData, tempSpeaker, metadataColumn[ counter ] ] )

    # Create a chocolate.Strawberry().
    mySpreadsheet = chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( [ 'rawText', 'speaker', 'metadata' ] )

    # Add data entries.
    for entry in temporaryList:
        mySpreadsheet.appendRow( [ entry[ 0 ], entry[ 1 ], entry[ 2 ] ])

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

    # The input file is actually a .csv which is a type of spreadsheet already, so do the lazy thing and convert it into a chocolate.Strawberry()
    tempSpreadsheet = chocolate.Strawberry( fileNameWithPath, fileEncoding=settings['fileEncoding'], removeWhitespaceForCSV=True )

    rawDataColumnOriginal = tempSpreadsheet.getColumn( 'D' )
    metadataColumnOriginal = tempSpreadsheet.getColumn( 'A' )

    translatedData = mySpreadsheet.getColumn( outputColumn )
    speakerDataFromNew = mySpreadsheet.getColumn( 'B' )
    metadataColumnNew = mySpreadsheet.getColumn( 'C' )

    assert ( len(rawDataColumnOriginal) == len(translatedData) )
    assert ( len(rawDataColumnOriginal) == len(speakerDataFromNew) )
    assert ( len(rawDataColumnOriginal) == len(metadataColumnNew) )

    # The metadataColumnOriginal[counter] must match metadataColumnNew[counter] for every entry after the first row or something is corrupt.
    # The output also needs to be formatted with new lines.
    # If the character name/speaker is present, it must be prepended before the first line of the dialogue. It should also be in the rawDataColumnOriginal at the start of the data in the untranslated form.
    # The translatedData does not have any new lines, so they need to be inserted manually. The number of lines should be taken from the rawDataColumnOriginal while considering whether or not the number of new lines includes a line for the speaker.
    # Sounds complicated. Do it later. Just do a blind replace for now and hope for the best.

    # Spreadsheet row numbers start with 1, not 0. Setting this to 0 will result in an off-by-1 error and have the target translations up-shifted by 1 cell.
    currentRow=1
    for counter,translationRaw in enumerate(translatedData):
        if counter == 0:
            currentRow+=1
            continue

        assert ( metadataColumnOriginal[counter] == metadataColumnNew[counter] )

        if speakerDataFromNew[counter] != None:
            untranslatedSpeakerName=None
            # Find original speaker name.
            # There is no way to verify the speaker is correct without characterDictionary because speakerDataFromNew[counter] presumably has the translated name and there is no way to get back the original string to compare with the start of rawDataColumnOriginal[counter]. That mapping of the post-translated name to the original name can only be provided by characterDictionary.
            if characterDictionary != None:
                if speakerDataFromNew[counter] in characterDictionary.values():
                    # Find the untranslated name.
                    for key,value in characterDictionary.items():
                        if value == speakerDataFromNew[counter]:
                            untranslatedSpeakerName=key
                            break
                    if untranslatedSpeakerName != None:
                        assert ( rawDataColumnOriginal[counter].strip().startswith(untranslatedSpeakerName) )

        # At this point, both the metadata and the speaker, if any, match. That should mean the data is safe to process.
        # Just do a blind replace for now and hope for the best.

        if speakerDataFromNew[ counter ] == None:
            tempTranslatedData = translationRaw
        else:
            tempTranslatedData = speakerDataFromNew[counter]+ '\n' + translationRaw

        # Fix a few more one off things.
        # This replaces all non-valid cp932 characters with empty strings. There is a warning printed about this if it happens.
        tempTranslatedData=functions.normalizeEncoding(tempTranslatedData, defaultTargetEncoding)

        # Now that the data has been processed, insert it into the spreadsheet in memory.
        # The correct location is the current row at Column E.
        tempSpreadsheet.setCellValue( 'E' + str(currentRow), tempTranslatedData )

        # Increment the current row, and then go to the next entry.
        currentRow += 1

    # Once tempSpreadsheet is fully updated, just send it back to the calling function so it can be written out to disk.
    # The calling function will check if it is a chocolate.Strawberry(), and if not, then assume it is a string that needs to be written out as-is so there is no need to handle converting it into a string here.
    return tempSpreadsheet

