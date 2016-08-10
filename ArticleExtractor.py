#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))

import nltk
import requests, html
import xmltodict
from pprint import pprint
from stemming.porter2 import stem
from ArticleManager import ArticleManager
from DatabaseManager import DatabaseManager

import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, unescape
from bs4 import BeautifulSoup

class ArticleExtractor(ArticleManager):
	"""
	Depends on:

	Functions from inherited from ArticleManager:
		get_choices
		check
		ask
	See ArticleManager for additional documentation
	"""

	def __init__(self,**kwargs):
		super(ArticleExtractor,self).__init__(**kwargs)

	def clean_entry(self):
		"""
		For fields in ArticleExtractor.entry attribute with multiple entries, remove duplicates and format the final input
		Runs on ArticleExtractor.entry attribute
		Return: ArticleExtractor.entry attribute (dictionary)
		Article.entry must be type: dictionary

		Example:
		>>> ae = ArticleExtractor()
		...
		>>> ae.entry
		{
			'article_doi':'10.1016/j.arth.2015.12.012',
			'analysis_sw':'SAS,SPSS,SAS',
			'grant_ids':'#29861982,     #EI98239',
			'primary_research':1
		}
		>>> clean_entry()
		{
			'article_doi':'10.1016/j.arth.2015.12.012',
			'analysis_sw':'SAS, SPSS',
			'grant_ids':'#29861982, #EI98239',
			'primary_research':1
		}

		Raise TypeError when entry is not a dictionary
		>>> print(ae.entry)
		['a', 'b']
		>>> ae.clean_entry()
		TypeError: clean_entry called on: ['a', 'b']
		invalid type: <class 'list'>
		"""
		if (type(self.entry) is not dict):
			raise TypeError("clean_entry called on: {0} \ninvalid type: {1}".format(self.entry,type(self.entry)))
			return self.entry
		for (k,v) in self.entry.items():
			copy = v
			try:
				val = copy.split(',')
				val = list(map(str.strip, val))
				val = set(val)
				val = ', '.join(val)
				self.entry[k] = val
			except AttributeError:
				#copy.split(',') failed because val was not a string
				#v was already clean
				pass
		return self.entry

	def get_reviewer(self):
		"""
		Get the name of the person reviewing the article
		Use computer's username to take a guess, or ask for input if cant determine a guess
		Return: Void

		Example:
		>>> ae = ArticleExtractor()
		>>> ae.get_reviewer()
		I think 'Whos reviewing the article?' should be 'Elvis' based on: 'user of computer'
		Is this correct? (if no, type no and press enter; otherwise, press enter):

		>>> ae.get_reviewer()
		Whos reviewing the article?:
		#TODO, finish
		"""
		username = os.getlogin() or pwd.getpwuid(os.getuid())[0]	#username of the person using the computer
		users = self.get_choices("reviewer")
		for user in users:
			if (re.search(username,user,re.I)):
				self.check("Whos reviewing the article?",users[user],user,"user of computer","reviewer")
				return
		self.ask("Whos reviewing the article?","reviewer")

	def chunker(self,sentence : 'string or bytes object') -> 'nltk.tree.Tree':
		"""
		Chunk a sentence
		Args: sentence	(string)
		Return: nltk.tree.Tree object, traversable,
			chunks begin with and end with proper noun (singular or plural)
			and these may occur between the two proper nouns:
				proper noun, noun, ',', '(', ')', ':', demonstrative adjective, conjuction, preposition
		For more information, see:
			http://www.nltk.org/book/ch07.html

		Example:
		>>> ae = ArticleExtractor()
		>>> ae.chunker("The Institute for American Greatness has partnered with The University of Iceland")
		Tree('S', [('The', 'DT'), \
		Tree('Chunk', [('Institute', 'NNP'), ('for', 'IN'), ('American', 'NNP'), ('Greatness', 'NNP')]), \
		('has', 'VBZ'), ('partnered', 'VBN'), ('with', 'IN'), ('The', 'DT'), \
		Tree('Chunk', [('University', 'NNP'), ('of', 'IN'), ('Iceland', 'NNP')]) \
		])

		Except TypeError when sentence is not a string, retry by casting sentence to string
		>>> ae.chunker(12)
		chunker called on: '12'
		12 is type <class 'int'> but must be a string or bytes-like object
		retrying with cast to string
		Tree('S', [('12', 'CD')])
		"""
		try:
			words = nltk.word_tokenize(sentence)
			tagged = nltk.pos_tag(words)
			#tagged = nltk.pos_tag([word.rstrip(''.join([str(i) for i in range(10)])) for word in words])
			chunkGram = r"Chunk: {<NNP.?><NNP.?|NN.?|,|\(|\)|:|IN|CC|DT>*<NNP.?|\)>}"
			chunkedParser = nltk.RegexpParser(chunkGram)
			chunked = chunkedParser.parse(tagged)
			return chunked
		except TypeError as e:
			print("chunker called on: '{}' \n{} is type: {} but must be a string or bytes-like object".format(sentence,sentence,type(sentence)))
			print("retrying with cast to string")
			return self.chunker(str(sentence))


	def get_clinical_domain(self,key_words : 'words to search against the clinical domain choices') -> 'int (redcap key)':
		"""
		Get the clinical domain of the article
		Args: list of keywords
		Return: int value corresponding to redcap key for given domain, or 0 if no keyword matches (unknown domain) or keywords is invalid type

		Example:
		>>> ae = ArticleExtractor()
		>>> ae.get_clinical_domain(['Neurology'])
		23
		>>> ae.get_clinical_domain(['The American Dream'])
		0
		>>> ae.get_clinical_domain(12)
		0
		"""
		if ('clinical_domain' in self.entry):
			return
		if (type(key_words) is not list):
			return 0
		stopwords = nltk.corpus.stopwords.words('english') + ['health','disease','medicine','medical','sciences','medicine','international']
		key_words = [stem(word.lower().strip()) for word in key_words if word.lower() not in stopwords]
		domains = self.get_choices("clinical_domain")
		for word in key_words:
			for domain in domains:
				if (re.search(re.escape(word),domain,re.I)):
					return domain
		return 0

	def _get_hypotheses(self,text : 'string') -> 'int (redcap key)':
		"""
		Determine whether the study in the article was 'Hypothesis Driven or Hypothesis Generating'
			and if they stated the null and alternative hypotheses
		Args: string to be extracted (text from the article)
		Return: int value corresponding to redcap key for hypothesis type

		Example:
		>>> ae = ArticleExtractor()
		>>> ae._get_hypotheses("We hypothesized that patients undergoing extended BEV therapy could have altered patterns of recurrence and symptoms of recurrence due to its novel mechanism of action")
		1
		#from article: 23632207.pdf (doi: 10.1016/j.ygyno.2013.04.055)
		>>> ae._get_hypotheses("")
		#TODO, finish

		"""
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'we.*?hypothes',each_sent,re.I)):
				self.check("Hypothesis Driven or Hypothesis Generating",1,"driven",each_sent,"hypothesis_gen_or_driv")
				if ("hypothesis_gen_or_driv" in self.entry):
					#self.generate_chooser("Does the publication state null and alternative hypotheses?",each_sent,self.get_choices("clear_hypothesis"))
					#if (self.user_choice != -1):
					#	self.entry['clear_hypothesis'] = self.user_choice
					return self.entry['hypothesis_gen_or_driv']
		self.entry['hypothesis_gen_or_driv'] = 2
		return self.entry['hypothesis_gen_or_driv']

	#	**26784271 - weird format :(
	def _get_funding(self,text):
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'funded.*?by',each_sent,re.I|re.S)): 	#TODO, or re.search(r'supported.*?by',each_sent,re.I|re.S)):
				search = re.search(r"grant.*?(\w*\d[\w\d/-]*)",each_sent,re.I)
				if (search):
					self.check("Grant ID",search.group(1).strip(),search.group(1).strip(),each_sent,"grant_ids")
				search = re.search(r'grant.*?from (.*?)[^\w\s-]',each_sent,re.I|re.S)
				if (search):
					self.check("Funders",search.group(1).strip(),search.group(1).strip(),each_sent,"funders")
				else:
					search = re.search(r'funded.*?by (.*?)[^\w\s-]',each_sent,re.I|re.S)
					self.check("Funders",search.group(1).strip(),search.group(1).strip(),each_sent,"funders")

	def _get_inex_criteria(self,text):	#TODO, expand
		for each_sent in nltk.sent_tokenize(text):
			copy = each_sent
			if(re.search(r'were\W*includ',each_sent,re.I) or re.search(r'were\W*exclud',each_sent,re.I) or
				re.search(r'inclus',each_sent,re.I) or (re.search(r'exclus',each_sent,re.I) and not re.search(r'exclusively',each_sent,re.I))):
				if ("inclusion_and_exclusion_stated" not in self.entry):
					self.check_boolean("Inclusion Exclusion Criteria Stated",1,"yes",each_sent,"inclusion_and_exclusion_stated")
				if ("inclusion_and_exclusion_stated" in self.entry):
					self.entry['inclusion_exclu_location___3'] = 1
					self.check_ontol(each_sent)
					return

	def _get_ontol_vocab(self,text): #TODO, if ontol occurs outside of inclusion / exclusion
		ont_dict = self.get_choices("proc_vocabulary")
		ont_dict.update(self.get_choices("diag_vocabulary"))
		ont_dict.update(self.get_choices("med_vocab"))
		ont_dict.update(self.get_choices("lab_vocab"))
		ontols = list(ont_dict.keys())

	def check_ontol(self,info):
		if ("ontol_and_vocab_stated" in self.entry):
			return
		"""
		if (not self.indi):
			print("based on:")
			print(info)
		if (self.ask_question("Are any standard ontologies stated (such as CPT, ICD9, etc)?")):
			self.entry['ontol_and_vocab_stated'] = 1
			c1 = {
				"Procedure":1,
				"Diagnosis":2,
				"Medication":3,
				"Laboratory":4
				}
			c2 = {
				"Procedure":"proc_vocabulary",
				"Diagnosis":"diag_vocabulary",
				"Medication":"med_vocab",
				"Laboratory":"lab_vocab"
				}
			c3 = dict((v,k) for k,v in c1.items())
			self.generate_chooser("What categories are the ontologies a part of?",info,c1)
			if (self.user_choice != -1):
				self.ask("What ontologies are given for the category " + c3[self.user_choice] + "?",c2[c3[self.user_choice]])
		"""

	def _get_databases(self,text):

		def longest(tree):
			max_list = []
			for each_list in tree:
				if (len(each_list) > len(max_list)):
					max_list = each_list
			return max_list


		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'database',each_sent,re.I)):		#re.search(r'electronic.*?records',each_sent,re.I) or
				tree = self.chunker(each_sent)
				sts = []
				try:
					for st in tree.subtrees(lambda tree: tree.height() == 3):
						for st2 in st.subtrees(lambda tree: tree.height() == 2):
							sts.append([str(tup[0]) for tup in st2.leaves()])
					if (len(sts) > 0):
						self.check("Database Name",' '.join(longest(sts)),' '.join(longest(sts)),each_sent,"db_citation_1")		#TODO, it there's more than one
					if ('db_citation_1' in self.entry):
						self.entry['state_data_sources'] = 1
						self.entry['state_database_where___4'] = 1
						#self.ask("Do they cite the database?","database_cited")		#TODO, what does it mean to site a database?
						return
				except AttributeError as e:
					#chunker run on invalid data type, didnt return a tree
					pass
		self.entry['state_data_sources'] = 0

	def _get_query(self,text):
		self.entry['query_script_shared'] = 0
		for each_sent in nltk.sent_tokenize(text):		#TODO, how to tell??
			if (re.search(r'abstracted',each_sent,re.I) or
					re.search(r'manual',each_sent,re.I) or
					re.search(r'query',each_sent,re.I) or
					(re.search('records',each_sent,re.I) and re.search('review',each_sent,re.I))):
				self.check_boolean("Query Method Stated",1,"yes",each_sent,"query_method_stated")
			if ('query_method_stated' in self.entry):
				self.entry['query_method_location___4'] = 1
				return
		self.entry['query_method_stated'] = 0

	def _get_nlp(self,text):
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'language\spro',each_sent,re.I) or re.search(r'\snlp\s',each_sent,re.I)):
				self.check_boolean("Research Involves Natural Language Processing",1,"yes",each_sent,"text_nlp_yn")
				if ("text_nlp_yn" in self.entry):
					if (self.ask_without_choices("Does the publication state source of the text from which data were mined? (ex: emergency department summary, operative notes, etc)\n","Enter the source of text: ","text_mine_source")):
						if (re.search(r'appendix',each_sent,re.I)):
							if (self.check_boolean("Manuscript shares a pre-processed sample text source in",9,"appendix",each_sent,"nlp_source_shared_loc")):
								self.assign("text_mining_preprocess",1)
						elif (re.search(r'\Wgit',each_sent,re.I)):
							if (self.check_boolean("Manuscript shares a pre-processed sample text source in",5,"GitHub",each_sent,"nlp_source_shared_loc")):
								self.assign("text_mining_preprocess",1)
						if ("text_mining_preprocess" not in self.entry):
							if (self.ask_question("Do they share a pre-processed sample of the text source?")):
								self.assign("text_mining_preprocess",1)
								self.ask("Where is the sample shared?","nlp_source_shared_loc")
					#self.nlp_validation()		#TODO
						if (self.ask_without_choices("Does the publication state software used for text mining?","Enter softwares used: ","nlp_software")):
							self.ask("Is the software open or proprietary?","nlp_software_open")
						return

	def _get_analysis(self,text):
		return #TODO, run machine learning algorithm
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'statistical analys[ie]s',each_sent,re.I) or re.search(r'data analys[ie]s',each_sent,re.I)):
				if (self.check_boolean("Publications States Analysis Methodology And Process",1,"yes",each_sent,"analysis_processes_clear")):
					self.entry['data_analysis_doc_loc'] = 4
					return



	def _get_stats(self,text):
		self.check_standards(text)
		if ("analysis_sw" in self.entry):
			self.entry['software_analysis_code'] = 1
			return

		for each_sent in nltk.sent_tokenize(text):
			search = re.search(r'analys[ie]s (were)?(was)? performed\s+\w+\W+(.*?)\s',each_sent,re.I)
			if (search):
				self.check("Analyses Software",search.group(3).strip(),search.group(3).strip(),each_sent,"analysis_sw")
			#if (not search):
			#	search = re.search(r'analys',each_sent,re.I) and re.search(r'\s(.*?)\swas used',each_sent,re.I)
			#	if (search):
			#		self.check("Analyses Software",search.group(1).strip(),search.group(1).strip(),each_sent,"analysis_sw")
			else:
				search = re.search(r'analys',each_sent,re.I) and re.search(r'were\s\w*\susing\s(.*?)\s',each_sent,re.I)
				if (search):
					self.check("Analyses Software",search.group(1),search.group(1),each_sent,"analysis_sw")
			if ("analysis_sw" in self.entry):
				self.entry['software_analysis_code'] = 1

				search = re.search(self.entry['analysis_sw'] + r'.*?(\d[\d\.]*\d)',each_sent,re.I|re.S)
				if (search):
					self.check("Analysis Software Version",search.group(1),search.group(1),each_sent,"analysis_sw_version")
				self.check_operating_system(each_sent)
				return
		self.entry['software_analysis_code'] = 0

	def check_standards(self,text):
		stands = ["STATA","SAS","SPSS"]
		for each_sent in nltk.sent_tokenize(text):
			for stand in stands:
				if re.search(stand,each_sent):
					self.check("Analysis Software",stand,stand,each_sent,"analysis_sw")
					if ("analysis_sw" in self.entry and stand in self.entry['analysis_sw']):
						self.entry['analysis_software_open___1'] = 1		#TODO, how to enter in redcap
						search = re.search(stand + r'.*?(\d[\d\.]*\d)',each_sent)
						if (search):
							self.check("Analysis Software Version",search.group(1),search.group(1),each_sent,"analysis_sw_version")
						self.check_operating_system(each_sent)
			if (re.search(r'analys',each_sent,re.I) and re.search(r'\sR\s',each_sent)):
				self.check("Analysis Software","R","R",each_sent,"analysis_sw")
				if ("analysis_sw" in self.entry and "R" in self.entry['analysis_sw']):
					search = re.search(r'\sR\s.*?(\d[\d\.]*\d)',each_sent)
					if (search):
						self.check("Analysis Software Version",search.group(1),search.group(1),each_sent,"analysis_sw_version")
					self.entry['analysis_software_open___2'] = 1
					search = re.search(r'\sR\s.*?(\d[\d\.]*\d)',each_sent)
					#self.ask_without_choices("Does the publication list the operating system used in analyses?","Type the operating system used: ","analysis_os")

	def check_operating_system(self,text):
		for os in ['Windows','Mac','Linux','Unix']:
			if (re.search(os,text,re.I)):
				self.check_boolean("Operating System Used For Analyses",os,os,text,"analysis_os")
				if ("analysis_os" in self.entry):
					return
		#if (self.ask_question("Do they cite what operating system they used?")):
		#	self.ask("What operating system was used for analyses?","analysis_os")

	def _get_limitations(self,text):
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'shortcomings',each_sent,re.I) or re.search(r'limitation',each_sent,re.I) or re.search(r'(was)?(is)? limited',each_sent,re.I)):
				self.check_boolean("Publication Documents Limitations Of The Study",1,"yes",each_sent,"limitations_where___7")
				if ("limitations_where___7" in self.entry):
					return

	def _get_primary_research(self,text):
		return
		#TODO, run machine learning algorithm on text

	def _get_clear_analysis(self,text):
		return
		#TODO, run machine learning algorithm on text

	def _get_institution(self,institution):
		af_from_xml = institution.split(", ")

		for option in af_from_xml:		#could tweak slightly
			if (re.search(r'hospital',option,re.I) or re.search(r'university',option,re.I) or re.search(r'school',option,re.I) or re.search(r'college',option,re.I) or re.search(r'institute',option,re.I)):
				self.check("Institution",option,option,"affiliation: '{}'".format(institution),"institution_corr_author")
			if ("institution_corr_author" in self.entry):
				return
		try:
			self.check("Institution",af_from_xml[1],af_from_xml[1],"affiliation: '{}'".format(institution),"institution_corr_author")
		except IndexError:
			pass

	def get_clinical_domain_from_xml(self,institution):
		#TODO, chooser doesnt have scrollbar
			#option is to switch check to check_boolean if run out of time

		def _clinical_asides(afs):
			department = division = ""
			for option in afs:
				search = re.search(r'departments? of(.*)',option,re.I)
				if (search):
					department = search.group(1).strip()
				search = re.search(r'division of(.*)',option,re.I)
				if (search):
					division = search.group(1).strip()
			return (department,division)

		af_from_xml = institution.split(", ")
		(department, division) = _clinical_asides(af_from_xml)

		cd_from_department = self.get_clinical_domain(department.split())
		if (cd_from_department):
			self.check_boolean("Clinical Domain",self.get_choices("clinical_domain")[cd_from_department],cd_from_department,"Department: {0}".format(department),"clinical_domain")

		cd_from_division = self.get_clinical_domain(division.split())
		if (cd_from_division):
			self.check_boolean("Clinical Domain",self.get_choices("clinical_domain")[cd_from_division],cd_from_division,"Division: {0}".format(division),"clinical_domain")


		cd_from_journal = self.get_clinical_domain(self.entry['journal_publication'].split())
		if (cd_from_journal):
			self.check_boolean("Clinical Domain",self.get_choices("clinical_domain")[cd_from_journal],cd_from_journal,"Journal Title: " + self.entry['journal_publication'],"clinical_domain")

		cd_from_title = self.get_clinical_domain(self.entry['article_title'].split())
		if (cd_from_title):
			self.check_boolean("Clinical Domain",self.get_choices("clinical_domain")[cd_from_title],cd_from_title,"Article Title: " + self.entry['article_title'],"clinical_domain")
