from bs4 import BeautifulSoup
import requests
from collections import defaultdict
from string import ascii_uppercase
import json
import os

class WikiPhone:

	def __init__(self):

		self.model_urls = defaultdict()
		self.model_info = []

	def _explore_category(self, manufacturer):
		"""
		find a category page by the mobile phone manufacturer name; it's expected to be something like 
		https://en.wikipedia.org/wiki/Category:Samsung_mobile_phones
		"""

		def __has_type_and_class(tag):

			if any([tag.text not in ascii_uppercase, not tag.parent, tag.name != 'h3']):
				return None

			par = tag.parent

			return (par['class'][0] == 'mw-category-group')

		url = f'https://en.wikipedia.org/wiki/Category:{manufacturer.title()}_mobile_phones'

		while True:

			r = requests.get(url).text
			soup = BeautifulSoup(r, "lxml")

			for p in soup.find_all(__has_type_and_class):

				for _ in p.parent.find_all('a'):
						self.model_urls[_['title']] = 'https://en.wikipedia.org' + _['href']

			# try to find a link to the next page; if no such link can be found, next_page_ will be None
			next_page_ = soup.find('a', text='next page')

			if next_page_:
				url = 'https://en.wikipedia.org' + next_page_['href']
			else:
				print('no more pages')
				break

		print(f'found {len(self.model_urls)} model urls..')

		return self

	def _get_phone_details(self, url):

		# find an infobox
		r = requests.get(url).text
		soup = BeautifulSoup(r, "lxml")

		infobox = soup.find('table', class_='infobox')

		if not infobox:
			print('no infobox')
			return None

		inf_ = defaultdict()

		for row in infobox.find_all('tr'):

			dp = row.find(lambda x: x.name == 'th')
			v = row.find(lambda x: x.name == 'td')

			if dp and v:
				inf_[dp.text.lower().strip()] = v.text.lower().strip()

		return inf_

	def get_details(self):

		for model in self.model_urls:
			_ = self._get_phone_details(self.model_urls[model])
			if _:
				self.model_info.append(_)

		print(f'collected {len(self.model_info)} model information summaries.')

		return self

	def save(self):

		if not os.path.exists('data'):
			os.mkdir('data')

		json.dump(self.model_info, open('data/phone_info.json', 'w'))

		return self


if __name__ == '__main__':

	wp = WikiPhone() \
		._explore_category('samsung') \
		.get_details() \
		.save()