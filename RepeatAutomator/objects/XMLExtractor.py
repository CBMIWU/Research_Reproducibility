#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re
import requests
from bs4 import BeautifulSoup
from DatabaseManager import DatabaseManager

class XMLExtractor(DatabaseManager):
	"""
	Load xml from ncbi site,
	Parse xml using BeautifulSoup
	Extract data using BeautifulSoup

	Depends on imported modules:
		requests		-- http://docs.python-requests.org/en/master/
		beautiful soup	-- https://www.crummy.com/software/BeautifulSoup/bs4/doc/
		os				-- https://docs.python.org/3/library/os.html
		sys				-- https://docs.python.org/3/library/sys.html
		re				-- https://docs.python.org/3/library/re.html
	Inherited methods from DatabaseManager:
		record_error
	See documentation for more information
	"""

	def xml_load(self,site):
		"""
		Get xml data on an article, record error in the sql database if http request fails
		Args: site -- url address where xml data lives (string)
		Return: bs4.BeautifulSoup object, BeautifulSoup of xml data
				0 to indicate an error occurred

		Example:
		>>> xe = XMLExtractor()
		>>> xe.xml_load("http://www.ncbi.nlm.nih.gov/pubmed/24433938?report=xml&format=text")
		<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
		<html><body><pre>
		<pubmedarticle>
		    <medlinecitation owner="NLM" status="MEDLINE">
		        <pmid version="1">24433938</pmid>
		        <datecreated>
		            <year>2014</year>
		            <month>06</month>
		            <day>14</day>
		        </datecreated>
		        ...

		Requests module manages error handling
		>>> xe.xml_load("this is not a valid url")
		request to site: 'this is not a valid url'
		failed. error information from requests:
			 Invalid URL 'this is not a valid url': No schema supplied. Perhaps you meant http://this is not a valid url?
		0
		"""
		xml_text = ''
		try:
			xml_text = requests.get(site).text
		except Exception as e:
			self.record_error(method='xml_load',object_caller='XMLExtractor',field=site,notes=str(e))
			print("request to site: '{}'\nfailed. error information from requests:".format(site))
			print("\t",e)
			return 0
		xml_text = re.sub(r'&lt;',"<",xml_text)
		xml_text = re.sub(r'&gt;',">",xml_text)
		data = self.parse_xml(xml_text)
		if (not isinstance(data,BeautifulSoup)):
			print("xml could not be interpretted for site: {}".format(site))
			#in this case data is the error message from beautifulsoup
			self.record_error(method='parse_xml',object_caller='XMLExtractor',field=site,notes=data)
			return 0
		return data

	def parse_xml(self,xml):
		"""
		Parse an xml string
		Args: xml -- xml formatted string to be parsed (string)
		Return: bs4.BeautifulSoup object, BeautifulSoup of xml data
				0 to indicate an error occurred
		Called by xml_load to parse xml from the ncbi website

		Example:
		>>> xe = XMLExtractor()
		>>> bs = xe.parse_xml("<PubmedArticle><MedlineCitation Owner="NLM" Status="MEDLINE"><PMID Version="1">24433938</PMID><DateCreated><Year>2014</Year> ...")
		#from article: pubmed id: 24433938 -- see http://www.ncbi.nlm.nih.gov/pubmed/24433938?report=xml&format=text
		>>> bs.articletitle
		<ArticleTitle>Differences between intentional and non-intentional burns in India: implications for prevention.</ArticleTitle>
		>>> bs.articletitle.text
		'Differences between intentional and non-intentional burns in India: implications for prevention.'
		>>> bs.forename.text
		'Mangai'

		Throws error if:
			input is wrong type (not string)
			improperly formatted (not from ncbi site), check that pubmedarticle tag is in BeautifulSoup to verify
		>>> xe.parse_xml(12)
		parse_xml called on: '12'
		invalid type, arg must be type string but is: <class 'int'>

		>>> bs = xe.parse_xml("<ImportantInformation><BestDinosaur>triceratops</BestDinosaur><BestCountry>Ireland</BestCountry></ImportantInformation>")
		xml was not proper format (no 'pubmedarticle' tag found). likely, the wrong (but valid) website was entered"

		As far as I can tell, BeautifulSoup wont throw an error as long as the argument is a string.
		"""
		if (type(xml) is not str):
			print("parse_xml called on: '{}'\n invalid type, arg must be type string but is: {}".format(xml,type(xml)))
			return 0
		data = BeautifulSoup(xml,'lxml')
		if (not data.pubmedarticle):
			e = "xml was not proper format (no 'pubmedarticle' tag found). likely, the wrong (but valid) website was entered"
			print(e)
			return e
		return data

	def xml_extract(self,bs):
		"""
		Extract redcap fields from the BeautifulSoup object
		Args: bs -- xml data from ncbi site (bs4.BeautifulSoup object)
		Return: dictionary of redcap data
				empty dictionary if errors occur

		Example:
		>>> xe = XMLExtractor()
		>>> bs = xe.xml_load("http://www.ncbi.nlm.nih.gov/pubmed/24433938?report=xml&format=text)
		>>> xe.xml_extract(bs)
		{'article_doi': '10.1016/j.burns.2013.12.002',
		 'article_title': 'Differences between intentional and non-intentional burns '
		                  'in India: implications for prevention.',
		 'author_email': 'mnatarajan@jjay.cuny.edu.',
		 'author_fn': 'Mangai',
		 'author_ln': 'Natarajan',
		 'journal_publication': 'Burns : journal of the International Society for Burn '
		                        'Injuries',
		 'publication_date': '2014-06-14'}

		>>> xe.xml_extract(0)
		{}
		>>> xe.xml_extract("oh no, green slime!")
		xml_extract called on invalid argument: 'oh no, green slime!'
		type of arg is: <class 'str'> but should be a <class 'bs4.BeautifulSoup'>
		{}
		"""

		if (not bs):
			#likely, xml download failed because invalid url or misformatted data (user has already been notified in xml_load or parse_xml method calls)
			#return empty dictionary so that redcap entry doesnt throw errors
			return {}
		if (not isinstance(bs,BeautifulSoup)):
			#verify xml is a beautiful soup object
			print("xml_extract called on invalid argument: '{}'\ntype of arg is: {} but should be a {}".format(bs,type(bs),type(BeautifulSoup())))
			self.record_error(method='xml_extract',object_caller='XMLExtractor',value=bs,notes="xml_extract called on invalid argument: '{}'\ntype of arg is: {} but should be a {}".format(bs,type(bs),type(BeautifulSoup())))
			#return empty dictionary so that redcap entry doesnt throw errors
			return {}

		#call try_xml on each field so that if any field isnt found, extraction skips that field and continues
		journalName = self.try_xml(bs,'title')
		day = self.try_xml(bs,'day')
		month = self.try_xml(bs,'month')
		year = self.try_xml(bs,'year')
		publisher = self.try_xml(bs,'copyrightinformation')
		doi = self.try_xml(bs,("elocationid",{"eidtype":"doi"}))
		articleTitle = self.try_xml(bs,'articletitle')

		#redcap only allows alpha characters for first and last name. sub out some common invalid characters
		lastName = re.sub('[\W_\s]','',self.try_xml(bs,"lastname"))
		firstName = re.sub('[\W_\s]','',self.try_xml(bs,'forename'))

		institution = self.try_xml(bs,'affiliation')
		if ('@' in institution):
			search = re.search(r'\s((\w|\.)+@.+)',institution);
			email = search.group(1);
			if ('Electronic address:' in institution):
				search = re.search(r'(.*) Electronic address:',institution)
				institution = search.group(1);
			else:
				search = re.search(r'(.*)\s.+@',institution)
				institution = search.group(1);
		else:
			email = ""
		self.institution = institution
		#self.institution is used later in ArticleExtractor.get_institution and ArticleExtractor.get_clinical_domain_from_pdf method calls
		#see executer or ArticleExtractor for more information

		return ({
			'article_doi':doi,
			'journal_publication':journalName,
			'publication_date':"{0}-{1}-{2}".format(year,month,day),
			'author_fn':firstName,
			'author_ln':lastName,
			'author_email':email,
			'article_title':articleTitle,
			})

	def try_xml(self, bs, search):
		"""
		Handle errors that occur when tags arent found in BeautifulSoup so script doesnt Force-quit when a field isnt found
		Args:
			bs 		-- xml data from ncbi site (bs4.BeautifulSoup object)
			search 	-- string or tuple, argument in BeautifulSoup.find method call
		Return: data in form of string
				empty string if nothing found
		Called by xml_extractor

		Example:
		>>> xe = XMLExtractor()
		>>> bs = BeautifulSoup("<ImportantInformation><BestDinosaur>triceratops</BestDinosaur><BestCountry>Ireland</BestCountry></ImportantInformation>",'lxml')
		>>> xe.try_xml(bs,'bestcountry')
		'Ireland'
		>>> xe.try_xml(bs,madonna)
		''
		>>> bs = BeautifulSoup("<article-id pub-id-type='doi'>10.1016/j.annemergmed.2013.08.019</article-id>")
		>>> xe.try_xml(bs,('article-id',{'pub-id-type':'doi'}))
		10.1016/j.annemergmed.2013.08.019
		"""
		try:
			return bs.find(search).text
		except AttributeError as e:
			#field not found
			return ""
