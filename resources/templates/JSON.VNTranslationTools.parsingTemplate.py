#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
This script parses vntranslationtools.json files, https://github.com/arcusmaximus/VNTranslationTools , and returns a spreadsheet.
It also takes a spreadsheet and outputs the hopefully translated contents back into the file.
That spreadsheet is implemented as a Strawberry() class found in the chocolate.py library. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

API concept art:
input() processes raw data and converts it to a spreadsheet for further processing.
output() takes data from a processed spreadsheet and inserts it back into the original file.

CLI Usage:
python py3Any2Spreadsheet.py --help
python py3Any2Spreadsheet.py input vntranslationtools.json json.vnTranslationTools.parsingTemplate.py
python py3Any2Spreadsheet.py output vntranslationtools.json json.vnTranslationTools.parsingTemplate.py --spreadsheet vnTranslationTools.json.xlsx

py3Any2Spreadsheet.py Usage:
import 'resources\templates\srt.subrip.parsingTemplate.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Algorithim:
Parse linearly in order. Extract the speaker name if there is one. Reinsert the same way.

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

#https://docs.python.org/3.7/library/codecs.html#standard-encodings
inputErrorHandling = 'strict'
#inputErrorHandling = 'backslashreplace'
#outputErrorHandling = 'namereplace'  #This is set dynamically below.


# import stuff
import sys                                                         # Used to sys.exit() in case of an error and to check system version.
import json

import resources.chocolate as chocolate            # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.
# To import directly:
# import sys
# import pathlib
# sys.path.append( str( pathlib.Path( 'C:/resources/chocolate.py' ).resolve().parent ) )
# import chocolate

#Using the 'namereplace' error handler for text encoding requires Python 3.5+, so use an older one if necessary.
sysVersion = sys.version_info.minor
if sysVersion >= 5:
    outputErrorHandling = 'namereplace'
elif sysVersion < 5:
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

    #By this point, the file has already been checked to exist and the encoding correctly determined, so just open it and read contents into a string. Then use that epicly long string for processing.
    # Alternative method that keeps the file open for a long time but uses less memory: https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects
    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        #inputFileContents = myFileHandle.read()
        #inputFileContentsJSON = myFileHandle.read()
        inputFileContentsJSON = json.loads( myFileHandle.read() )
        #inputFileContentsJSONRaw = json.loads(myFileHandle.read())

    temporaryList=[]

    # The actual json takes the form of [ {"message" : "value"}, {"name" : "the name", "message" : "value"} ]
    # So, a list where each entry in the list is a dictionary.

    if debug == True:
        print( type( inputFileContentsJSON ) )  #This is a list
        print( type( inputFileContentsJSON[0] ) )  #This is a dictionary.

        print( str(inputFileContentsJSON).encode(consoleEncoding) )
        #print( str(inputFileContentsJSON[1]).encode(consoleEncoding) )

        print (type(inputFileContentsJSON))
        print( str(inputFileContentsJSON).encode(consoleEncoding) )

#    sys.exit(1)

    # inputFileContentsJSON is a list.
    for entryNumber,entry in enumerate(inputFileContentsJSON):
        tempDialogueLine=''
        tempSpeaker=None

        # entry is a dictionary
        for key, value in entry.items():
            if key == 'message':
                # Then add value it to dialogue list.
                tempDialogueLine=value
            elif key == 'name':
                # Then add value as speaker.
                tempSpeaker=value

        # Update tempSpeaker with characterDictionary.
        if (characterDictionary != None) and (tempSpeaker != None):
            if tempSpeaker in characterDictionary.keys():
                tempSpeaker = characterDictionary[ tempSpeaker ]
            else:
                print( ('Warning: The following speaker was not found in the character Dictionary:' + str(tempSpeaker) ).encode(consoleEncoding) )

        # Once dictionary has finished processing a list entry, append the entry to temporaryList and increment entryNumber.
        temporaryList.append( [ tempDialogueLine, tempSpeaker, str(entryNumber) ] )

        #Old debug code.
        #print( 'key=' + key )
        #print( 'value=' + value )

    if debug == True:
        print( str(temporaryList).encode(consoleEncoding) )
        #sys.exit(0)

    print( ('Finished reading input of:' + fileNameWithPath).encode(consoleEncoding))

    # Debug code.
    #sys.exit(0)

    # Create a chocolate.Strawberry().
    mySpreadsheet=chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker','metadata' ] )

    # Add data entries.

    for entry in temporaryList:
        lengthOfEntry=len(entry)
        mySpreadsheet.appendRow( [ entry[0], entry[1], entry[2] ])

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
    #untranslatedLines = mySpreadsheet.getColumn( 'A' )
    #translatedLines = mySpreadsheet.getColumn( outputColumn )
    #speakerList = mySpreadsheet.getColumn( 'B' )
    #metadataColumn = mySpreadsheet.getColumn( 'C' )

    # Remove header.
    # https://www.w3schools.com/python/ref_list_pop.asp
    #untranslatedLines.pop( 0 )
    #translatedLines.pop( 0 )
    #speakerList.pop( 0 )
    #metadataColumn.pop( 0 )

    # Read original json into a string.
    with open( fileNameWithPath, 'r', encoding=settings[ 'fileEncoding' ], errors=inputErrorHandling ) as myFileHandle:
        #inputFileContents = myFileHandle.read()
        #inputFileContentsJSON = myFileHandle.read()
        inputFileContentsJSON = json.loads( myFileHandle.read() )

    # The actual json takes the form of [ {"message" : "value"}, {"name" : "the name", "message" : "value"} ]
    # inputFileContentsJSON is a list containing dictionaries for each entry. To get a specific one, do inputFileContentsJSON[counter]

    # Replace any untranslated contents, strings, in column A in the strings in outputColumn. In the literal strings, new lines should be replaced as \r\n , not just \n when writing back to file. How?
    # if \n in original string
        # Then create new temporary ColumnB/outputColumn string based upon breaking up \n, then replace \n with \\r\\n in the string, then replace. That should output \r\n in the file. #If there is no \n, then whatever, just replace as-is and print Warning about it to standard output.
        # Should probably update logic to handle word wrapping natively at some point.

    untranslatedLines=mySpreadsheet.getColumn('A')
    metadataList=mySpreadsheet.getColumn( 'C' )
    # outputColumn might be an integer or a letter. The library will take care of that conversion internally for this one method.
    translatedLines=mySpreadsheet.getColumn( outputColumn )

    currentJSONEntry=0

    #for every line/row in Strawberry()
    for counter,entry in enumerate(untranslatedLines):
        # Ignore header row, as always.
        if counter == 0:
            continue

        #print('counter=',counter)
        if debug == True:
            print('counter=',counter)
            print(metadataList[counter])
            print(currentJSONEntry)
            print( type(counter) )
            print( type(metadataList[counter]) )
            print( type(currentJSONEntry) )

        # Double check sanity to make sure the correct entry is being replaced.
        assert( int( metadataList[counter] ) == currentJSONEntry )

        input=untranslatedLines[counter].strip()
        output=translatedLines[counter]

        try:
            assert input == inputFileContentsJSON[currentJSONEntry]['message'].strip()
        except:
            if input.find('\n') == -1:
                print( 'Error: Assertion failed. assert input == inputFileContentsJSON[currentJSONEntry][message].strip()' )
                print( ('Input=' + input).encode(consoleEncoding) )
                print( ('message=' + inputFileContentsJSON[currentJSONEntry]['message'].strip() ).encode(consoleEncoding) )
                print( ('Output=' + str(output) ).encode(consoleEncoding) )
                sys.exit(1)

            # The input gets processed but not actually modified. The line breaks are still present as \n. However, the original file has new lines as \r\n, so \n alone will not match. Convert back for comparison.
            input=input.replace('\n','\r\n')
            try:
                assert input == inputFileContentsJSON[currentJSONEntry]['message'].strip()
            except:
                print( 'Error: Assertion failed. assert input == inputFileContentsJSON[currentJSONEntry][message].strip()' )
                print( ('Input=' + input).encode(consoleEncoding) )
                print( ('message=' + inputFileContentsJSON[currentJSONEntry]['message'].strip() ).encode(consoleEncoding) )
                print( ('Output=' + str(output) ).encode(consoleEncoding) )
                sys.exit(1)

        if ( output != None ) and ( output != '' ):
            # Some processing of the output should occur here, new line handing/word wrapping, or other predefined changes.
            # General fixes.
            output=output.strip()
            output=output.replace('\n','\\r\\n')

            # Data specific fixes.
            output=output.replace('「','"')
            output=output.replace('」','"')
            if output == '"...?"':
                output = '"..."'
            if output == '"............"':
                output='"..."'

            # Once post processing is complete, do the thing.
            inputFileContentsJSON[currentJSONEntry]['message']=output

        # TODO: Update the characterDictionary handling code to assume it is directly available instead of being passed within the settings dictionary.
        # Update the character name if applicable.
        if ( 'name' in inputFileContentsJSON[currentJSONEntry] ) and ( isinstance( settings[ 'characterDictionary' ], dict) == True ):
            if inputFileContentsJSON[currentJSONEntry]['name'] in settings[ 'characterDictionary' ]:
                inputFileContentsJSON[currentJSONEntry]['name']=settings[ 'characterDictionary' ][ inputFileContentsJSON[currentJSONEntry][ 'name' ] ]
            else:
                print( ('Warning: Unable to find character name in character dictionary: ' + inputFileContentsJSON[currentJSONEntry][ 'name' ] ).encode(consoleEncoding) )

        currentJSONEntry+=1

    # Once inputFileContentsJSON is fully updated, convert it to a string that represents a file and send it back to the calling function so it can be written out.
    # json.dumps returns a string. json.dump writes to a file. # indent=4 is more readable, but VNT uses indent=2. Use 2 here to match with VNT.
    return json.dumps(inputFileContentsJSON, ensure_ascii=False, indent=2)

