# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CosmeticItem(scrapy.Item):
    product_name = scrapy.Field()
    brand = scrapy.Field()
    ingredients = scrapy.Field()
    product_category = scrapy.Field()
    product_detail = scrapy.Field()
    page_url = scrapy.Field()
    article_number = scrapy.Field()
    parse_date = scrapy.Field()
