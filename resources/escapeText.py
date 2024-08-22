#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
The goals of this escapeText library are to:
1) convert 'pie {\i0}pies{\i}, piez'
to a list:
[ 'pie ', [ '{\i0}' ], 'pies', [ '{\i}' ], 'piez' ]
where each entry is either text or notText. All whitespace is preserved.
2) And help approximate where {\i0} and {\i} should be reinserted into new strings that do not have {\i0} and {\i} already based upon the length of the original string.

To do the above, escapeText.EscapeText() attempts to determine and internally manage automatic escaping of schema like <>, [], {}, and one off escape sequences.

Usage: See below. Like at the bottom.

Concepts:
- An 'escapeSchema' signifies a pair of values that denote the start and end of characters that must be escaped.
An example is <p>pie</p>.
< means the start of the escape schema, and > means the end of the schema. The above string contains 2 of this schema.
Therefore, the symbols that correctly represent the escapeSchema above are < >

- An 'escapeSequence' signifies a specific sequence of characters that should be removed from the string when considering the true meaning of the string.
An example is 'pie \color52pie2'.
The meaning of the string is 'pie pie2' but the \color52 part tells some parser somewhere to manipulate the contents in a special way prior to displaying it. Since \color52 is not part of the core meaning of the string, but rather parser syntax, it should be removed when considering underlying meaning.
Therefore, the symbols that correctly represents the escapeSequence are \color52.

- In Python, escapeSequences should be represented as r'\color52' where the string is formed with an r in front of it which means 'this is a raw string'. Without the raw string syntax, the r in front, Python would interpret '\c' in '\color52' as an escape sequence and try to find some sort of meaning in '\c' and manipulate the string as a result of '\c' thus possibly distorting the result if it found one. The r syntax removes this unintended behavior and tells Python to not alter the string.

- Strings that include escape sequences in Python are displayed in a distorted way when printing them out. This does not mean the underlying data is corrupt, just that Python, and computers in general, often do not display strings accurately.
'\color52'         prints out as =>  '\\color52'
r'\color52'        prints out as =>  '\\color52'
print( r'\color52' )   prints as => \color52
'\aolor52'              => '\x07olor52'
r'\aolor52'             => '\\aolor52'
print( r'\aolor52' )  => \aolor52
Conclusion: Do not worry too much about how the data is displayed. The underlying data is not corrupt. Just remember to use r in front.

- The string.find() method can check if a string appears in another string and it returns the position where it is found.
'pie'.find('p') would return 0 because the p character is at the start of the string and strings are indexed starting from 0.
'pie'.find('e') would return 2 because the e character appears starting at index position 2 of the string. Index position 2 is the 3rd character in the string.
'pie'.find('w') returns -1 because the w character does not appear in the string. -1 means 'does not appear'.
'\color52'.find(r'\color52') => 0
r'\color52'.find(r'\color52') => 0
r'\aolor52'.find(r'\aolor52') => 0
'\aolor52'.find(r'\aolor52') => -1
Conclusion: Python will sometimes leave characters with \ in front of them alone, but other times not. To avoid this unpredictible and inconsistent behavior when dealing with arbitrary escape characters of other parsers, always use the raw string sytax, put an r in front of the string, to instruct the Python parser to behave itself.

- string objects are instantiated classes that can use the string methods associated with the string class. In contrast, b in front of a string means 'binary data' and binary data cannot use string methods. It is possible to convert strings to binary data using encode() and to convert binary data back into strings using decode().
r'\color52'.encode('utf-8')    =>  b'\\color52'
r'\color52'.find(r'\color52') => 0
r'\color52'.encode('utf-8').find(r'\color52') => TypeError.
r'\color52'.encode('utf-8').decode('utf-8').find(r'\color52') => 0
r'\co'lor52'.encode('utf-8')    => SyntaxError.
r"\co'lor52".encode('utf-8')   => b"\\co'lor52"
r'\co"lor52'.encode('utf-8')   => b'\\co"lor52'
r'\co\'lor52'.encode('utf-8')   => b"\\co\\'lor52"
b"\\co\\'lor52".decode('utf-8') => "\\co\\'lor52"
print( b"\\co\\'lor52".decode('utf-8') ) => \co\'lor52
Conclusion: Do not worry too much about how the data is displayed. The underlying data is not corrupt. Always use r when creating strings that have escapes in them. The strings might need some coercion to display properly. Creating and displaying strings can be complicated, but once created, a string is a string. It does not become corrupt regardless of how it is displayed. It is what it is.

Copyright (c) 2024 gdiaz384; License: See main program.
"""
__version__='2024.08.07'


# Import stuff.
import sys
import string

# Set defaults.
consoleEncoding = 'utf-8'
defaultGoLeftForSplitMode = False
defaultSplitDelimiter = ' '

#escapeSchema specify a pair of opening and closing tags that denote a seperate meaning from the literal text in computer code. Examples are <> [] and {}. Use a dictionary instead of a list to more strongly associate each pair.
defaultEscapeSchema = {}
defaultEscapeSchema[ '<' ] = '>' # half-width version
defaultEscapeSchema[ '＜' ] = '＞' # full-width version
#defaultEscapeSchema[ '(' ] = ')' # These are used a lot in text, so these are very situational.
#defaultEscapeSchema[ '（' ] = '）' # These are used a lot in text, so these are very situational.
defaultEscapeSchema[ '[' ] = ']' # half-width version
defaultEscapeSchema[ '［' ] = '］' # full-width version
defaultEscapeSchema[ '{' ] = '}' # half-width verision
defaultEscapeSchema[ '｛' ] = '｝' # full-width version

# escapeSequences are one off special series of characters that need to be removed and sometimes replaced with something else in order for strings to carry their intended meaning. The most common ones begin with \ such as \n, \N, \uxxx, \oxx, \xxx.
# escapeSequences that are always inside of escapeSchema should not be included here.
# In Python, the escapeSequences should always be defined with an r in front, as in r'sequence', to prevent triggering the escapeSequence when creating the string.
# https://docs.python.org/3/reference/lexical_analysis.html#strings
pythonEscapeSequences = [
r'\\',  # This is actually \\ which means there is no escape sequence for a single \. Should there be? To add a single \ as an escape sequence, create the string without the r as in '\\' but then it is no longer unique and conflicts with all of the other escape sequences.
r'\'',
r'\"',
r'\a',
r'\b',
r'\f',
r'\n',
r'\r',
r'\t',
r'\v',
r'\o',   # Requires special handling.
r'\x',   # Requires special handling.
r'\N',
r'\u',  # Requires special handling.
r'\U'   # Requires special handling.
]

# http://www.tcax.org/docs/ass-specs.htm
# TODO: This part.
assSubtitlesEscapeSequences = [ ]

# https://docs.fileformat.com/video/srt/
# TODO: This part.
srtSubtitlesEscapeSequences = [ ]

userDefinedEscapeSequences = [ ]

alphabetEscapeSequences = [ ]
for i in string.ascii_lowercase:
    alphabetEscapeSequences.append( '\\' + i )
for i in string.ascii_uppercase:
    alphabetEscapeSequences.append( '\\' + i )


class EscapeText:
    def __init__(self, string, escapeSchema=None, escapeSequences=None):
        self.string=string
        self.goLeftForSplitMode = defaultGoLeftForSplitMode
        self.splitDelimiter = defaultSplitDelimiter

        if escapeSchema == None:
            self.escapeSchema = defaultEscapeSchema
        else:
            # Then the user specified something.
            if isinstance( escapeSchema, ( list, tuple ) ):
                # This must specify pairs of values or it will error out.
                for entry in escapeSchema:
                    assert( len( entry ) == 2 )
                    self.escapeSchema[ entry[ 0 ] ] = entry[ 1 ]
            elif isinstance( escapeSchema, dict ):
                # Blindly assume everything is fine.
                self.escapeSchema = escapeSchema

        # Sometimes, certain characters in escape sequences must be handled differently. Like \u and \U specify that a certain number of arbitrary characters after it must also be escaped. These flags exist to keep track of if \u means '\u' or '\uxxxx'.
        self.escapeSequencesIncludePython = False
        self.escapeSequencesIncludeAss = False
        self.escapeSequencesIncludeSrt = False

        self.escapeSequences = userDefinedEscapeSequences.copy()
        if escapeSequences != None:
            # The user specified something. Valid entries are a list or tuple where each entry consists of an escape sequence, 'python', 'srt, 'ass'.
            if isinstance( escapeSequences, ( tuple, list ) ):
                for entry in escapeSequences:
                    #print(escapeSequences)
                    #if not entry in escapeSequences:
                    self.escapeSequences.append( entry )
            elif isinstance( escapeSequences, str ):
                if escapeSequences == 'python':
                    self.escapeSequences = pythonEscapeSequences
                    self.escapeSequencesIncludePython = True
                elif escapeSequences == 'ass':
                    self.escapeSequences = assSubtitlesEscapeSequences
                elif escapeSequences == 'srt':
                    self.escapeSequences = srtSubtitlesEscapeSequences
                elif escapeSequences == 'alphabet':
                    self.escapeSequences = alphabetEscapeSequences
                else:
                    print( ('Warning: Invalid escape sequence specified:' + escapeSequences ).encode(consoleEncoding) )

        # Old syntax:
        #self.asAList=self.convertStringToList( self.string )
        # New syntax compatible with @property:
        #self.asAList=asAList

        # Old syntax:
        #self.text=''
        #for item in self.asAList:
        #    if isinstance( item, str ):
        #        self.text=self.text + item
        # New syntax:
        #global text
        #self.text=text
        # Setting these, self.asAList and self.text, to initial values makes sense if they are specified during the creation of the object in the API. However, if they are always calculated dynamically anyway, then there is no reason to set these if they are @properties/properties(). Defining them here does require them to be added to the API, as [] and None at least, so they are better off not getting defined here during __init__ explicitly.


    # No. Just use the class attributes directly.
#    def getEscapeSchema():
#        return escapeSchema
#    def setEscapeSchema(self, listOfPairs ):
#        self.escapeSchema=listOfPairs


    # https://docs.python.org/3/howto/descriptor.html
    # https://www.programiz.com/python-programming/property
    # property(fget=None, fset=None, fdel=None, doc=None)
    # Basically, using the @property/property() syntax instead of defining asAList as a static value allows for it to return an updated value whenever the state of the object changes. Library authors also use it to maintain backwards compatibility.
    #@property
    #def asAList( self ):
    def get_asAList( self ):
        # convertStringToList() sometimes returns empty strings as list items. This is a lazy fix to that bug.
        tempList = [ ]
        tempList2 = self.convertStringToList( self.string )
        for entry in tempList2:
            if entry != '':
                tempList.append( entry )
        return tempList

    #@asAList.setter
    #def asAList(self, value):
    def set_asAList( self, value ):
        self._asAList = value

    # This syntax is the same as using @property + @asAList.setter, but more explicit.
    asAList = property( get_asAList, set_asAList )


    # This returns the text in the string which is the string after it has all of the escape sequences removed.
    # Old code.
#    def getText(self):
        # TODO: Put stuff here.
#        return _text
#    text=property(getText)

    @property
    def text(self):
        tempText=''
        #print(self.asAList)
        #print(type( self.asAList) )
        #print(len( self.asAList) )
        #assert( self.asAList != None )
        for item in self.asAList:
            #print(item)
            if isinstance( item, str ):
                tempText=tempText + item
        return tempText

    @text.setter
    def text(self, value):
        _text=value


    # Adds another schema which is a pair of items to exclude all text in the middle.
    def addEscapeSchema(self, myPair ):
        assert( len(myPair) == 2 )
        self.escapeSchema[ myPair[0] ]=myPair[1]


    # Adds another escapeSequence to the list. These are always treated literally.
    # For special behavior, like \u means remove \u and the next 2 characters after \u, then that requires special handling and adjusting the code manually.
    # Is there a way to automate that? Maybe addSpecialEscapeSequence( \u, 5) where 5 is the number of characters after \u to remove? Humm.
    def addEscapeSequence(self, myItem ):
        if isinstance( myItem, str):
            self.escapeSequences.append(myItem)
        elif isinstance( myItem, (list, tuple) ):
            for i in myItem:
                self.escapeSequences.append(myItem)
        else:
            print( 'Unrecognized type when adding escape sequence.' )


    # This function converts: 'pie {\i0}pies{\i}, piez'
    # to a list:
    # [ 'pie ', ( '{\i0}' ), 'pies', ( '{\i}' ), 'piez' ]
    # Algorithim:
    # For sanity checking, count the number of schema present overall.
    # For every schema, assign an index.
    # The schema that has the lowest index takes priority.
    # Process that schema with the lowest index. Process means split any contents before the start character in the schema into a list as a string 'pie '. Then remove that string and the schema as a tuple ('{\i0}', adding both to the list. Decriment sanity counter by 1 every time a schema is removed from the string and added to the ongoing list. And then process the next schema from the start of the new string. At the end, assert counter == 0.
    # Next, for each entry in the list that is a string process each string for escape sequences and split the entry in the list accordingly.
    # Same algorithim as above. Try to find the first escape sequence that occurs in the string, and split based upon that. Until more escape sequences remain in the string, continue.
    # return the list
    # Bug: There is this bug where if multiple escape schema are in one line, then only the first one detected will be removed. # Update fixed. Problem was not clearing  currentLowestIndex = [ None, None ]  on every iteration of the loop.
    # New bug: Sometimes, but not always, an empty string gets appended when going from print(tempList) \n assert( schemaFoundCounter == 0 ) -> end of escapeSequences processing code when a text entry consists solely of an escapeSequence.
    def convertStringToList( self, string ):
        schemaFoundCounter = 0
        for key,value in self.escapeSchema.items():
            if ( string.find( key ) != -1 ) and ( string.find( value ) != -1 ):
                schemaFoundCounter = schemaFoundCounter + string.count( key )

        #print( 'schemaFoundCounter=' + str(schemaFoundCounter) )
        schemaFoundCounterBackup = schemaFoundCounter
        tempList = []
        if schemaFoundCounter == 0:
            tempList.append( string )
        #else:
        tempString=string
        for i in range( schemaFoundCounter ):
            # [index, first pair in self.escapeSchema]
            currentLowestIndex = [ None, None ]
            for key,value in self.escapeSchema.items():
                if tempString.find( key ) != -1: # This should be redundant because the loop should only iterate over the string as many times as key, the first part of a schema like {, appears in the string. Update: No. It is always needed. Not clear why though. Update: Maybe because there are different schema in different parts of the string and the remainder of the string will not necessarily have every schema? Without this, tempString.find( key ) == -1 if it is not found which is < currentLowestIndex[0] and hence would corrupt the index.
                    if currentLowestIndex[0] == None:
                        currentLowestIndex = [ tempString.find( key ), key ]
                    # if the next key has a lower index than the current one
                    elif tempString.find( key ) < currentLowestIndex[0]:
                        currentLowestIndex = [ tempString.find( key ), key ]
            #index = tempString.find( currentLowestIndex[1] )
            index = currentLowestIndex[0]
            if index != 0:
                preString = tempString.partition( currentLowestIndex[1] )[0]
                tempList.append( preString ) # Append text as a string.
                tempString = currentLowestIndex[1] + tempString.partition( currentLowestIndex[1] )[2]
            # index is now 0.
            endIndex = tempString.find( self.escapeSchema[ currentLowestIndex[1] ] )
            tempList.append([ tempString[ 0 : endIndex + 1 ] ]) # Append the schema as a list to differentiate it from the unescaped text which are added as strings.
            tempString = tempString.partition( self.escapeSchema[ currentLowestIndex[1] ])[2]
            #print( tempString )
            schemaFoundCounter -= 1
            if ( ( i + 1 ) == schemaFoundCounterBackup ):
                tempList.append( tempString )

        #print(tempList)
        assert( schemaFoundCounter == 0 )

        #for key,value in self.escapeSchema.items():
        #    if ( string.find( key ) != -1 ) and ( string.find( value ) != -1 ):
        #        schemaFoundCounter=schemaFoundCounter + string.count( key )
        #assert( schemaFoundCounter == 0 )

        if len( self.escapeSequences ) == 0:
            return tempList

        # Some string entries in tempList need to be split into multiple entries in-place which means the original entry gets removed and an arbitrary number of new entries added. Since looping over tempList is required to determine those mappings and it is probably not a good idea to modify the list while iterating through it, put the string as a key in adjustEntryMappings, a Python dictionary, that maps that key to a list of every item that belongs in place of that string for reinsertion later.
        adjustEntryMappings = {}

        for entry in tempList:
            if isinstance( entry, str ):
                tempList2 = []
                escapeSequenceFoundCounter = 0
                tempString = entry

                #print(self.escapeSequences)
                for item in self.escapeSequences:
                    if tempString.find( item ) != -1:
                        escapeSequenceFoundCounter = escapeSequenceFoundCounter + tempString.count( item )
                        #print(escapeSequenceFoundCounter)
                        #print(item)
                        #print(tempString)

                if escapeSequenceFoundCounter == 0:
                    continue

                escapeSequenceFoundCounterBackup=escapeSequenceFoundCounter
                #print(escapeSequenceFoundCounterBackup)

                for i in range( escapeSequenceFoundCounter ):
                    currentLowestIndex=[ None, None ]
                    for item in self.escapeSequences:
                        if tempString.find( item ) != -1:
                            if currentLowestIndex[0] == None:
                                currentLowestIndex=[ tempString.find( item ), item ]
                            elif currentLowestIndex[0] > tempString.find( item ):
                                currentLowestIndex=[ tempString.find( item ), item ]

                    #print(escapeSequenceFoundCounterBackup)
                    #print(currentLowestIndex)
                    index = tempString.find( currentLowestIndex[1] )
                    if index != 0:
                        preString = tempString.partition( currentLowestIndex[1] )[0]
                        tempList2.append( preString ) # Append text as a string.
                        tempString = currentLowestIndex[1] + tempString.partition( currentLowestIndex[1] )[2]
                    # index is now 0.
                    endIndex = tempString.find( currentLowestIndex[1] )
                    # TODO: Certain escapeSequences need to be handled differently like \u \u \o? \h? if certain flags are set. Check for them here. Specifically, the length of currentLowestIndex[1] might need to be adjusted
                    tempList2.append([ tempString[ 0 : endIndex + len( currentLowestIndex[1] ) ] ]) # Append the escapeSequence itself as a list.
                    tempString = tempString.partition( currentLowestIndex[1] )[2]
                    escapeSequenceFoundCounter -= 1
                    if ( ( i + 1 ) == escapeSequenceFoundCounterBackup ):
                        tempList2.append( tempString )

                assert( escapeSequenceFoundCounter == 0 )

                adjustEntryMappings[ entry ] = tempList2.copy()

        #print('adjustEntryMappings=' + str(adjustEntryMappings) )

        if len( adjustEntryMappings ) > 0:
            # With the enumerate() syntax, the list will keep getting extended and listCounter will keep incrementing as the list grows. That could potentially lead to an infinite loop with exactly the wrong data. To avoid that possibility, keep listCounter outside of the loop and manage it manually. Copy the list as well to prevent iteration through the newly inserted items completely. # Safety first.
            listCounter = 0
            for entry in tempList.copy():
                if isinstance(entry, str):
                    if entry in adjustEntryMappings:
                        # Then replace the current list item with the items in adjustEntryMappings.
                        tempList.remove(entry)
                        for entry2 in reversed( adjustEntryMappings[ entry ] ):
                            tempList.insert( listCounter, entry2 )
                        listCounter = listCounter + len( adjustEntryMappings[ entry ] )
                        continue
                listCounter+=1

        return tempList


    # This returns a string with all of the escape characters inserted into the string.
    def getTranslatedStringWithEscapesInserted( self, translatedString ):
        tempString=''

        translatedStringAsAList = self.convertTranslatedStringToList( translatedString )
        currentTranslatedStringEntry = 0
        for entry in self.asAList:
            if isinstance( entry, str ):
                tempString = tempString + translatedStringAsAList[ currentTranslatedStringEntry ]
                currentTranslatedStringEntry+=1
            #elif isinstance( entry, list ):
            else:
                tempString=tempString + entry[0]
        return tempString

    # These next two functions together perform a psudo lexical analysis based upon the position of strings and a delimiter to determine where they should be reinserted.
    # Algorithim:
    # Obtain number # of strings to split the translation into. If 1, then do nothing.
    # if 2 or more, then take first part as a % based upon the length of the untranslated string's part1.
    # Obtain an index based upon that %.
    # if goLeftForSplitMode == True:
    #     go left of the index to the first space to obtain the end of first part of the string.
    # else:
    #     go right of the index to the first space to obtain the end of first part of the string.
    # After the index is obtained, split based upon that index and put the first part of the translated string into a list.
    # Send the second part of the string into a loop based upon the number of additional splits.
    # For the last part, just add the rest of the remaining string to the list.
    # otherwise if not last part,
    # As parts are extracted, add the parts to the list.
    # if the last character in the string is not a blank space ' ', then adjust the index left or right based upon goLeftForSplitMode boolean.
    # TODO: There should be special handling for escape schema and sequences that appear at the start and end of the string to boost insertion accuracy in these cases.
    def convertTranslatedStringToList( self, translatedString ):
        originalStringInAList = [ ]
        for i in self.asAList:
            if isinstance( i, str ):
                originalStringInAList.append( i )
        #print( originalStringInAList )
        numberOfPartsToSplit = len( originalStringInAList )
        #print( numberOfPartsToSplit )
        tempString = ''
        for i in originalStringInAList:
            tempString = tempString + i
        originalStringLength = len( tempString )

        translatedStringAfterBeingSplit = []

        # The point of this code block is to convert translated strings into the same number of blocks as the untranslated string.
        if numberOfPartsToSplit <= 1:
            translatedStringAfterBeingSplit.append( translatedString )
        elif numberOfPartsToSplit > 1:
            # do stuff
            previousPartLength = 0
            previousPartEndIndex = 0
            for i in range( numberOfPartsToSplit ):
                currentPart = originalStringInAList[ i ]
                currentPartLengthRaw = int( len( currentPart ) / originalStringLength * len( translatedString ) )
                #print( 'len( currentPart )=', len( currentPart ) )
                #print( 'len( originalStringLength )=', originalStringLength )
                #print( 'len( translatedString )=', len( translatedString ) )
                #print( len( currentPart ) / originalStringLength * len( translatedString ) )

                # The point of this highly confusing code block is to round up or down based upon the factional part of currentPartLengthRaw like 23.67 -> 24, instead of int(23.67) -> 23, so the approximate index is as accurate as possible which should mean more accurate splits.
                currentPartLengthRawFraction=( len( currentPart ) / originalStringLength * len( translatedString ) ) - currentPartLengthRaw
                #print( currentPartLengthRaw )
                #print( currentPartLengthRawFraction )
                currentPartLengthRaw = currentPartLengthRaw + int( round( currentPartLengthRawFraction, 0 ) )
                #print( currentPartLengthRaw )

                # if the current part is not the last part, then the end index must not be -1.
                # For the last part, the end index might be -1 for goLeftForSplitMode=False .
                # For the first part, the end index might be -1 for goLeftForSplitMode=True .
                if ( ( i + 1 ) != numberOfPartsToSplit ):
                    currentPartEndIndex = self._adjustIndex( previousPartLength + currentPartLengthRaw, translatedString )
                    try:
                        assert( currentPartEndIndex != -1 )
                        endResult = translatedString[ previousPartEndIndex : currentPartEndIndex ]
                    except:
                        endResult = translatedString[ previousPartEndIndex : previousPartLength + currentPartLengthRaw ]
                        translatedStringAfterBeingSplit.append( endResult )
                        previousPartLength = currentPartLengthRaw
                        previousPartEndIndex = previousPartLength + currentPartLengthRaw
                        continue
                else:
                    endResult = translatedString[ previousPartEndIndex :  ]

                # Export current part.
                translatedStringAfterBeingSplit.append( endResult )
                previousPartLength = currentPartLengthRaw
                previousPartEndIndex = currentPartEndIndex

        #print(translatedStringAfterBeingSplit)
        return translatedStringAfterBeingSplit


    def _adjustIndex(self, approximateIndex, translatedString ):
        #print( 'approximateIndex=' + str(approximateIndex) )
        #print( 'translatedString=' + translatedString )
        #global goLeftForSplitMode
        #global splitDelimiter

        # if the index is already at a blank space ' ', lucky.
        if translatedString[ approximateIndex : approximateIndex + 1 ]  == self.splitDelimiter:
            #then just return the approximateIndex
            adjustedIndex=approximateIndex
        # Normal/unlucky.
        else:
            if self.goLeftForSplitMode == True:
                # Take part 1 of the string and find the last empty space ' '.
                adjustedIndex=translatedString[ : approximateIndex ].rfind( self.splitDelimiter )
                # failure case
                if adjustedIndex == -1:
                    return approximateIndex
            else:
                # Take the rest of the string that is not part 1 and find the first empty space ' '.
                adjustedIndex=translatedString[ approximateIndex :  ].find( self.splitDelimiter )
                # failure case
                if adjustedIndex == -1:
                    return approximateIndex
                adjustedIndex=approximateIndex + adjustedIndex

        try:
            assert( translatedString[ adjustedIndex : adjustedIndex + 1 ] == self.splitDelimiter )
        except:
            print( 'approximateIndex=' + str(approximateIndex) )
            print( 'translatedString[ adjustedIndex : adjustedIndex + 5 ]=' + translatedString[ adjustedIndex : adjustedIndex + 5 ])
            print( 'self.splitDelimiter=' + '\''+self.splitDelimiter + '\'' )
            raise

        return adjustedIndex




"""
#Usage:
#test_escapeText.py

import sys
import pathlib
sys.path.append( str( pathlib.Path( '../resources/escapeText.py' ).resolve().parent ) )
import escapeText

escapeObject = escapeText.EscapeText( r'p\zie {\i0}pies{\i}, piez', escapeSequences=[ r'\z' ] )
print( 'escapeObject.escapeSequences=', escapeObject.escapeSequences )
print( 'escapeObject.string=', escapeObject.string )
print( 'escapeObject.asAList=', escapeObject.asAList )
print( 'escapeObject.text=', escapeObject.text )


originalString='but welcome back to {\i1}Elder Tale{\i0}, Naotsugu.'
# Number of parts = 3
#'but welcome back to ' + 'Elder Tale' + ', Naotsugu.'

translatedString=r'pero bienvenido de nuevo a Elder Tale, Naotsugu.'
# \z
translatedString=r'aber willkommen zurück bei Elder Tale, Naotsugu.'

# It is possible to reuse an existing object with a new string. All the internals will also change appropriately. Fancy.
escapeObject.string = originalString
print( 'escapeObject.string=', escapeObject.string )
print( 'escapeObject.asAList=', escapeObject.asAList )
print( 'escapeObject.text=', escapeObject.text )

#escapeObject.goLeftForSplitMode = True
#print( 'escapeObject.string=', escapeObject.string )
#print( 'escapeObject.asAList=', escapeObject.asAList )
#print( 'escapeObject.text=', escapeObject.text )

print( escapeObject.convertTranslatedStringToList( translatedString ) )
escapeObject.goLeftForSplitMode=True
print( escapeObject.convertTranslatedStringToList( translatedString ) )

print( '' )
escapeObject.goLeftForSplitMode = False
print( escapeObject.getTranslatedStringWithEscapesInserted( translatedString ) ) # Beautiful.

"""
