#!/usr/bin/python
import sys
from os import scandir, getcwd, path
from os.path import isdir, splitext, split
import ntpath
import re
import csv
try:
    import urllib.request, urllib.parse
    from urllib.error import URLError, HTTPError
    from lxml import html
    from bs4 import BeautifulSoup, Tag
except ImportError:
    raise ImportError('Missing BS4, try:  pip install beautifulsoup4 and re-run')

# These are better handled at the global level
homedir = str()
outdir = str()
rawdir = str()
csvdir = str()
reportdir = str()

# Put this in an easy to find location for modification if desired
report_header = r'''<!DOCTYPE html><html><head><style>table {  font-family: arial, sans-serif;  border-collapse: collapse;  width: 100%;  word-wrap:break-word;}th {  border: 1px solid #dddddd;  text-align: left;  padding: 8px;  white-space: nowrap;}td {  border: 1px solid #dddddd;  text-align: left;  padding: 8px;}tr:nth-child(even) {  background-color: #dddddd;}h1 {  border-bottom: 5px solid red;}</style></head><body><h1>Bug List</h1>'''
report_footer = r'''</body></html>'''
empty_report_header = r'''<html lang="en"><body><main><div class="bug-template"><div class="container"><div class="row"><div class="col-md-12"></div></div><div class="row"><div class="col-md-12 middlecontent"><div class="row"><div class="col-sm-12 col-md-12">'''
empty_report_footer = r'''<p class="last-modified"><span class="standard-text standard-field">   </span></p></div></div></div></div></main></body></html>'''

class GeneralFailure(Exception):
    pass

class NotADirectory(Exception):
    pass

class UnfixableException(Exception):
    """
    An issue that cannot be resolved or worked around, so the program will exit.
    """
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

#raise InvalidURL("The url is invalid", url)


def main():
    """
    Main entry point into program, walks through the different parts of processing the files

    Parameters
    ---------
    Nothing

    Returns
    -------
    Nothing on success
    -1 on error

    Raises
    ------
    None

    """
    try:
        # Get the list of files in the rawdir
        if False == (files := getFileList(rawdir) ):
            raise GeneralFailure("Error finding anything to process in the rawdir... exiting")

        # Process the raw files and put the clean output into outdir
        if False == processRawFiles(files):
            raise GeneralFailure("Error trying to process raw files in raw dir to the out folder... exiting")

        # Get the list of files in the outdir
        if False == (files := getFileList(outdir) ):
            raise GeneralFailure("Error finding anything to process in the outdir... exiting")

        # Process the cleaned text files into CSV files, output into csvdir.  Also create a combined csv file
        if False == (processCSVFiles(files) ):
            raise GeneralFailure("Error trying to process the txt files into csv files or combining them into an ALL.csv")

        # Create the html report
        createDetailedReport()

    except GeneralFailure as e:
        print(e.args)
        exit(-1)


def getFileList(dir:str):
    """
    getFileList is used to collect a list of files within a given directory.  Will catch a permissions
    issue and return an error.

    Parameters
    ---------
    dir : str           String containing the directory to be scanned

    Returns
    -------
    List of files on success
    None on failure

    Raises
    ------
    None
    """
    try:
        if isdir(dir):
           # Get the list of files in the directory
            files = [entry.path for entry in scandir(dir) if entry.is_file()]
            return files

        raise NotADirectory()

    except TypeError as e:
        print('Improper parameter passed to getFileList: {}'.format(e.args) )
        return False
    except PermissionError as e:
        print('Unable to parse directory {} due to permissions.'.format(dir) )
        return False
    except NotADirectory:
        print('{} is not a directory'.format(dir) )
        return False

def processRawFiles(files:list):
    """
    processRawFiles Takes a list of files and for each one processes the 'dirty file', removing 
    unwanted text and formatting the bugs as one per line.  Writes to the outdir global as its output.

    Parameters
    ---------
    files : list        List of files to process
    
    Returns
    -------
    True on success
    False on Failure

    Raises
    ------
    None
    """
    # Process each file
    try:
        for file in files:
            if file.endswith(".txt"): 
                # only .txt files are accepted, and the name of the file should ONLY be the family name of the buglist
                family = splitext(ntpath.basename(file))[0]
                processRaw(file, family)
            else:
                print("non-text file found in directory... skipping.")

        return True

    except IOError as e:
        print('Operation failed: %s' % e.strerror)
        return False
    except OSError as e:
        if e.errno in (errno.EACCES, errno.EPERM):
            print('Permission denied accessing: {}'.format(file))
        elif e.errno == errno.ENOENT:
            print('File not found accessing: {}'.format(file))
        return False



def processRaw(fname:str, family:str):
    """
    processRaw performs the conversion of a single file by finding lines via regex and deleting them.  It
    also moves around some of the data and single-lines each bug so that its easy to convert into a CSV.
    Note it does NOT catch file/permission errors for file access.  Output files are written to the
    global outdir.

    Parameters
    ---------
    fname : string          The filename to convert
    family : string         The "family" of the bugs (LTM, GTM, TMOS, etc..)

    Returns
    -------
    Nothing

    Raises
    ------
    Nothing

    """
    # Set up regex signatures to clean garbage out of file    
    bt = re.compile(r"^Bug Tracker")
    md = re.compile(r"^Modification Date:.*")

    # Read in file and process, then write out to the output directory
    with open(fname) as fp:
        lines = fp.readlines()
        bt_removed = [i for i in lines if not bt.match(i)]
        md_removed = [i for i in bt_removed if not md.match(i)]

        merged = [family+" "+j.replace("\n", " ")+i for i,j in zip(md_removed[::2], md_removed[1::2])]

        out = outdir+"\\"+ntpath.basename(fname)
        with open(out, 'w') as fp_out:
            fp_out.writelines(merged)


def processCSVFiles(files:list):
    """
    processCSVFiles Takes a list of files in the outdir directory, and then processes each one into a
    CSV file.  It then combines all the csvfiles into a single 'all' csv file.

    Parameters
    ---------
    files : list        List of files to process
    
    Returns
    -------
    True on success
    False on Failure

    Raises
    ------
    None
    """
    try:
        # Convert each file into a csv
        for file in files:
            processCSV(file)

        # Create a single csv file, and strip headers - promote the return value to the caller
        return combineCSVFiles()

    except IOError as e:
        print('Operation failed: %s' % e.strerror)
        return False
    except OSError as e:
        if e.errno in (errno.EACCES, errno.EPERM):
            print('Permission denied accessing: {}'.format(file))
        elif e.errno == errno.ENOENT:
            print('File not found accessing: {}'.format(file))
        return False


def processCSV(file):
    """
    processCSVF Takes a single text file (formated into single lines) and outputs a csv file into csvdir.
    Exceptions are NOT caught and processed here but rather roll up to the function that processes the 
    entire directory.

    Parameters
    ---------
    files : list        List of files to process
    
    Returns
    -------
    None

    Raises
    ------
    None
    """
    # Open the destination file
    with open(file) as fp:
        csvfname = splitext(split(file)[1])[0]+'.csv'

        # Open the source file
        with open(csvdir+"\\"+csvfname, 'w', newline='') as csvfile:
            # Setup the csv writer, read the lines into 'lines' and then write the header for the CSV file
            csvfp = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
            lines = fp.readlines()
            _writecsvheader(csvfp)

            # Walk each line and write it out
            for line in lines:
                words = line.split()
                _writecsvline(csvfp, words)

def _writecsvline(csvfp, words):
    """ Helper fuunction to write a line in the csv file and deal with the occasional burp of a K article """
    if words[2] == '|':
        # Handle a K article number in the line
        row = [words[0], words[1], words[6].rstrip(':'), words[3], " ".join(words[7::])]
    else:
        # Normal case    
        row = [words[0], words[1], words[4].rstrip(':'), "", " ".join(words[5::])]

    csvfp.writerow(row)

def _writecsvheader(csvfp):
    """ Helper function to write out a header - this should be refactored so its not static.. but for now its fine """
    csvfp.writerow(['Family', 'Bug severity', 'Bug ID', 'K Article', 'Description'])

def combineCSVFiles():
    """
    combineCSVFiles takes the csvdir, and writes the first file to a 'combined file'.  It then takes the remaining
    csv file, strips off the header (as we only need one) and the appends each of them.
    Parameters
    ---------
    None

    Returns
    -------
    True on success
    False on Failure

    Raises
    ------
    None
    """
    # Get the list of files in the csvdir
    if False == (files := getFileList(csvdir) ):
        return False

    # Output filename       
    filename = csvdir + "\\ALL.csv"

    with open(filename, 'w') as dest:
        # enumerate the list of files and keep an index
        for index, file in enumerate(files):
            with open(file) as source:
                if index == 0:
                    # For the first file, copy the entire thing in
                    dest.write(source.read())
                else:
                    # For the remaining files, skip the header (first line) and then copy the rest in.
                    for ln, line in enumerate(source):
                        if ln == 0:
                            continue
                        else:
                            dest.write(line)

    return True


def createDetailedReport():
    """

    Parameters
    ---------

    Returns
    -------

    Raises
    ------

    """
    try:
        # Get the list of files in the directory
        buglistfile = csvdir+"\\ALL.csv"
        report_name = reportdir+"\\BugScrub.html"
        report = str()

        # Build Report
        with open(buglistfile, newline='') as fp:
            reader = csv.reader(fp, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            page_list = list()

            # Build report
            report += report_header

            for index, row in enumerate(reader):           
                if index == 0:
                    # Build header for bug list
                    report += "<table>"
                    report += _buildrow(row, True)

                    # Skip processing detail page for header
                    continue
                    
                # Build table tow
                report += _buildrow(row)

                url = _buildurl(row[2])
                if False == (soup := queryAndCleanURL(url) ):
                    # Unable to get the detailed HTML, so insert something generic and move on
                    page_list.append( _buildEmptyDetailedReport(row[2]) )
                else:
                    # Did get the processed 
                    page_list.append( soup )

            # Close the table, and start next section
            report += "</table>"
            report += "<h1>Bug Detail</h1>"

            # Walk the page_list and add the detailed items to the report
            for page in page_list:
                report += page.prettify()
                report += "<hr>"
            
            # Close the report
            report += report_footer

            # Create HTML 
            outsoup = BeautifulSoup(report, 'lxml')
            with open(report_name, "w") as outfp:
                outfp.write(outsoup.prettify())

    except IOError as e:
        print('Operation failed: %s' % e.strerror)
    except Exception as e:
        print('Unhandled exception: %s' % e.strerror)


def _buildrow(data:list, isheader:bool=False):
    """ Helper function to make it easier to loop through and build rows of data for tables """
    buffer = "<tr>"
    for item in data:
        if isheader:
            buffer += "<th>{}</th>".format(item)
        else:
            buffer += "<td>{}</td>".format(item)
    buffer += "</tr>"
    return buffer


def _buildurl(bugid):
    """ Helper function to build a url """
    return "https://cdn.f5.com/product/bugtracker/ID{}.html".format(bugid)


def queryAndCleanURL(url):
    """
    queryAndCleanURL takes a url and then pulls the resource down.  Once it has the html, it 
    processes it by removing unwanted tags and content and if successful returns the 'soup' obj
    to the caller.  The url request is bracketed in a loop that will make 3 attempts - if there
    is a URLError, it will retry accordingly and if it finally fails out, catch the exception and
    return false.  A break helps the loop drop out on a first (or subsequent) success and the 
    soup is thusly returned.

    Parameters
    ---------
    url : string        the url to query

    Returns
    -------
    soup object on success
    False on failure

    Raises
    ------
    None
    """
    max_attempts = 3
    for retry in range(max_attempts):
        try:
            with urllib.request.urlopen(url) as fp:
                buffer = fp.read().decode("utf8")
                soup = BeautifulSoup(buffer, 'lxml')

                # Remove unwanted garbage
                _deletetag(soup, 'head')
                _deletetag(soup, 'ul', {"class": "bread-crumbs"})
                _deletetag(soup, 'iframe', {"src": "https://www.googletagmanager.com/ns.html?id=GTM-PPZPQ6" })
                _deletetag(soup, 'script', {"type": "text/javascript"})
                _deletetag(soup, 'div', {"class": "header"})
                _deletetag(soup, 'footer' )
                _deletedumboutliertag(soup, 'h4', "Guides & references")
                _deletetag(soup, 'a', {"href": "https://my.f5.com/manage/s/article/K10134038"} )

            break

        except HTTPError as err:
            if err.code == 400:
                print(f'{err.code} Bad request reaching {url}')
            if err.code == 401:
                print(f'{err.code} Unauthorized while attempting {url}')
            if err.code == 404:
                print(f'{err.code} File or resource not found while trying {url}' )   
            if err.code == 500:
                print(f'{err.code} Internal server error attempting {url}')    
            else:
                print(f'A HTTPError was thrown: {err.code} {err.reason}')
            return False

        except URLError as err:
            if retry < (max_attempts-1):
                continue
            else:
                print(f'Unable to reach {url} after 3 attempts: {str(err.reason)}' )
            return False

    return soup


def _deletetag(soup, tag:str, attrs:dict=None):
    """Helper function to delete a tag in BS4 soup """
    removals = soup.find_all(tag, attrs)
    for match in removals:
        match.decompose()

def _deletedumboutliertag(soup, tag:str, crap:str):
    """Helper function to delete a PITA tag in BS4 soup """
    removals = soup.find_all(tag, text = re.compile(crap) )
    for match in removals:
        match.decompose()

def _buildEmptyDetailedReport(id:str):
    """ Helper function to build a generic detailed entry if we cannot get the detailed page """
    buffer = empty_report_header
    buffer += f'<h2 class="bug-title">Bug ID {id}: Unable to retrieve detailed bug information</h2>'
    buffer += empty_report_footer

    soup = BeautifulSoup(buffer, 'lxml')
    return soup

if __name__ == "__main__":
    homedir = getcwd()
    outdir = homedir + "\\out"
    rawdir = homedir + "\\raw"
    csvdir = homedir + "\\csv"
    reportdir = homedir + "\\report"

    main()


