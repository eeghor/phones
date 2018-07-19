from bs4 import BeautifulSoup
import requests
from collections import defaultdict
from string import ascii_uppercase
import json
import os
import arrow

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

import time

class WikiPhone:

	def __init__(self):

		self.manufacturers = {'samsung': 'Samsung', 'huawei': 'Huawei', 'htc': 'HTC', 
								'oneplus': 'OnePlus','lg': 'LG_Electronics',
									'sony': 'Sony', 'asus': 'Asus'}

		self.model_urls = defaultdict()
		self.model_info = []
		self.model_prices = []

	def explore_categories(self):
		"""
		find a category page by the mobile phone manufacturer name; it's expected to be something like 
		https://en.wikipedia.org/wiki/Category:Samsung_mobile_phones
		"""

		def __has_type_and_class(tag):

			if any([tag.text not in ascii_uppercase, not tag.parent, tag.name != 'h3']):
				return None

			par = tag.parent

			return (par['class'][0] == 'mw-category-group')

		for manuf in self.manufacturers:

			print(f'collecting {manuf.upper()} phone urls..')

			url = f'https://en.wikipedia.org/wiki/Category:{self.manufacturers[manuf]}_mobile_phones'

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
					break

		print(f'found {len(self.model_urls)} model urls..')

		return self

	def _get_phone_details(self, url):

		# find an infobox
		r = requests.get(url).text
		soup = BeautifulSoup(r, "lxml")

		inf_ = defaultdict()

		infobox = soup.find('table', class_='infobox')

		if not infobox:
			return None

		capt_ = infobox.find('caption')

		inf_['phone_name'] = capt_.text.lower().strip() if capt_ else None

		for row in infobox.find_all('tr'):

			dp = row.find(lambda x: x.name == 'th')
			v = row.find(lambda x: x.name == 'td')

			if dp and v:
				inf_[dp.text.lower().strip()] = v.text.lower().strip()

		return inf_

	def get_details(self):

		for model in self.model_urls:

			print(f'{model}...', end='')

			_ = self._get_phone_details(self.model_urls[model])

			if _:
				self.model_info.append(_)
				print('ok')
			else:
				print('failed')

		print(f'collected {len(self.model_info)} model information summaries.')

		return self

	def save(self):

		if not os.path.exists('data'):
			os.mkdir('data')

		if self.model_info:
			json.dump(self.model_info, open(f'data/phones_{arrow.utcnow().to("local").format("YYYYMMDD")}.json', 'w'))

		if self.model_prices:
			json.dump(self.model_prices, open(f'data/phone_prices_{arrow.utcnow().to("local").format("YYYYMMDD")}.json', 'w'))

		return self

	def get_price(self):
		"""
		get phone names and prices from Mobileciti
		"""
		driver = webdriver.Chrome('webdriver/chromedriver')

		for manuf in self.manufacturers:

			print(f'searching for {manuf.upper()} phone prices...')

			url = f'https://mobileciti.com.au/mobile-phones/{manuf}'	

			try:
				driver.get(url)
			except:
				continue

			time.sleep(7)

			driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

			time.sleep(7)

			for i, prod in enumerate(driver.find_elements_by_class_name('product-item'), 1):

				name_ = price_ = rrp_ = None

				try:
					name_ = prod.find_element_by_tag_name('h2').text.strip()
				except:
					# if no model name it's something dodgy, skip altogether
					continue

				for cl_name in ['price-discount', 'price']:

					try:
						price_ = prod.find_element_by_class_name(cl_name).text.strip()
					except:
						continue

				for price in ['price-normal', 'price']:

					try:
						rrp_ = prod.find_element_by_class_name(price).text.strip()
					except:
						continue

				if all([name_, price_, rrp_]):

					self.model_prices.append({'name': name_, 'price': price_, 'rrp': rrp_, 'manufacturer': manuf})

		driver.close()

		return self

if __name__ == '__main__':

	wp = WikiPhone() \
		.explore_categories() \
		.get_details() \
		.get_price() \
		.save()