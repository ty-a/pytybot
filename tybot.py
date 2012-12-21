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
		
	def postToWikiaApi(self,data):
		"""
		POSTS content to the Wikia API in the json format
		
		:param data (dict): A dict of what is being posted.
		:returns: The response from the API
		"""
		
		data = urllib.urlencode(data)
		response = self.opener.open(self.wiki + "/wikia.php", data)
		
		response = response.read()
		response = json.loads(response, 'utf-8')
		
		return response
		
	def postToWiki(self,data):
		"""
		POSTs content to the wiki's API in json format
		
		:param data (dict): An dict of what is being posted.
		:returns: the response from the API
		"""
		data = urllib.urlencode(data)
		response = self.opener.open(self.wiki + "/api.php", data);
	
		response = response.read()
		response = json.loads(response, 'utf-8')
	
		return response

	def login(self,username,password):
		"""
		Logins into the wiki via API
		
		:param username (str): The username of the user
		:param password (str): The user's password
		:returns: boolean based on success
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
		
		:param user (str): The user to get the string for
		:returns: dict of groups
		"""
		data = {
			"action":"query",
			"list":"users",
			"ususers":user,
			"usprop":"groups",
			"format":"json"
		}
	
		response = self.postToWiki(data)
		try:
			groups = tuple(response["query"]["users"][0]["groups"])
		except: 
			groups = (u'*')
			
		return groups

	def getTokens(self):
		"""
		Gets the tokens required to perform many actions
		
		:param none: (uses the username provided when making tybot object)
		:returns: dict of tokens
		"""
		groups = self.getGroups(self.username)
	
		if "sysop" in groups:
			data = {
				"action":"query",
				"prop":"info",
				"intoken":"delete|edit|protect|block|unblock|watch",
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
					"block":intoken["blocktoken"],
					"watch":intoken["watchtoken"]
				}
			
			response = self.postToWiki(data)
			response = response["query"]["deletedrevs"]
		
			for intoken in response:
				tokens["undelete"] = intoken["token"]
		
		else:
			for intoken in response:
				tokens = {
					"edit":intoken["edittoken"],
					"watch":intoken["watchtoken"]
				}

		return tokens
	
	def get_page_content(self,page):
		"""
		Gets the current content of a page on the wiki.
		
		:param page (str): The page to get the content of.
		:returns: string with the page content or '' if page does not exist
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
		
		:param page (str): The page to edit
		:param content (str): What to put on the page
		:param summary (str): The edit summary (Default: '')
		:param bot (bool): Mark the edit as a bot or not (Default: 1)
		:returns: boolean based on success
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
		
		:param page (str): The page to delete
		:param summary (str): The deletion summary (Default:'')
		:returns: boolean based on success
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
		
		:param page (str): The page to undelete
		:param summary (str): The undeletin summary (Default: '')
		:returns: boolean based on success
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
	
	def block(self,target,summary='',expiry="infinite"):
		"""
		Blocks users via the API
		
		:param target (str): The user to block
		:param summary (str): The block summary
		:param expiry (str): Expiry timestamp or relative time. (Default: infinite)
		:returns: boolean based on success
		"""
		data = {
			"action":"block",
			"user":target,
			"reason":summary,
			"expiry":expiry,
			"token":self.tokens["block"],
			"format":"json"
		}
		
		response = self.postToWiki(data)
		
		try:
			print response["error"]["code"]
			return False
		except:
			return True
	
	def unblock(self,target,summary=''):
		"""
		Unblocks users via the API
		
		:param target (str): The user to unblock
		:param reason (str): The unblock reason
		:returns: boolean based on success
		"""
		data = {
			"action":"unblock",
			"user":target,
			"reason":summary,
			"token":self.tokens["unblock"],
			"format":"json"
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
		
		:param category (str): The category to get pages from (Add Category: prefix!)
		:param limit (int): How many pages to get back. (Default "max - 500 for normal users, 5000 for users with APIhighlimits)
		:returns: list of page titles
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
					
	def get_all_pages(self,redirects="nonredirects",namespace=0,):
		"""
		Get all pages on a wiki
		
		:param  redirects (str): show redirects, only redirects, or no redirects (default: nonredirects)
			legal values: all, redirects, nonredirects
		:param namespace (int): The numerical ID of namespace to return pages for (default: 0)
		:returns: list of page titles
		"""
		
		pages = []
		apfrom = ''
		
		if((redirects != "nonredirects") and (redirects != "all") and (redirects != "redirects")):
			return False
		
		while (1):
			dataToPost = {
				'action':'query',
				'list':'allpages',
				'apfrom':apfrom,
				'apfilterredir':redirects,
				'apnamespace':namespace,
				'aplimit':'max',
				'format':'json'
			}
			
			response = self.postToWiki(dataToPost)
			
			try:
				print response["error"]["code"]
				return False
			except:
				pass
				
			response2 = response["query"]["allpages"]
			
			for page in response2:
				pages.append(page['title']) 
				
			try:
				apfrom = response["query-continue"]["allpages"]["apfrom"]
			except:
				return pages
				
	def watch(self, page, unwatch=False):
		"""
		Watches a page on the wiki
		
		:param page (str): The page to watch
		:param unwatch (bool): Whether or not to unwatch the page. (Default: False)
		:returns: bool based on success
		"""
		
		if unwatch == False:
			dataToPost = {
				"action":"watch",
				"title":page,
				'format':'json',
				"token":self.tokens["watch"]
			}
		else:
			dataToPost = {
				"action":"watch",
				"title":page,
				"unwatch":'',
				'format':'json',
				"token":self.tokens["watch"]
			}
		
		response = self.postToWiki(dataToPost)
		
		try:
			print response["error"]["code"]
			return False
		except:
			return True
			
	def get_users_by_group(self, group, amount = "max"):
		dataToPost = {
			'action':'query',
			'list':'allusers',
			'format':'json',
			'augroup':group,
			'aulimit':amount
		}
		
		response = self.postToWiki(dataToPost)
		
		try:
			print response["error"]["code"]
			return False
		except:
			pass
			
		users = []
		
		for user in response["query"]["allusers"]:
			users.append(user["name"])
		
		return users
		
	def get_pages_by_prefix(self, prefix, namespace = "0"):
		dataToPost = {
			'action':'query',
			'list':'allpages',
			'apprefix':prefix,
			'apnamespace':namespace,
			'aplimit':'max',
			'format':'json'
		}
		
		response = self.postToWiki(dataToPost)
		
		try:
			print response["error"]["code"]
			return False
		except:
			pass
			
		pages = []
		
		for page in response["query"]["allpages"]:
			pages.append(page["title"])
			
		return pages
