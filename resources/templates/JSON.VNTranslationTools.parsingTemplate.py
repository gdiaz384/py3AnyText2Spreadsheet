#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description: This file parses a JSON from VNTranslationTools as input and returns a chocolate.Strawberry(). It also takes a chocolate.Strawberry() and outputs the hopefully translated contents back into the file.

# Concept art and description:
# input() processes raw data and converts it to a spreadsheet for further processing. output() takes data from a processed spreadsheet and inserts it back into the original file. While in memory, that spreadsheet is implemented as a Strawberry() class found in the chocolate.py library.

Usage: This file is meant to be run as py3Any2Spreadsheet('templates\JSON.VNTranslationTools.py')

Within py3Any2Spreadsheet.py, it can be run as:
parsingScript='templates\JSON.VNTranslationTools.py'
# import parsingScript  # But with fancier/messier import syntax.

License: See main program.
"""
__version__ = '2024.05.18'


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
    #                    print( ('Error: Could not find column \'' + str( settings[ 'outputColumn' ] ) + '\' in spreadsheet. Using default value \'' + str(defaultOutputColumn) + '\'' ).encode(consoleEncoding) )
    #                    outputColumn=defaultOutputColumn
        else:
            outputColumn=defaultOutputColumn
    #elif 'outputColumn' not in settings:
    else:
        # This sets
        outputColumn=defaultOutputColumn

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

