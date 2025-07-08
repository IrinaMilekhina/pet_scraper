import logging
from datetime import datetime, timezone

import scrapy
from scrapy.http import HtmlResponse

from items import CosmeticItem
from settings import ingredients_statistics


class CosmeticsSpider(scrapy.Spider):
    name = "cosmetics"
    start_url = "https://cosmetic.de/marken/"

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
                    url=self.start_url + f'/{category}' + f'?order=beliebtheit&p={next_page_number}',
                    callback=self.parse_category_page,
                    cb_kwargs={
                        'category': category
                    }
                )

    def parse_product_info(self, response: HtmlResponse, category: str):
        item = CosmeticItem(
            product_name=response.xpath('//h1[@class="product-detail-name"]/text()').get(),
            brand=self.extraxt_brand(response),
            ingredients=self.extract_ingredients(response),
            product_detail=self.extraxt_details(response),
            page_url=response.url,
            article_number=
            response.xpath('//span[@class="product-detail-ordernumber"]/text()').get(),
            parse_date=datetime.now(timezone.utc),
            product_category=category,
        )
        for attr, val in item.items():
            if not val or val == "":
                logging.warning(f"No value for {attr} on {response.url}")
            if isinstance(val, str):
                item[attr] = self.clear_strings(val)
                if '\n' in item[attr]:
                    logging.error(f"Need to clear {attr} on {response.url}")
        yield item

    @staticmethod
    def clear_strings(val: str) -> str:
        return " ".join(val.split())

    @staticmethod
    def extraxt_brand(response: HtmlResponse) -> str:
        brand = response.xpath('//img[@class="cms-image product-detail-manufacturer-logo"]/@title').get()
        if not brand:
            brand = response.xpath('//a[@class="cms-image-link product-detail-manufacturer-link"]/@title').get()
        return brand

    @staticmethod
    def extraxt_details(response: HtmlResponse) -> str:
        product_detail = ' '.join(
            response.xpath('//div[@class="product-detail-description-text"]//text()').getall()).strip()
        return product_detail

    @staticmethod
    def extract_ingredients(response: HtmlResponse) -> list:
        keyword = response.xpath(
            '//text()[re:test(., "(?i)Zutaten|Inhaltsstoffe|Inhaltstoffe|INGREDIENTS")]'
        ).get(default='')

        ingredients = []
        if "INGREDIENTS" in keyword.upper():
            ingredients = response.xpath(
                '//div[./b/u[contains(translate(text(), "ingredients", "INGREDIENTS"), "INGREDIENTS")]]'
                '/following-sibling::div[1]//text()'
            ).getall()
            if ingredients:
                ingredients_statistics[1] += 1
        elif any(kw in keyword for kw in ["Inhaltsstoffe", "Inhaltstoffe", "Zutaten"]):
            # First, try typical paragraph structure
            ingredients = response.xpath(
                '//p[preceding::span[contains(text(), "Inhaltsstoffe")]][1]//text()'
            ).getall()
            if ingredients:
                ingredients_statistics[2] += 1
            # If that fails, try a fallback (e.g., span-following structure)
            if not ingredients:
                ingredients_text = response.xpath(
                    '//span[. = "Inhaltsstoffe|INGREDIENTS"]/ancestor::p/following-sibling::p[1]/span/text()'
                ).get()
                if ingredients_text:
                    ingredients = [ingredients_text]
                    if ingredients:
                        ingredients_statistics[3] += 1
            if not ingredients:
                ingredients = response.xpath('//b[contains(text(), "Inhaltstoffe:")]/following-sibling::text()[1]').get()
                if ingredients:
                    ingredients_statistics[4] += 1
            if not ingredients:
                texts = response.xpath('//strong[contains(text(), "Inhaltsstoffe")]/ancestor::p//text()').getall()
                ingredients = [t.strip() for t in texts if t.strip() and "Inhaltsstoffe" not in t]
                if ingredients:
                    ingredients_statistics[5] += 1
            if not ingredients:
                texts = response.xpath('//p[contains(text(), "Inhaltsstoffe")]//text()').getall()
                ingredients = [t.strip() for t in texts if t.strip() and "Inhaltsstoffe" not in t]
                if ingredients:
                    ingredients_statistics[6] += 1
        if not ingredients:
            ingredients_text = response.xpath(
                '//*[contains(text(),"Aqua") and contains(text(),"Parfum")]/text()'
            ).get()
            if ingredients_text:
                ingredients = [ingredients_text]
                if ingredients:
                    ingredients_statistics[7] += 1
        if not ingredients:
            ingredients_text = response.xpath(
                '//*[contains(text(),"Aqua")]/text()'
            ).get()
            if ingredients_text:
                ingredients = [ingredients_text]
                if ingredients:
                    ingredients_statistics[8] += 1
        if not ingredients:
            ingredients_statistics["no"] += 1
            return []
        # Final cleanup
        if isinstance(ingredients, list):
            flat_text = ' '.join(ingredients)
        else:
            flat_text = ingredients or ''

        return [x.strip() for x in flat_text.split(',') if x.strip()]
