#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description: This file parses a ddsystem.txt file, https://vndb.org/r?f=fwDDSystem- , as input and returns a chocolate.Strawberry(). It also takes a chocolate.Strawberry() and outputs the hopefully translated contents back into the file. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

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
# New API:
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
        # Update: It might be that none of the code lines have \n, and every dialogue line has \n. Is that correct, or are there any counter examples?
#        if line.find( '@' ) != -1:
#            continue

#        if line.find( '_' ) != -1:
#            continue

        # Ignore lines where the the last character is a number.
#        if line[-1:].isdigit() == True:
#            continue

        # Ignore lines where the 2nd to last character is a number.
#        if line[-2:-1].isdigit() == True:
#            continue

        # Ignore lines where the 3rd to last character is a number if the 2nd to last is also an underscore.
#        if ( line[-3:-2].isdigit() == True ) and ( line[-2:-1] == '_' ):
#            continue

        # Ignore lines if the last three characters end in "dat" after converting it to lowercase.
#        if line[-3:].lower() == 'dat':
#            continue

        #Next, process the string.
        speaker = None
        #codeForMetadata = None

        # There is always an address/code in between two ◆. Store it as metadata along with the line number.
        codeForMetadata = line[ 1: line.rfind( '◆' ) ]

        # The address/code has been processed, so remove it now.
        line=line[1:].partition('◆')[2]

        # One off fixes.
#        if ( line.startswith('bg_') ) or ( line =='black' ) or ( line.startswith('ev_') ):
#        if line =='black': # What does this mean?
#            continue

        # if the line starts with \n then ignore the first character and set the line equal the the rest of the line.
        if line[ :2 ] == r'\n':
            line=line[ 2: ].strip() #Added .strip() to ensure no whitespace.
            #speaker=None
        else:
            # if the line has a new line character, right next to an "「" then it might be the part before that is the speaker's name => "\n「" Do not store the new line character.
            #if line.find(r'\n') != -1:
            #index=line.find(r'\n')
            # if the first character after \n is '「'
            #if line[index+2:index+3] in speakerNameDelimiterList:
            speaker=line.partition( r'\n' )[0].strip()
            line=line.partition( r'\n' )[2].strip()

        if ( speaker != None ) and ( characterDictionary != None ):
            if speaker in characterDictionary:
                speaker=characterDictionary[speaker]
            else:
                print( 'Warning: Speaker encountered that was not in character dictionary at line', currentLineNumber)

        # if the line ends in _ then ignore it the _ at the end, up to a max of 3 characters/reptitions.
        # This is probably not necessary since lines with _ at the end are assumed to be code.
#        for i in range(3):
#            if line[-1:] == '_':
#                line=line[:-1]

        # Whatever is left is the contents of the line. Append everything found so far to temporaryList.
        temporaryList.append( [ line, speaker, currentLineNumber, codeForMetadata ] )

    # Create a chocolate.Strawberry().
    mySpreadsheet=chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker','metadata' ] )

    # Add data entries and format metadata column appropriately.
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
# New API:
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
                # This sets outputColumn to a string like 'D'. If the search string was not found, then the function returns None.
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

    # The input file is actually a .txt file so read it in and convert it into a list of strings.
    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read().splitlines()

    # Get the untranslated lines, the translated lines, and related metadata.
    untranslatedLines = mySpreadsheet.getColumn( 'A' )
    translatedLines = mySpreadsheet.getColumn( outputColumn )
    speakerListAfterTranslation = mySpreadsheet.getColumn( 'B' )
    metadataColumnNew = mySpreadsheet.getColumn( 'C' )

    # Spreadsheets start with row 1 but row 1 contains headers. Therefore, row 2 is the first row with valid data. However, the 'correct' row number has all the data put into a series lists for processing. Lists begin their indexes at 0, so decrement 1 in order to get the correct 2nd item in the spreadsheet.
    currentRow=2 - 1
    nextTranslatedLine=None
    #metadataFromSpreadsheet=None
    #hasEmptyLineAtTheStartOfTheSecondPart=False

    for currentLineNumber,currentLine in enumerate(inputFileContents):
        if nextTranslatedLine == None:
            nextTranslatedLine=metadataColumnNew[currentRow].partition(metadataDelimiter)[0]
            metadataFromSpreadsheet=metadataColumnNew[currentRow].partition(metadataDelimiter)[2]
            #currentSpeakerForLineFromFile=None
            #hasEmptyLineAtTheStartOfTheSecondPart=False

        # Keep going until the next line that has a translation in the spreadsheet.
        if currentLineNumber < nextTranslatedLine:
            continue

        # Do a sanity check on the metadata now.
        # There is always an address/code in between two ◆. Store it as metadata for the current line.
        metadataFromFile = currentLine[ 1: currentLine.rfind( '◆' ) ]
        assert( metadataFromFile == metadataFromSpreadsheet )

        # The code has been processed, so get the rest of the line now.
        secondPartOfLineRaw=currentLine[1:].partition('◆')[2]

        # This might be a mistake. If there is a \n in the line, odds are that before it is the speaker name, but a \n at the start might mean a deliberately empty speaker name. A second \n means a line break in the dialogue script (untested). Therefore, it might be required that every dialogue line have a \n. Are there any counter examples? # Update: That is exactly what it means, probably. No counter examples were located.
        secondPartOfLine=None
        # if the line starts with \n then save that information, and then continue processing the string.
        if secondPartOfLineRaw[ :2 ] == r'\n':
            currentSpeakerForLineFromFile=None
            secondPartOfLine=secondPartOfLineRaw[ 2: ]
        else:
            #secondPartOfLine=secondPartOfLineRaw
            # if the line has a new line character, right next to an "「" or similar limited characters, then the part before that might be the speaker's name. syntax example: "\n「" Do not strip whitespace.
            if secondPartOfLineRaw.find(r'\n') == -1:
                print( 'Unspecified error parsing data.' )
                sys.exit( 1 )
            else:
                index=secondPartOfLineRaw.find(r'\n')
                # if the first character after \n is '「'
                #if secondPartOfLineRaw[index+2:index+3] in speakerNameDelimiterList:
                currentSpeakerForLineFromFile=secondPartOfLineRaw.partition( r'\n' )[0]
                #speakerDelimiter=r'\n'
                secondPartOfLine=secondPartOfLineRaw.partition( r'\n' )[2]

        # Sanity check that the line has the untranslated contents.
        assert( secondPartOfLine.find( untranslatedLines[currentRow] ) != -1 )

        # Sanity check the speaker name, if any. The only way to do this is to use the characterDictionary for the mapping of untranslated to translated names.
        if currentSpeakerForLineFromFile != None:
            # then assert that the speaker from the spreadsheet is not None.
            assert( speakerListAfterTranslation[currentRow] != None )
            if isinstance( characterDictionary, dict) == True:
                if speakerListAfterTranslation[currentRow].strip() in characterDictionary.values():
                    untranslatedSpeakerName=None
                    for key,value in characterDictionary.items():
                        # Retrieve the speaker name from the current row in the spreadsheet and reverse translate it back to the untranslated name
                        if speakerListAfterTranslation[currentRow].strip() == value:
                            untranslatedSpeakerName=key
                            break
                    # assert the un-translated name from speakerListAfterTranslation[currentRow] is the same as the currentSpeaker for the current line from the input file in order to validate the translated speaker entry: speakerListAfterTranslation[currentRow] 
                    # assert ( currentSpeakerForLineFromFile.find( untranslatedSpeakerName )  != -1 ) # Which of these are better logic?
                    assert( untranslatedSpeakerName == currentSpeakerForLineFromFile.strip() ) # The intent is more clear here.
                #elif currentSpeakerForLineFromFile not in characterDictionary.values():
                else:
                    print( ( 'Warning: The character dictionary does not have the name \''+ speakerListAfterTranslation[currentRow] + '\' at row number '+ str(currentRow+1) + '.' ).encode(consoleEncoding) )
        #elif currentSpeakerForLineFromFile == None:
#        else:
            # Change from None to empty string to simplify the replacement logic later. #Incorrect. The name needs to come from speakerListAfterTranslation[currentRow]
            #currentSpeakerForLineFromFile=''

        # Fix a few more one off things in the post-translated data. Sort of like post-processing? Word wrap, if any, should be done here.
        # This replaces all non-valid cp932 characters with empty strings. There is a warning printed about this if it happens.
        tempTranslatedData=fixString(translatedLines[currentRow], defaultTargetEncoding)

        # The line number was validated. The metadata was validated. The speaker, if any, was validated. The translated value is in the spreadsheet is exists, probably. Now it is time to rebuild the string from scratch and replace the line in the file with this new string.

        # How it gets built differs depending upon if there is a speaker or not. This could be updated to be simpler, but whatever.
        if speakerListAfterTranslation[currentRow] == None:
            newString='◆' + metadataFromFile + '◆' + r'\n' + tempTranslatedData
        else:
            newString='◆' + metadataFromFile + '◆' + speakerListAfterTranslation[currentRow] + r'\n' + tempTranslatedData

        # Update the input file and move on to the next entry.
        inputFileContents[currentLineNumber] = newString
        currentRow+=1

    # Once inputFileContents is fully updated, just send it back to the calling function so it can be written out to disk.
    # The calling function will check if the return type is a chocolate.Strawberry(), a string, or a list and handle writing out the file appropriately, so there is no need to do anything more here.
    return inputFileContents

