"""
Google Reader 0.2
Copyright (C) 2009  Matt Behrens <askedrelic@gmail.com> http://asktherelic.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Convenience methods and data types for working with the "unofficial" Google Reader API.
Google may break this at anytime, not my fault.

"""

import urllib
import urllib2
import time
import xml.dom.minidom
import sys
import simplejson as json

#Set due to ascii/utf-8 problems with internet data
reload(sys)
sys.setdefaultencoding( "latin-1" )

class Feed:
    """
    Class for representing an individual feed.
    """

    def __str__(self):
        return "<%s, %s>" % (self.title, self.url)

    def __init__(self, title, url, categories=None):
        """
        Key args:
        title (str)
        url (str, possible urlparse obj?)
        categories (list) - list of all categories a feed belongs to, can be empty
        """
        self.title = title
        self.url = url
        self.categories = categories

class GoogleReader:
    """
    Class for using the unofficial Google Reader API and working with 
    the data it returns.

    Requires valid google username and password.
    """

    def __str__(self):
        return "<Google Reader object: %s>" % self.username

    def __init__(self, username, password):
        """
        Key args:
        username (str)
        password (str)

        Sets up secure Reader connection via _getToken and _getSID or fails.
        """
        self.username = username
        self.password = password
        self.sid = self._getSID()
        self.token = self._getToken(self.sid)
        self.feedlist = []

    def toJSON(self):
        """
        TODO: build a json object to return via ajax
        """
        pass

    def getFeeds(self):
        """
        Returns a list of Feed objects containing all of a users subscriptions.
        """
        return self.feedlist

    def getReadingList(self):
        """
        Returns a list of everything the user still has to read?
        """
        return self._httpGet('http://www.google.com/reader/api/0/stream/contents/user/-/state/com.google/reading-list')

    def getUserInfo(self):
        """
        Returns a dictionary of user info that google stores.
        """
        userJson = self._httpGet('http://www.google.com/reader/api/0/user-info')
        return json.loads(userJson)

    def getUserHumanAge(self):
        """
        Returns the human readable date of when the user signed up for google reader.
        """
        userinfo = self.getUserInfo()
        timestamp = int(float(userinfo["signupTimeSec"]))
        return time.strftime("%m/%d/%Y %H:%M", time.gmtime(timestamp))

    def _httpGet(self, url, extraargs={}):
        """
        Convenience method for requesting to google with proper cookies/params.
        """
        #ck is a timecode to help google with caching
        params = urllib.urlencode( {'ck':time.time(), 'client':'lolbot'} )
        if len(extraargs):
            params += '&' + urllib.urlencode( extraargs )
        req = urllib2.Request(url + "?" + params)
        req.add_header('Cookie', 'SID=%s;T=%s' % (self.sid, self.token))
        r = urllib2.urlopen(req)
        data = r.read()
        r.close()
        return data

    def _httpPost(self, request):
        pass

    def buildSubscriptionList(self):
        """
        Hits Google Reader for a users's alphabetically ordered list of feeds.

        Returns true if succesful.
        """
        xmlSubs = self._httpGet('http://www.google.com/reader/api/0/subscription/list')

        #Work through xml list of subscriptions
        dom = xml.dom.minidom.parseString(xmlSubs)
        #Object > List > subscription objects
        subs = dom.firstChild.firstChild
        for sub in subs.childNodes:
            #Work through the dom for the important elements
            url = str(sub.firstChild.firstChild.data.lstrip('feed/'))
            title = str(sub.childNodes[1].firstChild.data)
            categories = sub.childNodes[2]
            #Build a python list of Feeds from Dom elements
            catList = []
            for cat in categories.childNodes:
                catList.append(cat.childNodes[1].firstChild.data)
            #Add Feed to the main list
            feed = Feed(title,url,catList)
            self._addFeeds(feed)

        return True
        
    def _addFeeds (self, feed):
        self.feedlist.append(feed)

    def _getSID(self):
        """
        First step in authorizing with google reader.

        Request to google returns 4 values, SID is the only value we need.
        """
        params = urllib.urlencode( {'service':'reader','Email':self.username,'Passwd':self.password} )
        try:
            conn = urllib2.urlopen('https://www.google.com/accounts/ClientLogin', params)
            data = conn.read()
            conn.close()
        except Exception:
            print "Error getting the SID, have you entered a correct username and password?"
            sys.exit()

        #Strip newline and non SID text.
        sid = data[4:208].strip()
        return sid

    def _getToken(self, sid):
        """
        Second step in authorizing with google reader.
        Requires SID from first step.

        Request to google returns just a token value.
        """
        req = urllib2.Request('http://www.google.com/reader/api/0/token')
        req.add_header('Cookie', 'name=SID;SID=%s;domain=.google.com;path=/;expires=1600000' % sid)
        try:
            conn = urllib2.urlopen(req)
            token = conn.read()
            conn.close()
        except Exception:
            print "Error getting the token."
            sys.exit()

        return token


def main():
    reader = GoogleReader('email addy','password')
    if reader.buildSubscriptionList():
        for feed in reader.getFeeds():
            print feed.title, feed.url, feed.categories

if __name__ == '__main__':
    main()
