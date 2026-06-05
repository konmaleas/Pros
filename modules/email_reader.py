# continuation from 1.3.6
# in case of py2exe must use parameter --hidden import win32timezone

import sys
from time import time as t2
from modules.path_manipulation import slash_conv, path_exists, dst_exists
from modules.file_opers import save_pickles, read_pickles
from modules.Log import timestamp
from os.path import join, exists
from os.path import expanduser as home
from datetime import datetime as dt2
from time import time, sleep
import win32com.client
import pywintypes
import win32ui
from os import startfile


class Outlook:
	def __init__(self):
		self.outlook = ''
		if self.outlook_is_running():
			self.outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
		self.path_cache = dst_exists(slash_conv(join(home('~'), r'AppData/Roaming/Pros/cache')))
		self.fp = join(self.path_cache, 'last_mail_read_fst.pkl')
		self.sp = join(self.path_cache, 'last_mail_read_snd.pkl')
		self.fst_archived = join(self.path_cache, 'last_mail_archived_fst.pkl')
		self.first_mailbox = join(self.path_cache, 'first_mailbox.pkl')
		self.second_mailbox = join(self.path_cache, 'second_mailbox.pkl')

	@staticmethod
	def outlook_is_running() -> bool:
		try:
			win32ui.FindWindow(None, "Microsoft Outlook")
			return True
		except win32ui.error:
			# startfile("outlook")
			return False

	def accounts(self):
		'''
		Searches for mailboxes
		:return: mailbox's name as str
		'''
		for e, f in enumerate(self.outlook.Folders, 1):
			yield str(f)

	def folders(self, mailbox: str):
		#ToDo iterate to discover all folders in mailbox
		'''
		Searches for mailboxes
		:return: mailbox's name as str
		'''
		for e, f in enumerate(self.outlook.Folders(mailbox).Folders, 1):
			yield f

	def sub_folders(self, mailbox: str, folder: str, sub_folder: str) -> str:
		#ToDo iterate to discover all folders in mailbox
		'''
		Searches for mailboxes
		:return: mailbox's name as str
		'''
		for e, f in enumerate(self.outlook.Folders(mailbox).Folders(folder).Folders(sub_folder).Items, 1):
			yield f

	def folder_items(self, mailbox: str, folder: str) -> str:
		#ToDo iterate to discover all folders in mailbox
		'''
		Searches for mailboxes
		:return: mailbox's name as str
		'''
		for e, f in enumerate(self.outlook.Folders(mailbox).Folders(folder).Items, 1):
			yield f

	def inbox(self, mailbox: str):
		'''
		:param mailbox: name of to work with
		:return: the mails of the mailbox
		'''
		return self.outlook.Folders(mailbox).Folders('Inbox').Items

	def sent(self, mailbox: str):
		'''
		:param mailbox: name of to work with
		:return: the mails of the mailbox
		'''
		return self.outlook.Folders(mailbox).Folders('Sent Items').Items

	@staticmethod
	def domain_fetcher(domain: str, subdomain=True, pos=1) -> str:
		if subdomain:
			return ''.join(domain.split('@')[-pos])
		domain = domain.split('@')[-1]
		if len(domain.split('.')) > 2:
			if domain.split('.')[-pos] == 'com':  # in case of @domain.com.gr
				return '.'.join(domain.split('.')[-pos - 1:])
			return '.'.join(domain.split('.')[-pos:])

	def mark_unread(self, fst_mailbox: str, read=True):
		for fste, fst_message in enumerate(self.inbox(fst_mailbox), 1):
			try:
				fst_message.Unread = read
			except TypeError as te:
				# print(f'\n0.0) te({te})')
				pass
			except AttributeError as ae:
				# print(f'\n1.0) ae({ae})')
				pass
			except UnicodeEncodeError as uee:
				# print(f'\n1.1) uee({uee})')
				pass
			except Exception as e:
				# print(f'\n1) {e}')
				pass

	def message_reader(self, message: str, obj: str):
		try:
			message = self.outlook.OpenSharedItem(message)
			if obj == 'Subject':
				return str(message.Subject)
			elif obj == 'Body':
				return str(message.Body)
			elif obj == 'SenderName':
				return str(message.SenderName)
			elif obj == 'SenderEmailAddress':
				return str(message.SenderEmailAddress)
			elif obj == 'SenTo':
				return str(message.SenTo)
			elif obj == 'To':
				return str(message.To)
			elif obj == 'CC':
				return str(message.CC)
			elif obj == 'BCC':
				return str(message.BCC)
			elif obj == 'Subject':
				return str(message.Subject)
			elif obj == 'Body':
				return str(message.Body)
			elif obj == 'ReceivedTime':
				return str(message.ReceivedTime)
			elif obj == 'SentTime':
				return str(message.SendTime)

		except TypeError as te:
			print(f'\n0.0) te({te})')
		except AttributeError as ae:
			print(f'\n1.0) ae({ae})')
		except UnicodeEncodeError as uee:
			print(f'\n1.1) uee({uee})')
		except FileNotFoundError as fnf:
			print(f'fnf({fnf})')
		except Exception as e:
			print(f'\n1) {e}')

	def save_message(self, path, message):
		# Has to recieve message from other func to save
		# Below statement unworkable cause message.SaveAs() can't exists
		# only join(path, message) can
		if exists(message.SaveAs(join(path, message))):
			return True
		return False

