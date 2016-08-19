# Research_Reproducibility Tool

##Authors:
John Christian Lukas -- clukas812@gmail.com

##Objects:
* DatabaseManager -- query redcap and enter errors into a sql database
* XMLExtractor -- extract data from the xml version of the pubmed site for an article
* ArticleManager -- handle user interaction and enter data into redcap database
* ArticleExtractor -- extract data from the text of an article
* Article -- PDFArticle and XMLArticle classes depending what type of article is extracted

##Management:
* query_redcap -- manage DatabaseManager methods
* executer -- manage extraction of data for PDFArticle and XMLArticle

##Dependencies:
	os				-- https://docs.python.org/3/library/os.html
	sys				-- https://docs.python.org/3/library/sys.html
	getopt 			-- https://docs.python.org/3.1/library/getopt.html
	pprint 			-- https://docs.python.org/3/library/pprint.html
	re				-- https://docs.python.org/3/library/re.html
	beautiful soup	-- https://www.crummy.com/software/BeautifulSoup/bs4/doc/
	pycurl 			-- http://pycurl.io/docs/latest/index.html
	requests 		-- http://docs.python-requests.org/en/master/
	io 				-- https://docs.python.org/3/library/io.html
	tkinter 		-- https://docs.python.org/3/library/tk.html
	textract        -- http://textract.readthedocs.io/en/latest/python_package.html
	nltk 			-- http://www.nltk.org/
	stemming 		-- https://pypi.python.org/pypi/stemming/1.0
	json 			-- https://docs.python.org/3.4/library/json.html
	csv 			-- https://docs.python.org/3/library/csv.html
	difflib 		-- https://docs.python.org/2/library/difflib.html
	sqlite3			-- https://docs.python.org/3/library/sqlite3.html
	time			-- https://docs.python.org/3.0/library/time.html
	
##Video Tutorials:
1. [Intro](https://www.youtube.com/watch?v=byCT6yb_9lA)
2. [DatabaseManager](https://www.youtube.com/watch?v=FSD5t8SCNZQ)
3. [XMLExtractor](https://www.youtube.com/watch?v=d5v4LsMz99A)
4. [ArticleManager](https://www.youtube.com/watch?v=J6kvrPczfMU)
5. [ArticleExtractor](https://www.youtube.com/watch?v=sV7jGREY-GQ)
6. [Article](https://www.youtube.com/watch?v=iPUkUB-8Hzc)
7. [executer and query_redcap](https://www.youtube.com/watch?v=EznR-Sdf6Uc)

All commands available in: otherthings/Commands text document

##Future Directions:
* Expand to extract more fields (see otherthings/fields_status.xlsx for information on currently supported fields and extraction methods for those fields); Steps:
  * In ArticleExtractor, define a new method:
  ```
  def _get_{field}(self,text):
      #where {} represent a place to substitute your given value
      for sent in nltk.sent_tokenize(self.text):
          if (re.search({regular expression indicating value for {field},sent,re.I)):
              self.check({readable format of field},{value of field},sent,{redcap codebook key for field},{readable format of field})
  #Example:
  def _get_data_cleaned(self,text):
      for sent in nltk.sent_tokenize(self.text):
          if (re.search(r'data.*?cleaned',sent,re.I)):
              self.check("Data Were Cleaned",1,sent,'data_cleaned_yn',display='yes')
  ```
  * In Article, defined new methods in PDFArticle and XMLArticle classes:
  ```
  #PDFArticle class
  def get_{field}(self):
      return self._get_{field}(self.text)
      #PDFArticle always takes full article text as its extraction parameter
      #call ArticleExtractor inherited method
  #Example:
  def get_data_cleaned(self):
      return self._get_data_cleaned(self.text)
    
  #XMLArticle class
  def get_{field}(self):
      return _self._get_{field}(self.xml_section({section(s) to search for data}))
      #XMLArticle can take full text or a specific section of the article as its extraction parameter
      #call same ArticleExtractor inherited method
  #Example:
  def get_data_cleaned(self):
      return self._get_data_cleaned(self.xml_section('methods','results')
  ```
  * In executer, in text_extract function, call PDFArticle / XMLArticle method
  ```
  def text_extract(art):
      art.get_reviewer()
      ...
      art.get_{field}()
      #Example:
      art.get_data_cleaned()
  ```
* Record how data from the article was extracted (run_style=0 or run_style=1), whether the user accepted the tools proposed answer or replaced the proposal with their own
* auto-increment redcap record_ids for entry (now, all redcap entry is uploaded into the 9b7057f5f8894c9c - a dummy redcap entry - unless run using the DatabaseManager explicitly)
* Develop Trainer:
  * Save classifier for use in future extractions
  * Improve accuracy
  * Expand to allow for xml articles
  * Reformat pubmed.json to: {record_id: {'doi':'10.2217/pgs.11.164','pmid':2443893'}}
* Expand query_redcap to allow more advanced data requests
* Dont require PDF files to be named their identifiers
* Dont require PDF files to be named their pubmed code in order to run XMLExtraction
