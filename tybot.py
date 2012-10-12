##########################################################################
# PyTyBot - A MediaWiki wrapper for use on wikis. 
#    Copyright (C) 2012  TyA <tya.wiki@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################

import urllib
import urllib2
import cookielib
import json

class tybot(object):

	def __init__(self,username,password,wiki):
		self.username = username
		self.password = password
		self.wiki = wiki
		
		self.cookiejar = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.opener.add_headers = [('User-Agent','Python TyBot')]
		self.login(self.username,self.password)
		self.tokens = self.getTokens()
		
	def postToWiki(self,data):
		"""
		POSTs content to the wiki's API in json format
		
		@param array data - An array of what is being posted.
		@return the response from the API
		"""
		data = urllib.urlencode(data)
		response = self.opener.open(self.wiki, data);
	
		response = response.read()
		response = json.loads(response)
	
		return response

	def login(self,username,password):
		"""
		Logins into the wiki via API
		
		@param string username - The username of the user
		@param string password - The user's password
		@return boolean based on success
		"""
		data = {
			"action":"login",
			"lgname":username,
			"lgpassword":password,
			"format":"json"
		}
		response = self.postToWiki(data)
	
		logintoken = response["login"]["token"]
	
		data = {
			"action":"login",
			"lgname":username,
			"lgpassword":password,
			"lgtoken":logintoken,
			"format":"json"
		}
	
		response = self.postToWiki(data)
	
		if response["login"]["result"] == "Sucess":
			return True
		else:
			print response["login"]["result"]
			return False

	def getGroups(self,user):
		"""
		Gets the usergroup a user is in
		
		@param string user - The user to get the string for
		@return dict of groups
		"""
		data = {
			"action":"query",
			"list":"users",
			"ususers":user,
			"usprop":"groups",
			"format":"json"
		}
	
		response = self.postToWiki(data)
		groups = tuple(response["query"]["users"][0]["groups"])
		return groups

	def getTokens(self):
		"""
		Gets the tokens required to perform many actions
		
		@param none (uses the username provided when making tybot object)
		@return dict of tokens
		"""
		groups = self.getGroups(self.username)
	
		if "sysop" in groups:
			data = {
				"action":"query",
				"prop":"info",
				"intoken":"delete|edit|protect|block|unblock",
				"titles":"Main Page",
				"format":"json"
			}
		else:
			data = {
				"action":"query",
				"prop":"info",
				"intoken":"edit",
				"titles":"Main Page",
				"format":"json"
			}
	
		response = self.postToWiki(data)
		response = response["query"]["pages"].values()
	
		if "sysop" in groups:
	
			data = {
				"action":"query",
				"list":"deletedrevs",
				"drprop":"token",
				"format":"json"
			}
		
			for intoken in response:
				tokens = {
					"edit":intoken["edittoken"],
					"delete":intoken["deletetoken"],
					"protect":intoken["protecttoken"],
					"unblock":intoken["unblocktoken"],
					"block":intoken["blocktoken"]
				}
			
			response = self.postToWiki(data)
			response = response["query"]["deletedrevs"]
		
			for intoken in response:
				tokens["undelete"] = intoken["token"]
		
		else:
			for intoken in response:
				tokens = {
					"edit":intoken["edittoken"]
				}

		return tokens
	
	def get_page_content(self,page):
		"""
		Gets the current content of a page on the wiki.
		
		@param string page - The page to get the content of.
		@return string with the page content or '' if page does not exist
		"""
		data = {
			"action":"query",
			"prop":"revisions",
			"rvprop":"content",
			"titles":page,
			"format":"json"
		}
	
		response = self.postToWiki(data)
		response = response["query"]["pages"].values()
	
		for page in response:
			try:
				content = page['revisions'][0]["*"]
			except:
				content = ""
		return content
	
	def edit(self,page,content,summary='',bot=1):
		"""
		Makes the actual edit to the page
		
		@param string page - The page to edit
		@param string content - What to put on the page
		@param string summary - The edit summary (Default: '')
		@param boolean bot - Mark the edit as a bot or not (Default: 1)
		@return boolean on success
		"""
		data = {
			"action":"edit",
			"title":page,
			"summary":summary,
			"text":content,
			"bot":bot,
			"token":self.tokens["edit"],
			"format":"json"
		}
	
		response = self.postToWiki(data)
		try:
			print response["error"]["info"]
			return False
		except:
			return True

	def delete(self,page, summary=''):
		""" 
		Deletes pages via the API
		
		@param string page - The page to delete
		@param string summary - The deletion summary (Default:'')
		@return boolean on success
		"""
		data = {
			"action":"delete",
			"token":self.tokens["delete"],
			"title":page,
			"summary":summary,
			"format":"json"
		}
	
		response = self.postToWiki(data)
	
		try:
			print response["error"]["info"]
			return False
		except:
			return True
			
	def undelete(self,page,summary=''):
		"""
		Undeletes pages via the API
		
		@param string page - The page to undelete
		@param string summary - The undeletin summary (Default: '')
		@return boolean on success
		"""
		
		data = {
			"action":"undelete",
			"title":page,
			"reason":summary,
			"format":"json",
			"token":self.tokens["undelete"]
		}
		
		response = self.postToWiki(data)
		
		try:
			print response["error"]["code"]
			return False
		except:
			return True

	def get_category_members(self,category,limit="max"):
		"""
		Get members of a category
		
		@param string category - The category to get pages from (Add Category: prefix!)
		@param limit - How many pages to get back. (Default "max - 500 for normal users
														5000 for users with APIhighlimits)
		@return list of page titles
		"""
		cmcontinue = ''
		pages = []
		if limit != "max":
			data = {
				"action":"query",
				"list":"categorymembers",
				"cmtitle":category,
				"cmlimit":limit,
				"cmprop":"title",
				"format":"json"
			}
		
			response = self.postToWiki(data)
			response = response["query"]["categorymembers"]

			for page in response:
				pages.append(page["title"])
			
			return pages
		
		else:
			while 1:
				data = {
					"action":"query",
					"list":"categorymembers",
					"cmtitle":category,
					"cmlimit":"max",
					"cmprop":"title",
					"cmcontinue":cmcontinue,
					"format":"json"
				}
		
				response = self.postToWiki(data)
			
				response2 = response["query"]["categorymembers"]
			
				for page in response2:
					pages.append(page["title"])
			
				try:
					cmcontinue = response["query-continue"]["categorymembers"]["cmcontinue"]
				except:
					return pages