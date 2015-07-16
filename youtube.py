import json
import urllib2
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo


def is_mv(title):
    mv_words = ["MV", "M/V", "MUSIC VIDEO"]
    not_words = ["TEASER", "TRAILER"]

    title = title.upper()

    for mv_word in mv_words:
        if mv_word in title:

            for not_word in not_words:
                if not_word in title:
                    return False
            
            return True

    return False



sec_filename = "./.secret/secrets"
sec_file = open(sec_filename, "r")
sec = json.load(sec_file)
sec_file.close()

API_KEY = sec["api"]
QUERY_CHANNEL = "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forUsername="
QUERY_PLAYLIST = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId="

channel_name = "loenent"
playlist_id = "UUweOkPb1wVVH0Q0Tlj4a5Pw"  #loenent's uploads playlist
etag_filename = "etag"

#read cached etag
etag_file = open(etag_filename, "r")
etag = etag_file.read().strip()
etag_file.close()
#etag = "\"iDqJ1j7zKs4x3o3ZsFlBOwgWAHU/ch3qCP11h1vDtpXH7Aa5eJn8Tkz\""  #fake etag to force query

endpoint = "http://104.131.16.56/xmlrpc.php"
username = sec["user"]
password = sec["pass"]


# Channel request only needs to be done once to obtain the playlist ids
#request = QUERY_CHANNEL + channel_name + "&key=" + API_KEY
#response = urllib2.urlopen(request).read()

url = QUERY_PLAYLIST + playlist_id + "&key=" + API_KEY
request = urllib2.Request(url, headers={"If-None-Match": etag})

try:
    print "carrying out request"
    response = urllib2.urlopen(request)
    if (response.getcode() == 200):
        print "all ok"
        data = json.loads(response.read())

        #cache etag of current query
        etag = data["etag"]
        etag_file = open(etag_filename, "w")
        etag_file.write(etag)
        etag_file.close()

        #for playlistitem in data["items"]:
        playlistitem = data["items"][0]
        title = playlistitem["snippet"]["title"]
        videoid = playlistitem["snippet"]["resourceId"]["videoId"]

        #check if video is an mv first before posting
        if (is_mv(title)):
            wp = Client(endpoint, username, password)
            post = WordPressPost()
        
            post.title = playlistitem["snippet"]["title"]
            content = '<iframe width="560" height="315" src="https://www.youtube.com/embed/{}" frameborder="0" allowfullscreen></iframe>'.format(videoid)
            content += "\n\n"
            content += playlistitem["snippet"]["description"]
            post.content = content
            #thumbnail at playlistitem["snippet"]["thumbnails"]["default"]["url"]
            post.terms_names = {
                "post_tag": ["test", "post"],  #todo: parse title to get tags?
                "category": ["MV"]
            }
            post.post_status = "publish"
            
            wp.call(NewPost(post))
            print "post published"

except urllib2.HTTPError, err:
    if (err.code == 404):
        print "resource not found"
    elif (err.code == 403):
        print "access denied"
    elif (err.code == 304):
        print "data not modified since last etag"
    else:
        print "Something happened!", err
except urllib2.URLError, err:
    print "urllib2.URLError:", err.reason
except Exception, e:
    print e

