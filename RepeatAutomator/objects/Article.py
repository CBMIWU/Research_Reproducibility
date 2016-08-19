#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from ArticleExtractor import ArticleExtractor
from XMLExtractor import XMLExtractor
import bs4
import re,sys
import textract, nltk

class RawArticle(object):
	def __init__(self,file):
		self.text = self.get_text(file)


	def get_text(self,file):
		if (not re.search(r'.pdf',file)):
			file = file + ".pdf"
		try:
			text = textract.process(file)
			text = text.strip()
			text = re.sub(b'\n+',b" ",text)
			text = re.sub(b'\s+',b" ",text)
			return text.decode("utf-8")
		except Exception as e:
			print("file: {} not found\ninformation from textract:\n\t{}".format(file,e))
			return 0

class XMLArticle(ArticleExtractor,XMLExtractor):
	def __init__(self,article_id,identifier,**kwargs):
		assert ('xmltext' in kwargs) or ('bs' in kwargs),"XMLArticle constructor called without xmltext or bs keyword argument (must have at least one)"
		if ('bs' in kwargs):
			assert isinstance(kwargs['bs'],bs4.element.Tag),"XMLArticle constructor called and bs kwarg was invalid type - should be type 'BeautifulSoup Tag' but is type: {}".format(type(kwargs['bs']))
			self.bs = kwargs['bs']
		else:
			self.bs = bs4.BeautifulSoup(kwargs['xmltext'],"lxml")
		kwargs.pop('bs',0)			#remove bs and xmltext from kwargs so that ArticleManager constructor
		kwargs.pop('xmltext',0)		#doesnt throw an error when called with invalid argments

		self.entry = {}
		super(XMLArticle,self).__init__(**kwargs) 	#pass run_style and metadata keyword argument on to ArticleExtractor constructor (if provided)
		self.article_id = article_id
		self.identifier = identifier

	def pmid(self,bs):
		try:
			return bs.find(("article-id",{"pub-id-type":"pmid"})).text
		except AttributeError as e:
			#pubmed id not found
			return ""

	def section(self,sections,tag):
		tags = self.bs.find_all(tag)
		for tag in tags:
			for section in sections:
				if (re.search(section,tag.get_text(),re.I)):
					sect = re.sub(r'title','',tag.get('id'))
		try:
			return self.bs.div(id=sect)[0]
		except UnboundLocalError as e:
			#couldnt find sect
			return self.bs

	def search(self,regex):
		#return self._get_funding(self.search(re.compile(r'funded.*?by',re.I)).get_text())
		try:
			return self.bs.find(text=regex).parent.parent
		except AttributeError:
			#match occurred at top level of tree
			return self.bs
		except IndexError:
			#regex search returned no results
			return 0

	def xml_section(self,*titles):
		for title in titles:
			if (self.bs.find("sec",{"sec-type":title})):
				return self.bs.find("sec",{"sec-type":title}).text
			if (self.bs.find("title",text=title)):
				return self.bs.find("title",text=re.compile(title,re.I)).parent.text
		return self.bs.text

	def get_hypotheses(self):
		return self._get_hypotheses(self.xml_section('background','introduction'))

	def get_funding(self):
		return self._get_funding(self.bs.text)

	def get_inex_criteria(self):
		return self._get_inex_criteria(self.xml_section('methods'))

	def get_databases(self):
		return self._get_databases(self.xml_section('methods'))

	def get_query(self):
		return self._get_query(self.xml_section('methods'))

	def get_nlp(self):
		return self._get_nlp(self.xml_section('methods'))

	def get_analysis(self,classifier):
		return self._get_analysis(classifier.classify(self.xml_section('methods')))

	def get_stats(self):
		return self._get_stats(self.xml_section('methods'))

	def get_limitations(self):
		return self._get_limitations(self.xml_section('discussion','conclusion'))

	def get_institution(self,affiliation):
		return self._get_institution(affiliation)

class PDFArticle(ArticleExtractor,XMLExtractor):
	def __init__(self,file,article_id,identifier,**kwargs):
		self.entry = {}
		super(PDFArticle,self).__init__(**kwargs)
		self.text = RawArticle(file).text
		self.article_id = article_id
		self.identifier = identifier

	def get_clinical_domain_from_pdf(self):
		for each_sent in nltk.sent_tokenize(self.text):
			search = re.search(r'key.*?words(.*)',each_sent,re.I)
			if (search):
				key_words = re.sub(r'[()]',"",search.group(1))
				key_words = key_words.split()
				self.get_clinical_domain(key_words)

	def get_hypotheses(self):
		return self._get_hypotheses(self.text)

	def get_funding(self):
		return self._get_funding(self.text)

	def get_inex_criteria(self):
		return self._get_inex_criteria(self.text)

	def get_databases(self):
		return self._get_databases(self.text)

	def get_query(self):
		return self._get_query(self.text)

	def get_nlp(self):
		return self._get_nlp(self.text)

	def get_stats(self):
		return self._get_stats(self.text)

	def get_limitations(self):
		return self._get_limitations(self.text)

	def get_analysis(self):
		return #TODO, run machine learning
		return self._get_analysis(self.text)

	def get_institution(self,affiliation):
		return self._get_institution(affiliation)
