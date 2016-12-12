import json
import os
import re
import string
import tweepy
from tweepy import OAuthHandler
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import vincent

# Extract tweets from Donald Trump and Hilary Clinton's account,
# process the tweets to get most frequently occured words
# and visualize them using Vincent

emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""
 
regex_str = [
    emoticons_str,
    r'<[^>]+>', # HTML tags
    r'(?:@[\w_]+)', # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs
    r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
    r'(?:[\w_]+)', # other words
    r'(?:\S)' # anything else
]   
 
tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^'+emoticons_str+'$', re.VERBOSE | re.IGNORECASE)
 
def tokenize(s):
    return tokens_re.findall(s)
 
def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    return tokens

# extract tweets from a specific screen name
def extract_tweets(target_screen_name, dst_json_file):
	all_tweets = []	

	new_tweets = api.user_timeline(screen_name = target_screen_name, count=200)
	all_tweets.extend(new_tweets)

	oldest_tweet_id = all_tweets[-1].id - 1

	# Fetch new tweets
	while len(new_tweets) > 0:
		print "Fetching tweet id before %s" % (oldest_tweet_id)	
		new_tweets = api.user_timeline(screen_name = target_screen_name, count=200, max_id=oldest_tweet_id)
		# add newly fetch tweets
		all_tweets.extend(new_tweets)
		oldest_tweet_id = all_tweets[-1].id - 1
		print "...%s tweets downloaded" % (len(all_tweets))

	json_objs = [tweet._json for tweet in all_tweets]
	json_strings = [json.dumps(json_obj) for json_obj in json_objs]  

	#write to txt json
	with open(dst_json_file, "w") as outfile:
		json.dump(json_strings, outfile, indent=4)
	outfile.close()

def extract_most_frequent_terms(dst_file):
	    # Get the stopwords
	punctuation = list(string.punctuation)
	print punctuation
	stop = stopwords.words('english') + punctuation + ['rt', 'via', 'RT', 'AND']

	print "Reading json file %s" % dst_file
	# Analyze each tweets
	all_tweets =  {}
	terms_count = Counter();
	with open(dst_file, 'r') as json_data:
		all_tweets = json.load(json_data)
	for entry in all_tweets :
		tweet = json.loads(entry)
		terms = [term for term in preprocess(tweet['text']) if term not in stop and not term.startswith(('#', '@'))]
		#print json_entry['text']
		terms_count.update(terms)
	print(terms_count.most_common(20))
	return terms_count

if __name__ == "__main__":

	auth = OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_secret)
	api = tweepy.API(auth)
	target_screen_names = ['HillaryClinton', 'realDonaldTrump']

	for name in target_screen_names :
		dst_file = name + '_data.json'
		
		# ===============================================
		# Data extraction: parse tweets using Twitter API 
		# and save to a json file
		# ===============================================
		extract_tweets(name, dst_file)

		# ============================================
		# Extract most frequent terms from a json file
		# ============================================
		terms_count = extract_most_frequent_terms(dst_file)
		
		# ================================================================
		# Data visualization : print result to graph using Vincent / D3.js
		# ================================================================
		word_freq = terms_count.most_common(20)
		labels, freq = zip(*word_freq)
		data = {'data': freq, 'x': labels}
		bar = vincent.Bar(data, iter_idx='x')
		bar.to_json(name + '_term_freq.json', html_out=True, html_path=name +'chart.html')
