#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description: This file parses a KAG3.ks file as input and returns a chocolate.Strawberry(). It also takes a chocolate.Strawberry() and outputs the hopefully translated contents back into the file.

# Concept art and description:
# input() processes raw data and converts it to a spreadsheet for further processing. output() takes data from a processed spreadsheet and inserts it back into the original file. While in memory, that spreadsheet is implemented as a Strawberry() class found in the chocolate.py library.

Usage: This file is meant to be run as py3Any2Spreadsheet('templates\KAG3.py')

Within py3Any2Spreadsheet.py, it can be run as:
parsingScript='templates\KAG3.py'
# import parsingScript  # With fancier import syntax where the parent directory is added to sys.path first:
parsingScriptObject=pathlib.Path(parsingScript).absolute()
sys.path.append( str(parsingScriptObject.parent) )
parser=parsingScriptObject.name
import parser
parser.input('A01.ks',)

self.importFromTextFile(myFileName,fileEncoding,parseSettingsDictionary,charaNamesDict)
def importFromTextFile(self,inputFile,fileEncoding,characterDictionary):
def importFromTextFile(fileNameWithPath, fileEncoding, parseFile, parseFileEncoding):

License: See main program.
"""
__version__ = '2024Feb29'


# Set program defaults.
verbose=False
debug=False
consoleEncoding='utf-8'
defaultTextEncoding='utf-8'
metadataDelimiter='_'
inputErrorHandling='strict'
#outputErrorHandling='namereplace'  #This is set dynamically below.


# import stuff
import sys                                                         # Used to sys.exit() in case of an error and to check system version.
import resources.chocolate as chocolate     # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.


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
def input( fileNameWithPath, parseSettingsDictionary=None, fileEncoding=defaultTextEncoding, charaNamesDict=None):

    # parseSettingsDictionary must exist. It can either be defined within this file or imported.
    if parseSettingsDictionary == None:
        print( 'Error: parseSettingsDictionary must exist.' ) 
        sys.exit(1)
    if not isinstance(parseSettingsDictionary, dict):
        print( 'Error: parseSettingsDictionary is not a Python dictionary:' + str(type(parseSettingsDictionary)) )

    # charaNamesDict may or may not exist, so set it to None by default.
    #The file has already been checked to exist and the encoding correctly determined, so just open it and read contents into a string. Then use that epicly long string for processing.
    # Alternative method: https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects
    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
        inputFileContents = myFileHandle.read()

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

    #previousLine2=None
    #previousLine1=None
    #currentLineLastTime=None
    lastThreeLines=[None,None,None]
    startDelimiterForCharaName=str(parseSettingsDictionary['theCharacterNameAlwaysBeginsWith']).strip()
    endDelimiterForCharaName=str(parseSettingsDictionary['theCharacterNameAlwaysEndsWith']).strip()

    #while line is not empty (at least \n is present)
    while inputFileContents != '':
        myLine=inputFileContents.partition('\n')[0] #returns first line of string to process in the current loop

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
        inputFileContents=inputFileContents.partition('\n')[2] #removes first line from string
        #continue processing file onto next line normally without database insertion code until file is fully processed and dictionary is filled
        #Once inputFileContents == '', the loop will end and the dictionary can then be fed into the main database.

    if inputFileContents == '' :
        #TODO: Update this to say the file name of whatever has finished processing.
        print('inputFileContents is now empty of everything including new lines.'.encode(consoleEncoding))
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


# This function takes a chocolate.Strawberry() and inserts the contents back to fileNameWithPath
# exportToTextFile
def output(fileNameWithPath, parseSettingsDictionary, mySpreadsheet, fileEncoding=defaultTextEncoding, charaNamesDict=None):
    print('Hello, world!')


