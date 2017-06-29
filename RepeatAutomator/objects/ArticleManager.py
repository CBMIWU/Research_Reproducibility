#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Attempt at python2/python3 compatibility
try:
    from tkinter import *
except ImportError:
    from Tkinter import *

from bs4 import BeautifulSoup
from pprint import pprint
import io
import json
import os
import pycurl
import re
import sys
from DatabaseManager import DatabaseManager


class ArticleManager(DatabaseManager):

    """
    Manage interaction between user and program
    Manage storage of fields for an article
    Enter an entry into redcap
    (Note that most of these methods are not intended to be executed by themselves so, in a vacuum, they will seem redundant or inpractical)


    Depends on imported modules:
            os				-- https://docs.python.org/3/library/os.html
            sys				-- https://docs.python.org/3/library/sys.html
            re				-- https://docs.python.org/3/library/re.html
            pycurl 			-- http://pycurl.io/docs/latest/index.html
            json 			-- https://docs.python.org/3.4/library/json.html
            io 				-- https://docs.python.org/3/library/io.html
            pprint 			-- https://docs.python.org/3/library/pprint.html
            beautiful soup	-- https://www.crummy.com/software/BeautifulSoup/bs4/doc/
            tkinter 		-- https://docs.python.org/3/library/tk.html
    Inherited methods from DatabaseManager:
            record_error
    See documentation for more information
    """

    def __init__(self, metadata=DatabaseManager().get_metadata(), run_style=1):
        self.run_style = run_style
        self.metadata = self.verify_meta(metadata)
        self.entry = {}

    def verify_meta(self, metadata):
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
            raise TypeError("metadata must be type 'list' but is type: {} \n\nmetadata: {} \nexample metadata: {}".format(
                type(metadata), metadata, example))
        for item in metadata:
            if (type(item) is not dict):
                raise TypeError(
                    "each list-item of metadata must be a dict but item: {} is type: {} \nexample metadata: {}".format(item, type(item), example))
            if ('field_name' not in item or 'field_type' not in item or 'select_choices_or_calculations' not in item):
                raise KeyError(
                    "each list-item in metadata must contain at least the keys: 1) 'field_name', 2) 'field_type', 3) 'select_choices_or_calculations' .\nitem: {}\nexample metadata: {}".format(item, example))
        return metadata

    def ask(self, question, redcap):
        """
        Ask user for the value of redcap field {redcap}
        Args:
                question 	-- ask if user knows the value of {redcap} (string)
                redcap 		-- redcap codebook key (string)
        Return
                1 if user entered a value
                0 if the user did not enter a value

        Example:
        >>> am = ArticleManager(run_style=0)
        >>> am.entry
        {}
        >>> am.ask("Do you know what software was used for analyses?",'analysis_sw')
        Do you know what software was used for analyses? (if yes, type yes and press enter; otherwise, press enter):
        0
        >>> am.entry
        {}
        >>> am.ask("Do you know what software was used for analyses?",'analysis_sw')
        Do you know what software was used for analyses? (if yes, type yes and press enter; otherwise, press enter): yes
        Please enter the value: Excel
        Excel
        1
        >>> am.entry
        {'analysis_sw':'Excel'}
        >>> am.ask("Whos reviewing the article?",'reviewer')	#user interface requests choice
        1
        >>> am.entry
        {'analysis_sw':'Excel','reviewer':'Leslie McIntosh'}

        >>> am = ArticleManager(run_style=1)
        >>> am.entry
        {}
        >>> am.ask("Do you know what software was used for analyses?",'analysis_sw')
        0
        >>> am.ask("Whos reviewing the article?",'reviewer')
        0
        >>> am.entry
        {}
        """
        if (self.run_style == 1):
            return 0
        choices = self.get_choices(redcap)
        if (choices == -1):
            return self.ask_without_choices(question, "Please enter the value: ", redcap)
        self.generate_chooser(question, choices)
        if (self.user_choice != -1):
            self.entry[redcap] = self.user_choice
            return 1
        return 0

    def ask_without_choices(self, question, prompt, redcap):
        """
        Ask user for the value of redcap field {redcap}
        Args:
                question 	-- ask if user knows the value of {redcap} (string)
                prompt 		-- prompt for user to enter the value
                redcap 		-- redcap codebook key (string)
        Return
                1 if user entered a value
                0 if the user did not enter a value

        >>> am = ArticleManager(run_style=0)
        >>> am.entry
        {}
        >>> am.ask_without_choices("Do you know what software was used for analyses?","Please enter the value",'analysis_sw')
        Do you know what software was used for analyses? (if yes, type yes and press enter; otherwise, press enter):
        0
        >>> am.ask_without_choices("Do you know what software was used for analyses?","Please enter the value: ",'analysis_sw')
        Do you know what software was used for analyses? (if yes, type yes and press enter; otherwise, press enter): yes
        Please enter the value: TI-84
        TI-84
        1
        >>> am.entry
        {'analysis_sw':'TI-84'}

        >>> am = ArticleManager(run_style=1)
        >>> am.entry
        {}
        >>> am.ask_without_choices("Do you know what software was used for analyses?","Please enter the value: ",'analysis_sw')
        0
        >>> am.entry
        {}
        """
        if (self.run_style == 1):
            return 0
        if (self.ask_question(question)):
            self.user_choice = input(prompt)
            print(self.user_choice)
            print("\n\n")
            self.assign(redcap, self.user_choice)
            return 1
        return 0

    def ask_question(self, question):
        """
        Ask user for input in the form of a 'yes' or 'no' question
        Args: question -- the question prompt for the user (string)
        Return: 1 if answered 'yes'
                        0 if did not answer 'yes'

        Example:
        >>> am = ArticleManager()
        >>> am.ask_question("Is the state bird of alaska the flamingo?")
        Is the state bird of alaska the flamingo? (if yes, type yes and press enter; otherwise, press enter):
        0

        >>> am.ask_question("Would I lie to you?")
        Would I lie to you? (if yes, type yes and press enter; otherwise, press enter): yes
        1

        >>> am.ask_question("Is this your first rodeo?")
        Is this your first rodeo? (if yes, type yes and press enter; otherwise, press enter): no
        0
        """
        if self.run_style == 1:
            return 0
        print(question)
        can_answer = input(
            " (if yes, type yes and press enter; otherwise, press enter): ")
        print("\n\n")
        if re.search(r'yes', can_answer, re.I):
            return 1
        else:
            return 0

    def generate_chooser(self, variable, choices, info=''):
        """
        Generate pop up window with options for the user to choose the value of a given variable
        Args:
                variable 		-- field (or description of field) user chooses a value for (string)
                choices 		-- dictionary of options for {variable} and their corresponding redcap values (dictionary)
        KeywordArgs: info 	-- extra information relative to the user (will be displayed in the pop-up window) (string)
        Return: user_choice -- option the user chose (string)

        Example:
        >>> am = ArticleManager()
        >>> am.generate_chooser('restriction_db_1',{'Closed':1,'Restricted departmental database':2,'Restricted access to only those within authors institution or clinical practice':3})
        2
        #user chose 'Restricted departmental database'

        Run the code above to see the window
        """
        if self.run_style == 1:
            self.user_choice = -1
            return

        # see tkinter for more documentation --
        # https://docs.python.org/3/library/tk.html
        root = Tk()
        v = IntVar()
        v.set(1)
        root.title("Chooser GUI")
        Message(root, text=variable).pack(fill=X)
        Button(root, text='OK', width=25, command=root.destroy).pack()
        for choice in choices:
            Radiobutton(
                root, text=choice, padx=30, variable=v, value=choices[choice]).pack()
        Radiobutton(
            root, text="None of the options", padx=30, variable=v, value=-1).pack()
        root.mainloop()
        self.user_choice = v.get()
        return self.user_choice

    def get_choices(self, redcap):
        """
        Get options for a redcap field
        Args: redcap -- redcap codebook key (string)
        Return:
                dictionary of format: {option:value} where value is always an integer
                for the given {redcap} field
                -1 if the field:
                        isnt limited to select choices
                        is not found in the given metadata

        Example:
        >>> am = ArticleManager()
        >>> am.get_choices('reviewer')
        {'Anthony Juehne': '2',
         'Christian Lukas': '6',
         'Cynthia Hudson-Vitale': '3',
         'Leslie McIntosh': '1',
         'Roberta Grannemann': '7',
         'Sam Johnson': '4',
         'Xiaoyan Liu': '5'}

        >>> am.get_choices('analysis_sw')
        -1
        >>> am.get_choices('my address')
        -1
        """
        opt_str = ''
        for item in self.metadata:
            if (item['field_name'] == redcap):
                if (item['field_type'] == "yesno"):
                    return {"yes": 1, "no": 0}
                opt_str = item['select_choices_or_calculations']
        if (not opt_str):
            return -1
        opt_tup = opt_str.split('|')
        opt_dic = {}
        for each_tup in opt_tup:
            (val, opt) = each_tup.split(',')
            val = val.strip()
            opt = opt.strip()
            opt_dic[opt] = val
        return opt_dic

    def assign(self, redcap, value):
        """
        Update object's entries dictionary to the given value
        Args:
                redcap -- redcap codebook key (string)
                value  -- value of {redcap} field (string or int)
        Return: void

        Example:
        >>> am = ArticleManager()
        >>> am.entry
        {}
        >>> am.assign('clear_hypothesis',1)
        >>> am.entry
        {'clear_hypothesis':1}
        >>> am.assign('funders','NIH')
        >>> am.entry
        {'clear_hypothesis':1,'funders':'NIH'}
        >>> am.assign('funders','the lottery')
        >>> am.entry
        {'clear_hypothesis':1,'funders':'NIH,the lottery'}
        """
        if (redcap in self.entry):  # if assign has already been called for {redcap}
            # tack on new value to the end
            self.entry[redcap] += "," + str(value)
        else:
            self.entry[redcap] = str(value)

    def check(self, variable, value, info, redcap, display=0):
        """
        Check if the redcap field {variable} is truly equal to {display} based on {info}
        Args:
                variable 		-- user friendly interpretation of the variable being checked (often the redcap field label) (string)
                value 			-- value to be entered into redcap (string or int (for fields which allow only a specific set of options))
                info 			-- sentence or relevant text (sample from the article) for determining the value of {variable} (string)
                redcap 			-- redcap codebook key (string)
        KeywordArgs:
                display			-- user friendly interpretation of the redcap fields value
        Return: void

        Example:
        >>> am = ArticleManager(run_style=0)
        >>> am.entry
        {}
        >>> am.check("Operating System Used For Analyses",'Windows',"Statistical Analyses were performed using SAS on a Windows 10 machine",'analysis_os')
        I think 'Operating System Used For Analyses' should be: 'Windows' based on:
        Statistical Analyses were performed using SAS on a Windows 10 machine
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> am.entry
        {'analysis_os': 'Windows'}

        >>> am = ArticleManager(run_style=0)
        >>> am.entry
        {}
        >>> am.check("Operating System Used For Analyses",'Windows',"Statistical Analyses were performed using SAS on a computer using an unknown operating system",'analysis_os')
        I think 'Operating System Used For Analyses' should be: 'Windows' based on:
        Statistical Analyses were performed using SAS on a computer using an unknown operating system
        Is this correct? (if no, type no and press enter; otherwise, press enter): no
        Do you know the correct value? (if yes, type yes and press enter; otherwise, press enter):
        >>> am.entry
        {}
        >>> am.check("Operating System Used For Analyses",'Windows',"Statistical Analyses were performed using SAS on a Windows 10 machine",'analysis_os')
        I think 'Operating System Used For Analyses' should be: 'Windows' based on:
        Statistical Analyses were performed using SAS on a Windows 10 machine
        Is this correct? (if no, type no and press enter; otherwise, press enter): no
        Do you know the correct value? (if yes, type yes and press enter; otherwise, press enter): yes
        Type the correct value for 'Operating System Used For Analyses': Macintosh
        >>> am.entry
        {'analysis_os': 'Macintosh'}

        >>> am.check("Whos reviewing the article?",6,'user of computer','reviewer',display='Christian Lukas')
        I think 'Whos reviewing the article?' should be: 'Christian Lukas' based on:
        user of computer
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> am.entry
        {'reviewer': '6', 'analysis_os': 'Macintosh'}

        >>> am = ArticleManager(run_style=1) 		#am = ArticleManager() would return the same result
        >>> am.check("Whos reviewing the article?",6,'user of computer','reviewer',display='Christian Lukas')
        >>> am.entry
        {'reviewer': '6'}
        """
        if (not display):  # if not display keyword argument provided
            display = value
        correct = self.check_boolean(
            variable, value, info, redcap, display=display)
        if (correct == 1):
            return
        if (self.ask_question("Do you know the correct value?")):
            choices = self.get_choices(redcap)
            if (choices == -1):
                overwrite_val = input(
                    "Type the correct value for '{}': ".format(variable))
                overwrite_val.strip()
                self.user_choice = overwrite_val
                self.assign(redcap, overwrite_val)
                print("\n\n")
            else:
                self.generate_chooser(variable, choices, info=info)
            # with open("record.log",'a') as f:
            #	f.write("\t\t{}\n".format(self.user_choice))
            return self.assign(redcap, self.user_choice)
        else:
            return

    def check_boolean(self, variable, value, info, redcap, display=''):
        """
        Check if the redcap field {variable} is truly equal to {display} based on {info}
        Args:
                variable 		-- user friendly interpretation of the variable being checked (often the redcap field label) (string)
                value 			-- value to be entered into redcap (string or int (for fields which allow only a specific set of options))
                info 			-- sentence or relevant text (sample from the article) for determining the value of {variable}
                redcap 			-- redcap codebook key (string)
        KeywordArgs:
                display			-- user friendly interpretation of the redcap fields value
        Return:
                        1 if {value} for {variable} is correct
                        0 if {value} for {variable} is not correct

        Example:
        >>> am = ArticleManager(run_style=0)
        >>> am.entry
        {}
        >>> am.check_boolean("Inclusion Exclusion Criteria Stated",1,'Patients who were aliens were excluded',"inclusion_and_exclusion_stated",display='yes')
        I think 'Inclusion Exclusion Criteria Stated' should be: 'yes' based on:
        Patients who were aliens were excluded
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        1
        >>> am.entry
        {'inclusion_and_exclusion_stated': '1'}

        >>> am = ArticleManager(run_style=0)
        >>> am.entry
        {}
        >>> am.check_boolean("Query Method Stated",1,'This information is irrelevant to query; I like dogs',"query_method_stated",display='yes')
        I think 'Query Method Stated' should be: 'yes' based on:
        This information is irrelevant to query; I like dogs
        Is this correct? (if no, type no and press enter; otherwise, press enter): no
        0
        >>> am.entry
        {}

        >>> am = ArticleManager(run_style=0)
        >>> am.entry
        {}
        >>> am.check_boolean("Inclusion Exclusion Criteria Stated",1,'Patients who were aliens were excluded',"inclusion_and_exclusion_stated",display='yes')
        1
        >>> am.entry
        {'inclusion_and_exclusion_stated': '1'}
        """
        if self.run_style == 1:
            self.assign(redcap, value)
            return 1

        if (not display):  # if not display keyword argument provided
            display = value
        print("I think '{}' should be: '{}' based on:\n{}".format(
            variable, display, info))

        correct = input(
            "Is this correct? (if no, type no and press enter; otherwise, press enter): ")
        print("\n\n")
        if re.search(r'no', correct, re.I):
            print("\n\n")
            return 0
        else:
            print("\n\n")
            self.assign(redcap, value)
            return 1

    def get_articles_xml(self, file, identifier, search_ids):
        """
        Read xml file in the format of 'pmc_result.xml'
        Args:
                file 		-- directory where file is located (string)
                identifier 	-- type of article_id (doi, pmc, pmid) (string)
                search_ids	-- article ids to return beautifulsoup of (list of strings)
        Return: generator of beautiful soup objects for the list of articles in {search_ids}

        Example:
        >>> am = ArticleManager()
        >>> ge = am.get_articles_xml("/Users/christian/Desktop/cbmi/reproduce/python/articles/sub_pmc_result.xml","pmid",['23449283','26395541'])
        >>> next(ge)
        (<article article-type="research-article" xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink">
        <?properties open_access?>
        <front>
        <journal-meta>
        <journal-id journal-id-type="nlm-ta">Prev Chronic Dis</journal-id>
        <journal-id journal-id-type="iso-abbrev">Prev Chronic Dis</journal-id>
        <journal-id journal-id-type="publisher-id">PCD</journal-id>
        <journal-title-group>
        ...
        </article>, '23449283')
        >>> bs = next(ge)[0]
        >>> bs.surname
        <surname>Eysenbach</surname>
        #See BeautifulSoup for more information
        """
        if (type(search_ids) is not list):
            raise TypeError(
                "get_articles_xml method called on invalid type. search_ids must be a list but is type: {}".format(type(search_ids)))
        search_ids = set(map(str, search_ids))

        with open(file, 'r') as x:
            bs = BeautifulSoup(x.read(), "lxml")

        for ass in bs.find_all("article"):
            try:
                article_id = ass.find(
                    'article-id', {'pub-id-type': identifier}).text
                # ass.find('article-id',{'pub-id-type':'pmc'}).text
            except AttributeError as e:
                # article doesnt have identifier provided
                continue
            if (article_id in search_ids):
                search_ids.remove(article_id)
                if (ass.find(text=re.compile("The publisher of this article does not allow downloading of the full text in XML form"))):
                    # article isnt open access :(
                    continue
                # found open access article
                yield (ass, article_id)
                if (len(search_ids == 0)):
                    return  # all articles found
        if (len(search_ids) > 0):
            print("some articles were not found:\n{}".format(search_ids))
            return  # articles not found
        return  # all articles found

    def enter_redcap(self, entry, record_id):
        """
        Enter entry into redcap
        Args:
                entry 		-- redcap entry (dictionary where keys are redcap codebook keys)
                record_id 	-- redcap record id (string or int)
        KeywordArgs: record_id (string or int), default to next available record_id autoincrememnt
        Return: dictionary detailing:
                how many entrie were edited if upload was successful
                what caused the error and why if upload was unsuccessful

        Example:
        >>> am = ArticleManager(run_style=0)
        >>> am.enter_redcap({"author_fn":"kurt","author_ln":"vonnegut"},40)
        {'status': 'success', 'count': 1}
        >>> am = ArticleManager(run_style=1)
        >>> am.enter_redcap({"author_fn":"george","author_ln":"lucas"},40)
        {'status': 'success', 'count': 1}

        When errors occur, will give the user the option to edit the field or retry entry without the erroring field
        >>> am = ArticleManager(run_style=0)
        >>> am.enter_redcap({'author_fn':'HeithLedger','author_ln':'special characters $#_! and spaces are not allowed'},40)
        redcap entry failed on field: 'author_ln'
        because: 'The value you provided could not be validated because it does not follow the expected format. Please try again.'
        Would you like to edit field: 'author_ln' (if yes, type yes and press enter; otherwise, press enter):
        retrying entry without that field
        {'status': 'success', 'count': 1}

        >>> am.enter_redcap({'author_fn':'HeithLedger','author_ln':'special characters $#_! and spaces are not allowed'},40)
        redcap entry failed on field: 'author_ln'
        because: 'The value you provided could not be validated because it does not follow the expected format. Please try again.'
        Would you like to edit field: 'author_ln' (if yes, type yes and press enter; otherwise, press enter): yes
        Please enter the value: ValidLastName
        ValidLastName
        {'status': 'success', 'count': 1}

        If running independently, will automatically retry entry without the erroring field
        >>> am = ArticleManager(run_style=1)
        >>> am.enter_redcap({'author_fn':'john doe','author_ln':'halpert'},40)
        redcap entry failed on field: 'author_fn'
        because: 'The value you provided could not be validated because it does not follow the expected format. Please try again.'
        retrying entry without that field
        {'status': 'success', 'count': 1}

        or note if no fields remain
        >>> am.enter_redcap({'author_fn':'only field in this entry'},40)
        redcap entry failed on field: 'author_fn'
        because: 'The value you provided could not be validated because it does not follow the expected format. Please try again.'
        retrying entry without that field
        {'status': 'fail', 'count': 0}

        Invalid redcap keys throw a different error and always fail
        >>> am.enter_redcap({'most_magical_place_on_earth':'doesnt matter, not a redcap field','analysis_sw':'STATA'},40)
        redcap entry failed because an invalid redcap field was present in entry (key that is not a redcap codebook key)
        {'status': 'fail', 'count': 0}
        """
        # entry['record_id'] = record_id                  #leave out for now so
        # I dont destroy redcap...
        entry['record_id'] = '9b7057f5f8894c9c'

        # see redcap api documentation --
        # https://redcap.wustl.edu/redcap/srvrs/prod_v3_1_0_001/redcap/api/help/
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
        if (re.search(b'error', redcap_return)):
            if (re.search(b'There were errors with your request', redcap_return)):
                print(
                    "redcap entry failed because an invalid redcap field was present in entry (key that is not a redcap codebook key)")
                self.redcap_return = {"status": "fail", "count": 0}
                return self.redcap_return
            splitreturn = list(map(bytes.decode, redcap_return.split(b'\\"')))
            fails = {"status": "error", "record_id": splitreturn[1], "redcap_field": splitreturn[
                3], "value": splitreturn[5], "reason": splitreturn[7]}
            print("redcap entry failed on field: '{}'\nbecause: '{}'".format(
                fails['redcap_field'], fails['reason']))

            self.record_error(method='enter_redcap', object_caller='`ArticleManager`', record_id=splitreturn[
                              1], field=splitreturn[3], value=splitreturn[5], notes=splitreturn[7])

            # note if it was resolved
            if (self.ask("Would you like to edit field: '{}'".format(fails['redcap_field']), fails['redcap_field'])):
                entry[fails['redcap_field']] = self.user_choice
                return self.enter_redcap(entry, record_id)
            else:
                print("retrying entry without that field")
                del entry[fails['redcap_field']]
                # so that entry is empty if no other fields
                del entry['record_id']
                if (not entry):
                    # entry is empty, no fields left to attempt to upload to
                    # redcap
                    self.redcap_return = {"status": "fail", "count": 0}
                    return self.redcap_return
                return self.enter_redcap(entry, record_id)
        self.redcap_return = {"status": "success", "count": 1}
        return self.redcap_return
