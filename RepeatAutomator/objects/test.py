#!/usr/bin/env python2

from pprint import pprint
import DatabaseManager

print("~~~ Testing DatabaseManager ~~~")

dm = DatabaseManager.DatabaseManager()

dm.get_data('author_ln')
dm.get_data('reviewer')

dm.get_matches("analysis_sw",1,"SAS")
dm.get_matches("reviewer",0,6)

dm.get_searches("analysis_sw",1,'SAS')
dm.get_searches('article_doi',1,'10.1097')
dm.get_searches('article_title',1,'cancer')

dm.get_metadata()

dm.get_ml_data("analysis_processes_clear")

print("~~~ Testing XMLExtractor ~~~")

import XMLExtractor
xe = XMLExtractor.XMLExtractor()

from bs4 import BeautifulSoup

bs = BeautifulSoup("<ImportantInformation><BestDinosaur>triceratops</BestDinosaur><BestCountry>Ireland</BestCountry></ImportantInformation>",'lxml')
bs = xe.xml_load("http://www.ncbi.nlm.nih.gov/pubmed/24433938?report=xml&format=text")
xe.xml_load("http://www.github.com")
xe.xml_load("not a url :(")

pprint(xe.xml_extract(bs))
pprint(xe.xml_extract(xe.xml_load("http://www.ncbi.nlm.nih.gov/pubmed/24433938?report=xml&format=text")))

print("~~~ Testing ArticleManager ~~~")

import ArticleManager
am = ArticleManager.ArticleManager()

# TODO
# ge = am.get_articles_xml("./otherthings/test-resources/pmc_result_samp.xml","pmid",['23449283'])
# next(ge)

# ge = am.get_articles_xml("./otherthings/test-resources/pmc_result_samp.xml","pmc",['3592787'])
# next(ge)

# am.enter_redcap({'author_fn':'Johnny','author_ln':'Cash'},'9b7057f5f8894c9c')
# am.enter_redcap({'clinical_domain':'cardiology','article_title':'lions have big hearts'},'9b7057f5f8894c9c')
# am.enter_redcap({'clinical_domain':'cardiology'},'9b7057f5f8894c9c')

# am = ArticleManager.ArticleManager(run_style=0)
# am.enter_redcap({'author_fn':'bruce','author_ln':'willis'},'9b7057f5f8894c9c')
# am.enter_redcap({'author_fn':'the green goblin','author_email':'BlueGoblinsSUCK@greenmail.com'},'9b7057f5f8894c9c')

from Article import RawArticle
ra = RawArticle("./otherthings/test-resources/PCD-10-E29.pdf")
ra.text[:1000]

print("~~~ Testing ArticleExtractor ~~~")

import ArticleExtractor
ae = ArticleExtractor.ArticleExtractor(run_style=0)
ae.get_reviewer()
ae.entry
ae._get_hypotheses(ra.text)
ae._get_funding(ra.text)
ae._get_inex_criteria(ra.text)
ae._get_stats(ra.text)
ae._get_limitations(ra.text)

ae = ArticleExtractor.ArticleExtractor(run_style=1)
ae.entry
ae._get_inex_criteria(ra.text)
ae._get_stats(ra.text)
ae._get_limitations(ra.text)
ae.entry

print("~~~ Testing Article ~~~")

import Article
pdf = Article.PDFArticle('/Users/christian/Desktop/cbmi/reproduce/python/articles/21411379.pdf','21411379','pmid',run_style=1)
pdf.get_inex_criteria()
pdf.get_stats()
pdf.get_limitations()

xmla = Article.XMLArticle('10.5888/pcd10.120097','doi',bs=next(am.get_articles_xml('/Users/christian/Desktop/cbmi/reproduce/python/articles/sub_pmc_result.xml','doi',['10.5888/pcd10.120097']))[0])
import sys
sys.stdout.write(xmla.bs.text[:1000])

sys.stdout.write(xmla.xml_section('methods','background'))
xmla.get_hypotheses()
xmla.get_stats()
xmla.get_inex_criteria()
