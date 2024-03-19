#!/usr/bin/python
import sys
import os
import ntpath
import re
import csv
try:
    import urllib.request, urllib.parse
    from urllib.error import URLError, HTTPError
    from lxml import html
    from bs4 import BeautifulSoup, Tag
except ImportError:
    raise ImportError('Missing BS4, try:  pip install beautifulsoup4 and rerunning')

# These are better handled at the global level
homedir = str()
outdir = str()
rawdir = str()
csvdir = str()
reportdir = str()

# Put this in an easy to find location for modification if desired
report_header = r'''<!DOCTYPE html><html><head><style>table {  font-family: arial, sans-serif;  border-collapse: collapse;  width: 100%;  word-wrap:break-word;}th {  border: 1px solid #dddddd;  text-align: left;  padding: 8px;  white-space: nowrap;}td {  border: 1px solid #dddddd;  text-align: left;  padding: 8px;}tr:nth-child(even) {  background-color: #dddddd;}h1 {  border-bottom: 5px solid red;}</style></head><body><h1>Bug List</h1>'''
report_footer = r'''</body></html>'''

def batch():
    try:
        # Get the list of files in the directory
        files = [entry.path for entry in os.scandir(rawdir) if entry.is_file()]

        # Process each file
        for file in files:
            if file.endswith(".txt"): 
                # only .txt files are accepted, and the name of the file should ONLY be the family name of the buglist
                family = os.path.splitext(ntpath.basename(file))[0]
                process(file, family)
            else:
                print("non-text file found in directory... skipping.")

        # Get the processed list of files
        files = [entry.path for entry in os.scandir(outdir) if entry.is_file()]
        
        # Convert each file into a csv
        for file in files:
            processCSV(file)

        # Create a single csv file, and strip headers
        combinecsvfiles()

    except IOError as e:
        print('Operation failed: %s' % e.strerror)

def process(fname:str, family:str):
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

def processCSV(file):
        with open(file) as fp:
            csvfname = os.path.splitext(os.path.split(file)[1])[0]+'.csv'
            with open(csvdir+"\\"+csvfname, 'w', newline='') as csvfile:
                csvfp = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
                lines = fp.readlines()
                writecsvheader(csvfp)

                for line in lines:
                    words = line.split()
                    writecsvline(csvfp, words)

def writecsvline(csvfp, words):
    if words[2] == '|':
        # Handle a K article number in the line
        row = [words[0], words[1], words[6].rstrip(':'), words[3], " ".join(words[7::])]
    else:
        # Normal case    
        row = [words[0], words[1], words[4].rstrip(':'), "", " ".join(words[5::])]

    csvfp.writerow(row)

def writecsvheader(csvfp):
    csvfp.writerow(['Family', 'Bug severity', 'Bug ID', 'K Article', 'Description'])

def combinecsvfiles():
    files = [entry.path for entry in os.scandir(csvdir) if entry.is_file()]
    filename = csvdir + "\\ALL.csv"

    with open(filename, 'w') as dest:
        for index, file in enumerate(files):
            with open(file) as source:
                if index == 0:
                    # For the first file, copy the entire thing in
                    dest.write(source.read())
                else:
                    # For the remaining files, strip off the header and then copy the rest in.
                    for ln, line in enumerate(source):
                        if ln == 0:
                            continue
                        else:
                            dest.write(line)

def createdetailedreport():
    try:
        # Get the list of files in the directory
        buglistfile = csvdir+"\\ALL.csv"
        report_name = homedir+"\\BugScrub.html"
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

                url = buildurl(row[2])
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
    buffer = "<tr>"
    for item in data:
        if isheader:
            buffer += "<th>{}</th>".format(item)
        else:
            buffer += "<td>{}</td>".format(item)
    buffer += "</tr>"
    return buffer


def buildurl(bugid):
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

    try:

        with urllib.request.urlopen(url) as fp:
            buffer = fp.read().decode("utf8")
            soup = BeautifulSoup(buffer, 'lxml')

            # Remove unwanted garbage
            deletetag(soup, 'head')
            deletetag(soup, 'ul', {"class": "bread-crumbs"})
            deletetag(soup, 'iframe', {"src": "https://www.googletagmanager.com/ns.html?id=GTM-PPZPQ6" })
            deletetag(soup, 'script', {"type": "text/javascript"})
            deletetag(soup, 'div', {"class": "header"})
            deletetag(soup, 'footer' )
            deletedumboutliertag(soup, 'h4', "Guides & references")
            deletetag(soup, 'a', {"href": "https://my.f5.com/manage/s/article/K10134038"} )

    except HTTPError as e:
        # Need to catch and handle 404s and so on...
        print('Error code: ', e.code)
    except URLError as e:
        # do something
        print('Reason: ', e.reason)

    return soup

def deletetag(soup, tag:str, attrs:dict=None):
    removals = soup.find_all(tag, attrs)
    for match in removals:
        match.decompose()

def deletedumboutliertag(soup, tag:str, crap:str):
    removals = soup.find_all(tag, text = re.compile(crap) )
    for match in removals:
        match.decompose()



if __name__ == "__main__":
    homedir = os.getcwd()
    outdir = homedir + "\\out"
    rawdir = homedir + "\\raw"
    csvdir = homedir + "\\csv"
    reportdir = homedir + "\\report"
    #batch()
    createdetailedreport()
