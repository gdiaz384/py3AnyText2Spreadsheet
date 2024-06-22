#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
This script parses subrip.srt files, http://en.wikipedia.org/wiki/SubRip , and returns a spreadsheet.
It also takes a spreadsheet and outputs the hopefully translated contents back into the file.
That spreadsheet is implemented as a Strawberry() class found in the chocolate.py library. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

API concept art:
input() processes raw data and converts it to a spreadsheet for further processing.
output() takes data from a processed spreadsheet and inserts it back into the original file.

CLI Usage:
python py3Any2Spreadsheet.py --help
python py3Any2Spreadsheet.py input subripFile.srt srt.parsingTemplate.py
python py3Any2Spreadsheet.py output subripFile.srt srt.parsingTemplate.py --spreadsheet subripFile.srt.xlsx

py3Any2Spreadsheet.py Usage:
import 'resources\templates\srt.subrip.parsingTemplate.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Algorithim:
SRTs do not usually have speakers, so just extract contents and the entry # as metadata.
Sometimes multiple lines per entry represent different speakers if each line is prepended by '- ', so fudge the speaker column if there are multiple speakers. 
SRTs have some light formatting as well, so use some .SRT specific quirks like {} always being at the start, '<>' always existing in pairs as '<>data<>', to strip that unwanted formatting information and re-insert it based upon original lines after translation.

External Dependencies:
This file uses the pysrt library: https://pypi.org/project/pysrt/
It must be installed using pip as: pip install pysrt
Developed using pysrt==1.1.2
Tried the 'srt' library, but it does not work -at all- when used with actual data.

Licenses:
pysrt is GPLv3: https://github.com/byroot/pysrt/blob/master/LICENCE.txt
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
defaultTargetEncoding='cp932'
genericSpeakerName='speaker'

#https://docs.python.org/3.7/library/codecs.html#standard-encodings
inputErrorHandling='strict'
#inputErrorHandling='backslashreplace'
#outputErrorHandling='namereplace'  #This is set dynamically below.


# import stuff
import sys                                                         # Used to sys.exit() in case of an error and to check system version.
#import os                                                           # Required for srt.compose.
#import json

import resources.chocolate as chocolate            # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.
# To import directly:
# import sys
# import pathlib
# sys.path.append( str( pathlib.Path('C:/resources/chocolate.py').resolve().parent) )
# import chocolate

import pysrt
#import srt
#import srt_tools
#import srt_tools.utils

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
[ '「勉強ねぇ」', None, 'p-009_body p_288' ]  # .ebook ; .ebook ; Column C is the filename_css search tag_entry number, with _ being used as a delimter.
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

    # The input file is actually an .srt txt file so read it in as-is without convert it into a list of strings.
#    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
#        inputFileContents = myFileHandle.read() #.splitlines()
    # Update, pysrt has a convinence function.
    subtitleFile = pysrt.open(fileNameWithPath, encoding=fileEncoding)

    temporaryList=[]
    for counter,subtitle in enumerate( subtitleFile ):
        formattingRemoved=False
        #print(counter)
        #print(subtitle.text)
        if ( subtitle.text.find('{') != -1 ) or ( subtitle.text.find('<') != -1 ):
            tempSubs = stripFormatting( subtitle.text )
            formattingRemoved=True
        else:
            tempSubs = subtitle.text
        if ( tempSubs.find('\n') != -1 ) and ( tempSubs[:1] == '-' ) and ( tempSubs[1:].find( '-' ) != -1 ):
            # Then is is probably a line with multiple speakers.
            # Assume that this only has to deal with the simple case of each line being prepended by '- ' with entries lasting one line each.
            # while loops are always mildly terrifying.
            tempCounter = 0
            while ( tempSubs[:1] == '-' ):
                if tempSubs.find('\n') != -1:
                    temporaryList.append([ tempSubs[1: tempSubs.find('\n') ].strip(), genericSpeakerName+str(tempCounter), counter, formattingRemoved ])
                else:
                    temporaryList.append([ tempSubs[1: ].strip(), genericSpeakerName+str(tempCounter), counter, formattingRemoved ])
                # If there are no new lines, then this will return an empty string.
                tempSubs=tempSubs.partition('\n')[2].strip()
                tempCounter += 1
                if tempCounter > 10:
                    print('Unspecified error at sub entry ' + str(counter) + '.')
                    break
        else:
            # list.append([ string, speakerName, currentSubEntry, formattingRemovedOrNot ])
            temporaryList.append([ tempSubs, None, counter, formattingRemoved ])

    # Create a chocolate.Strawberry().
    mySpreadsheet=chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker', 'metadata' ] )

    # Add data entries and format metadata column appropriately.
    for entry in temporaryList:
        # list.append([ string, speakerName, currentSubEntry_formattingRemovedOrNot ])
        mySpreadsheet.appendRow( [ entry[0], entry[1], str( entry[2] ) + metadataDelimiter + str( entry[3] ) ])

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

    # The input file is actually a .txt file so read it in and convert it into a list of strings.
#    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
#        inputFileContents = myFileHandle.read().splitlines()
    subtitleFile = pysrt.open(fileNameWithPath, encoding=fileEncoding)

    # Get the untranslated lines, the translated lines, and related metadata.
    untranslatedLines = mySpreadsheet.getColumn( 'A' )
    translatedLines = mySpreadsheet.getColumn( outputColumn )
    speakerList = mySpreadsheet.getColumn( 'B' )
    metadataColumn = mySpreadsheet.getColumn( 'C' )

    # Spreadsheets start with row 1 but row 1 contains headers. Therefore, row 2 is the first row with valid data. However, the 'correct' row number has all the data put into a series lists for processing. Lists begin their indexes at 0, so decrement 1 in order to get the correct 2nd item in the spreadsheet.
    currentRow=2 - 1
    nextTranslatedLine=None
    #metadataFromSpreadsheet=None
    #hasEmptyLineAtTheStartOfTheSecondPart=False

    # the srt entries start at 1, but currentSubtitleCounter starts at 0, therefore, currentSubtitleCounter+1 ==  srt entry # in spreadsheet. The value for srt entry number in spreadsheet can be obtained from metadataColumn.partition(metadataDelimiter)[0]
    for currentSubtitleCounter,currentSubtitleObjectRaw in enumerate(subtitleFile):
        # TODO: Put more assertions everywhere to spot errors easier.
        currentSpeaker=speakerList[ currentRow ]
        currentSRTEntryNumberTakenFromSpreadsheet=int( metadataColumn[currentRow].partition( metadataDelimiter )[0] )
        currentLineHasFormatting=metadataColumn[currentRow].partition( metadataDelimiter )[2]
        if currentLineHasFormatting.lower() == 'true':
            currentLineHasFormatting=True
        else:
            currentLineHasFormatting=False

        # if there is no speaker for the current row, then set the currentTranslatedLine and move on to formatting.
        if currentSpeaker==None:
            numberOfEntriesTotalForCurrentSRTEntry=1
            currentTranslatedLine=translatedLines[currentRow].strip()

        #elif there is a speaker in the currentRow, then lines need to be merged. They were split for translation, but now they need '- ' prepended before each line and \n between each line (but not at the end).
        else:
            #tempString = '- ' + translatedLines[currentRow].strip() + '\n'
            # Get the data for the next entry and the entry after that until the next line is reached. Next line being reached means would call an index > len( metadataColumn ) value for that cell (or that cell is None?).
            # Once it no longer matches, that row -1 is the total range of data to pull.
            # srt does not support speakers, so just ignore the data in the speaker column, but merge the lines from the range using - and \n.
            tempSearchRange = currentRow
            counter=0
            while True:
                tempSearchRange += 1
                # Special failure case.
                if tempSearchRange > len( metadataColumn ):
                    break
                tempSRTNumber=int( metadataColumn[ tempSearchRange ].partition(metadataDelimiter)[0] )
                if tempSRTNumber > currentSRTEntryNumberTakenFromSpreadsheet:
                    break
                counter+=1
                if counter > 10:
                    print('Unspecified error.')
                    sys.exit(1)
            numberOfEntriesTotalForCurrentSRTEntry = tempSearchRange - currentRow
            #print( 'numberOfEntriesTotalForCurrentSRTEntry=', numberOfEntriesTotalForCurrentSRTEntry )
            tempString=''
            for i in range( numberOfEntriesTotalForCurrentSRTEntry ):
                tempString = tempString + '- ' + translatedLines[ currentRow + i ].strip() + '\n'
            # This removes the last trailing \n.
            currentTranslatedLine=tempString.strip()

        # Apply word wrapping.
        #TODO: Put stuff here.
        # formattedLine=applyWordWrap(currentTranslatedLine)

        # Then check if there was any formatting in the original line.
        currentTranslatedLine=inferFormatting(currentSubtitleObjectRaw.text, currentTranslatedLine)

        #output as-is.
        currentSubtitleObjectRaw.text=currentTranslatedLine

        # Go to next line.
        currentRow=currentRow + numberOfEntriesTotalForCurrentSRTEntry

    # Once the srt object is fully updated, send it back to the calling function so it can be written out to disk.
    tempString=''
    # at the very end, go through each object in the subtitleFile and ask it to convert itself to a string.
    for currentSubtitleObjectRaw in subtitleFile:
        # Then take each string and stitch them all together (without appending \n).
        # Well, not appending new lines did not work, so just append them now.
        tempString=tempString + str(currentSubtitleObjectRaw).strip() + '\n' + '\n'
    # Once stitched together, call strip() to remove excessive new lines before the string and \n\n after.
    # Append exactly 1 new line at the end for posix reasons, and then return that string to be written out as a plain text file.
    tempString=tempString.strip()+'\n'

    # The code that calls this function will check if the return type is a chocolate.Strawberry(), a string, or a list and handle writing out the file appropriately, so there is no need to do anything more here.
    return tempString


# This stripFormatting() function leaves \n alone.
# Strips {} if they occur at the start of the string.
# strips <> if they occur at both the start and the end of the string.
def stripFormatting(string):
    if ( string[ 0:1 ] == '{' ) and ( string.find( '}' ) != -1 ):
        #index=string.find( '}' )
        #removeMe=string[ 0 : index+1 ]
        #string=string.replace( removeMe, '' ).strip()
        string=string.replace( string[ 0 : string.find( '}' )+1 ] , '' ).strip()

    if ( string.find( '<' ) != -1 ) and ( string.find( '>' ) != -1 ):
        counter=0
        while ( string.find( '<' ) != -1 ) and ( string.find( '>' ) != -1 ):
            #index1=string.find( '<' )
            #index2=string.find( '>' )
            #string=string[ index1+1 : index2+1 ]
            #removeMe=string[ string.find( '<' ) : string.find( '>' )+1 ]
            #string=string.replace( removeMe, '' ).strip()
            #print(string)
            string=string.replace( string[ string.find( '<' ) : string.find( '>' )+1 ] , '' ).strip()
            #print(string)
            counter+=1
            if counter > 10:
                print( ('error processing string: '+ string).encode(consoleEncoding) )
                print('removeMe='+ string[ string.find( '<' ) : string.find( '>' )+1 ])
                print('string.find( '<' )=', string.find( '<' ) )
                print('string.find( '>' )=' + str( string.find( '>' ) ) )
                print('counter=' + str( counter ) )
                break
        #print('string=',string)
    return string


# This function takes the original untranslated string and the translated string and returns the translated string with the formatting present in the untranslated string.
# translatedString should be after multiple speakers are merged.
def inferFormatting(originalStringFromSRT, translatedString):
    if ( originalStringFromSRT.find( '{' ) == -1 ) and ( originalStringFromSRT.find( '<' ) == -1 ):
        return translatedString
    #else there are { or < that need to be inserted.

    # check if start has {}
    if originalStringFromSRT.startswith( '{' ) and ( originalStringFromSRT.find( '}' ) != -1 ):
        #index=originalStringFromSRT.find( '}' )
        #translatedString=originalStringFromSRT[ 0 : index + 1] + translatedString
        translatedString=originalStringFromSRT[ 0 : originalStringFromSRT.find( '}' ) + 1] + translatedString

    if originalStringFromSRT.find( '<' ) == -1:
        return translatedString
    #print('pie')

    # check if there are <> anywhere
    numberOfPairs=0
    tempSearchString=originalStringFromSRT
    while ( tempSearchString.find( '<' ) != -1 ) and ( tempSearchString.find( '>' ) != -1 ):
        numberOfPairs+=1
        tempSearchString=tempSearchString.partition('>')[2]

    #print( 'numberOfPairs=', numberOfPairs )

    if numberOfPairs != 2:
        print( ('Warning: Unsupported number of <tag> formatting ' + str(numberOfPairs) + ' for line: ' + originalStringFromSRT).encode(consoleEncoding) )
    else:
        # if there are two pairs, then assume one pair goes at the start and the other goes at the end.
        dataForFirstPair=originalStringFromSRT[ originalStringFromSRT.find( '<' ) : originalStringFromSRT.find( '>' ) + 1]
        tempSearchString=originalStringFromSRT.partition('>')[2]
        dataForSecondPair=tempSearchString[ tempSearchString.find( '<' ) : tempSearchString.find( '>' ) + 1]
        translatedString=dataForFirstPair + translatedString + dataForSecondPair

        #print('dataForFirstPair=', dataForFirstPair)
        #print('dataForSecondPair=', dataForSecondPair)
        #print('tempSearchString=', tempSearchString)
        #print('translatedString=', translatedString)

    return translatedString
