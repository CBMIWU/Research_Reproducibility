#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))

from getopt import getopt
from Article import XMLArticle, PDFArticle
from ArticleManager import ArticleManager
from Trainer import Trainer
import nltk
from DatabaseManager import DatabaseManager
from pprint import pprint
from ArticleExtractor import ArticleExtractor
from XMLExtractor import XMLExtractor

import re, requests
import subprocess

from bs4 import BeautifulSoup

ncbi_site = "https://www.ncbi.nlm.nih.gov/"
xml_tag = "?report=xml&format=text"

def get_command_args(argv):
	firstarticles = ["24433938","26513432","23632207","25266841","25203000","26236002","24119466",
					"20842022","21411379","23552606","21700714","26850871","25883689","24934411",
					"24656777","25839735","25368396","26231634","23374784"]
	secondarticles = ["26775158","26815253","26825406","26824374","26803428","26795617","26784271","26783357","26783356","26781389"]
	pmcarticles = ['23632207','25266841','24119466','21700714','25883689','24934411','25368396','26775158','26803428','26784271']
	pmcs = ['PMC3852715','PMC4527599','PMC4254085','PMC3137948','PMC4384267','PMC4070347','PMC4221799','PMC4715304','PMC4747833','PMC4742403']
	xmltests = ['23449283','24672566','22733976','25565678','24228257','24107106','23355463','24433938']
	#24433938 is from firstarticles, doesnt exist in xml
	#23355463 is not open acces
	#for debugging
	#"26775158,26815253,26825406,26824374,26803428,26795617,26784271,26783357,26783356,26781389"

	articles = []
	#articles = firstarticles #+ secondarticles
	#articles = xmltests

	identifier = "pmid"
	indi = xml = pdf = redcap = down = train = zxml = 0
	opts, args = getopt(argv,"a:bdf:i:xprt:z:",["articles=","by-itself","download","file=","identifier=","xml","pdf","redcap","train=","zxml="])
	for opt,arg in opts:
		if opt in ("-a","--articles"):
			articles.extend(arg.split(','))
		elif opt in ("-b","--by-itself"):
			indi = 1
		elif opt in ("-f","--file"):
			with open(arg,'rb') as f:
				text = f.read().decode()
				articles.extend(re.sub(r'[^\w/\.]+',' ',text).split())
		elif opt in ("-i","--identifier"):
			identifier = arg
		elif opt in ("-x","--xml"):
			xml = 1
		elif opt in ("-p","--pdf"):
			pdf = 1
		elif opt in ("-r","--redcap"):
			redcap = 1
		elif opt in ("-d","--download"):
			down = 1
		elif opt in ("-t","--train"):
			train = arg
		elif opt in ("-z","--zxml"):
			zxml = arg
	return ({
		'indi':indi,
		'ident':identifier,
		'xml':xml,
		'pdf':pdf,
		'redcap':redcap,
		'down':down,
		'train':train,
		'zxml':zxml
		}, articles)

def main(argv):
	opts, articles = get_command_args(argv)
	metadata = DatabaseManager().get_metadata()

	if (opts['train']):

		#meta_analysis = Trainer("meta_analysis",articles)
		#meta_analysis.pickle()

		#primary_research = Trainer("primary_research",articles)

		for field in opts['train'].split(','):
			tr = Trainer(field.strip(),articles)
		searchwords = ['statistical','analysis','standard','deviation','sd','chi-squared','test','significance','t-test','Poisson',
						'regression','model','data','intercepts','hazard','odds','ratio','Cox','normally','distributed','multivariate']
		return

	for each_article in articles:
		print(each_article)
		os.environ['article_id'] = each_article
		os.environ['identifier'] = opts['ident']

		if (opts['zxml']):
			try:
				#opts['zxml'] is the xml file
				art = XMLArticle(ArticleManager().read_xml(opts['zxml'],opts['ident'],each_article),opts['indi'],each_article,opts['ident'],metadata=metadata)
				#instantiation is redundant but allows ArticleManager to be used without XMLArticle
			except TypeError as e:
				#article not found or not open access
				print("{} not found".format(each_article))
				continue
		else:
			try:
				art = PDFArticle("articles/{}".format(each_article),each_article,'pmid',run_style=opts['indi'],metadata=metadata)
			except TypeError as e:
				raise
				print("{} not found".format(each_article))
				continue

		if (opts['xml']):
			xe = XMLExtractor()
			xml = xe.xml_load("{0}pubmed/{1}{2}".format(ncbi_site,each_article,xml_tag))
			art.entry.update(xe.xml_extract(xml))

			try:
				art.get_institution(xe.institution)
				art.get_clinical_domain_from_xml(xe.institution)
			except AttributeError as e:
				#'XMLExtractor' object has no attribute 'institution'
				#xml extract failed during http request or parsing, user already notified
				pass

		if (opts['down']):
			art.download_pdf()

		if (opts['pdf']):

			art.get_reviewer()
			art.get_hypotheses()
			art.get_funding()

			art.get_inex_criteria()
			art.get_ontol_vocab()
			## ^^ TODO

			art.get_databases()
			art.get_query()		#TODO
			art.get_nlp()

			#left off for pmc here:
			art.get_analysis()
			art.get_stats()

			art.get_limitations()


		art.entry = art.clean_entry()
		pprint(art.entry)
		print(len(art.entry))

		if (opts['redcap']):
			art.enter_redcap(art.entry,'9b7057f5f8894c9c')
			print(str(art.redcap_return))

		print("\n\n\n\n")

	del os.environ['article_id']
	del os.environ['identifier']


if __name__ == "__main__":
	main(sys.argv[1:])
