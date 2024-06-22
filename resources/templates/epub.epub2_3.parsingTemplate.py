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
python py3Any2Spreadsheet.py output title.epub srt.parsingTemplate.py --spreadsheet title.epub.xlsx

py3Any2Spreadsheet.py Usage:
import 'resources\templates\epub.epub2_3.parsingTemplate.py' as customParser # But with fancier/messier import syntax.
customParser.input()
customParser.output()

Algorithim:
EPUBs do not usually have speakers, so just extract contents and the metadata.
The contents are web pages, so parse them with Beautiful Soup.
The metadata consists of the file name, search term, and entry #.

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
Source Code: https://github.com/aerkalov/ebooklib
BeautifulSoup4 is MIT/expat: https://www.crummy.com/software/BeautifulSoup/
Source Code: https://code.launchpad.net/beautifulsoup

License for this file: See main program.
"""
__version__ = '2024.06.21'


# Set program defaults.
verbose=False
debug=False
consoleEncoding='utf-8'
defaultTextEncoding='utf-8'
defaultOutputColumn=4
metadataDelimiter='_'
#defaultTargetEncoding='cp932'
defaultTargetEncoding='utf-8'
genericSpeakerName='speaker'

#https://docs.python.org/3.7/library/codecs.html#standard-encodings
inputErrorHandling='strict'
#inputErrorHandling='backslashreplace'
#outputErrorHandling='namereplace'  #This is set dynamically below.


# import stuff
import sys                                                         # Used to sys.exit() in case of an error and to check system version.
#import json

import resources.chocolate as chocolate            # Main data structure that wraps openpyxl. This import will fail if not using the syntax in Usage.
# To import directly:
# import sys
# import pathlib
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

    # The input file is actually an .srt txt file so read it in as-is without convert it into a list of strings.
#    with open( fileNameWithPath, 'rt', encoding=fileEncoding, errors=inputErrorHandling ) as myFileHandle:
#        inputFileContents = myFileHandle.read() #.splitlines()

    print( 'Reading ebook...' )

    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html
    myEbook = ebooklib.epub.read_epub(fileNameWithPath) # (, encoding=fileEncoding) #No encoding information? Are all ebooks always utf-8?
    print( ('myEbook.title=' + str(myEbook.title) ).encode(consoleEncoding) )
    print( ('myEbook.version=' + str(myEbook.version) ).encode(consoleEncoding) )
    print( ('myEbook.uid=' + str(myEbook.uid) ).encode(consoleEncoding) )

    # This returns file names. 9 means 'ITEM_DOCUMENT'
    #myEbook.get_items_of_type(9)
    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubItem.get_type
    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubBook.get_items_of_type
    fileList=[]
    for htmlFile in myEbook.get_items_of_type(9):
        #print( 'type=' + str( type(htmlFile) ) )
        #print( htmlFile.get_content() )
        #print( htmlFile.set_content() )
        #soup.prettify()
        if htmlFile.is_chapter() == True:
            #htmlFile <-Object
            fileList.append( ( htmlFile.id, htmlFile.get_content() ) )

    temporaryList=[]
    for file in fileList:
        # This sends ( title, contents )
        # And gets back a list that contains [ untranslatedString, speaker=None, fileNameById, css search expression as a string,  the string sequence counter]
        temporaryList.append( parseXHTML( file[0], file[1] ) )

    #print( temporaryList )
    #print( str(temporaryList).encode(consoleEncoding) )

    # Create a chocolate.Strawberry().
    mySpreadsheet=chocolate.Strawberry()

    # Very important: Create the correct header.
    mySpreadsheet.appendRow( ['rawText', 'speaker', 'metadata' ] )

    # Add data entries and format metadata column appropriately.
    for fileContents in temporaryList:
        if len(fileContents) > 0:
            for entry in fileContents:
                # list.append([ string, speakerName, fileNameByID_cssSearchExpression_stringSequenceCounter ])
                mySpreadsheet.appendRow([ entry[0], entry[1], str( entry[2] ) + metadataDelimiter + str( entry[3] ) + metadataDelimiter + str( entry[4] ) ])

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

    # Algorithim:
    # For every file, gather the entries that need to be reinserted for that file. Put those entries into a temporary list that has:
    # tempList=[untranslated data, the page title, the css search selector, and the enumerate entry number, translated data ]
    # Send that file to be parsed into a function which returns the translated data.
    # Use epub.EpubItem.set_content() to update the content in the ebook.
    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubItem.set_content
    # Write out the ebook natively.
    # return None to calling function.

    # To gather, take the existing metadata column and split it into 3 parts:
    # 1) the file name an entry belongs to
    # 2) the css search selector
    # 3) and the enumerate() entry #, a counter, for that css search.
    #metadataColumnRaw = mySpreadsheet.getColumn( 'C' )
    metadataFileName=[]
    metadataSearchTerm=[]
    metadataEntryNumber=[]
    for entry in metadataColumn:
        #https://www.w3schools.com/python/ref_string_split.asp
        #'p-titlepage_body p_4' => [ 'p-titlepage', 'body p', 4 ]
        tempList=entry.split( metadataDelimiter )
        metadataFileName.append( tempList[0] )
        metadataSearchTerm.append( tempList[1] )
        metadataEntryNumber.append( int( tempList[2] ) )

    assert( len(metadataColumn) == len(untranslatedLines) == len(metadataEntryNumber) )

    print( 'Reading ebook...' )
    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html
    myEbook = ebooklib.epub.read_epub(fileNameWithPath) # (, encoding=fileEncoding) #No encoding information? Are all ebooks always utf-8? Maybe the encoding is set by the inner .html files or per file.
    print( ('myEbook.title=' + str(myEbook.title) ).encode(consoleEncoding) )
    print( ('myEbook.version=' + str(myEbook.version) ).encode(consoleEncoding) )
    print( ('myEbook.uid=' + str(myEbook.uid) ).encode(consoleEncoding) )

    # This returns file names. 9 means 'ITEM_DOCUMENT'
    #myEbook.get_items_of_type(9)
    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubItem.get_type
    # https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubBook.get_items_of_type
    fileList=[]
    for htmlFile in myEbook.get_items_of_type(9):
        #print( 'type=' + str( type(htmlFile) ) )
        #print( htmlFile.get_content() )
        #print( htmlFile.set_content() )
        #soup.prettify()
        if htmlFile.is_chapter() == True:
            #htmlFile <-Object
            # [ title, html content, updatedContent ]
            fileList.append( [ htmlFile.id, htmlFile.get_content(), None ] )

    temporaryList=[]
    # file is itself a list.
    for file in fileList:
        # This sends ( title, contents )
        # And gets back a list that contains [ untranslatedString, speaker=None, fileNameById, css search expression as a string,  the string sequence counter]
        #temporaryList.append( parseXHTML( file[0], file[1] ) )

        # Gather entries that match that file.
        tempParsedList=[]
        for counter,filenameFromMetadata in enumerate( metadataFileName ):
            if file[0] == filenameFromMetadata:
                # tempList=[untranslated data, the page title, the css search selector, and the enumerate entry number, translated data ]
                tempParsedList.append( [ untranslatedLines[counter], filenameFromMetadata, metadataSearchTerm[counter], metadataEntryNumber[counter], translatedLines[counter] ] )

        # Send that file to be parsed into a function which returns the translated data.
        if len(tempParsedList) > 0:
            # insertIntoXHTML(filename, raw untranslated content, tempParsedList )
            #returnedXHTML=insertIntoXHTML( filename, inputFileContents, parsedList )
            translatedFileContents = insertIntoXHTML( file[0], file[1], tempParsedList )
            #print(translatedFileContents) #This prints the correctly updated/translated XHTML file.

            # Use epub.EpubItem.set_content() to update the content in the ebook.
            # update the item in the list. Lists are pointers. Does this update the original item or not? # Update: This does not actually update anything. Somewhat expected.
            #file[1]=translatedFileContents
            # Otherwise... for file in fileList
            #myEbook.get_item_with_id( file[0] ).set_content( translatedFileContents ) #Update: This zeroes out the contents. Why?
            #print ( myEbook.get_item_with_id( file[0] ).get_content() ) # This returns empty filenames. Why?
            #epub.EpubItem(uid=,content=t
            #https://docs.sourcefabric.org/projects/ebooklib/en/latest/ebooklib.html#ebooklib.epub.EpubHtml
            #ebooklib.epub.EpubHtml
            #print( type( myEbook.get_item_with_id( file[0] )) ) # <class 'ebooklib.epub.EpubHtml'>
            #print ( myEbook.get_item_with_id( file[0] ).get_content() ) # This returns the full content.
            #tempEpubHTMLItem=ebooklib.epub.EpubHtml(file_name=file[0] + '.xhtml' , title=file[0], content=translatedFileContents )
            #tempEpubHTMLItem=ebooklib.epub.EpubItem(file_name=file[0], title=file[0], content=translatedFileContents )
            #tempEpubHTMLItem.set_content(translatedFileContents)
            #myEbook.get_item_with_id( file[0] ).set_content( tempEpubHTMLItem )
            #myEbook.get_item_with_id( file[0] ).set_content( translatedFileContents )
            #myEbook.get_item_with_id( file[0] ).set_content( translatedFileContents.encode( defaultTargetEncoding ) )
            #print( type( myEbook.get_item_with_id( file[0] )) ) <class 'ebooklib.epub.EpubHtml'>
            #print ( myEbook.get_item_with_id( file[0] ).get_content() ) # This returns empty filenames. Why?

            # Okay, figured it out. So .set_content() expects a byte encoded string of all things. Weird. Not, a regular python unicode string like would actually make sense, not an epubhtml() or epubitem() class but a string after .encode() has been called on it to convert it into bytes. Some documentation on this would have been nice, but whatever.
            # utf-8 is probably the only sane encoding to use here, but leave it configurable using file/module-level defaults.
            myEbook.get_item_with_id( file[0] ).set_content( translatedFileContents.encode( defaultTargetEncoding ) )

    # Write out the ebook natively.
    tempOutputName = fileNameWithPath + '.translated.epub'
    ebooklib.epub.write_epub( tempOutputName, myEbook )

    # return None to calling function.
    return None

    # The code that calls this function will check if the return type is a chocolate.Strawberry(), a string, or a list and handle writing out the file appropriately, so there is no need to do anything more here.
    #return tempString


#This needs to convert '<span class='pie'><ruby>膳<rt>ぜ</rt>所<rt>ぜ</rt></ruby>から</span>' to '膳所から' 
#<outerTag class='pie><innerTag><nestedTag></nestedTag></innerTag></outerTag>
def extractKanjiFromRubyXHTML( string, innerTag=None, nestedTag=None, removeOuter=True):
    if ( string == None ) or ( string == '' ):
        return ''
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

        # Using while loops always results in an infinite loop sooner or later. Maybe count the total number of instances and then use a 'for range(count)' loop instead? That is a less natural way of solving the problem, but less error prone as well. while loops are too high risk. Update this later.
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
    print( str(fileName).encode(consoleEncoding) )
    temporaryList=[]

    for counter,item in enumerate( mySoup.select('body p') ): # Perfect.
#        if item.text.strip() != '':
#            if ( str(item).find( '<ruby' ) == -1 ) and ( str(item).find( '<span' ) == -1 ) and ( str(item).find( '<a' ) == -1 ):
#                temporaryList.append([ item.text.strip(), None, fileName, 'body p', counter ])
#                continue

        if item.text.strip() != '':
            returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag=None, nestedTag=None, removeOuter=True )
            if returnedString.find( '<ruby' ) != -1:
                returnedString=extractKanjiFromRubyXHTML( returnedString, innerTag='ruby', nestedTag='rt', removeOuter=False )
            if returnedString.find( '<span' ) != -1:
                returnedString=extractKanjiFromRubyXHTML( returnedString, innerTag='span', nestedTag=None, removeOuter=False )
            if returnedString.find( '<a' ) != -1:
                returnedString=extractKanjiFromRubyXHTML( returnedString, innerTag='a', nestedTag=None, removeOuter=False )
            if returnedString.find( '<em' ) != -1:
                returnedString=extractKanjiFromRubyXHTML( returnedString, innerTag='em', nestedTag=None, removeOuter=False )
            if returnedString.find( '<code' ) != -1:
                returnedString=extractKanjiFromRubyXHTML( returnedString, innerTag='code', nestedTag=None, removeOuter=False )
            if returnedString.find( '<br>' ) != -1:
                returnedString=returnedString.replace( '<br>', '' )
            if returnedString.find( '<br/>' ) != -1:
                returnedString=returnedString.replace( '<br/>', '' )
            returnedString=returnedString.strip()
            if returnedString != '':
                temporaryList.append([ returnedString, None, fileName, 'body p', counter ])

    if len(temporaryList) > 0:
        return temporaryList
    #else:
    for counter,item in enumerate( mySoup.select('body h2') ): # Perfect.
        if item.text.strip() != '':
            # Old syntax. The one above is better.
            if str(item).find( '<ruby' ) == -1:
                temporaryList.append([ item.text.strip(), None, fileName, 'body h2', counter ])
            else:
                returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                temporaryList.append([ returnedString, None, fileName, 'body h2', counter ])
        return temporaryList

    return temporaryList

    # Old code.
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
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body span' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='span', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body span' ])
        return temporaryList

    # Very old code.
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
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body div p' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body div p' ])
        return temporaryList

    if fileName == 'p-001':
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body span') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body span' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body span' ])
        return temporaryList

    if ( fileName == 'p-002' ) or ( fileName == 'p-004' ) or ( fileName == 'p-006' ) or ( fileName == 'p-008' ) or ( fileName == 'p-010' ):
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body h2') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                if str(item).find('<ruby') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body h2' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    temporaryList.append([ returnedString, None, fileName, counter, 'body h2' ])
        return temporaryList

    pparserList=[ 'p-003', 'p-005', 'p-007', 'p-009', 'p-011', 'p-013', 'p-014']
    if fileName in pparserList:
        #print(mySoup)
        for counter,item in enumerate( mySoup.select('body p') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                #print( ( 'item=' + str(item)).encode(consoleEncoding) )
                #print( ( 'item.text=' + str(item.text)).encode(consoleEncoding) )
                if ( str(item).find( '<ruby' ) == -1 ) and ( str(item).find( '<span' ) == -1 ):
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body p' ])
                elif ( str(item).find( '<ruby' ) != -1 ):
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body p' ])
                elif ( str(item).find( '<span' ) == -1 ):
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='span', nestedTag=None, removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body p' ])
        return temporaryList

    if ( fileName == 'p-012' ):
        #print(mySoup)
        for counter,item in enumerate( mySoup.select( 'body p' ) ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                #print( ( 'item=' + str(item)).encode(consoleEncoding) )
                #print( ( 'item.text=' + str(item.text)).encode(consoleEncoding) )
                if str(item).find('<span') == -1:
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body p' ])
                else:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='span', nestedTag=None, removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body p' ])
        return temporaryList

    if ( fileName == 'p-colophon' ):
        for counter,item in enumerate( mySoup.select('body p') ): # Perfect. Returns a list with 2 items where calling .text on each item in the list returns only the item.
            if item.text.strip() != '':
                #print( ( 'item=' + str(item)).encode(consoleEncoding) )
                #print( ( 'item.text=' + str(item.text)).encode(consoleEncoding) )
                if ( str(item).find( '<ruby' ) == -1 ) and ( str(item).find( '<span' ) == -1 ) and ( str(item).find( '<a href' ) == -1 ):
                    temporaryList.append([ item.text.strip(), None, fileName, counter, 'body p' ])
                elif str(item).find('<span') != -1:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='span', nestedTag=None, removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body p' ])
                elif str(item).find('<ruby') != -1:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='ruby', nestedTag='rt', removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body p' ])
                elif str(item).find('<a href') != -1:
                    returnedString=extractKanjiFromRubyXHTML( str(item).strip(), innerTag='a', nestedTag=None, removeOuter=True)
                    #print( ( 'returnedString=' + str(returnedString) ).encode(consoleEncoding) )
                    if isinstance(returnedString, str) == True:
                        returnedString=returnedString.strip()
                    temporaryList.append([ returnedString, None, fileName, counter, 'body p' ])
                else:
                    print( 'unspecified error parsing p-colophon.')
        return temporaryList


# inferFormatting tries to put back the formatting that is in rawEntry back into translatedString. cssSelector is used for the outermost entry.
def inferFormatting(rawEntry, cssSelector, translatedString):
    if ( rawEntry.find( '<' ) == -1 ):
        return translatedString
    #else there are < that need to be inserted.
    # first, extractKanjiFromRubyXHTML()

    # This returns the second css selector in the string. 'body p' => 'p'
    cssSelector=cssSelector.split()[1]

    tempString='<' + cssSelector + '>' + translatedString + '</' + cssSelector + '>'

    returnedString=extractKanjiFromRubyXHTML( str(rawEntry).strip(), innerTag=None, nestedTag=None, removeOuter=True )

    # if after removing the edges, there are no '<', then it is a simple string with only outer <>.
    # Append the cssSelector tag to the translatedString and return it as-is.
    if returnedString.find( '<' ) == -1:
        return tempString
    #elif returnedString.find( '<' ) != -1:
    # There are additional tags in the string, like <span>, <em>, or <ruby>
    else:
        # Only support fully enclosing tags and assume the tag at the start is the same as the tag at the end.
        # Tags in the middle are too complicated to parse since that requires access to a translation engine directly in order to create the correct mapping, or the mapping itself. Without that information, there is no sane way to re-create those mappings of where the tags should go in the post-translated value.
        if ( returnedString.startswith( '<' ) == True ) and ( returnedString.endswith( '>' ) == True ):
            #index=
            startingTag = returnedString[ 0 : returnedString.find( '>' ) + 1 ]
            endingTag= returnedString[ returnedString.rfind( '<' ) : ]
            return '<' + cssSelector + '>' + startingTag + translatedString + endingTag + '</' + cssSelector + '>'
        else:
            return tempString


# This function takes XHTML file contents and translates them based upon the content in parsedList.
# parsedList is a list of lists where each inner list has the following:
# [ untranslated data, the page title, the css search selector, and the enumerate entry number, translated data ]
def insertIntoXHTML(filename, fileContents, parsedList ):
    # Sanity check.
    for entry in parsedList:
        try:
            assert( filename == entry[1] )
        except:
            print( 'filename=' + str(filename) )
            print( 'entry[1]=' + str(entry[1]) )
            raise

    #print(fileContents)
    #sys.exit(0)
    #return fileContents #Stub code.

    # Create a new Beautiful Soup.
    mySoup=bs4.BeautifulSoup( fileContents, features='lxml' ) # For XHTML.
    #assert( mySoup.is_xml != True )

    #print( fileContents )
    #print( str(mySoup) )
    #sys.exit(1)

    #return fileContents
    #return str(mySoup)
    #return str(mySoup).encode('utf-8') # Works!

    #print(fileContents)
    #print(mySoup)
    print( str(filename).encode(consoleEncoding) )

    # Use the for i in soup.select(): i.replace_with() syntax to update the soup.
    # https://stackoverflow.com/questions/40775930/using-beautifulsoup-to-modify-html
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#replace-with

    # Very dumb algorithim:
    # for every entry in parsed List, search using the css search term and update that entry using replacewith.
    for entry in parsedList:
        #assert( filename == entry[1] )
        for counter,item in enumerate( mySoup.select(entry[2]) ): # Perfect.
            if counter == entry[3]:
                # There should be code here that detects the original formatting, if any, and tries to replicate it.
                tempString=entry[4]
                if item.find('<') != -1:
                    # entry[4]='<p>' + entry[4] + '</p>'
                    # inferFormatting( rawentry, css selector, translated entry)
                    tempString=inferFormatting( str(item), entry[2], entry[4], )
                #print( ('item=' + str(item)).encode(consoleEncoding) )
                item.replace_with( bs4.BeautifulSoup( tempString, 'xml' ) )
                #print( ('item=' + str(item)).encode(consoleEncoding) )

    # Better algorithim:
    # TODO: put stuff here.

    #print( str(mySoup.prettify()) )
    return mySoup.prettify()
#    return mySoup.prettify().partition('\n')[2].partition('\n')[2] # Remove the first two lines.
    #tempList=mySoup.prettify().partition('<body>')
    tempList=str(mySoup).partition('<body>')
    return '<html>' + tempList[1] + tempList[2]
#    return mySoup


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
