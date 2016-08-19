#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME'])) #TODO
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))
from getopt import getopt

#objects
from Article import XMLArticle, PDFArticle
from ArticleManager import ArticleManager
from Trainer import Trainer
from DatabaseManager import DatabaseManager
from ArticleExtractor import ArticleExtractor
from XMLExtractor import XMLExtractor

from pprint import pprint
import re
from bs4 import BeautifulSoup


"""
Handle article extraction using:
	XMLArticle / PDFArticle
	ArticleExtractor
	XMLExtractor
	Trainer
Depends on imported methods:
	os				-- https://docs.python.org/3/library/os.html
	sys				-- https://docs.python.org/3/library/sys.html
	getopt 			-- https://docs.python.org/3.1/library/getopt.html
	pprint 			-- https://docs.python.org/3/library/pprint.html
	re				-- https://docs.python.org/3/library/re.html
	beautiful soup	-- https://www.crummy.com/software/BeautifulSoup/bs4/doc/
See documentation for more information

Command line arguments:
	--articles=, -a 				-- articles to be extracted
	--by-itself, -b 				-- tell extractors not to request user interaction
	--directory, -d					-- directory where pdf files are located
	--file=, -f						-- provide file with list of articles to be extracted separated by any character except: letter, number, period (.), forward slash (/), hyphen (-), underscore (_)
	--identifier=, -i				-- what identifier is used (doi, pmid, pmc, publisher-id)
	--xml, -x						-- perform xml extraction
	--text, -t						-- perform text extraction
	--redcap, -r 					-- enter extracted data into redcap database
	--machine-learning=, -m			-- run machine-learning trainer on given redcap field
	--zxml=, -z						-- run extraction on the provided xml file from pubmed central
(I ran out of letters)

As it's set up now, articles much be saved as: {identifier}.pdf
For example:
identifier: pmid
article: 24433938.pdf

Examples:
christian$ ./executer --articles=24433938 --directory=/Users/christian/Desktop/cbmi/reproduce/python/articles --identifier=pmid --xml --redcap
#run xml and pdf extraction
#on article: 24433938.pdf
#located in folder: /Users/christian/Desktop/cbmi/reproduce/python/articles
#24433938 is a pmid
#enter the results into redcap
#ask for user input

christian$ ./executer -f /Users/christian/Desktop/cbmi/reproduce/python/articles/articlefile.txt -d /Users/christian/Desktop/cbmi/reproduce/python/articles -i pmid -xtb
#run xml and text extraction
#on the articles listed in the file: /Users/christian/Desktop/cbmi/reproduce/python/articles/articlefile.txt
#pdfs are located in folder: /Users/christian/Desktop/cbmi/reproduce/python/articles
#the articles in: /Users/christian/Desktop/cbmi/reproduce/python/articles/articlefile.txt are pmids
#dont ask for user interaction

christian$ cat /Users/christian/Desktop/cbmi/reproduce/python/articles/articlefile.txt | head -n 8
24433938
26513432
23632207 ,,,

25266841,25203000 < 26236002
24119466
20842022
21411379

...
#the file is deliberately ugly to demonstrate the flexibility in reading the article list

christian$ ./executer -a 10.1186/s12884-015-0587-z,10.1186/s12947-015-0023-6,10.1136/bjophthalmol-2015-306683,10.1371/journal.pone.0127791,10.1097/MAJ.0000000000000382 --file=/Users/christian/Desktop/cbmi/reproduce/python/articles/articlefile.txt --identifier=doi --text --redcap --zxml=/Users/christian/Desktop/cbmi/reproduce/python/articles/pmc_result.xml
#perform text extraction
#on articles listed in the file: /Users/christian/Desktop/cbmi/reproduce/python/articles/articlefile.txt
#the articles are dois
#ask for user input
"""


ncbi_site = "https://www.ncbi.nlm.nih.gov/"
xml_tag = "?report=xml&format=text"

opts = dict()

def get_command_args(argv):

	articles = []

	identifier = "pmid"
	indi = xml = text = redcap = directory = ml = zxml = 0
	opts, args = getopt(argv,"a:bd:f:i:xprtm:z:",["articles=","by-itself","directory=","file=","identifier=","xml","pdf","redcap","text","--machine-learning=","zxml="])
	for opt,arg in opts:
		if opt in ("-a","--articles"):
			articles.extend(arg.split(','))
		elif opt in ("-b","--by-itself"):
			indi = 1
		elif opt in ("-f","--file"):
			with open(arg,'rb') as f:
				file_text = f.read().decode()
				articles.extend(re.sub(r'[^\w/\.\-\_]+',' ',file_text).split())
		elif opt in ("-i","--identifier"):
			identifier = arg
		elif opt in ("-x","--xml"):
			xml = 1
		elif opt in ("-t","--text"):
			text = 1
		elif opt in ("-r","--redcap"):
			redcap = 1
		elif opt in ("-d","--directory"):
			directory = arg
		elif opt in ("-m","--machine-learning"):
			ml = arg
		elif opt in ("-z","--zxml"):
			zxml = arg
	return ({
		'indi':indi,
		'ident':identifier,
		'xml':xml,
		'text':text,
		'redcap':redcap,
		'dir':directory,
		'ml':ml,
		'zxml':zxml
		}, articles)

def train(articles):
	global opts
	for field in opts['ml'].split(','):
		tr = Trainer(field.strip(),opts['dir'],articles)


def extract(article):
	global opts
	os.environ['article_id'] = str(article.article_id)
	os.environ['identifier'] = str(article.identifier)

	if (opts['xml']):
		xml_extract(article)


	if (opts['text']):
		text_extract(article)

	article.entry = article.clean_entry()
	pprint(article.entry)

	if (opts['redcap']):
		#TODO, new redcap entry id
		article.enter_redcap(article.entry,'9b7057f5f8894c9c')
		print(str(article.redcap_return))


	del os.environ['article_id']
	del os.environ['identifier']

	print("\n\n\n\n")
	return

def xml_extract(article):
	xe = XMLExtractor()
	if (article.identifier == 'pubmed' or article.identifier == 'pmid'):
		pmid = article.article_id
	else:
		if (isinstance(article,XMLArticle)):
			pmid = article.pmid(article.bs)
		else:
			#article is PDF article and no pubmed code provided
			print("couldnt perform xml extract for article: '{}' because no pubmed code provided".format(article.identifier))
			return

	xml = xe.xml_load("{0}pubmed/{1}{2}".format(ncbi_site,pmid,xml_tag))
	article.entry.update(xe.xml_extract(xml))
	try:
		article.get_institution(xe.institution)
		article.get_clinical_domain_from_xml(xe.institution)
	except AttributeError as e:
		#'XMLExtractor' object has no attribute 'institution'
		#xml extract failed during http request or parsing, user already notified
		pass

def text_extract(art):

	art.get_reviewer()
	art.get_hypotheses()
	art.get_funding()
	art.get_inex_criteria()
	art.get_databases()
	art.get_query()
	art.get_nlp()
	art.get_limitations()
	art.get_stats()


def main(argv):
	global opts
	opts, articles = get_command_args(argv)
	metadata = DatabaseManager().get_metadata()
	articles = list(set(articles))

	if (opts['ml']):
		train(articles)
		#cant run train and other functions
		return

	if (opts['zxml']):
		#opts['zxml'] is the xml file
		for (bs,each_id) in ArticleManager().get_articles_xml(opts['zxml'],opts['ident'],articles):
			art = XMLArticle(each_id,opts['ident'],run_style=opts['indi'],metadata=metadata,bs=bs)
			extract(art)
		return

	else:
		for each_article in articles:
			try:
				art = PDFArticle("{}/{}".format(opts['dir'],each_article),each_article,opts['ident'],run_style=opts['indi'],metadata=metadata)
				extract(art)
			except TypeError as e:
				print("{} not found".format(each_article))
				continue

if __name__ == "__main__":
	main(sys.argv[1:])
