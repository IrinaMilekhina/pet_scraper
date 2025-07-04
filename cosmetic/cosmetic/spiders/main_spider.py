from datetime import datetime, timezone
from pathlib import Path

import scrapy
import logging
from scrapy.http import HtmlResponse

from items import CosmeticItem


class CosmeticsSpider(scrapy.Spider):
    name = "cosmetics"
    start_url = "https://cosmetic.de/marken/"
    product_counter = 0
    min_url = "https://cosmetic.de/"

    async def start(self):
        yield scrapy.Request(url=self.start_url, callback=self.parse)

    def parse(self, response: HtmlResponse):
        """
        Parse start page to get all categories links
        """
        categories = response.css('li.category-navigation-entry a::attr(href)').getall()
        categories.append(self.start_url)
        logging.info(f"Found {len(categories)} categories pages")
        for category in categories:
            yield scrapy.Request(url=category,
                                 callback=self.parse_category_page,
                                 cb_kwargs={
                                     'category': category.rsplit('/')[-1] if category.rsplit('/')[-1] else
                                     category.rsplit('/')[-2]
                                 }
                                 )

    def parse_category_page(self, response: HtmlResponse, category: str):
        logging.info(f"category: {category}")
        logging.info(f"parse_category_page on url {response.url}")
        # collect all products links
        products = response.css('div.product-info a::attr(href)').getall()
        for product in products:
            yield scrapy.Request(
                url=product,
                callback=self.parse_product_info,
                cb_kwargs={
                    'category': category
                }
            )
        if not products:
            logging.info(f"No products on page {response.url}")
        else:
            # collect last page number
            next_page_value = response.xpath('//*[@id="p-next-bottom"]/@value').get()
            next_page_number = int(next_page_value) if next_page_value is not None else None
            if next_page_number:
                yield scrapy.Request(
                    url=self.min_url + f'/{category}' + f'?order=beliebtheit&p={next_page_number}',
                    callback=self.parse_category_page,
                    cb_kwargs={
                        'category': category
                    }
                )

    def parse_product_info(self, response: HtmlResponse, category: str):
        self.product_counter += 1
        logging.info(f"parsing product {self.product_counter} link: {response.url}")
        item = CosmeticItem(
            product_name=response.xpath('//h1[@class="product-detail-name"]/text()').get(),
            brand=response.xpath('//img[@class="cms-image product-detail-manufacturer-logo"]/@title').get(),

            ingredients=self.extract_ingredients(response),
            product_detail=' '.join(
                response.xpath('//div[@class="product-detail-description-text"]//p//text()').getall()).strip(),
            page_url=response.url,
            article_number=
            response.xpath('//span[@class="product-detail-ordernumber"]/text()').get(),
            parse_date=datetime.now(timezone.utc),
            product_category=category,
        )
        for attr, val in item.items():
            if not val or val == "":
                logging.error(f"No value for {attr} on {response.url}")
            if isinstance(val, str):
                item[attr] = self.clear_strings(val)
                if '\n' in item[attr]:
                    logging.error(f"Need to clear {attr} on {response.url}")
        logging.info(f"GOT ITEM\n{item}")
        yield item

    @staticmethod
    def clear_strings(val: str) -> str:
        return " ".join(val.split())

    @staticmethod
    def extract_ingredients(response: HtmlResponse) -> list:
        ingredients = response.xpath(
            '//span[. = "Inhaltsstoffe"]/ancestor::p/following-sibling::p[1]/span/text()').get()
        if not ingredients:
            ingredients = response.xpath('//text()[re:test(., "Zutaten|Inhaltsstoffe")]').get(default='')
        if not ingredients:
            ingredients = response.xpath(
                '//*[contains(text(),"Aqua") and contains(text(),"Parfum")]/text()'
            ).get()
        if not ingredients:
            ingredients = response.xpath(
                '//*[contains(text(),"Aqua")]/text()'
            ).get()
        if ingredients:
            return [x.strip() for x in ingredients.split(',')]
        logging.error(f"No ingredients found for {response.url}")
        return []
