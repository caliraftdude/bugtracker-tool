
# ![logo-small] Bugtracker-Tool
>This code is presented AS-IS with no warranty or support implied or otherwise and provided entirely free.

## About
Bugtracker-Tool is a tool used to simplify and streamline the process of building up a bugscrub.  It makes use of public resources found currently (2024.03.27) at this location [Bug Tracker](https://my.f5.com/manage/s/bug-tracker).  There are some specifics on how to properly 'feed' the data into the tool so that it will work (minimal effort is made to verify input format - so garbage in, even worse out).  Familiarize yourself with some of the details [here](./doc/README.md).

## Requirements
The tool isn't too esoteric but you will need the following:
- python 3.x, 3.15 or better should be fine
- BeautifulSoup, urllib, and lxml libraries for python
- Worked and tested on *nix and windows, but not extensively.

## Future Plans
This is an initial release of this tool to help me internally, deal with the tedious and time consuming chore of trying to produce a bugscub.  Its not meant to be the be-all, end-all of things but rather reduce the effort level from days/weeks to minutes/hours.  To that end, its a bit fragile and missing a lot of unit testing.  So:

- Add unit tests to deal with checking various boundary conditions like permissions on directories/files, access to resources, and especially the regex features for filtering.
- Improve filtering so that it can be applied at any stage of the processing and not just the report phase
- Integrate with APIs, should the become available, to populate the raw content automagically


[logo-tight]:    ./doc/img/logo_tight.png
[logo-small]:    ./doc/img/logo_small.png
