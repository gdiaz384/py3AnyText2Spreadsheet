#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description: This file parses a JSON from VNTranslationTools as input and returns a chocolate.Strawberry(). It also takes a chocolate.Strawberry() and outputs the hopefully translated contents back into the file.

# Concept art and description:
# This function processes raw data (.ks, .txt. .ts) using a parse file and converts it into a spreadsheet. The extracted data is meant to be loaded into the main workbook data structure for further processing. While in memory, that spreadsheet is implemented as a Strawberry() class found in the chocolate.py library, hence chocolate.Strawberry().

Usage: This file is meant to be run as py3Any2Spreadsheet('templates\JSON.VNTranslationTools.py')

Within py3Any2Spreadsheet.py, it can be run as:
parsingScript='templates\JSON.VNTranslationTools.py'
# import parsingScript  # But with fancier/messier import syntax.

License: See main program.
"""
__version__ = '2024Mar01'


# Set program defaults.
verbose=False
debug=False
consoleEncoding='utf-8'
defaultTextEncoding='utf-8'
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
# - an input file name
# - parseFileDictionary as a Python dictionary
# - the encoding for that text file (utf-8, shift-jis)
# - An optional character dictionary as a Python dictionary
# and creates a spreadsheet where the first column is the dialogue. The second column is the name of the speaker, if any, and the third column is metadata: the total number of lines that are represented by the dialogue entry, and the line number dialogue was extracted from. If dialogue was taken from more than one line, then the line number is the last line.

# input then updates the spreadsheet with the first row as metadata. The first column, column A, as the dialogue, the second column, Column B, as the speaker, and the third column, Column C, as a string containing metadata.
# The metadata is: 1) number of lines the rawText in column A represents 2) the line numbers the input is taken from, and what else?

# Newer list approach: In other words, [ [ ], [ ] , [ ], [ ] ] would make more sense. A single list, then each entry in that list is a list containing strings or None entries. Each entry is: dialogue, speaker, lineCount, lineNumberOfDialogue.

# parseSettingsDictionary is not needed for this parsing technique. It can either be defined within this file or imported.
# characterDictionary may or may not exist, so set it to None by default.
# A better name for characterDictionary at this stage is probably 'doNotIgnoreLinesThatStartWithThis'.
def input( fileNameWithPath, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, characterDictionary=None):

    #By this point, the file has already been checked to exist and the encoding correctly determined, so just open it and read contents into a string. Then use that epicly long string for processing.
    # Alternative method that keeps the file open for a long time but uses less memory: https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects
    with open( fileNameWithPath, 'r', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        #inputFileContents = myFileHandle.read()
        #inputFileContentsJSON = myFileHandle.read()
        inputFileContentsJSON = json.loads(myFileHandle.read())
        #inputFileContentsJSONRaw = json.loads(myFileHandle.read())

    temporaryList=[]

    # The actual json takes the form of [ {"message" : "value"}, {"name" : "the name", "message" : "value"} ]
    # So, a list where each entry in the list is a dictionary.

#    try:
#        pass
        #inputFileContentsJSON=json.JSONDecoder.decode(inputFileContentsJSONRaw)
#    except json.JSONDecodeError:
#        print( 'Error: There was an error decoding json from the following file:' )
#        print( fileNameWithPath.encode(consoleEncoding) )
#        sys.exit(1)

    if debug == True:
        print( type( inputFileContentsJSON ) )  #This is a list
        print( type( inputFileContentsJSON[0] ) )  #This is a dictionary.

        print( str(inputFileContentsJSON).encode(consoleEncoding) )
        #print( str(inputFileContentsJSON[1]).encode(consoleEncoding) )

        print (type(inputFileContentsJSON))
        print( str(inputFileContentsJSON).encode(consoleEncoding) )

#    sys.exit(1)

    entryNumber=0
    # inputFileContentsJSON is a list.
    for entry  in inputFileContentsJSON:
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

        # Once dictionary has finished processing a list entry, append the entry to temporaryList and increment entryNumber.
        temporaryList.append( [ tempDialogueLine, tempSpeaker, str(entryNumber) ] )
        entryNumber += 1

        #Old debug code.
        #print( 'key=' + key )
        #print( 'value=' + value )

    if debug == True:
        print( str(temporaryList).encode(consoleEncoding) )
        #sys.exit(0)

    print( ('Finished reading input of:' + fileNameWithPath).encode(consoleEncoding))

    #feed temporaryDictionary into spreadsheet #Edit: return dictionary instead.
    #return temporaryDict
    #for dialogue, metadata in temporaryDict.items():
        #print(x, y)
    #    self.appendRow([dialogue,metadata[0],metadata[1]])

    # Debug code.
    #sys.exit(0)

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
# exportToTextFile
def output(fileNameWithPath, mySpreadsheet, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, characterDictionary=None):
    #print('Hello, world!')
    #sys.exit(1)

    assert isinstance(mySpreadsheet, chocolate.Strawberry)

    # Read original json into a string.
    with open( fileNameWithPath, 'r', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read()
        #inputFileContentsJSON = myFileHandle.read()
        #inputFileContentsJSON = json.loads(myFileHandle.read())

    #replace any contents of column A in the string with column B. In the literal strings, new lines should be replaced as \r\n , not just \n when writing back to file. How?
   
    # if \n in original string
        # Then create new temporary ColumnB string based upon breaking up \n, then replace \n with \\r\\n in the string, then replace. That should output \r\n in the file. #If there is no \n, then whatever, just replace as-us and print Warning about it to standard output.
        # Should probably also update logic to handle word wrap.

    columnA=mySpreadsheet.getColumn('A')
    columnB=mySpreadsheet.getColumn('B')

    counter=0
    #for every line/row in Strawberry()
    for entry in columnA:
        input=columnA[counter].strip()
        output=columnB[counter].strip()

        if inputFileContents.find( input ) != -1:
            if verbose == True:
                print('Replacing literal:')
            if debug == True:
                print( ( input ).encode(consoleEncoding) )
                print('With:')
                print( ( output ).encode(consoleEncoding) )
            # Replace here.
            inputFileContents=inputFileContents.replace(input, output)

      # elif there was not a match, then try replacing new line character in input string with \\r\\n and see if it matches.
        elif inputFileContents.find( input.replace('\n','\\r\\n') ) != -1:
            #print('match found replacing \\n with literal \\r\\n')

            # If there is a match, then update the input, and perform the replacement.
            input=input.replace('\n','\\r\\n')
            # Fix the output as well to replace any line breaks with psudo-line breaks.
            output=output.replace('\n','\\r\\n')
            inputFileContents=inputFileContents.replace(input, output)
            if verbose == True:
                print('Replacing after replacing \\n with \\r\\n:')
            if debug == True:
                print( ( input ).encode(consoleEncoding) )
                print('With:')
                print( ( output ).encode(consoleEncoding) )

        elif inputFileContents.find( columnA[counter].strip().replace('\n','\r\n') ) != -1:
            print( 'Warning: match found replacing \\n with non-literal \\r\\n' )
            print( 'Warning: No replacement performed.' )

#splitlines()
#startswith('aaa')

        else:
            print( ( 'Runtime error: Entry not found: ' + columnA[counter].strip() ).encode(consoleEncoding) )
        counter += 1

    # This should actually be "postTranslatedDictionary" or maybe post writing to file dictionary. This only replaces character names currently oddly fits the dictionary name better than intended.
    if characterDictionary != None:
        for rawName, translatedName in characterDictionary.items():
            inputFileContents=inputFileContents.replace(rawName,translatedName)

    return inputFileContents

