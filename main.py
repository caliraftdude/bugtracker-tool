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


def createdetailedreport():
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
                    report += buildrow(row, True)

                    # Skip processing detail page for header
                    continue
                if index > 77:   # This is just for testing...
                    pass
                if index > 125:  # this explodes at 78.. which is odd, I thought there would be way more room for this..
                    break
                    
                # Build table tow
                report += buildrow(row)

                url = _buildurl(row[2])
                page_list.append( queryandcleanurl(url) )

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


def buildrow(data:list, isheader:bool=False):
    """

    Parameters
    ---------

    Returns
    -------

    Raises
    ------

    """
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

'''
# Dictionary to translate a status code to an error message
status_code_to_msg = {400:"400 Bad request.  The url is wrong or malformed\n",
                      401:"401 Unauthorized.  The client is not authorized for this action or auth token is expired\n",
                      404:"404 Not Found.  The server was unable to find the requested resource\n",
                      415:"415 Unsupported media type.  The request data format is not supported by the server\n",
                      422:"422 Unprocessable Entity.  The request data was properly formatted but contained invalid or missing data\n",
                      500:"500 Internal Server Error.  The server threw an error while processing the request\n",
}
# Handle 4xx and 5xx errors here.  Common 4xx and 5xx REST errors here
if not (error_message := status_code_to_msg.get(response.status_code) ):
    error_message = f"{response.status_code}.  Uncommon REST/HTTP error"



import urllib.error
try:
    post = urllib.request.urlopen(request)
    print(post.__dict__)
except urllib.error.HTTPError as e:
    print(e.__dict__)
except urllib.error.URLError as e:
    print(e.__dict__)


except urllib.error.URLError as e: ResponseData = e.read().decode("utf8", 'ignore')

https://proxiesapi.com/articles/handling-url-errors-gracefully-in-python-urllib

# - Generic except tree
import urllib.request
import urllib.error

try:
    response = urllib.request.urlopen('http://httpbin.org/status/400')
except urllib.error.HTTPError as err:
    if err.code == 400:
        print('Bad request!')
    if err.code == 401:
        print('Unauthorized!')
    if err.code == 404:
        print(f'A HTTPError was thrown: {err.code} {err.reason}')
    if err.code == 500:
        print('Internal server error!')    
    else:
        print(f'An HTTP error occurred: {err}')


To fix HTTP errors in Python, the following steps can be taken:
    Check the network connection and ensure it is stable and working.
    Check the URL being accessed and make sure it is correct and properly formatted.
    Check the request parameters and body to ensure they are valid and correct.
    Check whether the request requires authentication credentials and make sure they are included in the request and are correct.
    If the request and URL are correct, check the HTTP status code and reason returned in the error message. This can give more information about the error.
    Try adding error handling code for the specific error. For example, the request can be attempted again or missing parameters can be added to the request.


import urllib.request
import urllib.error

max_attempts = 3  # - for something like a timeout?
for retry in range(max_attempts):
    try: 
        response = urllib.request.urlopen("http://flaky.site")
        break
    except urllib.error.URLError:
        if retry < max_attempts-1:
            continue
        else:
            print("Site appears to be down")
            break



request = urllib2.Request('http://www.example.com', postBackData, { 'User-Agent' : 'My User Agent' })

try: 
    response = urllib2.urlopen(request)
except urllib2.HTTPError, e:
    checksLogger.error('HTTPError = ' + str(e.code))
except urllib2.URLError, e:
    checksLogger.error('URLError = ' + str(e.reason))
except httplib.HTTPException, e:
    checksLogger.error('HTTPException')
except Exception:
    import traceback
    checksLogger.error('generic exception: ' + traceback.format_exc())

'''

def queryandcleanurl(url):
    """

    Parameters
    ---------

    Returns
    -------

    Raises
    ------

    """
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

    except HTTPError as e:
        # Need to catch and handle 404s and so on...
        print('Error code: ', e.code)
    except URLError as e:
        # do something
        print('Reason: ', e.reason)

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



if __name__ == "__main__":
    homedir = getcwd()
    outdir = homedir + "\\out"
    rawdir = homedir + "\\raw"
    csvdir = homedir + "\\csv"
    reportdir = homedir + "\\report"
    #createdetailedreport()
    main()


