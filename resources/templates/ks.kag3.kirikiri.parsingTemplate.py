#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
This script parses KAG3.kirikri.ks files, https://kirikirikag.sourceforge.net/contents/index.html , and returns a spreadsheet.
Note that kirikiri, kirikiri2, and kirikiriZ should not be confused. KAG3 is typically used for kirikiri2. kirikri1 used KAG1 and 2. kirikiriZ typically use freemote.scn files.
It also takes a spreadsheet and outputs the hopefully translated contents back into the file.
That spreadsheet is implemented as a Strawberry() class found in the chocolate.py library. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

API concept art:
input() processes raw data and converts it to a spreadsheet for further processing.
output() takes data from a processed spreadsheet and inserts it back into the original file.

CLI Usage:
python py3Any2Spreadsheet.py --help
python py3Any2Spreadsheet.py input kirikiri.ks ks.kag3.kirikiri.parsingTemplate.py
python py3Any2Spreadsheet.py output kirikiri.ks ks.kag3.kirikiri.parsingTemplate.py --spreadsheet kirikiri.ks.xlsx

py3Any2Spreadsheet.py Usage:
import 'resources\templates\ks.kag3.kirikiri.parsingTemplate.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Algorithim:
Chaos.

License: See main program.
"""
__version__ = '2024.06.21'


# Set program defaults.
verbose = False
debug = False
consoleEncoding = 'utf-8'
defaultTextEncoding = 'utf-8'
metadataDelimiter = '_'
inputErrorHandling = 'strict'
#outputErrorHandling = 'namereplace'  #This is set dynamically below.


# import stuff
import sys                                                         # Used to sys.exit() in case of an error and to check system version.
import resources.chocolate as chocolate     # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.


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
        fileEncoding=settings['fileEncoding']
    else:
        fileEncoding=defaultTextEncoding

    if 'parseSettingsDictionary' in settings:
        parseSettingsDictionary=settings['parseSettingsDictionary']
    else:
        parseSettingsDictionary=None

    # parseSettingsDictionary must exist. It can either be defined within this file or imported.
    if parseSettingsDictionary == None:
        print( 'Error: parseSettingsDictionary must exist.' ) 
        sys.exit(1)
    if not isinstance(parseSettingsDictionary, dict):
        print( 'Error: parseSettingsDictionary is not a Python dictionary:' + str(type(parseSettingsDictionary)) )

    print( 'Reading: ' + fileNameWithPath )
    #The file has already been checked to exist and the encoding correctly determined, so just open it and read contents into a string. Then use that epicly long string for processing.
    # Alternative method: https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects
    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read().splitlines()

    #temporaryDict={}        #Dictionaries do not allow duplicates, so insert all entries into a dictionary first to de-duplicate entries, then read dictionary into first column (skip first line/row in target spreadsheet) Syntax:
    #thisdict.update({"x": "y"}) #add to/update dictionary
    #thisdict["x"]="y"              #add to/update dictionary
    #for x, y in thisdict.items():
    #  print(x, y)
    temporaryList=[]

    temporaryString=None     # set it to None (null) to initialize
    currentParagraphLineCount=0
    currentLineNumber=-1 # Start at negative one so adding one to the line number raises it to line 0 for the first line.
    currentLineNumberWasUpdated=False
    characterName=None

    #previousLine2 = None
    #previousLine1 = None
    #currentLineLastTime = None
    lastThreeLines = [ None, None, None ]
    startDelimiterForCharaName = str( parseSettingsDictionary[ 'theCharacterNameAlwaysBeginsWith' ] ).strip()
    endDelimiterForCharaName = str( parseSettingsDictionary[ 'theCharacterNameAlwaysEndsWith' ] ).strip()

    #while line is not empty (at least \n is present)
    # while inputFileContents != '':
    for myLine in inputFileContents:
        #myLine=inputFileContents.partition('\n')[0] #returns first line of string to process in the current loop

        #Update previous lines.
        lastThreeLines[2]=lastThreeLines[1] #move the previous line up by one
        lastThreeLines[1]=lastThreeLines[0] #move the line that was the current line last time, to previousLine1
        lastThreeLines[0]=myLine
        #TODO update lines with subsequent lines to handle situation of the character name appearing 'after' the dialogue lines.
        #TODO update handling of character names to include 'within' scenario.

        #It is annoying to search multiple times, so just dump them into an array/list and search the array
        #lastThreeLines=[currentLineLastTime,previousLine1,previousLine2]

        #try to find character name if name has not been found already and if character name handling is not disabled.
        if (characterName == None) and (parseSettingsDictionary['characterNamesAppearBeforeOrAfterDialogue'] != None):
            for entry in lastThreeLines:
                #Try to determine character using first line.
                if (str(entry).strip() != '') and ( len( str(entry).strip() ) >=3 ) and ( str(entry).strip() != 'None' ):
                    #entry.find() returns -1 if it did not find the string in the line
                    if ( entry.find(startDelimiterForCharaName ) != -1 ) and ( entry.find(endDelimiterForCharaName) != -1 ) and ( entry.find(startDelimiterForCharaName) < entry.find(endDelimiterForCharaName) ):
                        characterName=entry[ entry.find(startDelimiterForCharaName)+len(startDelimiterForCharaName) : entry.find(endDelimiterForCharaName) ]
                        if debug == True:
                            print( ('characterName=' + characterName).encode(consoleEncoding) )
                            print( ( str(entry.find(startDelimiterForCharaName)+len(startDelimiterForCharaName)) + ',' + str( entry.find(endDelimiterForCharaName)) ).encode(consoleEncoding)  )
                        #print( entry.encode(consoleEncoding) )
                        #print( entry[entry.find(startDelimiterForCharaName)+len(startDelimiterForCharaName)] ) )
                        break

        #debug code
        #print only if debug option specified
        if debug == True:
            print(myLine.encode(consoleEncoding)) #prints line that is currently being processed
        #myLine[:1]# This gets only the first character of a string #What will this output if a line contains only whitespace or only a new line? # Answer: '' -an empty string for new lines, but probably the whitespace for lines with whitespace.
        #if myLine[:1].strip() != '':# if the first character is not empty or filled with whitespace
        #    if debug == True:
        #        print(myLine[:1].encode(consoleEncoding))

        thisLineIsValid=True
        # if the line is empty, then always skip it regardless of paragraphDelimiter == emptyLine or newLine
        # Empty lines signify a new paragraph start, or it would be too difficult to tell when one paragraph ends and another starts.
        #if the newLine after .strip() == '' #an empty string
            #then end of paragraph reached. Commit any changes to temporaryString if there are any
            #and continue to next line of loop
        if myLine.strip()[:1] == '':
            thisLineIsValid=False
            #if paragraphDelimiter == 'emptyLine': #Old code.  if paragraphDelimiter='newLine', then this is the same as line-by-line mode, right?
        #else the line is not empty or filled with only whitespace.
        else:
            # if the first character is an ignore character or if the first character is whitespace, then set thisLineIsValid=False
            # ignoreLinesThatStartWith is part of the settings dictionary
            for i in parseSettingsDictionary['ignoreLinesThatStartWith']:
                if myLine.strip()[:1] == i:   #This should strip whitespace first, and then compare because sometimes dialogue can be indented but still be valid. Valid syntax: myLine.strip()[:1] 
                    thisLineIsValid=False
                    #It is possible that this line is still valid if the first non-whitespace characters in the line are an entry from the charaname dictionary.

                    #This will print the full string without returning an error. Use this logic to do a string comparison of myLine with the keys in characterDictionary.
                    #x = 'pie2'
                    #print(x[:9])
                    if charaNamesDict != None:
                        #myDict={'[＠クロエ]':'Chloe'}
                        for j,k in charaNamesDict.items():
                            if j[:1] == i:
                               #Then it might match if the first character matches.
                               #print('pie')
                               #if the dictionary entry is the same as the start of the line
                               #print( 'dictionaryKeyEntry=' + j )
                               #print( 'rawLine=\'' + myLine + '\'')
                               #print( 'cleanedUpLine=' + myLine.strip()[ :len(j) ] )
                               if j == myLine.strip()[ :len( j ) ]:
                                    #print('pie3')
                                    if debug == True:
                                        print( ('Re-adding line: '+myLine.strip() ).encode(consoleEncoding) )
                                    thisLineIsValid=True

        if thisLineIsValid == False: 
            #then commit any currently working string to databaseDatastructure, add to temporary dictionary to be added later
            if temporaryString != None:
                #temporaryDict[temporaryString] = str(currentParagraphLineCount)+'!+'False' #old. Not currently using metadata
                #temporaryDict[temporaryString] = [characterName,str(currentParagraphLineCount)]
                temporaryList.append( [ temporaryString, characterName, str(currentParagraphLineCount), str(currentLineNumber) ] )
            #and start a new temporaryString
            temporaryString = None
            #and reset currentParagraphLineCount
            currentParagraphLineCount = 0
            #and reset characterName
            characterName = None

        #while myLine[:1] != the first character is not an ignore character, #while the line is valid to feed in as input, then
        elif thisLineIsValid == True:
            currentLineNumber+=1
            currentLineNumberWasUpdated=True
            #if temporaryString is not empty, then append \n to temporaryString, and myLine
            if temporaryString != None:
                # append \n first, and then add line to temporaryString
                temporaryString = temporaryString + '\n' + myLine.strip()
                #increment currentParagraphLineCount by 1
                currentParagraphLineCount += 1

            #else if temporaryString is currently empty
            elif temporaryString == None:
                #then just append to temporaryString without \n
                temporaryString = myLine.strip()
                #and increment counter
                currentParagraphLineCount += 1
            else:
                #print('pie')
                sys.exit('Unspecified error.'.encode(consoleEncoding))

            #if max paragraph limit has been reached
            if (currentParagraphLineCount >= int( parseSettingsDictionary['maximumNumberOfLinesPerParagraph'] ) ) or (parseSettingsDictionary['paragraphDelimiter'] == 'newLine'):  
                #then commit currently working string to databaseDatastructure, #add to temporary dictionary to be added later
                #The True/False means, if True, the current line has been modified by a dictionary and so is not a valid line to insert into cache, ...if that feature ever materializes.
                #temporaryDict[temporaryString] = str( currentParagraphLineCount ) + '!False' #Old
                #temporaryDict[ temporaryString ] = [ characterName , str(currentParagraphLineCount) ]
                temporaryList.append( [temporaryString, characterName, str(currentParagraphLineCount), str(currentLineNumber) ] )

                #and start a new temporaryString
                temporaryString=None
                #and reset counter
                currentParagraphLineCount=0
                #and reset characterName
                characterName = None
        else:
            #print('pie2')
            sys.exit('Unspecified error.'.encode(consoleEncoding))

        if currentLineNumberWasUpdated == False:
            currentLineNumber+=1
        currentLineNumberWasUpdated=False

        # Remove the current line from inputFileContents, in preparating for reading the next line of inputFileContents.
        #inputFileContents=inputFileContents.partition('\n')[2] #removes first line from string
        #continue processing file onto next line normally without database insertion code until file is fully processed and dictionary is filled
        #Once inputFileContents == '', the loop will end and the dictionary can then be fed into the main database.

    if inputFileContents == '' :
        #TODO: Update this to say the file name of whatever has finished processing.
        #print('inputFileContents is now empty of everything including new lines.'.encode(consoleEncoding))
        #feed temporaryDictionary into spreadsheet #Edit: return dictionary instead.
        #return temporaryDict
        #for dialogue, metadata in temporaryDict.items():
            #print(x, y)
        #    self.appendRow([dialogue,metadata[0],metadata[1]])

        # Create a chocolate.Strawberry().
        mySpreadsheet=chocolate.Strawberry()

        # Very important: Create the correct header.
        mySpreadsheet.appendRow( ['rawText', 'speaker','metadata' ] )

        # Add data entries.
        for entry in temporaryList:
            lengthOfEntry=len(entry)
            mySpreadsheet.appendRow( [ entry[0], entry[1], entry[2] + metadataDelimiter + entry[3] ])

        if debug == True:
            mySpreadsheet.printAllTheThings()

        return mySpreadsheet


# This function takes mySpreadsheet as a chocolate.Strawberry() and inserts the contents back to fileNameWithPath.
def output( fileNameWithPath, mySpreadsheet, characterDictionary=None, settings={} ):
    print( 'Hello world!' )

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
    translatedLines = mySpreadsheet.getColumn( outputColumn )
    speakerList = mySpreadsheet.getColumn( 'B' )
    metadataColumn = mySpreadsheet.getColumn( 'C' )

    # Remove header.
    # https://www.w3schools.com/python/ref_list_pop.asp
    untranslatedLines.pop( 0 )
    translatedLines.pop( 0 )
    speakerList.pop( 0 )
    metadataColumn.pop( 0 )

