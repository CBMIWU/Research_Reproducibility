#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ArticleManager import ArticleManager
from DatabaseManager import DatabaseManager
from bs4 import BeautifulSoup
from pprint import pprint
from stemming.porter2 import stem
import nltk
import os
import pwd
import re
import requests
import sys

class ArticleExtractor(ArticleManager):

    """
    Extract study information from the article text

    Depends on:
            os				-- https://docs.python.org/3/library/os.html
            sys				-- https://docs.python.org/3/library/sys.html
            re				-- https://docs.python.org/3/library/re.html
            nltk 			-- http://www.nltk.org/
            requests 		-- http://docs.python-requests.org/en/master/
            pprint 			-- https://docs.python.org/3/library/pprint.html
            stemming 		-- https://pypi.python.org/pypi/stemming/1.0
            beautiful soup	-- https://www.crummy.com/software/BeautifulSoup/bs4/doc/
    Functions from inherited from ArticleManager:
            get_choices
            check
            check_boolean
            ask
            ask_without_choices
    See ArticleManager for additional documentation
    """

    def __init__(self, **kwargs):
        # pass run_style and metadata keyword argument on to ArticleManager
        # constructor (if provided)
        kwargs.pop("bs", None)
        super(ArticleExtractor, self).__init__(**kwargs)

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
            raise TypeError("clean_entry called on: {0} \ninvalid type: {1}".format(
                self.entry, type(self.entry)))
            return self.entry
        for (k, v) in self.entry.items():
            copy = v
            try:
                val = copy.split(',')
                val = list(map(str.strip, val))
                val = set(val)
                val = ', '.join(val)
                self.entry[k] = val
            except AttributeError:
                # copy.split(',') failed because val was not a string
                # v was already clean
                pass
        return self.entry

    def get_reviewer(self):
        """
        Get the name of the person reviewing the article
        Use computer's username to take a guess, or ask for input if cant determine a guess
        Return: Void

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae.get_reviewer()
        I think 'Whos reviewing the article?' should be 'Elvis' based on: 'user of computer'
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'reviewer':'Elvis'}

        If a guess cant be determined, ask user whos reviewing the article
        >>> ae.get_reviewer()
        #popup window appears

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae.get_reviewer()
        >>> ae.entry
        {'reviewer':'Elvis'}
        """
        username = ""
        try:
            username = os.getlogin()
        except FileNotFoundError:
            username = pwd.getpwuid(os.getuid())[0]  # username of the person using the computer
        users = self.get_choices("reviewer")
        for user in users:
            if (re.search(username, user, re.I)):
                self.check("Whos reviewing the article?", users[
                           user], "user of computer", "reviewer", display=user)
                return
        self.ask("Whos reviewing the article?", "reviewer")

    def chunker(self, sentence):
        """
        Chunk a sentence
        Args: sentence -- (string)
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
            print("chunker called on: '{}' \n{} is type: {} but must be a string or bytes-like object".format(
                sentence, sentence, type(sentence)))
            print("retrying with cast to string")
            return self.chunker(str(sentence))

    def get_clinical_domain(self, key_words):
        """
        Get the clinical domain of the article
        Args: key_words 	-- words to search against the clinical domain choices (list of strings)
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
        stopwords = nltk.corpus.stopwords.words(
            'english') + ['health', 'disease', 'medicine', 'medical', 'sciences', 'medicine', 'international']
        key_words = [stem(word.lower().strip())
                     for word in key_words if word.lower() not in stopwords]
        domains = self.get_choices("clinical_domain")
        for word in key_words:
            for domain in domains:
                if (re.search(re.escape(word), domain, re.I)):
                    return domain
        return 0

    def _get_hypotheses(self, text):
        """
        Determine whether the study in the article was 'Hypothesis Driven or Hypothesis Generating'
                and if they stated the null and alternative hypotheses
                assign the value to entry
        Args: text -- text from the article to be extracted (string)
        Return: void

        Article that were 'hypothesis driven' usually presented their hypotheses in the format:
                "we hypothesized ..."

        Example:
        >>> ae = ArticleExtractor()
        >>> ae._get_hypotheses("We hypothesized that patients undergoing extended BEV therapy could have altered patterns of recurrence and symptoms of recurrence due to its novel mechanism of action")
        >>> ae.entry
        {'hypothesis_gen_or_driv':1}
        #from article: 23632207.pdf (doi: 10.1016/j.ygyno.2013.04.055)
        >>> ae.entry
        {'hypothesis_gen_or_driv':1}
        >>> ae._get_hypotheses("We randomly collected data with no direction *hand slap")
        >>> ae.entry
        {'hypothesis_gen_or_driv':2}

        """
        for each_sent in nltk.sent_tokenize(text):
            if (re.search(r'we.*?hypothes', each_sent, re.I)):
                self.check("Hypothesis Driven or Hypothesis Generating",
                           1, each_sent, "hypothesis_gen_or_driv", display="driven")
                if ("hypothesis_gen_or_driv" in self.entry):
                    # we didnt encounter any articles that stated null and
                    # alternate hypotheses. Here's how we might ask
                    self.generate_chooser("Does the publication state null and alternative hypotheses?", self.get_choices(
                        "clear_hypothesis"), info=each_sent)
                    if (self.user_choice != -1):
                        self.entry['clear_hypothesis'] = self.user_choice
                    return
        self.entry['hypothesis_gen_or_driv'] = 2
        return

    def _get_funding(self, text):
        """
        Get funding and grant information for the study in an article
        Args: text -- text from the article to be extracted (string)
        Return: void

        Articles usually presented their funding in the format:
                "This study was funded in part by ... (grant #NIH8982)"
                "This study was funded by a grant from ..."

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_funding("Our study was funded by the NIH (grant id: #3234Gj8)")
        I think 'Grant ID' should be: '3234Gj8' based on:
        Our study was funded by the NIH (grant id: #3234Gj8)
        Is this correct? (if no, type no and press enter; otherwise, press enter):

        I think 'Funders' should be: 'the NIH' based on:
        Our study was funded by the NIH (grant id: #3234Gj8)
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'funders': 'the NIH', 'grant_ids': '3234Gj8'}

        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_funding("Our study was not funded by the NIH, but rather my mom")
        I think 'Funders' should be: 'the NIH' based on:
        Our study was not funded by the NIH, but rather my mom
        Is this correct? (if no, type no and press enter; otherwise, press enter): no
        Do you know the correct value? (if yes, type yes and press enter; otherwise, press enter): yes
        Type the correct value for 'Funders': researchers mom
        >>> ae.entry
        {'funders': 'researchers mom'}


        >>> ae = ArticleExtractor(run_style=1)
        >>> ae._get_funding("Our study was funded by the NIH (grant id: #3234Gj8)")
        >>> ae.entry
        {'funders': 'the NIH', 'grant_ids': '3234Gj8'}

        >>> ae._get_funding("The research was funded by Wayne Enterprises.")
        >>> ae.entry
        {'funders': 'Wayne Enterprises'}
        """
        for each_sent in nltk.sent_tokenize(text):
            if (re.search(r'funded.*?by', each_sent, re.I | re.S)):
                search = re.search(
                    r"grant.*?(\w*\d[\w\d/-]*)", each_sent, re.I)
                if (search):
                    self.check(
                        "Grant ID", search.group(1).strip(), each_sent, "grant_ids")
                search = re.search(
                    r'grant.*?from (.*?)[^\w\s-]', each_sent, re.I | re.S)
                if (search):
                    self.check(
                        "Funders", search.group(1).strip(), each_sent, "funders")
                else:
                    search = re.search(
                        r'funded.*?by (.*?)[^\w\s-]', each_sent, re.I | re.S)
                    self.check(
                        "Funders", search.group(1).strip(), each_sent, "funders")

    def _get_inex_criteria(self, text):
        """
        Determine if the study in an article documented their inclusion / exclusion criteria
        Args: text -- text from the article to be extracted (string)
        Return: void

        Search for:
                "... were included", "... were excluded", "inclusion", "exclusion"
                indicator phrases

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_inex_criteria("Aliens and other reptiles were excluded from our study")
        I think 'Inclusion Exclusion Criteria Stated' should be: 'yes' based on:
        Aliens and other reptiles were excluded from our study
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'inclusion_and_exclusion_stated': '1', 'inclusion_exclu_location___3': 1}
        #location___3 is body of article

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae._get_inex_criteria("Aliens and other reptiles were excluded from our study")
        >>> ae.entry
        {'inclusion_and_exclusion_stated': '1', 'inclusion_exclu_location___3': 1}

        """
        for each_sent in nltk.sent_tokenize(text):
            copy = each_sent
            if(re.search(r'were\W*includ', each_sent, re.I) or re.search(r'were\W*exclud', each_sent, re.I) or
                    re.search(r'inclus', each_sent, re.I) or (re.search(r'exclus', each_sent, re.I) and not re.search(r'exclusively', each_sent, re.I))):
                if ("inclusion_and_exclusion_stated" not in self.entry):
                    self.check_boolean("Inclusion Exclusion Criteria Stated", 1,
                                       each_sent, "inclusion_and_exclusion_stated", display='yes')
                if ("inclusion_and_exclusion_stated" in self.entry):
                    self.entry['inclusion_exclu_location___3'] = 1
                    self.check_ontol(each_sent)
                    return

    def check_ontol(self, info):
        """
        Ask user if any inclusion / exclusion criteria are presenting relative to standard ontologies
                (method is called when a sentence is found indicating that inclusion / exclusion criteria was stated)
        Args: info -- sentence that indicated inclusion / exclusion criteria was stated (string)
        Return: void

        #TODO, this needs to be expanded to check for standard ontologies that occur outside of the sentence which
                indicated that inclusion / exclusion criteria were stated
        This is difficult because a variety of names exist (ICD-9, ICD9, 'International Classification of Diseases')
                and it is difficult to discern which category ('Procedure', 'Diagnosis', 'Medication', 'Laboratory')
                the ontology belongs to
        For now, prompts user whenever 'inclusion_and_exclusion_stated' set to True

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae.check_ontol("Patients suffering from sleep apnea (ICD-9 327.23) were excluded")
        based on:
        Patients suffering from sleep apnea (ICD-9 327.23) were excluded
        Are any standard ontologies stated (such as CPT, ICD9, etc)? (if yes, type yes and press enter; otherwise, press enter): yes
        #user interacts with GUI
        >>> ae.entry
        {'ontol_and_vocab_stated': 1, 'diag_vocabulary': 1}
        """
        if ("ontol_and_vocab_stated" in self.entry):
            return
        if (not self.run_style):
            print("based on:")
            print(info)
        if (self.ask_question("Are any standard ontologies stated (such as CPT, ICD9, etc)?")):
            self.entry['ontol_and_vocab_stated'] = 1
            c1 = {
                "Procedure": 1,
                "Diagnosis": 2,
                "Medication": 3,
                "Laboratory": 4
            }
            c2 = {
                "Procedure": "proc_vocabulary",
                "Diagnosis": "diag_vocabulary",
                "Medication": "med_vocab",
                "Laboratory": "lab_vocab"
            }
            c3 = dict((v, k) for k, v in c1.items())
            self.generate_chooser(
                "What categories are the ontologies a part of?", c1)
            if (self.user_choice != -1):
                self.ask("What ontologies are given for the category {}?".format(
                    c3[self.user_choice]), c2[c3[self.user_choice]])

    def _get_databases(self, text):
        """
        Determine if article cited databases used in the study
        Args: text -- text from the article to be extracted (string)
        Return: void

        If a sentence has the word 'database', guesses that the database is the largest chunk (see chunker method for more information)
                Sometimes correct, but probaby the best default

        #TODO, if there's more than one database

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_databases("The study database was obtained retrospectively from the Swedish National Stroke Register, Riksstroke and comprised all consecutive patients diagnosed with acute ischemic stroke or intracerebral hemorrhage admitted to Danderyd Hospital within 7 days of symptom onset be- tween January 1, 2005, and January 1, 2006 (n 5 725)")
        #from article: {doi: 10.1016/j.jstrokecerebrovasdis.2015.06.043, pmid: 26236002}
        I think 'Database Name' should be: 'National Stroke Register , Riksstroke' based on:
        The study database was obtained retrospectively from the Swedish National Stroke Register, Riksstroke and comprised all consecutive patients diagnosed with acute ischemic stroke or intracerebral hemorrhage admitted to Danderyd Hospital within 7 days of symptom onset be- tween January 1, 2005, and January 1, 2006 (n 5 725)
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'db_citation_1': 'National Stroke Register , Riksstroke', 'state_data_sources': 1}

        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_databases("This is a really short article")
        >>> ae.entry
        {'state_data_sources':0}

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae._get_databases("The study database was obtained retrospectively from the Swedish National Stroke Register, Riksstroke and comprised all consecutive patients diagnosed with acute ischemic stroke or intracerebral hemorrhage admitted to Danderyd Hospital within 7 days of symptom onset be- tween January 1, 2005, and January 1, 2006 (n 5 725)")
        #from article: {doi: 10.1016/j.jstrokecerebrovasdis.2015.06.043, pmid: 26236002}
        >>> ae.entry
        {'db_citation_1': 'National Stroke Register , Riksstroke', 'state_data_sources': 1}
        """

        for each_sent in nltk.sent_tokenize(text):
            if (re.search(r'database', each_sent, re.I)):
                tree = self.chunker(each_sent)
                sts = []
                try:
                    for st in tree.subtrees(lambda tree: tree.height() == 3):
                        for st2 in st.subtrees(lambda tree: tree.height() == 2):
                            sts.append([str(tup[0]) for tup in st2.leaves()])
                    if (len(sts) > 0):
                        longest_chunk = max(sts, key=len)
                        self.check(
                            "Database Name", ' '.join(longest_chunk), each_sent, "db_citation_1")
                    if ('db_citation_1' in self.entry):
                        self.entry['state_data_sources'] = 1
                        self.entry['state_database_where___4'] = 1
                        return
                except AttributeError as e:
                    # chunker run on invalid data type, didnt return a tree
                    pass
        self.entry['state_data_sources'] = 0

    def _get_query(self, text):
        """
        Determine method used for extracting data
        Args: text -- text from the article to be extracted (string)
        Return: void

        Look for word indicators:
                'abstracted', 'manually', 'query',
                'records' and 'review'

        Few articles documented query methods. Further review should be conducted

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_query("Data were manually abstracted")
        I think 'Query Method Stated' should be: 'yes' based on:
        Data were manually abstracted
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'query_method_stated': '1', 'query_method_location___4': 1}

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae._get_query("Data were manually abstracted")
        >>> ae.entry
        {'query_method_stated': '1', 'query_method_location___4': 1}
        """
        for each_sent in nltk.sent_tokenize(text):
            if (re.search(r'abstracted', each_sent, re.I) or
                    re.search(r'manual', each_sent, re.I) or
                    re.search(r'query', each_sent, re.I) or
                    (re.search('records', each_sent, re.I) and re.search('review', each_sent, re.I))):
                self.check_boolean(
                    "Query Method Stated", 1, each_sent, "query_method_stated", display='yes')
            if ('query_method_stated' in self.entry):
                # query method given in body of article
                self.entry['query_method_location___4'] = 1
                return
            else:
                self.entry['query_method_stated'] = 0
                return
        self.entry['query_method_stated'] = 0

    def _get_nlp(self, text):
        """
        Check if study used natural language Processing
        Args: text -- text from the article to be extracted (string)
        Return: void

        Look for word indicators:
                'language proc', 'nlp'
        Few articles used natural language processing. Further review should be conducted

        Ask user if article states source of text from which data were mined
        """
        for each_sent in nltk.sent_tokenize(text):
            if (re.search(r'language\spro', each_sent, re.I) or re.search(r'\snlp\s', each_sent, re.I)):
                self.check_boolean(
                    "Research Involves Natural Language Processing", 1, each_sent, "text_nlp_yn", display='yes')
                if ("text_nlp_yn" in self.entry):
                    if (self.ask_without_choices("Does the publication state source of the text from which data were mined? (ex: emergency department summary, operative notes, etc)\n", "Enter the source of text: ", "text_mine_source")):
                        if (re.search(r'appendix', each_sent, re.I)):
                            if (self.check_boolean("Manuscript shares a pre-processed sample text source in", 9, each_sent, "nlp_source_shared_loc", display="appendix")):
                                self.assign("text_mining_preprocess", 1)
                        elif (re.search(r'\Wgit', each_sent, re.I)):
                            if (self.check_boolean("Manuscript shares a pre-processed sample text source in", 5, each_sent, "nlp_source_shared_loc", display="GitHub")):
                                self.assign("text_mining_preprocess", 1)
                        if ("text_mining_preprocess" not in self.entry):
                            if (self.ask_question("Do they share a pre-processed sample of the text source?")):
                                self.assign("text_mining_preprocess", 1)
                                self.ask(
                                    "Where is the sample shared?", "nlp_source_shared_loc")
                        if (self.ask_without_choices("Does the publication state software used for text mining?", "Enter softwares used: ", "nlp_software")):
                            self.ask(
                                "Is the software open or proprietary?", "nlp_software_open")
                        return

    def _get_analysis(self, text):
        return  # TODO, run machine learning algorithm
        for each_sent in nltk.sent_tokenize(text):
            if (re.search(r'statistical analys[ie]s', each_sent, re.I) or re.search(r'data analys[ie]s', each_sent, re.I)):
                if (self.check_boolean("Publications States Analysis Methodology And Process", 1, each_sent, "analysis_processes_clear", display='yes')):
                    self.entry['data_analysis_doc_loc'] = 4
                    return

    def _get_stats(self, text):
        """
        Determine software, version, and operating system used for statistical Analyses
        Args: text -- text from the article to be extracted (string)
        Return: void

        Articles often presented their analyses in the format:
                "analyses were performed on ..."
                "analysis was performed using ..."
        Since a few domains cover almost all cases, search for common software (SAS, SPSS, etc)

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_stats("Analyses were performed using SAS (version 9.1)")
        I think 'Analysis Software' should be: 'SAS' based on:
        Analyses were performed using SAS (version 9.1)
        Is this correct? (if no, type no and press enter; otherwise, press enter):

        I think 'Analysis Software Version' should be: '9.1' based on:
        Analyses were performed using SAS (version 9.1)
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'analysis_sw': 'SAS','analysis_sw_version': '9.1'}

        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_stats("Analyses were performed using SAS (version 9.1)")
        >>> ae.entry
        {'analysis_sw': 'SAS','analysis_sw_version': '9.1'}

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae._get_stats("Analyses were performed using GraphPad for Windows")
        {'analysis_sw': 'GraphPad', 'software_analysis_code': 1, 'analysis_os': 'Windows'}
        """
        self.check_standards(text)
        if ("analysis_sw" in self.entry):
            self.entry['software_analysis_code'] = 1
            return

        for each_sent in nltk.sent_tokenize(text):
            search = re.search(
                r'analys[ie]s (were)?(was)? performed\s+\w+\W+(.*?)\s', each_sent, re.I)
            if (search):
                self.check("Analyses Software", search.group(
                    3).strip(), each_sent, "analysis_sw")
            else:
                search = re.search(r'analys', each_sent, re.I) and re.search(
                    r'were\s\w*\susing\s(.*?)\s', each_sent, re.I)
                if (search):
                    self.check(
                        "Analyses Software", search.group(1), each_sent, "analysis_sw")
            if ("analysis_sw" in self.entry):
                self.entry['software_analysis_code'] = 1

                search = re.search(
                    self.entry['analysis_sw'] + r'.*?(\d[\d\.]*\d)', each_sent, re.I | re.S)
                if (search):
                    self.check("Analysis Software Version", search.group(
                        1), each_sent, "analysis_sw_version")
                self.check_operating_system(each_sent)
                return
        self.entry['software_analysis_code'] = 0

    def check_standards(self, text):
        """
        Check if 'STATA','SAS','SPSS','R' statistical softwares used in analyses
        Method is called by _get_stats method (user doesnt need to execute both)
        Args: text -- text from the article to be extracted (string)
        Return: void

        Example:
        >>> ae = ArticleExtractor(run_style=1)
        >>> ae.check_standards('SAS and SPSS were used in this study')
        I think 'Analysis Software' should be: 'SAS' based on:
        SAS and SPSS were used in this study
        Is this correct? (if no, type no and press enter; otherwise, press enter):

        I think 'Analysis Software' should be: 'SPSS' based on:
        SAS and SPSS were used in this study
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'analysis_sw':'SAS,SPSS',}
        """
        stands = ["STATA", "SAS", "SPSS"]
        for each_sent in nltk.sent_tokenize(text):
            for stand in stands:
                if re.search(stand, each_sent):
                    self.check(
                        "Analysis Software", stand, each_sent, "analysis_sw")
                    if ("analysis_sw" in self.entry and stand in self.entry['analysis_sw']):
                        # software is proprietary
                        self.entry['analysis_software_open___1'] = 1
                        search = re.search(
                            stand + r'.*?(\d[\d\.]*\d)', each_sent)
                        if (search):
                            self.check("Analysis Software Version", search.group(
                                1), each_sent, "analysis_sw_version")
                        self.check_operating_system(each_sent)
            if (re.search(r'analys', each_sent, re.I) and re.search(r'\sR\s', each_sent)):
                self.check("Analysis Software", "R", each_sent, "analysis_sw")
                if ("analysis_sw" in self.entry and "R" in self.entry['analysis_sw']):
                    search = re.search(r'\sR\s.*?(\d[\d\.]*\d)', each_sent)
                    if (search):
                        self.check("Analysis Software Version", search.group(
                            1), each_sent, "analysis_sw_version")
                    # software is open-source
                    self.entry['analysis_software_open___2'] = 1

    def check_operating_system(self, sentence):
        """
        Determine if article records what operating system was used for statistical analyses
        Called by _get_stats and check_standards methods when an analysis software is found
        Args: sentence -- sentence that indicated what analysis software was used in analyses (string)
        Return: void

        Searches for only the most common operating systems: 'Windows', 'Mac', 'Linux', 'Unix'
        """
        for os in ['Windows', 'Mac', 'Linux', 'Unix']:
            if (re.search(os, sentence, re.I)):
                self.check_boolean(
                    "Operating System Used For Analyses", os, text, "analysis_os")
                if ("analysis_os" in self.entry):
                    return

    def _get_limitations(self, text):
        """
        Determine if the article documented limitations of the study
        Args: text -- text from the article to be extracted (string)
        Return: void

        Articles often presented their limitations in the format:
                "There were several limitations to the study"
                "The study was limited by ..."
                "Our study had several shortcomings"

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_limitations("This study faced several limitations")
        I think 'Publication Documents Limitations Of The Study' should be: 'yes' based on:
        This study faced several limitations
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'limitations_where___7': '1'}

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae._get_limitations("This study faced several limitations")
        >>> ae.entry
        {'limitations_where___7': '1'}
        """
        for each_sent in nltk.sent_tokenize(text):
            if (re.search(r'shortcomings', each_sent, re.I) or re.search(r'limitation', each_sent, re.I) or re.search(r'(was)?(is)? limited', each_sent, re.I)):
                self.check_boolean("Publication Documents Limitations Of The Study",
                                   1, each_sent, "limitations_where___7", display='yes')
                if ("limitations_where___7" in self.entry):
                    return

    def _get_institution(self, affiliation):
        """
        Determine the institution of the primary author of the article
        Args: affiliation -- affiliation of the first author extracted from xml page of the article's corresponding ncbi page
        Return: void

        The affiliation tag of the ncbi site follows this format:
                <Affiliation>John Jay College of Criminal Justice, The City University of New York, Department of Criminal Justice, 524 West 59th Street, New York, NY 10019, United States. Electronic address: mnatarajan@jjay.cuny.edu.</Affiliation>
                #from article:
                        doi: 10.1016/j.burns.2013.12.002
                        pubmed code: 24433938
        The institution section often has one of the keywords:
                'hospital','university','school','college','institute'
        If none of the indicator words is found, guess the second section of the affiliation tag (sections broken by commas)

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae._get_institution("John Jay College of Criminal Justice, The City University of New York, Department of Criminal Justice, 524 West 59th Street, New York, NY 10019, United States. Electronic address: mnatarajan@jjay.cuny.edu.")
        I think 'Institution' should be: 'John Jay College of Criminal Justice' based on:
        affiliation: 'John Jay College of Criminal Justice, The City University of New York, Department of Criminal Justice, 524 West 59th Street, New York, NY 10019, United States. Electronic address: mnatarajan@jjay.cuny.edu.'
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'institution_corr_author': 'John Jay College of Criminal Justice'}

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae._get_institution("John Jay College of Criminal Justice, The City University of New York, Department of Criminal Justice, 524 West 59th Street, New York, NY 10019, United States. Electronic address: mnatarajan@jjay.cuny.edu.")
        >>> ae.entry
        {'institution_corr_author': 'John Jay College of Criminal Justice'}
        """
        af_from_xml = affiliation.split(", ")

        for option in af_from_xml:  # could tweak slightly
            if (re.search(r'hospital', option, re.I) or re.search(r'university', option, re.I) or re.search(r'school', option, re.I) or re.search(r'college', option, re.I) or re.search(r'institute', option, re.I)):
                self.check("Institution", option, "affiliation: '{}'".format(
                    affiliation), "institution_corr_author")
            if ("institution_corr_author" in self.entry):
                return
        try:
            self.check("Institution", af_from_xml[1], "affiliation: '{}'".format(
                affiliation), "institution_corr_author")
        except IndexError:
            pass

    def get_clinical_domain_from_xml(self, institution):
        """
        Determine the clinical domain of the article (oncology, Neurology, etc)
        Args: affiliation -- affiliation of the first author extracted from xml page of the article's corresponding ncbi page
        Return: void

        The affiliation tag of the ncbi site follows this format:
                <Affiliation>Department of Neurology, Aizawa Hospital, Matsumoto, Japan. Electronic address: aidr214@ai-hosp.or.jp.</Affiliation>
        #from article:
                        doi: 10.1016/j.clineuro.2015.10.004
                        pubmed code: 26513432

        Compare against possible clinical domain categorites:
                department
                division
                journal title
                article title

        Example:
        >>> ae = ArticleExtractor(run_style=0)
        >>> ae.get_clinical_domain_from_xml("Department of Neurology, Aizawa Hospital, Matsumoto, Japan. Electronic address: aidr214@ai-hosp.or.jp.")
        I think 'Clinical Domain' should be: 'Neurology' based on:
        Department: Neurology
        Is this correct? (if no, type no and press enter; otherwise, press enter):
        >>> ae.entry
        {'clinical_domain': '23'}

        >>> ae = ArticleExtractor(run_style=1)
        >>> ae.get_clinical_domain_from_xml("Department of Neurology, Aizawa Hospital, Matsumoto, Japan. Electronic address: aidr214@ai-hosp.or.jp.")
        >>> ae.entry
        {'clinical_domain': '23'}
        """

        def _clinical_asides(afs):
            """
            Retrieve department and divison from the affiliation info
            Args: afs -- affiliation tag from the ncbi site split into sections (list)
            Return: (department,division) tuple (string,string)

            Can only be called within the get_clinical_domain_from_xml method
            """
            department = division = ""
            for option in afs:
                search = re.search(r'departments? of(.*)', option, re.I)
                if (search):
                    department = search.group(1).strip()
                search = re.search(r'division of(.*)', option, re.I)
                if (search):
                    division = search.group(1).strip()
            return (department, division)

        af_from_xml = institution.split(", ")
        (department, division) = _clinical_asides(af_from_xml)

        cd_from_department = self.get_clinical_domain(department.split())
        if (cd_from_department):
            self.check_boolean("Clinical Domain", self.get_choices("clinical_domain")[
                               cd_from_department], "Department: {0}".format(department), "clinical_domain", display=cd_from_department)

        cd_from_division = self.get_clinical_domain(division.split())
        if (cd_from_division):
            self.check_boolean("Clinical Domain", self.get_choices("clinical_domain")[
                               cd_from_division], "Division: {0}".format(division), "clinical_domain", display=cd_from_division)

        try:
            cd_from_journal = self.get_clinical_domain(
                self.entry['journal_publication'].split())
            if (cd_from_journal):
                self.check_boolean("Clinical Domain", self.get_choices("clinical_domain")[
                                   cd_from_journal], "Journal Title: " + self.entry['journal_publication'], "clinical_domain", display=cd_from_journal)

            cd_from_title = self.get_clinical_domain(
                self.entry['article_title'].split())
            if (cd_from_title):
                self.check_boolean("Clinical Domain", self.get_choices("clinical_domain")[
                                   cd_from_title], "Article Title: " + self.entry['article_title'], "clinical_domain", display=cd_from_title)
        except KeyError as e:
            #journal_publication or article_title not in entry
            # xml_extract hasnt been run
            pass
