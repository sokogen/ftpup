#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function
from ftplib import FTP
from urlparse import urlparse
import argparse, operator, os

class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[91m'
    ENDC = '\033[0m'

def getargs():
	parser = argparse.ArgumentParser(
	description='''Программа синхронизации файлов локального и удаленного каталога по FTP.
	Файл конфигурации создается автоматически и рекомендуется к использованию.
	На время тестирования возможно использование ключей командной строки.''', 
	usage='%(prog)s [options] LOCALDIR [LOCALDIRS... ] ftp://[user:pass@]server/FULL/REMOTE/DIR',
	epilog=''' Особенности:
	Все файлы из всех каталогов складываются в один каталог.
	Поэтому во всех каталогах должны быть разные правила именования файлов. ''')
	parser.add_argument('dirs', nargs='+', help='Собираем локальные и удаленные директории')
	parser.add_argument('-v', '--verbose', dest='verb', action='store_true', help="Вывод отладочной информации")
	parser.add_argument('-V', '--version', action='version', version='%(prog)s 0.8')
	return parser.parse_args()

class SyncData:
	def __init__(self, dirs):
		self.ftpurl = urlparse(dirs[-1])
		self.localfnlist = self.getlocallist(dirs[:-1])
		self.FTPlogin()
		self.remotefnlist = self.getremotelist()
		self.execsync()
		self.FTPlogout()

	def getlocallist(self, dirs):
		#print (dict(map(lambda d: (d, tuple([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))])), dirs)))
		return dict(map(lambda d: (d, tuple([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))])), dirs))
		#return dict(map(lambda d: (d, tuple(os.listdir(d))), dirs))
	
	def getremotelist(self):
		try:
			fl = self.ftp.nlst(self.ftpurl.path)
			return map(self.getbasename, fl)
		except:
			return []

	def getbasename(self, fn):
		return os.path.basename(fn)

	def getdirname(self, fn):
		return os.path.dirname(fn)

	def uploadfile(self, localdir, remotedir, fn):
		print(fn)
		locfile, remfile = (os.path.join(localdir, fn), os.path.join(remotedir, fn))
		if args.verb: print('%s \t --> \t %s' % (locfile, remfile), end='')
		self.ftp.storbinary("STOR " + remfile, open(locfile, 'rb'))
		if args.verb: print(bcolors.OKGREEN + '\tDONE' + bcolors.ENDC)
		return None
	
	def removefile(self, fn):
		self.ftp.delete(fn)
		if args.verb: print('%s \t ' % fn, bcolors.WARNING + 'DELETED' + bcolors.ENDC)
		return None

	def execsync(self):
		# Upload files
		self.uploadlist = reduce(operator.concat, map(lambda (d, f): map(lambda fn: os.path.join(d, fn), filter(lambda lfn: lfn not in self.remotefnlist , f)) , self.localfnlist.items()))
		self.uploadfn = map(self.getbasename, self.uploadlist)
		if len(self.uploadfn) != len(set(self.uploadfn)):
			print(bcolors.WARNING + "WARNING:" + bcolors.ENDC, "неправильное именование файлов. Названия файлов в разных директориях не должны совпадать.")
		if len(self.uploadlist) > 0 and args.verb:
			print("Will be uploaded: %s." % ', '.join(self.uploadfn))
		map(lambda fn: self.uploadfile(self.getdirname(fn), self.ftpurl.path, self.getbasename(fn)), self.uploadlist)

		# Removing deleted locally files
		self.localbasenames = reduce(operator.concat, self.localfnlist.values())
		self.removelist = filter(lambda f: f not in self.localbasenames, self.remotefnlist)
		if len(self.removelist) > 0 and args.verb: print("Will be deleted: %s." % ', '.join(self.removelist))
		map(lambda fn: self.removefile(os.path.join(self.ftpurl.path, fn)), self.removelist)

	def FTPlogin(self):
		try:
			self.ftpauth, self.ftpaddr = tuple(self.ftpurl.netloc.split('@'))
			self.ftpuser, self.ftppass = self.ftpauth.split(':')
		except ValueError:
			self.ftpaddr = self.ftpurl.netloc
			self.ftpuser, self.ftppass = None
		self.ftp = FTP(self.ftpaddr, self.ftpuser, self.ftppass)
		return True
	
	def FTPlogout(self):
		if args.verb: print("INFO: Все задачи выполнены.")
		self.ftp.quit()


if __name__ == "__main__":
	args = getargs()
	data = SyncData(args.dirs)
