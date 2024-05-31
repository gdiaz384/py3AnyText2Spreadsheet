#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description: This file parses a livemaker.CSV as input and returns a chocolate.Strawberry(). It also takes a chocolate.Strawberry() and outputs the hopefully translated contents back into the file.

# Concept art and description:
# input() processes raw data and converts it to a spreadsheet for further processing. output() takes data from a processed spreadsheet and inserts it back into the original file. While in memory, that spreadsheet is implemented as a Strawberry() class found in the chocolate.py library.

Usage: This file is meant to be run as py3Any2Spreadsheet('templates\JSON.VNTranslationTools.py')

Within py3Any2Spreadsheet.py, it can be run as:
parsingScript='templates\JSON.VNTranslationTools.py'
# import parsingScript  # But with fancier/messier import syntax.

License: See main program.
"""
__version__ = '2024.05.24'


# Set program defaults.
verbose=False
debug=False
consoleEncoding='utf-8'
defaultTextEncoding='utf-8'
defaultOutputColumn=4
metadataDelimiter='_'
defaultTargetEncoding='cp932'

#https://docs.python.org/3.7/library/codecs.html#standard-encodings
inputErrorHandling='strict'
#inputErrorHandling='backslashreplace'
#outputErrorHandling='namereplace'  #This is set dynamically below.


# import stuff
import sys                                                         # Used to sys.exit() in case of an error and to check system version.
import resources.chocolate as chocolate     # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.
import json

#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
sysVersion=int(sys.version_info[1])
if sysVersion >= 5:
    outputErrorHandling='namereplace'
elif sysVersion < 5:
    outputErrorHandling='backslashreplace'    
else:
    sys.exit('Unspecified error.'.encode(consoleEncoding))


# input() accepts:
# - 1) An inputFileName
# - 2) parseSettingsDictionary has whatever settings were defined in thisScript.ini available as a Python dictionary.
# - 3) The raw character encoding for the inputFileName (utf-8, shift-jis)
# - 4) An optional characterDictionary.csv as a Python dictionary. The first row is ignored when going from csv->Python.

# input() then needs to create a spreadsheet where the first row is column headers. The first column, column A, has the untranslated dialogue, the second column, Column B, has the speaker for each line, and the third column, Column C, has a string containing whatever metadata is appropriate/required to reinsert the strings and verify where they were extracted from.

# Usually metadata for Column C is 1) the line numbers the input is taken from, and possibly 2) total number of lines column A, rawText, represents if there was any line merging done like for kirikiri files. If dialogue was taken from more than one line, then the line number is the last line or whatever makes sense.

# output() accepts a spreadsheet as input, assumes the data has already been translated, and tries to insert the translated text back into the original file.

# parseSettingsDictionary is not necessarily needed for this parsing technique. All settings can be defined within this file or imported from parsingScript.ini
# characterDictionary may or may not exist, so set it to None by default.
def input( fileNameWithPath, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, characterDictionary=None):

    if debug == True:
        print( ( 'characterDictionary=' + str(characterDictionary) ).encode(consoleEncoding) )

    # The input file is actually a .csv which is a type of spreadsheet already, so do the lazy thing and convert it into a chocolate.Strawberry()
    tempSpreadsheet = chocolate.Strawberry( fileNameWithPath, fileEncoding=fileEncoding, removeWhitespaceForCSV=True )

    rawDataColumn=tempSpreadsheet.getColumn( 'D' )
    metadataColumn=tempSpreadsheet.getColumn( 'A' )

    temporaryList=[]
    for counter,cell in enumerate(rawDataColumn):
        if counter == 0:
            continue

        tempData=None
        tempSpeaker=None

        if cell.find('「') == -1:
            tempData=cell.strip()
        elif cell.find('「') == 0:
            tempData=cell.strip()
        else:
            # Then assume a speaker is in the cell and try to extract it.
            tempSpeaker=cell.partition('「')[0].strip()
            tempData='「'+cell.partition('「')[2].strip()

        if tempSpeaker == '':
            tempSpeaker=None

        # Fix characterName.
        if ( tempSpeaker != None ) and ( characterDictionary != None ):
            if tempSpeaker in characterDictionary:
                tempSpeaker=characterDictionary[tempSpeaker]
            else:
                print( 'Warning: Speaker not in characterDictionary was found at line', counter ) 

        temporaryList.append( [tempData, tempSpeaker, metadataColumn[counter] ] )

    # Create a chocolate.Strawberry().
    mySpreadsheet=chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker','metadata' ] )

    # Add data entries.
    for entry in temporaryList:
        mySpreadsheet.appendRow( [ entry[0], entry[1], entry[2] ])

    if debug == True:
        mySpreadsheet.printAllTheThings()

    return mySpreadsheet


def checkEncoding(string, encoding):
    try:
        string.encode(encoding)
        return True
    except UnicodeEncodeError:
        return False


def fixString(string, encoding):
    if checkEncoding(string, encoding) == True:
        return string
    # Okay, so, something messed up. What was it? Check character by character and klobber the offender.
    tempString=''
    for i in range( len(string) ):
        if checkEncoding( string[ i : i+1 ], encoding) == True:
            tempString=tempString+string[ i : i+1 ]
        else:
            print( ('Warning: ' + string[ i : i+1 ] + ' cannot be encoded to valid ' + encoding + '.' ).encode(consoleEncoding) )
    print( ('Warning: Output changed to: \'' + tempString + '\'').encode(consoleEncoding) )
    return tempString


# This function takes mySpreadsheet as a chocolate.Strawberry() and inserts the contents back to fileNameWithPath.
# exportToTextFile
#def output(fileNameWithPath, mySpreadsheet, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, characterDictionary=None):
def output( fileNameWithPath, mySpreadsheet, characterDictionary=None, settings={} ):

    assert isinstance(mySpreadsheet, chocolate.Strawberry)

    #outputColumn=None
    if 'outputColumn' in settings:
        if isinstance( settings[ 'outputColumn' ], int) == True:
            # This sets outputColumn to an integer like 4.
            outputColumn = settings[ 'outputColumn' ]
        elif isinstance( settings[ 'outputColumn' ], str) == True:
            if len(settings[ 'outputColumn' ]) == 1:
                # Then assume it is already valid as-is.
                outputColumn=settings[ 'outputColumn' ]
            else:
                # This sets outputColumn to a string like 'D' or None if the search string was not found.
                outputColumn=mySpreadsheet.searchHeaders( settings[ 'outputColumn' ] )
                if outputColumn == None:
                    try:
                        outputColumn=int(settings[ 'outputColumn' ])
                    except:
                        outputColumn=len( mySpreadsheet.getRow(1) )
                        print( ('Warning: Could not find column \'' + str( settings[ 'outputColumn' ] ) + '\' in spreadsheet. Using furthest right column value \'' + str(defaultOutputColumn) + ':'+ str( mySpreadsheet.getColumn(outputColumn)[0] ) + '\'' ).encode(consoleEncoding) )
        else:
            outputColumn=defaultOutputColumn
    #elif 'outputColumn' not in settings:
    else:
        outputColumn=defaultOutputColumn

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
        tempTranslatedData=fixString(tempTranslatedData, defaultTargetEncoding)

        # Now that the data has been processed, insert it into the spreadsheet in memory.
        # The correct location is the current row at Column E.
        tempSpreadsheet.setCellValue( 'E' + str(currentRow), tempTranslatedData )

        # Increment the current row, and then go to the next entry.
        currentRow += 1

    # Once tempSpreadsheet is fully updated, just send it back to the calling function so it can be written out to disk.
    # The calling function will check if it is a chocolate.Strawberry(), and if not, then assume it is a string that needs to be written out as-is so there is no need to handle converting it into a string here.
    return tempSpreadsheet

