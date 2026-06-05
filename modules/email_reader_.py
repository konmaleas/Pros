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

	def folders(self, mailbox: str) -> str:
		#ToDo iterate to discover all folders in mailbox
		'''
		Searches for mailboxes
		:return: mailbox's name as str
		'''
		for e, f in enumerate(self.outlook.Folders(mailbox), 1):
			yield str(f)

	def inbox(self, mailbox: str):
		'''
		:param mailbox: name of to work with
		:return: the mails of the mailbox
		'''
		return self.outlook.Folders(mailbox).Folders('inbox').Items

	def sent(self, mailbox: str):
		'''
		:param mailbox: name of to work with
		:return: the mails of the mailbox
		'''
		return self.outlook.Folders(mailbox).Folders('Sent Items').Items

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

	def mark_read_equals(self, fst_mailbox: str, snd_mailbox: str):
		cnt = 0
		while True:
			try:
				if self.outlook_is_running():
					if cnt == 0:
						cnt += 1
						print(f'sleep({sleep(10)})')
					else:
						print(f'sleep({sleep(300)})')
					self.outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
					fst_pkl, snd_pkl = 1, 1
					if exists(self.sp) and exists(self.fp):
						fst_pkl = int(read_pickles(self.fp))
						print(f'fst_pkl({fst_pkl}) timestamp({timestamp(True, True)})')
						snd_pkl = int(read_pickles(self.sp))
						print(f'snd_pkl({snd_pkl}) timestamp({timestamp(True, True)})')
					else:
						sys.exit('No pickles to read.')
					for fste, fst_message in enumerate(self.inbox(fst_mailbox), 1):
						if fste < fst_pkl:
							continue
						fst_pkl += 1
						snd_pkl = int(read_pickles(self.sp))
						for snde, snd_message in enumerate(self.inbox(snd_mailbox), 1):
							if snde < snd_pkl:
								continue
							snd_pkl += 1
							try:
								if str(fst_mailbox) == str(snd_message.SenderEmailAddress):
									snd_message.Unread = False
								if str(fst_message.ReceivedTime) == str(snd_message.ReceivedTime):
									if str(fst_message.SenderEmailAddress) == str(snd_message.SenderEmailAddress):
										if str(fst_message.Subject) == str(snd_message.Subject):
											snd_message.Unread = False
							except Exception as e:
								print(e)
							except UnicodeEncodeError as uee:
								print(uee)
					save_pickles(self.fp, fst_pkl)
					save_pickles(self.sp, snd_pkl)
			except AttributeError as ae:
				print(ae)
				pass

	def mark_unread(self, fst_mailbox: str, snd_mailbox: str, read: bool):
		try:
			for fste, fst_message in enumerate(self.inbox(fst_mailbox), 1):
				fst_message.Unread = read

			for snde, snd_message in enumerate(self.inbox(snd_mailbox), 1):
				snd_message.Unread = read

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


# o = Outlook()
# o.mark_read_equals(read_pickles(o.first_mailbox), read_pickles(o.second_mailbox))
