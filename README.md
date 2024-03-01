# py3AnyText2Spreadsheet

Parses arbitrary text files to create spreadsheets that can be used in natural language translation.

The project goals are to:
- Support a wide variety of different parsers, including non-Python ones, for various textual formats.
- Extract strings to translate from various texual formats and insert them back after translation by using spreadsheets as the interchange format.

- Currently semi-supported:
    - KAG3 used in the kirikiri game engine (.ks).
    - Support for JSON produced by [VNTranslationTools](//github.com/arcusmaximus/VNTranslationTools).
    - Support for arbitrary text files, including JSON, via user defined parse files.

## Support is planned for:

- Random text files (.txt).
- DDWSystem2013, DDWorks Game System, fwDDSystem, [vndb.org](https://vndb.org/r?f=fwDDSystem-)
- JSON support:
    - Support for UlyssesWu's [FreeMote](//github.com/UlyssesWu/FreeMote) text files converted from PSB to JSON.
        - Is it possible to support .psb natively?
    - Support for JSON where all entries and are nested under `contents` and there is no additional nesting.
        - Multiple entries must be in a list surrounded by square brackets `[ ]`.
    - To process additional types of JSON, open an issue and provide an `example.json`.
- KAG3 used in TyranoBuilder (.ks/.ts?).
- Better documentation.

## Maybe:

- RPGM (MZ, MV, Ace... )

## Release Notes:

- The true name for this program is AnyText2ChocolateStrawberry.

## Dependencies

- Python 3.4+ TODO: Test this.
- openpyxl - The latest version of openpyxl requires Python [3.6? 3.7?]
- chardet The latest version of chardet requires Python 3.7+.


## License:

- Python's [license].
    - For an enumeration of the Python standard libraries used in this program, check the source code.
- The external plugins (.py) available under resources/templates/* may have their own licenses.
- Main program: GNU AGPLv3
