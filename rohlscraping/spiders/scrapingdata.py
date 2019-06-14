import scrapy
import re
import csv


class SiteProductItem(scrapy.Item):
    SKU = scrapy.Field()
    ASIN = scrapy.Field()
    Available_units = scrapy.Field()
    Price = scrapy.Field()
    Seller_information = scrapy.Field()


class Amazon(scrapy.Spider):
    name = "scrapingdata"
    allowed_domains = ['www.amazon.com']
    DOMAIN_URL = 'https://www.amazon.com'

    def __init__(self, **kwargs):

        # self.input_file = kwargs['input_file']
        self.input_file = 'rohl.xlsx'
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                                      "Chrome/57.0.2987.133 Safari/537.36"}

        with open(self.input_file, 'r+') as csvfile:
            reader = csv.reader(csvfile)
            self.sku_list = []
            self.asin_list = []
            self.available_units_list = []
            for row_index, row in enumerate(reader):
                if row_index != 0:
                    self.sku_list.append(row[0])
                    self.asin_list.append(row[2])
                    self.available_units_list.append(row[6])

    def start_requests(self):

        start_url = self.DOMAIN_URL
        yield scrapy.Request(url=start_url, callback=self.parse_pages)

    def parse_pages(self, response):

        row_numbers = len(self.asin_list)
        for index in range(0, row_numbers - 1):
            response.meta['sku'] = self.sku_list[index]
            asin = self.asin_list[index]
            response.meta['asin'] = asin
            response.meta['available_units'] = self.available_units_list[index]

            page_url = 'https://www.amazon.com/gp/offer-listing/{}'.format(asin)
            yield scrapy.Request(url=page_url, callback=self.parse_product,
                                 dont_filter=True, meta=response.meta)

    def parse_product(self, response):

        li_elements = response.xpath('//div[@id="olpOfferList"]//div[@class="a-row a-spacing-mini olpOffer"]')
        if li_elements != []:
            for li_element in li_elements:
                prod_item = SiteProductItem()
                price = self._parse_price(li_element)
                seller_information = self._parse_seller_information(li_element)

                prod_item['SKU'] = response.meta['sku']
                prod_item['ASIN'] = response.meta['asin']
                prod_item['Available_units'] = response.meta['available_units']
                prod_item['Price'] = price
                prod_item['Seller_information'] = seller_information

                yield prod_item

    @staticmethod
    def _parse_price(li_element):
        assert_prices = li_element.xpath('.//div[@class="a-column a-span2 olpPriceColumn"]'
                                         '/span[@class="a-size-large a-color-price olpOfferPrice a-text-bold"]'
                                         '/text()').extract()
        price = ''
        if assert_prices:
            price = str(assert_prices[0].strip())
        return price

    @staticmethod
    def _parse_seller_information(li_element):
        assert_seller_info_titles = li_element.xpath(
            './/div[@class="a-column a-span2 olpSellerColumn"]/h3//a/text()').extract()
        seller_title = ''
        if assert_seller_info_titles:
            seller_title = str(assert_seller_info_titles[0].strip())
        return str(seller_title)
