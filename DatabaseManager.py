#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from getopt import getopt
import csv, os, sys, re
sys.path.append("{0}/Desktop/cbmi/reproduce/python".format(os.environ['HOME']))
import pycurl, json, io
from pprint import pprint
from difflib import get_close_matches

import sqlite3
from time import strftime,localtime

from config import config
#config contains redcap login information



class DatabaseManager(object):
	"""
	Grab redcap data for a particular field
	Grab redcap entries that meet certain criteria
	Load study metadata from redcap
	Pull data in machine-learning format (intended to be used with Trainer module - see Trainer documenation for more information)

	Depends on imported modules:
		pycurl 			-- http://pycurl.io/docs/latest/index.html
		pprint 			-- https://docs.python.org/3/library/pprint.html
		json 			-- https://docs.python.org/3.4/library/json.html
		io 				-- https://docs.python.org/3/library/io.html
		csv 			-- https://docs.python.org/3/library/csv.html
		difflib 		-- https://docs.python.org/2/library/difflib.html
	See documentation for more information
	"""

	def record_error(self,article_id='',identifier='',record_id='',method='',object_caller='',field='',value='',notes='',time=strftime("%Y-%m-%d %H:%M:%S",localtime())):
		conn = sqlite3.connect('errors.db')
		c = conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS errortable(article_id TEXT, identifier TEXT, record_id TEXT, method TEXT, object TEXT, field TEXT, value TEXT, notes TEXT, datetimestamp TEXT)")

		#if theyre defined in environment variables
		if ('article_id' and 'identifier' in os.environ):
			#if they werent instantiated in keyword args
			if (not article_id):
				article_id = os.environ['article_id']
			if (not identifier):
				identifier = os.environ['identifier']

		c.execute("INSERT INTO errortable VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (article_id,identifier,record_id,method,object_caller,field,value,notes,time))
		conn.commit()
		c.close()
		conn.close()

	def get_data(self,field : 'string - redcap key') -> 'list of dictionaries':
		"""
		Pull data from redcap for a given field
		Args: redcap codebook key (string)
		Return: list of dictionaries - each with: record_id, article_doi, {field}
			for all redcap entries
				dictionary contains only record_id and article_doi if {field} is an invalid redcap key

		Example:
		>>> qu = Query()
		>>> qu.get_data('reviewer')[:5]
		[{'record_id': '1', 'reviewer': '1', 'article_doi': '10.3171/2015.10.JNS151846'},
		 {'record_id': '2', 'reviewer': '1', 'article_doi': ''},
		 {'record_id': '3', 'reviewer': '3', 'article_doi': 'doi:10.1093/jamia/ocu002'},
		 {'record_id': '4', 'reviewer': '1', 'article_doi': 'doi:10.1016/j.yebeh.2015.12.022'},
		 {'record_id': '5', 'reviewer': '1', 'article_doi': '10.1007/s00247-015-3519-1'}]

		>>> qu.get_data('HomerSimpson')[:5]
		[{'record_id': '1', 'article_doi': '10.3171/2015.10.JNS151846'},
		 {'record_id': '2', 'article_doi': ''},
		 {'record_id': '3', 'article_doi': 'doi:10.1093/jamia/ocu002'},
		 {'record_id': '4', 'article_doi': 'doi:10.1016/j.yebeh.2015.12.022'},
		 {'record_id': '5', 'article_doi': '10.1007/s00247-015-3519-1'}]
		"""

		#see redcap api documentation -- https://redcap.wustl.edu/redcap/srvrs/prod_v3_1_0_001/redcap/api/help/
		buf = io.BytesIO()
		data = {
		    'token': 'D9FFA77DB83AE7D9E3E92BB0B0CBBFDB',
		    'content': 'record',
		    'format': 'json',
		    'type': 'flat',
		    'fields[0]': 'article_doi',
		    'fields[1]': 'record_id',
		    'fields[2]': field,
		    'rawOrLabel': 'raw',
		    'rawOrLabelHeaders': 'raw',
		    'exportCheckboxLabel': 'false',
		    'exportSurveyFields': 'false',
		    'exportDataAccessGroups': 'false',
		    'returnFormat': 'json'
		}
		ch = pycurl.Curl()
		ch.setopt(ch.URL, 'https://redcap.wustl.edu/redcap/srvrs/prod_v3_1_0_001/redcap/api/')
		ch.setopt(ch.HTTPPOST, list(data.items()))
		ch.setopt(ch.WRITEFUNCTION, buf.write)
		ch.perform()
		ch.close()
		records = json.loads(buf.getvalue().decode())
		buf.close()
		return records

	def get_matches(self,redcap : 'string - redcap key',boolean : 'bool - how to match',val : 'string / int - value of redcap field') -> 'list of dictionaries':
		"""
		Query redcap for entries where a field matches (or doesnt match) a given value
		Args:
			redcap codebook key (string)
			boolean (1 or 0)
				1 - return all entries where the redcap field {redcap} matches the value {val}
				0 - return all entries where the redcap field {recap} DO NOT match the value {val}
			value of field
		Return: list of dictionaries - each with: record_id, article_doi, {field}
			for all redcap entries matching the given criteria
		*** get_matches() only returns exact matches; for near matches see get_searches() ***

		Example:
		>>> qu = Query()
		>>> qu.get_matches("analysis_sw",1,"SAS")
		[('10.1016/j.urology.2012.11.002', '17', 'SAS'),
		 ('10.1186/1472-6963-13-414', '23', 'SAS'),
		 ('10.1016/j.jmig.2011.01.009', '25', 'SAS'),
		 ('10.1158/1055-9965.EPI-14-0487', '36', 'SAS')]
		#all articles where ONLY SAS was used to analyze the data

		>>> qu.get_matches("article_doi",1,"10.1016/j.jaapos.2014.06.006")
		[('10.1016/j.jaapos.2014.06.006', '21', '10.1016/j.jaapos.2014.06.006')]
		#all articles with doi value of 10.1016/j.jaapos.2014.06.006

		>>> qu.get_matches("reviewer",0,6)
		[('10.3171/2015.10.JNS151846', '1', '1'),
		 ('doi:10.1093/jamia/ocu002', '3', '3'),
		 ('doi:10.1016/j.yebeh.2015.12.022', '4', '1'),
		 ('10.1007/s00247-015-3519-1', '5', '1'),
		 ('10.11909/j.issn.1671-5411.2015.06.009', '6', '1'),
		 ('10.1177/1060028015626161', '7', '1'),
		 ('10.1016/j.midw.2016.01.001', '13', '3'),
		 ('10.1002/ajh.23911', '15', '3'),
		 ('http://dx.doi.org/10.1016/j.yebeh.2015.12.022', '16', '2'),
		 ('10.1016/j.burns.2013.12.002', '18', '4'),
		 ('10.1016/j.ygyno.2013.04.055', '20', '4'),
		 ('10.1016/j.jstrokecerebrovasdis.2015.06.043', '22', '4'),
		 ('10.1016/j.joms.2016.01.001', '28', '4'),
		 ('10.1186/1471-2318-14-75', '30', '4'),
		 ('10.1111/edt.12260', '31', '4'),
		 ('10.1016/j.clinthera.2011.08.005', '32', '4'),
		 ('/pubmed/26212850', '34', '4'),
		 ('10.0126', '243aacb916cbefb1', '')]
		#all articled that were reviewed by someone other than reviewer 6

		Throws error if redcap field not found
		>>> qu.get_matches("analysissw")
		redcap field: 'analysissw'
		not found. did you mean: '['analysis_sw', 'analysis_os', 'meta_analysis']'?
		verify and try again
		"""
		matches = []
		try:
			for eachdict in self.get_data(redcap):
				if (boolean):
					if (eachdict[redcap].strip() == str(val)):
						matches.append((eachdict['article_doi'],eachdict['record_id'],eachdict[redcap]))
				else:
					if (eachdict[redcap].strip() != str(val)):
						matches.append((eachdict['article_doi'],eachdict['record_id'],eachdict[redcap]))
		except KeyError as e:
			print("redcap field: '{}'\nnot found. did you mean: '{}'?\nverify and try again".format(redcap,get_close_matches(redcap,[d['field_name'] for d in self.get_metadata()])))

		return matches

	def get_searches(self,redcap : 'string - redcap key',boolean : 'bool - how to match',val : 'string / int - value of redcap field') -> 'list of dictionaries':
		"""
		Query redcap for entries where a field matches (or doesnt match) a given value
		Args:
			redcap codebook key (string)
			boolean (1 or 0)
				1 - return all entries where the redcap field {redcap} matches the value {val}
				0 - return all entries where the redcap field {recap} DO NOT match the value {val}
			value of field
		Return: list of dictionaries - each with: record_id, article_doi, {field}
			for all redcap entries matching the given criteria
		*** get_searches() returns near matches; for exact matches see get_matches() ***

		Example:
		>>> qu = Query()
		>>> qu.get_searches("analysis_sw",1,'SAS')
		[('10.1016/j.urology.2012.11.002', '17', 'SAS'),
		 ('10.1186/1472-6963-13-414', '23', 'SAS'),
		 ('10.1016/j.jmig.2011.01.009', '25', 'SAS'),
		 ('10.1158/1055-9965.EPI-14-0487', '36', 'SAS'),
		 ('10.1542/hpeds.2014-0085', '38', 'SPSS, SAS')]
		#all articles that used SAS to analyze data
		#note, in last record, analysis_sw was: 'SPSS, SAS'

		>>> qu.get_searches('article_doi',1,'10.1097')
		[('10.1097/SPV.0000000000000241', '10', '10.1097/SPV.0000000000000241'),
		 ('10.1097/AJP.0b013e3181f06b06', '24', '10.1097/AJP.0b013e3181f06b06'),
		 ('10.1097/IOP.0b013e31828a92b0', '26', '10.1097/IOP.0b013e31828a92b0'),
		 ('10.1097/PSY.0b013e31821fbf9a', '27', '10.1097/PSY.0b013e31821fbf9a')]
		#all articles with doi that contains the string '10.1097'

		>>> qu.get_searches('article_title',1,'cancer')
		[('10.1016/j.urology.2012.11.002','17','Racial and Ethnic Differences in Time to Treatment for Patients With Localized Prostate Cancer '),
		 ('10.1016/j.ygyno.2013.04.055','20','Recurrence patterns after extended treatment with bevacizumab for ovarian, fallopian tube, and primary peritoneal cancers'),
		 ('10.1016/j.jpainsymman.2015.02.022','35','Music Therapy Is Associated With Family Perception of More Spiritual Support and Decreased Breathing Problems in Cancer Patients Receiving Hospice Care'),
		 ('10.1158/1055-9965.EPI-14-0487','36','Patient and provider characteristics associated with colorectal  breast and cervical cancer screening among Asian Americans'),
		 ('10.1111/apt.13505','39','Cirrhosis is under-recognised in patients subsequently diagnosed with hepatocellular cancer')]
		#all articles with 'cancer' in their title

		Throw error if redcap field not found
		Offer suggestions if any are available
		>>> qu.get_matches("analysissw")
		redcap field: 'analysissw'
		not found. did you mean: '['analysis_sw', 'analysis_os', 'meta_analysis']'?
		verify and try again
		"""
		matches = []
		try:
			for eachdict in self.get_data(redcap):
				if (boolean):
					if (re.search(str(val),eachdict[redcap].strip(),re.I)):
						matches.append((eachdict['article_doi'],eachdict['record_id'],eachdict[redcap]))
				else:
					if not (re.search(str(val),eachdict[redcap].strip(),re.I)):
						matches.append((eachdict['article_doi'],eachdict['record_id'],eachdict[redcap]))
		except KeyError as e:
			print("redcap field: '{}'\nnot found. did you mean: '{}'?\nverify and try again".format(redcap,get_close_matches(redcap,[d['field_name'] for d in self.get_metadata()])))

		return matches

	def get_metadata(self) -> 'list of dictionaries':
		"""
		Query redcap to retrieve study metadata
		Return: list of dictionaries,
			each dictionary has fields:
				 'branching_logic'
				 'custom_alignment'
				 'field_annotation'
				 'field_label'
				 'field_name'
				 'field_note'
				 'field_type'
				 'form_name'
				 'identifier'
				 'matrix_group_name'
				 'matrix_ranking'
				 'question_number'
				 'required_field'
				 'section_header'
				 'select_choices_or_calculations'
				 'text_validation_max'
				 'text_validation_min'
				 'text_validation_type_or_show_slider_number'

		Example:
		>>> qu = Query()
		>>> qu.get_metadata()
		[{'branching_logic': '',
		 'custom_alignment': '',
		 'field_annotation': '',
		 'field_label': 'Record ID',
		 'field_name': 'record_id',
		 'field_note': '',
		 'field_type': 'text',
		 'form_name': 'publication_overview_and_bibliographic_information',
		 'identifier': '',
		 'matrix_group_name': '',
		 'matrix_ranking': '',
		 'question_number': '',
		 'required_field': '',
		 'section_header': '',
		 'select_choices_or_calculations': '',
		 'text_validation_max': '',
		 'text_validation_min': '',
		 'text_validation_type_or_show_slider_number': ''},
		 ...
		]
		"""

		#see redcap api documentation -- https://redcap.wustl.edu/redcap/srvrs/prod_v3_1_0_001/redcap/api/help/
		buf = io.BytesIO()

		fields = {
		    'token': config['api_token'],
		    'content': 'metadata',
		    'format': 'json'
		}

		ch = pycurl.Curl()
		ch.setopt(ch.URL, config['api_url'])
		ch.setopt(ch.HTTPPOST, list(fields.items()))
		ch.setopt(ch.WRITEFUNCTION, buf.write)
		ch.perform()
		ch.close()

		metadata = json.loads(buf.getvalue().decode())
		buf.close()
		return metadata

	def get_ml_data(self,redcap) -> 'dictionary':
		"""
		Query redcap to retrieve data to use in machine learning algorithm
		Args: redcap codebook key (string)
		Return: dictionary of format:
				{record_id : redcap value}
				where redcap value is either 0 (for no) or 1 (for yes) or '' (for a blank field)
				for all redcap entries

		Example:
		>>> qu = Query()
		>>> qu.get_ml_data("analysis_processes_clear")
		{'2': '1', '39': '1', '30': '1', '28': '1', '24': '1', '15': '1', '16': '1', '13': '1', '9': '0', '25': '1', '27': '1', '36': '1', '4': '1', '8': '0', '3': '1', '35': '1',
		 '19': '0', '37': '1', '21': '0', '23': '1', '7': '0', '17': '1', '29': '1', '6': '1', '33': '1', '32': '', '34': '', '10': '1', '14': '1', '26': '0', '5': '0', '20': '1',
		 '18': '0', '38': '1', '1': '1', '31': '', '22': '1'}

		Force-quit if called on invalid redcap key
			(a redcap key can be invalid because its not a binary field or because it doesnt exist in the redcap metadata)
		>>> qu.get_ml_data("author_fn")
		get_data called on invalid redcap field: author_ln
		get_ml_data can only be called on fields of field_type yesno but field type of author_ln is: 'text'

		>>> qu.get_ml_data("meta-analysis")
		redcap field: 'meta-analysis'
		in get_ml_data() call not found. did you mean: '['meta_analysis', 'analysis_sw', 'analysis_os']'?
		verify and try again

		"""
		mldata = {}
		for item in self.get_metadata():
			if (item['field_name'] == redcap):
				if (item['field_type'] != "yesno"):
					print("get_data called on invalid redcap field: {}\nget_ml_data can only be called on fields of field_type yesno but field type of {} is: '{}'".format(redcap,redcap,item['field_type']))
					return
		try:
			for eachdict in self.get_data(redcap):
				mldata[eachdict['record_id'].strip()] = eachdict[redcap].strip()
		except KeyError as e:
			raise KeyError("redcap field: '{}'\nin get_ml_data() call not found. did you mean: '{}'?\nverify and try again".format(redcap,get_close_matches(redcap,[d['field_name'] for d in self.get_metadata()])))
		return mldata
