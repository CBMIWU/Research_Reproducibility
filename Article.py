#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from ArticleExtractor import ArticleExtractor
from XMLExtractor import XMLExtractor
from bs4 import BeautifulSoup
import re,sys
import textract, nltk

class RawArticle(object):
	def __init__(self,file):
		self.text = self.get_text(file)


	def get_text(self,file):		#TODO, clean up or remove proper nouns
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

			#TODO
		"""
		words = nltk.word_tokenize(text.decode('utf-8'))
		tagged = nltk.pos_tag(words)
		newwords = []
		print len(tagged)
		for word,part in tagged:
			if (re.search(r'NNP.?',part)):
				newwords.append(re.sub(r'\.','',word))
			else:
				newwords.append(word)
		text = ' '.join([word for word in newwords])
		text = re.sub(r'\s\.','.',text)
		print text
		sys.exit()
		"""
		#self.sents = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s',text)

class XMLArticle(ArticleExtractor,XMLExtractor):

	#TODO, fix here and others so that metadata has default if none provided
	def __init__(self,xmltext,run_style,article_id,identifier,**metadata):
		self.indi = run_style
		self.entry = {}
		if ('metadata' in metadata):
			super(XMLArticle,self).__init__(run_style=run_style,metadata=metadata['metadata'])
		else:
			super(XMLArticle,self).__init__(run_style=run_style)
		self.fulltext = xmltext
		self.bs = BeautifulSoup(self.fulltext,"lxml")
		self.article_id = article_id
		self.identifier = identifier

	def pmid(self,bs):
		try:
			return bs.find(("article-id",{"pub-id-type":"pmid"})).text
		except AttributeError as e:
			#field not found
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
		try:
			return self.bs.find(text=regex).parent.parent
		except AttributeError:
			#match occurred at top level of tree
			return self.bs
		except IndexError:
			#regex search returned no results
			return 0

	def xml_section(self,*titles):
		body = self.bs.body
		for title in titles:
			if (body.find("sec",{"sec-type":title})):
				return body.find("sec",{"sec-type":title}).text
			if (body.find("title",text=title)):
				return body.find("title",text=re.compile(title,re.I)).parent.text
		return self.bs.body		#unable to find section

	#TODO, if xml_section doesnt find choice, use a search instead of entire body
	def get_hypotheses(self):
		return self._get_hypotheses(self.xml_section('background','introduction'))

	def get_funding(self):		#nltk could improve; low priority now though
		#self.bs.find_all(string=re.compile(r'fund[ie]'))
		return self._get_funding(self.search(re.compile(r'funded.*?by',re.I)).get_text())

	def get_inex_criteria(self):	#TODO, expand
		return self._get_inex_criteria(self.xml_section('methods'))

	def get_ontol_vocab(self): #TODO, if ontol occurs outside of inclusion / exclusion
		return	#TODO
		return self._get_ontol_vocab(self.xml_section('methods'))

	def get_databases(self):
		return self._get_databases(self.xml_section('methods'))

	def get_query(self):
		return #TODO
		return self._get_query(self.fulltext)
		self.entry['query_script_shared'] = 0

	def get_nlp(self):
		return self._get_nlp(self.xml_section('methods'))

	def get_analysis(self):
		return #TODO
		return self._get_analysis(text)

	def get_stats(self):
		return #TODO
		return self._get_stats(text)

	def get_limitations(self):
		return self._get_limitations(self.xml_section('discussion','conclusion'))

	def get_primary_research(self):
		return #TODO
		return self._get_primary_research(text)
		#TODO, run machine learning algorithm on text

	def get_clear_analysis(self):
		return #TODO
		return self._get_clear_analysis(text)
		#TODO, run machine learning algorithm on text

	def get_institution(self,institution):
		return #TODO
		return self._get_institution(institution)

class PDFArticle(ArticleExtractor,XMLExtractor):
	#kwargs: metadata and run_style
	#TODO, change if this works
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

	def get_funding(self):		#nltk could improve; low priority now though
		#self.bs.find_all(string=re.compile(r'fund[ie]'))
		return self._get_funding(self.text)

	def get_inex_criteria(self):	#TODO, expand
		return self._get_inex_criteria(self.text)

	def get_ontol_vocab(self): #TODO, if ontol occurs outside of inclusion / exclusion
		return #TODO
		return self._get_ontol_vocab(self.text)

	def get_databases(self):
		return self._get_databases(self.text)

	def get_query(self):
		return self._get_query(self.text)
		self.entry['query_script_shared'] = 0

	def get_nlp(self):
		return self._get_nlp(self.text)

	def get_stats(self):
		return self._get_stats(self.text)

	def get_limitations(self):
		return self._get_limitations(self.text)

	def get_primary_research(self):
		return self._get_primary_research(self.text)
		#TODO, run machine learning algorithm on text


	def get_analysis(self):
		return
		return self._get_analysis(self.text)
	def get_clear_analysis(self):
		return
		return self._get_clear_analysis(self.text)
		#TODO, run machine learning algorithm on text

	def get_institution(self,institution):
		return self._get_institution(institution)
