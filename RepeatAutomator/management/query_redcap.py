#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from getopt import getopt
import os, sys
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME'])) #TODO
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))
from pprint import pprint
from DatabaseManager import DatabaseManager

"""
Interface for running DatabaseManager methods:
	get_data
	get_matches
	get_searches
	get_ml_data
See DatabaseManager for more information

Depends on imported modules:
	os				-- https://docs.python.org/3/library/os.html
	sys				-- https://docs.python.org/3/library/sys.html
	getopt 			-- https://docs.python.org/3.1/library/getopt.html
	pprint 			-- https://docs.python.org/3/library/pprint.html
See documentation for more information

Command line arguemnts:
	--redcap=, -r 			-- redcap codebook key
	--match, -m				-- return only exact matches (execute DatabaseManager.get_matches)
	--search, -s			-- return near matches (execute DatabaseManager.get_searches)
	--data, -d				-- return all observations
	--boolean, -b 			-- by default, returns observations that matched criteria; boolean flag returns observations that did not match
	--value=, -v			-- value {--redcap} argument compared to
	--machine-learning, -m	-- get data on {--redcap} argument in machine-learning format

Examples:
christian$ ./query_redcap --redcap=analysis_sw --value=SAS --match
[('10.1016/j.urology.2012.11.002', '17', 'SAS'),
 ('10.1186/1472-6963-13-414', '23', 'SAS'),
 ('10.1016/j.jmig.2011.01.009', '25', 'SAS'),
 ('10.1158/1055-9965.EPI-14-0487', '36', 'SAS')]
#calls DatabaseManager.get_matches method
#all articles where ONLY SAS was used to analyze the data

christian$ ./query_redcap -r analysis_sw -v SAS -s
[('10.1016/j.urology.2012.11.002', '17', 'SAS'),
 ('10.1186/1472-6963-13-414', '23', 'SAS'),
 ('10.1016/j.jmig.2011.01.009', '25', 'SAS'),
 ('10.1158/1055-9965.EPI-14-0487', '36', 'SAS'),
 ('10.1542/hpeds.2014-0085', '38', 'SPSS, SAS')]
#calls DatabaseManager.get_searches method
#all articles that used SAS to analyze data
#note, in last record, analysis_sw was: 'SPSS, SAS'

christian$ ./query_redcap.py --redcap=analysis_sw --value=SAS --search --boolean
[('10.3171/2015.10.JNS151846', '1', 'Stata'),
 ('doi:10.1093/jamia/ocu002', '3', ''),
 ('doi:10.1016/j.yebeh.2015.12.022', '4', ''),
 ('10.1007/s00247-015-3519-1', '5', 'SPSS'),
 ('10.11909/j.issn.1671-5411.2015.06.009', '6', ''),
 ('10.1177/1060028015626161', '7', ''),
 ('10.1016/j.arth.2015.12.012', '8', ''),
 ('10.1177/1060028015625660', '9', 'SPSS')
 ...
#calls DatabaseManager.get_searches
#all articles that did not use SAS to analyze their data

christian$ ./query_redcap.py -r reviewer -d
[{'record_id': '1', 'reviewer': '1', 'article_doi': '10.3171/2015.10.JNS151846'},
 {'record_id': '2', 'reviewer': '1', 'article_doi': ''},
 {'record_id': '3', 'reviewer': '3', 'article_doi': 'doi:10.1093/jamia/ocu002'},
 {'record_id': '4', 'reviewer': '1', 'article_doi': 'doi:10.1016/j.yebeh.2015.12.022'},
 {'record_id': '5', 'reviewer': '1', 'article_doi': '10.1007/s00247-015-3519-1'}]
 ...
#calls DatabaseManager.get_data method
#record_id, reviewer, and article_doi for all observations

christian$ ./query_redcap.py --redcap=analysis_processes_clear --machine-learning
{'1': True,
 '10': True,
 '13': True,
 '14': True,
 '15': True,
 '16': True,
 '17': True,
 '18': False,
 '19': False,
 '2': True,
 '20': True,
 '21': False,
 '22': True,
 '23': True,
 ...
#calls DatabaseManager.get_ml_data method
#a dictionary of format:
	#{record_id : analysis_processes_clear}
#for all redcap observations
"""


def get_command_args(argv):
	boolean = value = 1
	mach = data = match = search = 0
	opts, args = getopt(argv,"r:mbv:lds",["redcap=","match","boolean","value=","machine-learning","data","search"])
	for opt,arg in opts:
		if opt in ("-r","--redcap"):
			redcap = arg
		elif opt in ("-m","--match"):
			match = 1
		elif opt in ("-b","--boolean"):
			boolean = 0
		elif opt in ("-v","--value"):
			value = arg
		elif opt in ("-l","--machine-learning"):
			mach = 1
		elif opt in ("-d","--data"):
			data = 1
		elif opt in ("-s","--search"):
			search = 1
	return {
		'bool':boolean,
		'redcap':redcap,
		'match':match,
		'value':value,
		'mach':mach,
		'data':data,
		'search':search
		}

def main(argv):
	opts = get_command_args(argv)
	dm = DatabaseManager()

	if (opts['data']):
		pprint(dm.get_data(opts['redcap']))
	if (opts['match']):
		pprint(dm.get_matches(opts['redcap'],opts['bool'],opts['value']))
	if (opts['search']):
		pprint(dm.get_searches(opts['redcap'],opts['bool'],opts['value']))

	if (opts['mach']):
		pprint(dm.get_ml_data(opts['redcap']))

if __name__ == "__main__":
	main(sys.argv[1:])
