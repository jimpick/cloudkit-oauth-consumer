#! /usr/bin/python

# This is a modified version of the Fire Eagle Python tutorial

import httplib # used for talking to the CloudKit OAuth server
import oauth # the lib you downloaded
import urlparse

SERVER = 'labs.jimpick.com'
PORT = 9292
HOST = SERVER + ":" + str(PORT)

REQUEST_TOKEN_URL = "http://" + HOST + "/oauth/request_tokens"
ACCESS_TOKEN_URL = "http://" + HOST + "/oauth/access_tokens"
AUTHORIZATION_URL = "http://" + HOST + "/oauth/authorization"
QUERY_API_URL = "http://" + HOST

# key and secret you got from CloudKit OAuth when registering an application
CONSUMER_KEY = 'cloudkitconsumer'
CONSUMER_SECRET = ''

def pause(prompt='hit <ENTER> to continue'):
    return raw_input('\n'+prompt+'\n')

# pass an oauth request to the server (using
# httplib.connection passed in as param)
# return the response as a string
def fetch_response(oauth_request, connection, debug=True):
    url = oauth_request.to_url()
    o = urlparse.urlparse(url)
    connection.request(oauth_request.http_method, 
        o.path + '?' + o.query)
    response = connection.getresponse()
    s=response.read()
    if debug:
        print 'requested URL: %s' % url
        print 'server response: %s' % s
    return s

# main routine
def test_cloudkitauth():
    # setup some variables that we'll use when we actually
    # start doing things
    connection = httplib.HTTPConnection(SERVER, PORT)
        # a connection we'll re-use a lot
    consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
        # just a place to store consumer key and secret
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        # HMAC_SHA1 is CloudKit OAuth's preferred hashing method

    # get request token
    print '* Obtain a request token ...'

    # create an oauth request
    #oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
    #    http_url=REQUEST_TOKEN_URL)
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
        http_method='POST', http_url=REQUEST_TOKEN_URL)
    # the request knows how to generate a signature
    oauth_request.sign_request(signature_method, consumer, None)

    # use our fetch_response method to send the request to CloudKit OAuth
    resp=fetch_response(oauth_request, connection)
    print 'CloudKit OAuth response was: %s' % resp

    # if something goes wrong and you get an unexpected response,
    # you'll get an error on this next line
    # parse the response into an OAuthToken object
    token=oauth.OAuthToken.from_string(resp)
    print 'key: %s' % str(token.key)
    print 'secret: %s' % str(token.secret)

    # authorize the request token
    print '\n* Authorize the request token ...'

    # we don't need to sign this request
    auth_url="%s?oauth_token=%s" % (AUTHORIZATION_URL, token.key)

    # this time we'll print the URL, rather than fetching from it directly
    print 'Authorization URL:\n%s' % auth_url
    pause('Please go to the above URL and authorize the app ' +
        '-- hit <ENTER> when done.')

    # get access token
    print '\n* Obtain an access token ...'

    # note that the token we're passing to the new OAuthRequest is
    # our current request token
    #oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
    #    token=token, http_url=ACCESS_TOKEN_URL)
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
        http_method='POST', token=token, http_url=ACCESS_TOKEN_URL)
    oauth_request.sign_request(signature_method, consumer, token)
    resp=fetch_response(oauth_request, connection) # use our fetch_response
        # method to send the request to CloudKit OAuth
    print 'CloudKit OAuth response was: %s' % resp

    # now the token we get back is an access token
    # parse the response into an OAuthToken object
    token=oauth.OAuthToken.from_string(resp)

    print 'key: %s' % str(token.key)
    print 'secret: %s' % str(token.secret)

    # access protected resource
    print '\n* Access a protected resource ...'

    s=pause('enter a location:')
    params={}
    params['q']=s

    # for updates we must use HTTP POST
    # note the http_method='POST' param in the line below
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
        http_method='POST', token=token, http_url=QUERY_API_URL,
        parameters=params)
    oauth_request.sign_request(signature_method, consumer, token)
    # get the post data from oauth_request
    post_data=oauth_request.to_postdata()

    # set headers for POST request
    headers = {"Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"}

    print 'POSTing to %s' % QUERY_API_URL
    print 'sending headers: %s' % headers
    print 'sending data: %s' % post_data

    # do the POST
    connection.request('POST', QUERY_API_URL, oauth_request.to_postdata(),
        headers)
    print 'CloudKit OAuth says: %s' % connection.getresponse().read()
        # print the response


# app entry point
if __name__ == '__main__':
    test_cloudkitauth()
    print 'Done.'


