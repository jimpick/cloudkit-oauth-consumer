#! /usr/bin/python

'''
Example OAuth client for use with CloudKit
'''

# Modified from Yahoo's Fire Eagle Tutorial

#
# Licensing (BSD License)
#
# Copyright (c) 2008, Yahoo! Inc.
# All rights reserved.
#
# Unless otherwise specified, redistribution and use of this software in
# source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of Yahoo! Inc. or Fire Eagle nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission of Yahoo! Inc.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import httplib
import oauth
import pickle # for storing access token to file
import cgi # for playing with query strings
import urlparse
import urllib

# url escape
def escape(s):
    # escape '/' too
    return urllib.quote(s, safe='~')

# file to store access token
TOKEN_FILE = './access_token.pkl'

SERVER = 'localhost'
PORT = 9292
HOST = SERVER + ":" + str(PORT)

REQUEST_TOKEN_URL = "http://" + HOST + "/oauth/request_tokens"
ACCESS_TOKEN_URL = "http://" + HOST + "/oauth/access_tokens"
AUTHORIZATION_URL = "http://" + HOST + "/oauth/authorization"
QUERY_API_URL = "http://" + HOST

# key and secret you got from CloudKit when registering an application
CONSUMER_KEY = 'cloudkitconsumer'
CONSUMER_SECRET = ''

def pause(prompt='hit <ENTER> to continue'):
    return raw_input(prompt+'\n')

# pass an oauth request to the server (using httplib.connection passed in
# as param), return the response as a string
def fetch_response(oauth_request, connection, debug=True):
    url= oauth_request.to_url()
    o = urlparse.urlparse(url)
    connection.request(oauth_request.http_method,
        o.path + '?' + o.query)
    try:
        response = connection.getresponse()
        s=response.read()
        h=response.getheaders()
    except httplib.BadStatusLine, e:
        print "Bad Status Line"
        s="Error"
        h=[("Error", "Bad Status Line")]
    if debug:
        print 'requested URL: %s' % url
        print 'server response: %s' % s
    return s, h

# main routine
def test_cloudkit():

    # setup
    connection = httplib.HTTPConnection(SERVER, PORT) # a connection
        # we'll re-use a lot
    consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1() # HMAC_SHA1
        # is CloudKit's preferred hashing method

    # check if we've got a stored token
    try:
        pkl_file=open(TOKEN_FILE, 'rb')
        token=pickle.load(pkl_file)
        pkl_file.close()
    except:
        token=None
    if token:
        print 'You have an access token: %s' % str(token.key)
    else:
        # get request token
        print '* Obtain a request token ...'
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
            http_method='POST', http_url=REQUEST_TOKEN_URL) # create an
                # oauth request
        oauth_request.sign_request(signature_method, consumer, None) # the
            # request knows how to generate a signature
        resp,h=fetch_response(oauth_request, connection) # use our
            # fetch_response method to send the request to CloudKit
        print '\nCloudKit response was: %s' % resp
        # if something goes wrong and you get an unexpected response,
        # you'll get an error on this next line
        token=oauth.OAuthToken.from_string(resp) # parse the response into
            # an OAuthToken object
        print '\nkey: %s' % str(token.key)
        print 'secret: %s' % str(token.secret)

        # authorize the request token
        print '\n* Authorize the request token ...'
        # create a new OAuthRequest, this time for the AUTHORIZATION_URL
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
            http_method='POST', token=token, http_url=AUTHORIZATION_URL)
        oauth_request.sign_request(signature_method, consumer, token)
        # this time we'll print the URL, rather than fetching
        # from it directly
        full_url=oauth_request.to_url()
        print 'Authorization URL:\n%s' % full_url
        pause('Please go to the above URL and authorize the app -- ' +
              'hit <ENTER> when done.')

        # get access token
        print '\n* Obtain an access token ...'
        # note that the token we're passing to the new OAuthRequest is our
        # current request token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
            http_method='POST', token=token, http_url=ACCESS_TOKEN_URL)
        oauth_request.sign_request(signature_method, consumer, token)
        resp,h=fetch_response(oauth_request, connection) # use our
            # fetch_response method to send the request to CloudKit
        print '\nCloudKit response was: %s' % resp
        # now the token we get back is an access token
        token=oauth.OAuthToken.from_string(resp) # parse the response
            # into an OAuthToken object
        print '\nkey: %s' % str(token.key)
        print 'secret: %s' % str(token.secret)
        # try to store the access token for later user
        pkl_file=open(TOKEN_FILE, 'wb')
        pickle.dump(token, pkl_file)
        pkl_file.close()
        pause()
    # end if no token

    # access protected resource
    print '\n* Access a protected resource ...'
    print 'To try a query enter somthing like: %s' % QUERY_API_URL + "/notes"
    s=pause('enter a URL (empty string or <ENTER> to quit):')
    m=pause('enter method (GET/POST/PUT/DELETE/OPTIONS or' +
            'empty string or <ENTER> to quit):')
    while s and m:
        try:
            (path, query)=s.split('?',1)
            params=clean_params( cgi.parse_qs(query) )
        except ValueError:
            path=s
            params={}
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
            http_method=m, token=token, http_url=path, parameters=params)
        oauth_request.sign_request(signature_method, consumer, token)
        if m == 'POST' or m == 'PUT':
            headers = oauth_request.to_header(realm="http://" + SERVER + ":" + PORT)
            headers["Content-type"] = "application/x-www-form-urlencoded"
            headers["Accept"] = "*/*"
            headers["Accept-Encoding"] = "identity"
            headers["User-Agent"] = "cloudkit_oauth_client.py"
            d=pause('enter data:')
            post_data = str(d)
            o = urlparse.urlparse(path)
            url = o.path
            print '\n%sing to %s' % (m, url)
            print 'sending headers: %s' % headers
            print 'sending data: %s' % post_data
            connection.request(m, url, post_data, headers)
            try:
                r = connection.getresponse()
                print r.status, r.reason
                s = r.read()
                h=r.getheaders()
            except httplib.BadStatusLine, e:
                print "Bad Status Line"
                s = "Error"
                h=[("Error","Bad Status Line")]
        else:
            full_url=oauth_request.to_url()
            print '\n%s : %s' % (m, full_url)
            s,h=fetch_response(oauth_request, connection)
        print '\nthe server says: %s' % s
        print 'returned headers:'
        for hdr in h:
            print "  %s = %s" % hdr
        print 'To try a query enter somthing like: %s' % QUERY_API_URL
        s=pause('\nenter a URL (empty string or <ENTER> to quit):')
        m=pause('enter method (GET/POST/PUT/DELETE/OPTIONS or ' +
                'empty string or <ENTER> to quit):')

# cgi.parse_qs returns values as a list -- we want single values,
# we'll just keep the first for now...
def clean_params(p):
    for k in p.keys():
        p[k]=p[k][0]
    return p

# app entry point
if __name__ == '__main__':
    test_cloudkit()
    print 'Done.'
