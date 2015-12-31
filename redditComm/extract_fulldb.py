"""This module accepts dumps all the records in the dataset as a json object.
Run it with python extract_fulldb.py"""
#!/bin/python
from __future__ import division, print_function
from bz2 import BZ2File
import ujson
from time import time
from pandas import Timestamp, NaT, DataFrame
from toolz import dissoc
from castra import Castra
from toolz import peek, partition_all

logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('requests').setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

columns = ['archived', 'author', 'author_flair_css_class', 'author_flair_text',
           'body', 'controversiality', 'created_utc', 'distinguished', 'downs',
           'edited', 'gilded', 'link_id', 'name', 'parent_id',
           'removal_reason', 'score', 'score_hidden', 'subreddit', 'ups']

def to_json(line):
    """Convert a line of json into a cleaned up dict."""
    # Convert timestamps into Timestamp objects
    date = line['created_utc']
    line['created_utc'] = Timestamp.utcfromtimestamp(int(date))
    edited = line['edited']
    line['edited'] = Timestamp.utcfromtimestamp(int(edited)) if edited else NaT

    # Convert deleted posts into `None`s (missing text data)
    if line['author'] == '[deleted]':
        line['author'] = None
    if line['body'] == '[deleted]':
        line['body'] = None

    # Remove 'id', and 'subreddit_id' as they're redundant
    # Remove 'retrieved_on' as it's irrelevant
    return dissoc(line, 'id', 'subreddit_id', 'retrieved_on')

def to_df(batch):
    """Convert a list of json strings into a dataframe"""
    blobs = map(to_json, batch)
    df = DataFrame.from_records(blobs, columns = columns)
    return df.set_index('created_utc')

def execute():
    categories = ['distinguished', 'subreddit', 'removal_reason']
    with BZ2File('subreddit_dumps/RC_2015-05.bz2') as f:
        batches = partition_all(200000, f)
        df, frames = peek(map(to_df, batches))
        castra = Castra('subreddit_dumps/reddit_data.castra', template = df, categories = categories)
        castra.extend_sequence(frames, freq = '3h')

def main():
    ts = time()
    execute()
    print('Full extract took {}s'.format(time() - ts))

if __name__ == '__main__':
   main()
