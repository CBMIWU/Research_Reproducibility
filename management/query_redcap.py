#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from getopt import getopt
import csv, os, re, sys
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))

import pycurl, hashlib, json, nltk
import requests
from pprint import pprint
from DatabaseManager import DatabaseManager


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
		dm.get_ml_data(opts['redcap'])

if __name__ == "__main__":
	main(sys.argv[1:])
