"""
Please use Python version 3.7+
"""

import csv
from typing import List, Tuple
import functools
import re

class TweetIndex:

    def __init__(self):
        self.word_to_timestamp = {}
        self.timestamp_to_tweet = {}
        self.timestamps = set()

    # Starter code--please override
    def process_tweets(self, list_of_timestamps_and_tweets: List[Tuple[str, int]]) -> None:
        """
        process_tweets processes a list of tweets and initializes any data structures needed for
        searching over them.

        :param list_of_timestamps_and_tweets: A list of tuples consisting of a timestamp and a tweet.
        """

        for row in list_of_timestamps_and_tweets:

            timestamp = int(row[0])
            tweet = str(row[1])

            tweet_words = tweet.split(" ")
            for word in tweet_words:
                if word in self.word_to_timestamp:
                    self.word_to_timestamp[word] = self.word_to_timestamp[word] + [timestamp]
                else:
                    self.word_to_timestamp[word] = [timestamp]
            self.timestamp_to_tweet[timestamp] = tweet
            self.timestamps.add(timestamp)
            #self.list_of_tweets.append((tweet, timestamp))

    def get_matches(self, term) -> List[str]:
        """
        get_matches finds the timestamps of all tweets that contain a given word and returns these
        timestamps as a set

        :param term: a string representing a single word in a query
        """
        # deal with negation (! case)
        if "!" in term:
            #remove ! from beginning of word
            term = term[1:]
            if term in self.word_to_timestamp:
                return self.timestamps - set(self.word_to_timestamp.get(term))
            else:
                return self.timestamps - set()
        # term is not negated
        else:
            if term in self.word_to_timestamp:
                return set(self.word_to_timestamp.get(term))
            else:
                return set()

    def apply_operator(self, set1, set2, operator):
        """
        apply_operator applies a logical operator to two sets of timestamps and returns the resulting set

        :param set1: a set of timestamps
        :param set2: a set of timestamps
        :param operator: a logical operator, represented in string form, that can be applied to sets of timestamps
        """

        # perform set union
        if operator is "|":
            return set1 | set2
        # operator is "&"
        elif operator is "&":
            return set1 & set2


    def process_unnested_expression (self, query, negate=False):
        """
        process_unnested_expression evaluates a logical expression by iterating through query terms and logical symbols, 
        applying the logic of &, |, and !

        :param query: a list of strings representing an expression of logical operators and query search terms
        :param negate: a boolean value representing whether the set needs to be negated at the end of evaluation;
        True if the set should be inverted/negated and False otherwise (default)
        """
        
        start = query[0]
        if not isinstance(query[0], set):
            start = self.get_matches(query[0])
        
        while len(query) > 1:
            x = query[2]
            if not isinstance(x, set):
                x = self.get_matches(x)
            start = self.apply_operator(start, x, query[1])
            query = [start] + query[3:]
        if negate:
            return self.timestamps - query[0]
        return query[0]

    # "search" will call this and turn nested parens into nested lists
    def tweet_recur(self, query, negate = False):
        """
        tweet_recur is a recursive function that evaluates a search query that is represented by a list of expressions, 
        which may be nested. 

        :param query: a list of expressions (strings or lists of strings, or lists of lists of strings, etc.)
        :param negate: a boolean value representing whether the query needs to be negated at the end of evaluation;
        True if the set should be inverted/negated and False otherwise (default)-- this is important for evaluating
        negations (!) that occur outside a parenthetical expression (e.g. !(X & Y))
        """

        # base case-- no nested lists
        if len(query) == 1:
            return query

        # base case-- no nested lists
        if not any(isinstance(i, list) for i in query):
            if negate:
                return self.process_unnested_expression(query, negate=True)
            else:
                return self.process_unnested_expression(query)
        
        # recursive case -- some number of nested lists (parenthetical expressions)
        else:
            one = list(map(lambda x: self.tweet_recur(x, negate=True) if isinstance(x, list) and query[query.index(x) - 1] is "!" and x is not "!" else x, query))
            one1 = list(map(lambda x: self.tweet_recur(x) if isinstance(x, list) and x is not "!" else x, one))
            two = list(filter(lambda x: x != "!", one1))
            return self.tweet_recur(two)

    def process_parens(self, lst):
        """
        process_parens is a function which recursively transforms a list representing 
        nested parenthetical expressions into a list version of this expression.
        For example, [x , &, y, |, (, x, &, p, )] --> [x, &, y, |, [x, &, p]]

        :param lst: a semi-processed list of strings representing a potentially-nested
        parenthetical expression (logical query)

        """

        if len(lst) == 0:
            return []

        elif lst[0] is "(":
            i = 0
            while lst[i] is "(":
                i += 1
            
            open = i
            close = 0

            while close < open:
                if lst[i] is ")":
                    close += 1
                if lst[i] is "(":
                    open += 1
                i += 1
            
            return [self.process_parens(lst[1:i-1])] + self.process_parens(lst[i:])

        else:
            return [lst[0]] + self.process_parens(lst[1:])

    # turn expression of nested parentheses into list of lists
    def process_query(self, query:str):
        """
        process_query is a function which transforms a search query (string) into a list
        containing some combination of strings (terms) and list(s), where the potential 
        lists represent nested parenthetical queries

        :param query: a string representing a search query
        """
        mid1 = re.split(" |\(", query)
        
        i = 0 
        count = len(mid1)
        while i < count:
            if mid1[i] == "!":
                mid1.insert(i+1, "(")
                count += 1
            elif mid1[i] == "":
                mid1[i] = "("
            i = i + 1

        mid3 = list(map(lambda x: x.split(")") if ")" in x else x, mid1))

        count = len(mid3)
        x = 0
        while x < count:
            if isinstance(mid3[x], list):
                count = count + len(mid3[x]) - 1
                for y in range(len(mid3[x])):
                    if mid3[x][y] is "":
                        mid3[x][y] = ")"
                mid3 = mid3[:x] + mid3[x] + mid3[x+1:]
            x += 1

        processed = self.process_parens(mid3)
        return processed

    # Starter code--please override
    def search(self, query: str) -> List[Tuple[str, int]]:
        """
        search looks for the five most recent tweets (highest timestamps) that satisfy the logical expression
        represented by the "query" param

        :param query: the given query string
        :return: a list of five tuples of the form (tweet text, tweet timestamp), ordered by highest timestamp tweets first. 
        If no such tweet exists, returns empty list.
        """

        processed_query = self.process_query(query.lower())
        #print(processed_query)
        if len(processed_query) == 1:
            candidates = list(self.get_matches(processed_query[0]))
        else:
            candidates = list(self.tweet_recur(processed_query))
        candidates.sort(reverse = True)
        top_candidates = candidates[:5]
        tweet_list = list(map(lambda x: self.timestamp_to_tweet[x], top_candidates))
        return (tweet_list, top_candidates)

if __name__ == "__main__":
    # A full list of tweets is available in data/tweets.csv.
    #tweet_csv_filename = "../data/small.csv"
    tweet_csv_filename = "/Users/ebussmann/Desktop/Neeva_BE_Project/data/small.csv"
    list_of_tweets = []
    with open(tweet_csv_filename, "r") as f:
        csv_reader = csv.reader(f, delimiter=",")
        for i, row in enumerate(csv_reader):
            if i == 0:
                # header
                continue
            timestamp = int(row[0])
            tweet = str(row[1])
            list_of_tweets.append((timestamp, tweet))

    ti = TweetIndex()
    ti.process_tweets(list_of_tweets)

    assert ti.search("hello & !(yes | neeva) | !(hello & stuff)") == (['hello this is also neeva', 'hello not me', 'hello me', 'hello stuff', 'hello neeva this is bob'], [15, 14, 13, 12, 11])
    assert ti.search("hello & !(neeva | this)") == (['hello not me', 'hello me', 'hello stuff', 'hello hello', 'hello world'], [14, 13, 12, 9, 8])
    assert ti.search("!neeva") == (['hello not me', 'hello me', 'hello stuff', 'hello hello', 'hello world'], [14, 13, 12, 9, 8])
    # nested parentheses
    assert ti.search("hello & ((!neeva & this) & (not | is))") == (['hello this is me'], [6])
    assert ti.search("neeva & (me | it) & !this") == (['hello neeva me'], [5])
    assert ti.search("some | (her & he)") == (['some tweet'], [2])
    assert ti.search("yay") == (['yay'], [0])
    assert ti.search("neeva & Erika") == ([], [])
    assert ti.search("blueberries") == ([], [])
    assert ti.search("bob | is | he") == (['hello this is also neeva', 'hello neeva this is bob', 'hello neeva this is neeva', 'hello this is me', 'hello this is neeva'], [15, 11, 10, 6, 4])
    assert ti.search("!blueberries") == (['hello this is also neeva', 'hello not me', 'hello me', 'hello stuff', 'hello neeva this is bob'], [15, 14, 13, 12, 11])
    assert ti.search("tweet | world") == (['hello world', 'some tweet'], [8, 2])
    
    print("Success!")
