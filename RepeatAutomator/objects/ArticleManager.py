#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import *

import sys, re, os
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))

import pycurl, io, json
from pprint import pprint
from bs4 import BeautifulSoup
from DatabaseManager import DatabaseManager

class ArticleManager(DatabaseManager):

	def __init__(self,metadata=DatabaseManager().get_metadata(),run_style=1):
		self.indi = run_style
		self.metadata = self.verify_meta(metadata)
		self.entry = {}

	def verify_meta(self,metadata : 'list of dictionaries'):
		"""
		Affirm that metadata follows the proper format
			a metadata is:
				a list of dictionaries
				and each dictionary must have (minimum) keys:
					field_name
					field_type
					select_choices_or_calculations
		Args: proposed metadata
		Returns: metadata (if no errors occurred), (returns the parameter, unaltered)

		Example:
		>>> am = ArticleManager()
		>>> am.verify_meta([{'field_type': 'radio','field_name': 'hypothesis_gen_or_driv','select_choices_or_calculations': ''},{'field_type': 'checkbox','field_name': 'data_analysis_doc_loc','select_choices_or_calculations': '1, Dataset Metadata | 2, Supplementary Materials | 3, Appendix | 4, Body of Text'}])
		[{'field_name': 'hypothesis_gen_or_driv', 'field_type': 'radio', 'select_choices_or_calculations': ''},
		{'field_name': 'data_analysis_doc_loc', 'field_type': 'checkbox', 'select_choices_or_calculations': '1, Dataset Metadata | 2, Supplementary Materials | 3, Appendix | 4, Body of Text'}]

		Raise error if metadata doesnt follow proper format
		>>> am.verify_meta("red hot chili peppers")
		Traceback (most recent call last):
		  File "<stdin>", line 1, in <module>
		  File "/Users/christian/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects/ArticleManager.py", line 42, in verify_meta
		    raise TypeError("metadata must be type 'list' but is type: {0} \nmetadata: {1} \nexample metadata: {2}".format(type(metadata),metadata,example))
		TypeError: metadata must be type 'list' but is type: <class 'str'>
		metadata: red hot chili peppers
		example metadata: [{'select_choices_or_calculations': '', 'field_type': 'text', 'field_label': 'Record ID', 'field_name': 'record_id'},
		{'select_choices_or_calculations': '1, Hypothesis Driven | 2, Hypothesis Generating | 3, Unclear', 'field_type': 'radio',
		'branching_logic': '', 'field_label': 'Is the research hypothesis-driven or hypothesis-generating?', 'field_name': 'hypothesis_gen_or_driv'}]

		>>> am.verify_meta([{"field_name":'outfield'},{"field_name":'player'}])
		Traceback (most recent call last):
		  File "<stdin>", line 1, in <module>
		  File "/Users/christian/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects/ArticleManager.py", line 65, in verify_meta
		    raise KeyError("each list-item in metadata must contain at least the keys: 1) 'field_name', 2) 'field_type', 3) 'select_choices_or_calculations' .\nitem: {}\nexample metadata: {}".format(item,example))
		KeyError: "each list-item in metadata must contain at least the keys: 1) 'field_name', 2) 'field_type', 3) 'select_choices_or_calculations' .
		item: {'field_name': 'outfield'}
		example metadata: [{'select_choices_or_calculations': '', 'field_type': 'text', 'field_label': 'Record ID', 'field_name': 'record_id'},
		{'select_choices_or_calculations': '1, Hypothesis Driven | 2, Hypothesis Generating | 3, Unclear', 'field_type': 'radio',
		'branching_logic': '', 'field_label': 'Is the research hypothesis-driven or hypothesis-generating?', 'field_name': 'hypothesis_gen_or_driv'}]"
		"""
		example = """[{'select_choices_or_calculations': '', 'field_type': 'text', 'field_label': 'Record ID', 'field_name': 'record_id'},
{'select_choices_or_calculations': '1, Hypothesis Driven | 2, Hypothesis Generating | 3, Unclear', 'field_type': 'radio',
'branching_logic': '', 'field_label': 'Is the research hypothesis-driven or hypothesis-generating?', 'field_name': 'hypothesis_gen_or_driv'}]"""
		if (type(metadata) is not list):
			raise TypeError("metadata must be type 'list' but is type: {} \n\nmetadata: {} \nexample metadata: {}".format(type(metadata),metadata,example))
		for item in metadata:
			if (type(item) is not dict):
				raise TypeError("each list-item of metadata must be a dict but item: {} is type: {} \nexample metadata: {}".format(item,type(item),example))
			if ('field_name' not in item or 'field_type' not in item or 'select_choices_or_calculations' not in item):
				raise KeyError("each list-item in metadata must contain at least the keys: 1) 'field_name', 2) 'field_type', 3) 'select_choices_or_calculations' .\nitem: {}\nexample metadata: {}".format(item,example))
		return metadata

	def ask(self,question,redcap):
		if (self.indi == 1):
			return 0
		choices = self.get_choices(redcap)
		if (choices == -1):
			return self.ask_without_choices(question,"Please enter the value: ",redcap)
		self.generate_chooser(question,"",choices)
		if (self.user_choice != -1):
			self.entry[redcap] = self.user_choice
			return 1
		return 0

	def ask_without_choices(self,question,prompt,redcap):
		if (self.indi == 1):
			return 0
		if (self.ask_question(question)):
			self.user_choice = input(prompt)
			print(self.user_choice)
			print("\n\n")
			self.assign(redcap,self.user_choice)
			return 1
		return 0

	def ask_question(self,question):
		if (self.indi == 1):
			return 0
		can_answer = input(question + " (if yes, type yes and press enter; otherwise, press enter): ")
		print("\n\n")
		if re.search(r'yes',can_answer,re.I):
			return 1
		else:
			return 0

	def generate_chooser(self,variable,info,choices):
		if (self.indi == 1):
			self.user_choice = -1
			return
		root = Tk()
		v = IntVar()
		v.set(1)
		root.title("Chooser GUI")
		Message(root, text=variable).pack(fill=X)
		Button(root, text='OK', width=25, command=root.destroy).pack()
		for choice in choices:
			Radiobutton(root,text=choice,padx=30,variable=v,value=choices[choice]).pack()
		Radiobutton(root,text="None of the options",padx=30,variable=v,value=-1).pack()
		root.mainloop()
		self.user_choice = v.get()

	def get_choices(self,redcap):
		for item in self.metadata:
			if (item['field_name'] == redcap):
				if (item['field_type'] == "yesno"):
					return {"yes":1,"no":0}
				opt_str = item['select_choices_or_calculations']
		if (not opt_str):
			return -1
		opt_tup = opt_str.split('|')
		opt_dic = {}
		for each_tup in opt_tup:
			(val,opt) = each_tup.split(',')
			val = val.strip()
			opt = opt.strip()
			opt_dic[opt] = val
		return opt_dic


	def assign(self,redcap,value):
		if (redcap in self.entry):
			self.entry[redcap] += "," + str(value)
			return self.entry[redcap]
		self.entry[redcap] = str(value)
		return value

	def check(self,variable,value,display,info,redcap):
		correct = self.check_boolean(variable,value,display,info,redcap)
		if (correct == 1):
			return
		if (self.ask_question("Do you know the correct value?")):
			choices = self.get_choices(redcap)
			if (choices == -1):
				overwrite_val = input("Type the correct value for " + variable + ": ")
				overwrite_val.strip()
				self.user_choice = overwrite_val
				self.assign(redcap,overwrite_val)
				print("\n\n")
			else:
				self.generate_chooser(variable,info,choices)
			#with open("record.log",'a') as f:
			#	f.write("\t\t{}\n".format(self.user_choice))
			return self.assign(redcap,self.user_choice)
		else:
			return

	def check_boolean(self,variable,value,display,info,redcap):
		#with open("record.log",'a') as f:
		#	f.write("\t{}\n\t\t{}\n".format(variable,display))
		if (self.indi):
			self.assign(redcap,value)
			return 1

		print("I think '" + variable + "' should be: '" + display + "' based on:\n" + info)

		correct = input("Is this correct? (if no, type no and press enter; otherwise, press enter): ")
		print("\n\n")
		if re.search(r'no',correct,re.I):
			print("\n\n")
			return 0
		else:
			print("\n\n")
			self.assign(redcap,value)
			return 1

	def read_xml(self,file,identifier,search_id):
		search_id = str(search_id)
		with open(file,'r') as x:
			bs = BeautifulSoup(x.read(),"lxml")

		for ass in bs.find_all("article"):
			#if (ass.find('article-id',{'pub-id-type':'pmc'}).text == '3592787'):
			if (ass.find('article-id',{'pub-id-type':identifier}).text == search_id):
				if (ass.find(text=re.compile("The publisher of this article does not allow downloading of the full text in XML form"))):
					#article isnt open access :(
					return -1
				#found open access article
				return str(ass)
		return -1		#article not found

	def download_pdf(self):
		"""
		if (not os.path.isdir("articles/")):
			os.makedirs("articles/")

		ids = self.xml['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']
		for each_id in ids:
			if (each_id['@IdType'] == "pmc"):
				pmc = each_id['#text']

		xml = self.xml_load(ncbi_site + "pmc/" + pmc_tag + pmc)
		links = xml['OA']['records']['record']['link']
		for link in links:
			print(link)
			if (link['@format'] == 'pdf'):
				href = link['@href']
		print(href)
		bashCommand = "wget " + href
		subprocess.run(bashCommand.split())

		bashCommand = "mv " + href.split('/')[-1] + " " + self.pubmed_code + ".pdf"
		subprocess.run(bashCommand.split())
		"""
		return

	def enter_redcap(self,entry : 'dictionary', record_id, **kwargs):
		"""
		Enter entry into redcap
		Args: redcap entry (dictionary where keys are redcap codebook keys)
		KeywordArgs: record_id (string or int), default to next available record_id autoincrememnt
		Return: dictionary detailing:
			how many entrie were edited if upload was successful
			what caused the error and why if upload was unsuccessful

		Example:
		>>> am = ArticleManager()
		>>> am.enter_redcap({"author_fn":"kurt","author_ln":"vonnegut"},40)
		{'status': 'success', 'count': 1}
		>>> am.enter_redcap({"author_fn":"george","author_ln":"lucas"})
		{'status': 'success', 'count': 1}
		#TODO, left off on error management



		"""
		#entry['record_id'] = record_id			#leave out for now so I dont destroy redcap...
		entry['record_id'] = '9b7057f5f8894c9c'

		#see redcap api documentation -- https://redcap.wustl.edu/redcap/srvrs/prod_v3_1_0_001/redcap/api/help/
		from config import config
		buf = io.BytesIO()
		data = json.dumps([entry])
		fields = {
		    'token': config['api_token'],
		    'content': 'record',
		    'format': 'json',
		    'type': 'flat',
		    'data': data,
		}

		ch = pycurl.Curl()
		ch.setopt(ch.URL, config['api_url'])
		ch.setopt(ch.HTTPPOST, list(fields.items()))
		ch.setopt(ch.WRITEFUNCTION, buf.write)
		ch.perform()
		ch.close()

		redcap_return = buf.getvalue()
		buf.close()
		if (re.search(b'error',redcap_return)):
			splitreturn = list(map(bytes.decode,redcap_return.split(b'\\"')))
			fails = {"status":"error","record_id":splitreturn[1],"redcap_field":splitreturn[3],"value":splitreturn[5],"reason":splitreturn[7]}
			print("redcap entry failed on field: '{}'\nbecause: '{}'".format(fails['redcap_field'],fails['reason']))

			self.record_error(method='enter_redcap',object_caller='`ArticleManager`',record_id=splitreturn[1],field=splitreturn[3],value=splitreturn[5],notes=splitreturn[7])

			#note if it was resolved
			if (self.ask("Would you like to edit field: '{}'".format(fails['redcap_field']),fails['redcap_field'])):
				entry[fails['redcap_field']] = self.user_choice
				return self.enter_redcap(entry,record_id)
			elif (self.ask_question("Would you like to abandon entry?")):
				self.redcap_return = fails
				return self.redcap_return
			else:
				print("retrying entry without that field")
				del entry[fails['redcap_field']]
				del entry['record_id'] 			#so that entry is empty if no other fields
				if (not entry):
					#entry is empty, no fields left to attempt to upload to redcap
					self.redcap_return = {"status":"fail","count":0}
					return self.redcap_return
				return self.enter_redcap(entry,record_id)
		self.redcap_return = {"status":"success","count":1}
		return self.redcap_return

	def record_data(self,entrylog):
		return #TODO
		conn = sqlite3.connect('errors.db')
		c = conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS errortable(article_id TEXT, identifier TEXT, record_id TEXT, field TEXT, machine_value TEXT, human_value TEXT, altered INTEGER, run_style INTEGER, datetimestamp TEXT)")

		entry = {"article_id":'','identifier':'','record_id':'','method':'','object':'','field':'','value':'','notes':'','time':strftime("%Y-%m-%d %H:%M:%S",localtime())}
		entry.update(errorlog)
		c.execute("INSERT INTO errortable VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (entry['article_id'],entry['identifier'],entry['record_id'],entry['method'],entry['object'],entry['field'],entry['value'],entry['notes'],entry['time']))
		conn.commit()
		c.close()
		conn.close()
