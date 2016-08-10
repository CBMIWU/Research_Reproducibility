#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Article import RawArticle
from DatabaseManager import DatabaseManager
import json
import nltk
from pprint import pprint
import random
import re



class Trainer(object):
	#cant do redcap as *redcap because text to be searched could be from methods, discussion, etc
	def __init__(self,redcap,articles,searchwords=[]):
		self.articles = articles
		ml_data = DatabaseManager().get_ml_data(redcap)
		if (not searchwords):
			self.allwords = self.get_allwords()
		else:
			self.allwords = searchwords
		self.train(redcap,ml_data)

	def get_allwords(self):
		allwords = []
		for each_article in self.articles:
			art = RawArticle("articles/{}".format(each_article))
			try:
				allwords.extend([word for word in nltk.word_tokenize(art.text) if word not in nltk.corpus.stopwords.words('english')])
			except TypeError as e:
				#article not found
				pass

			#xmltext = ArticleManager().read_xml(file,identifier,each_article)
			#allwords.extend([word for word in nltk.word_tokenize(xmltext.text) if word not in nltk.corpus.stopwords.words('english')])
			#example of how Trainer could be used on xml articles

		allwords = list(set(allwords))
		return allwords

	def train(self,redcap,ml_data):
		print("training")
		pubmed = json.loads(open("pubmed.json").read())
		train = []
		featuresset = []


		for each_article in self.articles:
			art = RawArticle("articles/{}".format(each_article))

			#art = XMLArticle(ArticleManager().read_xml(file,identifier,each_article),1,each_article,identifier,metadata=metadata)
			#ex: art = XMLArticle(ArticleManager().read_xml('articles/sub_pmc_resul.xml','pmid',26781389),1,26781389,'pmid')
			#example of how Trainer could be applied to xml articles


			numwords = len(self.allwords)
			usewords = sorted(list(set(self.allwords)),key=self.allwords.count,reverse=True)[:int(numwords/1.5)]
			try:
				featuresset.append(({word: 1 if re.search(re.escape(word),art.text) else 0 for word in usewords},ml_data[str(pubmed[each_article]['record'])]=='1'))
				#featuresset.append(({word: 1 if re.search(re.escape(word),art.xml_section('methods').text) else 0 for word in self.allwords},ml_data[str(pubmed[each_article]['record'])]=='1'))
				#example of how Trainer could be applied to xml articles
			except KeyError:
				print("couldnt find article with record_id: {0}".format(each_article))

		acc = []
		for i in range(300):
			if (i%50 == 0):
				print(i)
			random.shuffle(featuresset)
			trainset = featuresset[:-1]
			testset = featuresset[-1:]
			classifier = nltk.NaiveBayesClassifier.train(trainset)
			acc.append(nltk.classify.accuracy(classifier,testset))
			#classifier.show_most_informative_features(10)
		print(sum(acc)/len(acc))
