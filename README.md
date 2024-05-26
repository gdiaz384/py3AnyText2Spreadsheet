# py3AnyText2Spreadsheet

py3AnyText2Spreadsheet parses arbitrary text files to create spreadsheets that can be used in natural language translation.

The intended use case is part of a larger workflow that involves [py3TranslateLLM] to translate the spreadsheets with different engines and possibly [py3translationServer] to power one or more of those engines. py3AnyText2Spreadsheet can then be used again once translation completes to reinsert the translated entries back into the original text files.

The project goals are to:
- Support fully automated extraction from text files into spreadsheets *after* the correct parser is written.
- Make it easier to write parsers by handling most or all of the backend logic and providing engine templates and documentation.
- Support a wide variety of different parsers, including non-Python ones like Javascript/ECMAScript, for various textual formats.
- Support parsers for non-encrypted texts part of obscure game engines.
- Extract strings to translate from various texual formats and insert them back after translation by using spreadsheets as the interchange format.
- Currently semi-supported:
    - KAG3 used in the kirikiri game engine (.ks).
    - Support for JSON produced by [VNTranslationTools](//github.com/arcusmaximus/VNTranslationTools).
    - pylivemaker CSV files.
    - Support for arbitrary text files, including JSON, via user defined parse files.

## Support is planned for:

- Line-by-line text files (.txt).
- srt files.
- epub files.
- DDWSystem2013, DDWorks Game System, fwDDSystem, [vndb.org](https://vndb.org/r?f=fwDDSystem-)
- JSON support:
    - Support for JSON where all entries and are nested under `contents` and there is no additional nesting.
        - Multiple entries must be in a list surrounded by square brackets `[ ]`.
    - To process additional types of JSON, open an issue and provide an `example.json`.
- KAG3 used in TyranoBuilder (.ks/.ts?).
- Better documentation.

## Maybe:

- RPGM (MZ, MV, Ace... ) # The dream.
- Support for UlyssesWu's [FreeMote](//github.com/UlyssesWu/FreeMote) text files converted from PSB to JSON.
    - Is it possible to support .psb natively with the FreeMote library?

## Usage Guide:

TODO: This section.

### The following files are required:

Variable name | Description | Examples
--- | --- | ---
`rawFile` | The file to translate. | `A01.ks`, `backup.2024Jan10.json`
`parsingScript` | Defines how to read and write to `rawFile`. Required if working from a text file or if outputting to one but not if only using spreadsheet formats. | `resources/ templates/ KAG3_kirikiri_parsingTemplate.txt`
`spreadsheet` | Only required for output. Optional for input. | `resources/ backup.2024Jan10.xlsx`

### The following files are optional:

TODO: This section.

## Installation guide

`Current version: 2024.05.24 alpha`

Alpha means the software is undergoing radical changes and core features are still under development.

TODO: This section.

## Release Notes:

- The parsingScript is copied to scratchpad\temp.py and importing scratchpad\temp.py is hardcoded because the parsingScript must be imported as a python module to be executed if it is going to be executed within the context of the main script. This makes sense because:
    1. It makes it possible import without worrying about source path.
    1. There are reduced conflicts in name since there are many unsupported.
    1. The importlib library to handle special import handling is no longer necessary at the cost of needing the shutil library to copy the file in a high-level way.
    1. `scratchpad` is marked as a temporary directory in git, so it will not interfere with updating the program using git.
- The use of regex is limited to cases where it is absolutely required. [Regular expressions](//wikipedia.org/wiki/Regular_expression) are fundamentally very cryptic and very difficult to debug. In contrast, writing a new input parser from scratch hardly takes an afternoon, especially with the templates provided. The idea is to write enough of them for enough file types and eventually in enough languages such that adjusting a pre-existing one should be possible to anyone who knows the parser's language and type of file they are processing.
- Since Python is especially very easy to work with, it is used as the default language.
- In accordance with the project goals, parser readability and portability within an engine is a major concern but parsing speed is not.

### Concept art:

- The design concept behind py3AnyText2Spreadsheet is to create a platform that has a few predefined templates but mostly serves as a proxy for other parsers. The only limitation is that such parsers must somehow return and accept a chocolate.Strawberry(), a logical spreadsheet, for data processing or some other transferable data structure.
- In addition, this project also seperates out the script and text parsing logic from the translation logic of py3TranslateLLM. The intent is to maintain them as seperate projects that are eventually used together as part of a larger workflow to translate arbitrary files/data.
- The true name for this program is AnyText2ChocolateStrawberry named after the chocolate.Strawberry() library that is the core data structure of this program py3TranslateLLM.

### Regarding Settings Files:

- These are optional script.ini files. Instead of defining a lot of settings directly in the input(), output() functions, settings defined in the script.ini will be made available as a Python dictionary.
- The idea is that these script.ini files may be less intimidating to edit for non-programmers and potentially allow the same script to adjust its behavior for different contents without directly updating them.
- The text formats used for templates and settings (.ini .txt) have their own syntax:
    - `#` indicates that line is a comment.
    - Values are specified by using `item=value` Example:
        - `paragraphDelimiter=emptyLine`
    - Empty lines are ignored.
- TODO: Update this part.
- For the text formats used for input (.txt, .ks, .ts), the inbuilt parser will use the user provided settings file to parse the file.
    - A settings file is required when parsing such raw text files.
    - Examples of text file parsing templates can be found under `resources/templates/`.

#### Regarding various dictionaries and chararacterNames.csv:

TODO: This section.

-  There are a lot of dictionary.csv files involved. Understanding the overall flow of the program should clarify how to use them:
1. If `fileToTranslate` is a text file, the following occurs:
    1. Settings related to parsing dialogue from `parsingSettingsFile` are considered.
    1. If present, `characterNamesDictionary` is also considered for which lines not to ignore in creating paragraphs from `fileToTranslate`.
    1. The untranslated dialogue paragraphs are then written to the first column of `mainSpreadsheet`.
1. Settings in this parsing template are considered as they relate to word wrap and outputing the translation into the text files (.txt, .ks, .ts).
1. The right most entry in each row is written to a copy of the text.ks file.
1. `postWritingToFileDictionary` is considered. This file is mostly intended to fix encoding errors when doing baseEncoding -> unicode -> baseEncoding conversions since codec conversions are not lossless.

### Regarding XLSX

- XLSX (XML... TODO: This part.) is the native format used in py3AnyText2Spreadsheet to store data internally during processing and should be the most convenient way to edit translated entries directly without any.
- Here are some free and open source software ([FOSS](//en.wikipedia.org/wiki/Free_and_open-source_software)) office suits that can read and write the spreadsheet formats (.csv, .xlsx, .xls, .ods):
    - Apache [OpenOffice](//www.openoffice.org). [License](//www.openoffice.org/license.html) and [source](//openoffice.apache.org/downloads.html). Note: Can read but not write to .xlsx.
    - [LibreOffice](//www.libreoffice.org). [License](//www.libreoffice.org/about-us/licenses) and [source](//www.libreoffice.org/download/download-libreoffice/).
    - [OnlyOffice](//www.onlyoffice.com/download-desktop.aspx) is [AGPL v3](//github.com/ONLYOFFICE/DesktopEditors/blob/master/LICENSE). [Source](//github.com/ONLYOFFICE/DesktopEditors).

### Text Encoding:

- Read the [Text Encoding](//github.com/gdiaz384/py3TranslateLLM/wiki/Text-Encoding) wiki entry.
- After reading the above wiki entry, the rest of this section should make more sense.
- For compatability reasons, data gets converted to binary strings for stdout which can result in the console sometimes showing utf-8 hexadecimal (hex) encoded unicode characters, like `\xe3\x82\xaf\xe3\x83\xad\xe3\x82\xa8`, especially with `debug` enabled. To convert them back to non-ascii chararacters, like `クロエ`, dump them into a hex to unicode converter.
    - Example: [www.coderstool.com/unicode-text-converter](//www.coderstool.com/unicode-text-converter)
- Some character encodings cannot be converted to other encodings. When such errors occur, use the following error handling options:
    - [docs.python.org/3.7/library/codecs.html#error-handlers](//docs.python.org/3.7/library/codecs.html#error-handlers), and [More Examples](//www.w3schools.com/python/ref_string_encode.asp) -> Run example.
    - The default error handler for input files is `strict` which means 'crash the program if the encoding specified does not match the file perfectly'.
    - On Python >= 3.5, the default error handler for the output file is `namereplace`.  This obnoxious error handler:
        - Makes it obvious that there were conversion errors.
        - Does not crash the program catastrophically.
        - Makes it easy to do ctrl+f replacements to fix any problems.
            - Tip: Use `postWritingToFileDictionary` or [py3stringReplace](//github.com/gdiaz384/py3stringReplace) to automate these ctrl+f replacements.
    - If there are more than one or two such conversion errors per file, then the chosen file encoding settings are probably incorrect.
- If the `chardet` library is available, it will be used to try to detect the character encoding of files via heuristics. While this imperfect solution is obviously very error prone, it is still better to have it than not.
    - To make it available: `pip install chardet`
    - If it is not available, then everything is assumed to be `utf-8` unless otherwise specified.

## Regarding Python Library Dependencies:

- py3AnyText2Spreadsheet was developed on Python 3.7.6.
- It is not necessarily clear what versions work with what other versions, in part due to the shenanigans of some developers creating deliberate incompatibilities, so just install whatever and hope it works.

Library name | Required, Reccomended, or Optional | Description | Install command | Version used to develop py3AnyText2Spreadsheet
--- | --- | --- | --- | ---
[openpyxl](//pypi.python.org/pypi/openpyxl) | Required. | Used for main data structure and Microsoft Excel Document (.xlsx) support. | `pip install openpyxl` | 3.1.2
chocolate | Required. | Has various functions to manage using openpyxl as a data structure. | Included with py3AnyText2Spreadsheet. | Unversioned.
dealWithEncoding | Required. | Handles text codecs and implements `chardet`. | Included with py3AnyText2Spreadsheet. | 0.1 2024Jan21.
[chardet](//pypi.org/project/chardet) | Reccomended. | Improves text codec handling. | `pip install chardet` | 5.2.0
[xlrd](//pypi.org/project/xlrd/) | Optional. | Provides reading from Microsoft Excel Document (.xls). | `pip install xlrd` | 2.0.1
[xlwt](//pypi.org/project/xlwt/) | Optional. | Provides writing to Microsoft Excel Document (.xls). | `pip install xlwt` | 1.3.0
[odfpy](//pypi.org/project/odfpy) | Optional. | Provides interoperability for Open Document Spreadsheet (.ods). | `pip install odfpy` | 1.4.1

Libraries can also require other libraries.
- odfpy requires: `defusedxml`.
- py3AnyText2Spreadsheet and the libraries above also use libraries from the Python standard library. For an enumeration of those, check the source code.
- openpyxl - The latest version of openpyxl requires Python [3.6? 3.7?]
- chocolate which implements openpyxl for use as a data structure. It also uses the other libraries that handle various types of spreadsheets.
- chardet The latest version of chardet requires Python 3.7+.
- Python 3.4+ Standard library. TODO: Test this. 

## Licenses:

- Python standard library's [license](//docs.python.org/3/license.html).
    - For an enumeration of the Python standard libraries used in this program, check the source code.
    - For the source code, open the Python installation directory on the local system `Python310\libs\site-packages\`.
- [openpyxl](//pypi.python.org/pypi/openpyxl)'s [license](//foss.heptapod.net/openpyxl/openpyxl/-/blob/3.1.2/LICENCE.rst) and [source code](//foss.heptapod.net/openpyxl/openpyxl).
- [chardet](//pypi.org/project/chardet)'s license is [LGPL v2+](//github.com/chardet/chardet/blob/main/LICENSE). [Source code](//github.com/chardet/chardet).
- [odfpy](//pypi.org/project/odfpy)'s, license is [GPL v2](//github.com/eea/odfpy/blob/master/GPL-LICENSE-2.txt). [Source code](//github.com/eea/odfpy).
- [xlrd](//pypi.org/project/xlrd)'s [license](//github.com/python-excel/xlrd/blob/master/LICENSE) and [source code](//github.com/python-excel/xlrd).
- [xlwt](//pypi.org/project/xlwt/)'s [license](//github.com/python-excel/xlwt/blob/master/LICENSE) and [source code](//github.com/python-excel).
- py3AnyText2Spreadsheet and the associated libraries immediately under `resources/` are [GNU Affero GPL v3](//www.gnu.org/licenses/agpl-3.0.html).
    - However, the external plugins (.py, .ini, .rb, .js, etc) available under resources/templates/* may have their own licenses. Check their source code for details.
    - If they say to see the main program, then they share the same license as py3AnyText2Spreadsheet.
