# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewscrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    news_title = scrapy.Field()
    news_keyword = scrapy.Field()
    news_section = scrapy.Field()
    author = scrapy.Field()
    publication_date = scrapy.Field()
    article = scrapy.Field()
    article_url = scrapy.Field()
