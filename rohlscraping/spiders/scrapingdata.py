import scrapy
import re
import csv
import pandas as pd
from scrapy import FormRequest
import json
import urllib
from scrapy import Request


class SiteProductItem(scrapy.Item):
    ASIN = scrapy.Field()
    Model_Number = scrapy.Field()
    Qty = scrapy.Field()


class MyScraper(scrapy.Spider):
    name = "scrapingdata"
    allowed_domains = ['extranet.rohlhome.com']
    DOMAIN_URL = 'http://extranet.rohlhome.com'
    LOGIN_URL = 'http://extranet.rohlhome.com/dealer-extranet.aspx'
    START_URL = 'http://extranet.rohlhome.com/dealer-extranet/ProductSearch.aspx?caller=prodsearch'
    USERNAME = 'ULEGROUP'
    PASSWORD = 'ECOMM54321'

    def __init__(self, **kwargs):

        # self.input_file = kwargs['input_file']
        self.input_file = 'rohl_.xlsx'
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36",
                        'Content-Type': 'application/x-www-form-urlencoded',
                        }

        xl = pd.ExcelFile(self.input_file)
        xl_content = xl.parse('Sheet1')
        self.sku_list = pd.Series.tolist(xl_content['SKU'])
        self.asin_list = pd.Series.tolist(xl_content['ASIN'])

    def start_requests(self):

        start_url = self.START_URL
        yield scrapy.Request(url=start_url, callback=self.login)

    def login(self, response):
        view_state = response.xpath("//input[@id='__VIEWSTATE']/@value").extract()[0]
        payload = {
            '__VIEWSTATE': view_state,
            'p$lt$zoneContent$pageplaceholder$p$lt$zoneLeft$usercontrol$userControlElem$txtUsername': self.USERNAME,
            'p$lt$zoneContent$pageplaceholder$p$lt$zoneLeft$usercontrol$userControlElem$txtPassword': self.PASSWORD,
            'lng': 'en-US',
            '__VIEWSTATEGENERATOR': 'A5343185',
            'manScript_HiddenField': '',
            'p$lt$zoneContent$pageplaceholder$p$lt$zoneLeft$usercontrol$userControlElem$ImgBtnLogin.x': '10',
            'p$lt$zoneContent$pageplaceholder$p$lt$zoneLeft$usercontrol$userControlElem$ImgBtnLogin.y': '5',
            '__EVENTARGUMENT': '',
            '__EVENTTARGET': '',

        }
        yield Request(url=self.LOGIN_URL,
                      callback=self.parse_pages,
                      headers=self.headers,
                      dont_filter=True,
                      method="POST",
                      body=urllib.urlencode(payload)
                      )

    def parse_pages(self, response):

        row_numbers = len(self.sku_list)
        for index in range(0, row_numbers - 1):
            response.meta['asin'] = self.asin_list[index]
            sku = self.sku_list[index]
            response.meta['sku'] = sku

            page_url = 'https://www.amazon.com/gp/offer-listing/{}'.format(sku)
            yield scrapy.Request(url=page_url, callback=self.parse_product,
                                 dont_filter=True, meta=response.meta)

    def parse_product(self, response):

        li_elements = response.xpath('//div[@id="olpOfferList"]//div[@class="a-row a-spacing-mini olpOffer"]')
        if li_elements != []:
            for li_element in li_elements:
                prod_item = SiteProductItem()
                qty = self._parse_qty(li_element)

                prod_item['SKU'] = response.meta['sku']
                prod_item['ASIN'] = response.meta['asin']
                prod_item['Qty'] = qty

                yield prod_item

    @staticmethod
    def _parse_qty(li_element):
        assert_available = li_element.xpath('.//div[@class="a-column a-span2 olpPriceColumn"]'
                                         '/span[@class="a-size-large a-color-price olpOfferPrice a-text-bold"]'
                                         '/text()').extract()
        qty = ''
        if assert_available:
            qty = str(assert_available[0].strip())
        return qty


