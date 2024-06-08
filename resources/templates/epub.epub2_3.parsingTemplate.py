#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
This script parses EPUB2.epub and EPUB3.epub files, https://en.wikipedia.org/wiki/EPUB , https://idpf.org/epub/30/spec/epub30-contentdocs.html , and returns a spreadsheet.
It also takes a spreadsheet and outputs the hopefully translated contents back into the file.
That spreadsheet is implemented as a Strawberry() class found in the chocolate.py library. A chocolate.Strawberry() is a type of spreadsheet that exists only in memory.

API concept art:
input() processes raw data and converts it to a spreadsheet for further processing.
output() takes data from a processed spreadsheet and inserts it back into the original file.

CLI Usage:
python py3Any2Spreadsheet.py --help
python py3Any2Spreadsheet.py input title.epub epub.parsingTemplate.py
python py3Any2Spreadsheet.py output title.epub srt.parsingTemplate.py --spreadsheet title.epub.csv

py3Any2Spreadsheet.py Usage:
import 'resources\templates\JSON.VNTranslationTools.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Algorithim:
EPUBs do not usually have speakers, so just extract contents and the metadata.
The metadata consists of the file name, and entry #.

External Dependencies:
This file uses the ebooklib library: https://pypi.org/project/EbookLib/
It must be installed using pip as: pip install ebooklib
Developed using pip install EbookLib==0.18
This file uses the beautifulsoup4 library: https://pypi.org/project/beautifulsoup4/
It must be installed using pip as: pip install beautifulsoup4, lxml
Developed using pip install beautifulsoup4==4.12.3
pip install lxml

Links:
https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html
https://www.w3.org/publishing/epubcheck/docs/getting-started/
https://beautiful-soup-4.readthedocs.io

Licenses:
EbookLib is AGPLv3: https://github.com/aerkalov/ebooklib/blob/master/LICENSE.txt
BeautifulSoup4 is MIT/expat: https://www.crummy.com/software/BeautifulSoup/

License for this file: See main program.
"""
__version__ = '2024.06.07'


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
#import json
import resources.chocolate as chocolate     # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.
# To import directly, use...
# sys.path.append( str( pathlib.Path('C:/resources/chocolate.py').resolve().parent) )
# import chocolate
import ebooklib
import ebooklib.epub
import bs4

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


#This needs to convert '<span class='pie'><ruby>膳<rt>ぜ</rt>所<rt>ぜ</rt></ruby>から</span>' to '膳所から' 
#<outerTag class='pie><innerTag><nestedTag></nestedTag></innerTag></outerTag>
def extractKanjiFromRubyXHTML( string, innerTag=None, nestedTag=None, removeOuter=True):
    if ( string == None ) or ( string == '' ):
        return None
    if ( string.find('<') == -1 ) or ( string.find('>') == -1 ):
        return string
    #string=str(string)

    if removeOuter == True:
        # This removes the counter tag. Example: '<span class='pie'>stuff<span>'  =>  'stuff'
        outerTagOpeningEnd=string.find('>')
        outerTagClosingStart=string.rfind('<')
        string=string[ outerTagOpeningEnd+1 : outerTagClosingStart ]

    if innerTag == None:
        return string

    innerTagStart='<' + innerTag
    innerTagEnd='</' + innerTag + '>'

    if nestedTag != None:
        # Lazy.
        nestedTagStart='<' + nestedTag + '>'
        nestedTagEnd='</' + nestedTag + '>'

    # This removes the innerTag from the middle of the line.
    # Example: 'pie<ruby>pie2<rt>ぜ</rt>所<rt>ぜ</rt></ruby>pie3' => 'piepie2<rt>ぜ</rt>所<rt>ぜ</rt>pie3'
    # Then, if there is a nested tag defined, it removes all contents between the nested tags.
    # Example: 'piepie2<rt>ぜ</rt>所<rt>ぜ</rt>pie3' => 'piepie2所pie3'
    # This parsing algorithim is slightly improper. Besides using unnecessary while loops, it should extract the text between <ruby>text</ruby>, process that, then replace it in the original string with the processed result, and then move on to the next <ruby> pair. The current logic treats nested tags as independent from the inner tags which is incorrect. The logic is nested to emphasize the relationship, but the code itself does not reflect that relationship adequately.
    # It does work however.
    while ( string.find( innerTagStart ) != -1 ) and ( string.find( innerTagEnd ) != -1 ):
        # Remove the first innerTagEnd that appears starting from the left.
        string=string.replace( innerTagEnd, '' , 1)
        # Remove innerTagStart after appending the closing >
        # Take, the end of the inner tag as the start index, '<innerTag' + 9, and search the rest of the string for the first >
        tempSearchString=string[ string.find(innerTagStart) + len(innerTagStart) : ]
        innerTagStartFull=innerTagStart + tempSearchString[ : tempSearchString.find('>') + 1 ]
        string=string.replace( innerTagStartFull, '' , 1)

        # Using while loops always results in an infinite loop sooner or later. Maybe count the total number of instances and then use a 'for range(count)' loop instead? That is a less natural way of solving the problem, but less error prone as well. while loops are too high risk.
        if nestedTag != None:
            while ( string.find(nestedTagStart) != -1 ) and ( string.find(nestedTagEnd) != -1 ):
                startIndex=string.find(nestedTagStart)
                endIndex=string.find(nestedTagEnd)
                charactersToRemove=string[string.find(nestedTagStart) : string.find(nestedTagEnd)+len(nestedTagEnd) ]
                #print( ( 'charactersToRemove='+charactersToRemove).encode(consoleEncoding) )
                #print( string.encode(consoleEncoding) )
                string=string.replace( charactersToRemove, '', 1)
                #print( string.encode(consoleEncoding) )
        #sys.exit()
    return string


# This takes fileName, and fileContents, and returns the translatable strings in a list containing lists [ [], [], [] ]
# each sub list contains [ untranslatedString, speaker=None, fileName, the string sequence counter, css search expression as a string ]
# The page title does not seem to parse correctly.
def parseXHTML( fileName, fileContents ):
    mySoup=bs4.BeautifulSoup( fileContents, features='lxml' ) # For XHTML.
    assert( mySoup.is_xml != True )

    #print(fileContents)
    #print(mySoup)
    print(fileName)
    temporaryList=[]

    # Parse table of contents.
    if fileName == 'p-toc-001':
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body span') ): # Search by CSS selector. Perfect.
            if item.text != '':
                temporaryList.append([ item.text, None, fileName, counter, 'body span' ])
            #print( 'item.text=' + item.text )
        for counter,item in enumerate( mySoup.select('body a') ): # Search by CSS selector.
            # This needs a pre-processor to remove content inside of <ruby> </ruby> tags.
            # TODO: Put item pre-processor here. Update: Added it.
            #print( 'item=' + str(item) )
            #print( 'item.text=' + str(item.text) )
            if item.text.strip() != '':
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body a' ])
                else:
                    #def extractKanjiFromRubyXHTML( string, innerTag=None, nestedTag=None, removeOuter=True):
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    if ( returnedString != None ) and ( returnedString != '' ):
                        temporaryList.append([ returnedString, None, fileName, counter, 'body a' ])
        return temporaryList

    if fileName == 'p-fmatter-001':
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body span') ):
            if item.text.strip() != '':
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, None, counter, 'body span' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='span', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, None, counter, 'body span' ])
        return temporaryList

    # Old code.
#    if fileName == 'p-titlepage':
        #print('pie')
        #for counter,item in enumerate( mySoup.find_all('a') ):
#        for counter,item in enumerate( mySoup.find('div', attrs='main').find_all('div') ):
#            temporaryList.append([ item.text, None, fileName, counter, ( 'find', 'div', 'main' ), find_all ])
#        for counter,item in enumerate( mySoup.find('div', attrs='main') ):
#            for counter,item in enumerate( mySoup.find_all('div', attrs='font-120per') ):
#            temporaryList.append([ item.text, None, fileName, counter, ( 'find', 'div', 'main' ), find_all ])
        #item0=mySoup.select('div.main div.font-120per p')[0].text
        #items=mySoup.select('div.main div p') # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.

    if fileName == 'p-titlepage':
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body div p') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, None, counter, 'body div p' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, None, counter, 'body div p' ])
        return temporaryList

    if fileName == 'p-001':
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body span') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, None, counter, 'body span' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, None, counter, 'body span' ])
        return temporaryList

    if ( fileName == 'p-002' ) or ( fileName == 'p-004' ) or ( fileName == 'p-006' ) or ( fileName == 'p-008' ) or ( fileName == 'p-010' ):
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body h2') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, None, counter, 'body h2' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    temporaryList.append([ returnedString, None, fileName, None, counter, 'body h2' ])
        return temporaryList

    pparserList=[ 'p-003', 'p-005', 'p-007', 'p-009', 'p-011', 'p-013', 'p-014']
    if fileName in pparserList:
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body p') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                #print( ( 'item=' + str(item)).encode(consoleEncoding) )
                #print( ( 'item.text=' + str(item.text)).encode(consoleEncoding) )
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, None, counter, 'body p' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, None, counter, 'body p' ])
        return temporaryList

    if ( fileName == 'p-012' ):
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body p') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                #print( ( 'item=' + str(item)).encode(consoleEncoding) )
                #print( ( 'item.text=' + str(item.text)).encode(consoleEncoding) )
                if str(item).find('<span') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, None, counter, 'body p' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='span', nestedTag=None, removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, None, counter, 'body p' ])
        return temporaryList

    if ( fileName == 'p-colophon' ):
        for counter,item in enumerate( mySoup.select('body p') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                #print( ( 'item=' + str(item)).encode(consoleEncoding) )
                #print( ( 'item.text=' + str(item.text)).encode(consoleEncoding) )
                if ( str(item).find('<span') == -1 ) and ( str(item).find('<span') == -1):
                    temporaryList.append([ item.text.strip(), None, fileName, None, counter, 'body p' ])
                elif str(item).find('<span') != -1:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='span', nestedTag=None, removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, None, counter, 'body p' ])
                elif str(item).find('<ruby') != -1:

    return temporaryList


# parseSettingsDictionary is not necessarily needed for this parsing technique. All settings can be defined within this file or imported from parsingScript.ini
# characterDictionary may or may not exist, so set it to None by default.
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
    print( 'Reading ebook...' )

    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html
    myEbook = ebooklib.epub.read_epub(fileNameWithPath) # (, encoding=fileEncoding) #No encoding information? Are all ebooks always utf-8?
    print( ('myEbook.title=' + str(myEbook.title) ).encode(consoleEncoding) )
    print( ('myEbook.version=' + str(myEbook.version) ).encode(consoleEncoding) )
    print( ('myEbook.uid=' + str(myEbook.uid) ).encode(consoleEncoding) )

    # This returns file names. 9 means 'ITEM_DOCUMENT'
    #myEbook.get_items_of_type(9)
    fileList=[]
    for htmlFile in myEbook.get_items_of_type(9):
        #print( htmlFile.get_content() )
        #print( htmlFile.set_content() )
        if htmlFile.is_chapter() == True:
            #htmlFile <-Object
            fileList.append( ( htmlFile.id, htmlFile.get_content() ) )

    tempList=[]
    for file in fileList:
        # This sends ( title, contents )
        # And gets back a list that contains [ untranslatedString, speaker=None, fileNameById, the string sequence counter, css search expression as a string ]
        tempList.append( parseXHTML( file[0], file[1] ) )

    print( tempList )
    #print( str(tempList).encode(consoleEncoding) )

    return None



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


def checkEncoding(string, encoding):
    try:
        string.encode(encoding)
        return True
    except UnicodeEncodeError:
        return False


def normalizeEncoding(string, encoding):
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

    # Use the for i in soup.select(): i.replace_with() syntax to update the soup.
    # https://stackoverflow.com/questions/40775930/using-beautifulsoup-to-modify-html
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#replace-with
    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubItem.set_content





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


"""
https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubBook.set_direction
https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubBook.set_title
https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubItem.set_content

standard.opf
<spine page-progression-direction="rtl">
change to
<spine page-progression-direction="ltr"

stanard-style.css
.vrtl {
  -webkit-writing-mode: vertical-rl;
  -epub-writing-mode:   vertical-rl;
}
/*
.vltr {
  -webkit-writing-mode: horizontal-tb;
  -epub-writing-mode:   horizontal-tb;

change to 
  -webkit-writing-mode: horizontal-tb;
  -epub-writing-mode:   horizontal-tb;
"""
