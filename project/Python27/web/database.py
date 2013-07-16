"""
@author Jiexin Guo

This is the wrapping of sqlite3 for python.

Copyright (C) 2013-2014 sysu-software. All Rights Reserved.

To use, simply 'import database' and connect the database of sqlite3!

"""

import sqlite3
import urllib2
import jsonUtil
import json
import os, sys
import logging
import logging.handlers

class SqliteDatabase:
	URL=''
	userId=-1
	logger=None
	def isDatabaseExist(self,database):
		if os.path.exists(database):  
			return True
		else:
			return False
		
	def _logFileInit(self):
		self.logger = logging.getLogger()
		self.logger.setLevel(logging.DEBUG)
		rh=logging.FileHandler("database.log") 
		fm=logging.Formatter("%(asctime)s  %(levelname)s - %(message)s","%Y-%m-%d %H:%M:%S")
		rh.setFormatter(fm)
		self.logger.addHandler(rh)		
		
	def __init__ (self,URL="igem.db"):
		self.URL=URL
		self._logFileInit()
		if not self.isDatabaseExist(self.URL):
			self.logger.error('database file not exist: %s'%self.URL)
			return
		else:
			self.logger.debug('database file exist: %s'%self.URL)
		self.__cx = sqlite3.connect(self.URL)
		self.logger.debug('connect to database: %s'%self.URL)
		self.__cursor = self.__cx.cursor()	
		
	"""
		return a json that after doing the selection of all the table(of the tableName)
		@author: Jiexin Guo
		@param self:
		@type self:
		@param tableName:
		@type tableName:
		@return:a json format from the selection result
		@rtype:json's list like:
		[{u'type': u'pre', u'desp': u'as you know', u'id': 123, u'name': u'test1'},
				{u'type': u'pre', u'desp': u'test', u'id': 124, u'name': u'test2'}]
	"""
	def selectAllOfTable(self,tableName='part_list'):
		excuteString='select * from '+str(tableName)
		self.__cursor.execute(excuteString)
		self.logger.debug('selectAllOfTable: %s'%excuteString)
		jsonEncoded = jsonUtil.turnSelectionResultToJson(self.__cursor.description,self.__cursor.fetchall())
		decodejson = json.loads(jsonEncoded)
		return decodejson
	
	def getMaxUserId(self,tableName='user_list'):
		self.__cursor.execute('select * from %s where id=(select max(id) from %s)'%(tableName,tableName))		
		jsonEncoded = jsonUtil.turnSelectionResultToJson(self.__cursor.description,self.__cursor.fetchall())
		decodejson = json.loads(jsonEncoded)	
		self.logger.debug('get max user id=%d'%decodejson[0]['id'])	
		return decodejson[0]['id']
	
	"You can only update the logined user"
	def updateUserPassword(self,password):
		if self.userId==-1:
			self.logger.error('not login but want to change the user password')
			return 'updateUserPassword failed'
		sql_cmd='UPDATE user_list SET password_MD5="%s" WHERE id=%d'%(password,self.userId)
		self.__cursor.execute(sql_cmd)
		self.logger.debug('update user password: %s'%sql_cmd)
		self.__cx.commit()
		return 'updateUserPassword succeed'
	
	def updateUserData(self,data):
		print data
		if self.userId==-1:
			self.logger.error('not login but want to save the user data')
			return 'updateUserData failed'
		sql_cmd='UPDATE user_save SET data="%s" WHERE user_id=%d'%(data,self.userId)
		print sql_cmd
		self.__cursor.execute(sql_cmd)
		self.logger.debug('update user: %s'%self.getUserNameById(self.userId))
		self.__cx.commit()
		return 'updateUserData succeed'		
	
	def insertUserData(self,data):
		if self.userId==-1:
			self.logger.error('not login but want to save the user data')
			return 'updateUserData failed'
		sql_cmd='INSERT INTO user_save (user_id,data) VALUES (%d,"%s")'%(self.userId,data)
		print sql_cmd
		self.__cursor.execute(sql_cmd)
		self.logger.debug('update user: %s'%self.getUserNameById(self.userId))
		print self.__cx.commit()
		return 'updateUserData succeed'	
		
	def insertAUser(self,name,password,email,group_id):
		nextId=self.getMaxUserId()+1
		excuteString='INSERT INTO user_list VALUES(%d,"%s","%s","%s",%d);'%(nextId,name,password,email,group_id)
		self.logger.debug('insert a user: %s ' %excuteString)
		self.__cursor.execute(excuteString)
		self.__cx.commit()
		
	def getUserPasswordById(self,name):
		excuteString='select * from user_list where name = "%s"' %name		
		self.__cursor.execute(excuteString)		
		jsonEncoded = jsonUtil.turnSelectionResultToJson(self.__cursor.description,self.__cursor.fetchall())
		decodejson = json.loads(jsonEncoded)
		if len(decodejson)==0:
			return None
		else:
			return decodejson[0]['password_MD5']		
	
	def isUserNameAndPasswordCorrect(self,name,password):
		if self.getUserPasswordById(name) is None:
			return 'No such user!'
		if password==self.getUserPasswordById(name):
			return 'Password correct!'
		else:
			return 'Password not correct!'
	
	def getUserNameById(self,id):
		excuteString='select * from user_list where id = %d' %id				
		self.__cursor.execute(excuteString)	
		self.logger.debug('get user name by id: %d'%id)	
		jsonEncoded = jsonUtil.turnSelectionResultToJson(self.__cursor.description,self.__cursor.fetchall())
		decodejson = json.loads(jsonEncoded)
		return decodejson[0]['name']		
		
	def getUserIdByName(self,name='Bobby'):
		excuteString='select * from user_list where name = "%s"' %name		
		self.__cursor.execute(excuteString)		
		jsonEncoded = jsonUtil.turnSelectionResultToJson(self.__cursor.description,self.__cursor.fetchall())
		decodejson = json.loads(jsonEncoded)
		return decodejson[0]['id']
		
	"the demo of selecting all data of part_list to the encoded json format"
	def demo1(self):
		pass
		#print self.selectAllOfTable()
		#print self.isUserNameAndPasswordCorrect(name='Bobby',password='1234')		
	
	"add a column to a table"
	def addColumnToTable(self,tableName,field, type, default=''):
		if len(default)==0:
			sql_cmd = '''alter table %s add column %s %s;''' % (tableName,field, type)			
		else:				
			sql_cmd = '''alter table %s add column %s %s default %s;''' % (tableName,field, type,default)
		self.__cursor.execute(sql_cmd)
		self.__cx.commit()		
	
	def printAllTableNames(self):
		result=self.__cursor.execute("select name from sqlite_master where type='table' order by name;")
		temp=''
		for row in result.fetchall():
			temp=temp+row[0]+','
		print temp
		return temp
	
	"""
		test if there is the same record in the table
		@author: Jiexin Guo		
		@param self:
		@type self:
		@param tableName:
		@type tableName:string
		@param recs:
		@type recs:json format
		@return:True means that the record exists in the table
		@rtype:boolean
	"""		
	def isRecordExist(self,tableName,recs=''):
		if(len(self.selectAllOfTable(tableName))==0):
			self.logger.debug('table:%s with no record'%tableName)
			return False
		recs=self.selectAllOfTable(tableName)[0]
		self.logger.debug(recs)	
		whereCommand=jsonUtil.changeADictToStringThatCanUseBySql(recs)
		sql_cmd="select * from %s where %s ;"%(tableName,whereCommand)
		self.__cursor.execute(sql_cmd)
		self.logger.debug(sql_cmd)
		res = self.__cursor.fetchall()
		if len(res) > 0:
			return True
		else:
			return False
			
	def __del__(self):
		self.__cursor.close()
		self.__cx.close()
		self.logger.debug('database close')
		self.logger.debug('')
		
if __name__=="__main__":
	sql=SqliteDatabase()
	#sql.addColumnToTable('part_relation','testw','integer',' 0')
	sql.demo1()
	#print sql.isRecordExist('part_list')
	#sql.selectAllOfTable('part_relation')
	#sql.printAllTableNames()