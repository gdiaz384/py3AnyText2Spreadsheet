#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description: This file parses a ddsystem.txt file, https://vndb.org/r?f=fwDDSystem- , as input and returns a chocolate.Strawberry(). It also takes a chocolate.Strawberry() and outputs the hopefully translated contents back into the file.

# API concept art:
# input() processes raw data and converts it to a spreadsheet for further processing. output() takes data from a processed spreadsheet and inserts it back into the original file. While in memory, that spreadsheet is implemented as a Strawberry() class found in the chocolate.py library.

Usage: This file is meant to be run as py3Any2Spreadsheet('templates\JSON.VNTranslationTools.py')

Within py3Any2Spreadsheet.py, it can be run as:
parsingScript='templates\JSON.VNTranslationTools.py'
# import parsingScript  # But with fancier/messier import syntax.

Algorithim:
skip empty lines
skip lines that start with ◇
Assert the line starts with ◆
There is always an address/code in between two ◆. Store it as metadata along with the line number.
Ignore lines where the the last character is a number.
Ignore lines where the 2nd to last character is a number.
Ignore lines if the last three characters end in "dat" after converting it to lowercase.
Next, process the string.
If the line starts with \n then ignore the first character.
If the line has a new line character, right next to an "「" then assume the part before that is the speaker's name => "\n「" Do not store the new line character.
If the line ends in _ then ignore it the _ at the end, up to a max of 3 characters/reptitions.

License: See main program.
"""
__version__ = '2024.05.30'


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
# Old API:
#def input( fileNameWithPath, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, characterDictionary=None):
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

    # The input file is actually a .txt file so read it in and convert it into a list of strings.
    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read().splitlines()

    speakerNameDelimiterList=[ '「', '『', '（' ]
    temporaryList=[]
    for currentLineNumber,line in enumerate(inputFileContents):
        # Skip empty lines.
        if line.strip () == '':
            continue
        line=line.strip()

        # Skip lines that start with ◇.
        if line[0:1]=='◇':
            continue

        # Assert the line starts with ◆.
        assert( line[0:1]=='◆' )

        # These appear to be untranslatable lines because they describe characters, their outfits, expressions and use @ and _ syntaxes.
        if line.find( '@' ) != -1:
            continue

        if line.find( '_' ) != -1:
            continue

        # Ignore lines where the the last character is a number.
        if line[-1:].isdigit() == True:
            continue

        # Ignore lines where the 2nd to last character is a number.
        if line[-2:-1].isdigit() == True:
            continue

        # Ignore lines where the 3rd to last character is a number if the 2nd to last is also an underscore.
#        if ( line[-3:-2].isdigit() == True ) and ( line[-2:-1] == '_' ):
#            continue

        # Ignore lines if the last three characters end in "dat" after converting it to lowercase.
        if line[-3:].lower() == 'dat':
            continue

        #Next, process the string.
        speaker = None
        #codeForMetadata = None

        # There is always an address/code in between two ◆. Store it as metadata along with the line number.
        codeForMetadata = line[ 1: line.rfind( '◆' ) ]

        # The code has been processed, so remove it now.
        line=line[1:].partition('◆')[2]

        # One off fixes.
#        if ( line.startswith('bg_') ) or ( line =='black' ) or ( line.startswith('ev_') ):
        if line =='black': # What does this mean?
            continue

        # if the line starts with \n then ignore the first character.
        if line[ :2 ] == r'\n':
            line=line[ 2: ]

        # if the line has a new line character, right next to an "「" then it might be the part before that is the speaker's name => "\n「" Do not store the new line character.

        if line.find(r'\n') != -1:
            index=line.find(r'\n')
            # if the first character after \n is '「'
            if line[index+2:index+3] in speakerNameDelimiterList:
                speaker=line.partition( r'\n' )[0].strip()
                line=line.partition( r'\n' )[2].strip()

            # Old code.
#            if line.find(index+2:index+3) == '「':
#                speaker=line.partition( r'\n' )[0].strip()
#                line=line.partition( r'\n' )[2].strip()
#            if line.find(index+2:index+3) == '（':
#                speaker=line.partition( r'\n' )[0].strip()
#                line=line.partition( r'\n' )[2].strip()
#            if line.find(index+2:index+3) == '『':
#                speaker=line.partition( r'\n' )[0].strip()
#                line=line.partition( r'\n' )[2].strip()

        if ( speaker != None ) and ( characterDictionary != None ):
            if speaker in characterDictionary:
                speaker=characterDictionary[speaker]
            else:
                print( 'Warning: Speaker encountered that was not in character dictionary at line', currentLineNumber)

        # if the line ends in _ then ignore it the _ at the end, up to a max of 3 characters/reptitions.
        # This is probably not necessary since lines with _ at the end are assumed to be code.
        for i in range(3):
            if line[-1:] == '_':
                line=line[:-1]

        # Whatever is left is the contents of the line. Append everything found so far to temporaryList.
        temporaryList.append( [ line, speaker, currentLineNumber, codeForMetadata ] )

    # Create a chocolate.Strawberry().
    mySpreadsheet=chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker','metadata' ] )

    # Add data entries.
    for entry in temporaryList:
        mySpreadsheet.appendRow( [ entry[0], entry[1], str( entry[2] ) + metadataDelimiter + entry[3] ])

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
    print( ('Warning: Output changed from to: \'' + tempString + '\'').encode(consoleEncoding) )
    return tempString


# This function takes mySpreadsheet as a chocolate.Strawberry() and inserts the contents back to fileNameWithPath.
# Old API:
#def output(fileNameWithPath, mySpreadsheet, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, characterDictionary=None):
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
