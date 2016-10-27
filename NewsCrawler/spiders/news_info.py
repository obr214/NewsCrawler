# -*- coding: utf-8 -*-
import re
import scrapy
import itertools
import logging
from urlparse import urlparse, parse_qs
from scrapy.spiders import CrawlSpider
from scrapy.utils.log import configure_logging
from NewsCrawler.items import NewscrawlerItem


class NewsInfoSpider(CrawlSpider):
    name = 'news_info'
    allowed_domains = ['activo.eluniversal.com.mx', 'archivo.eluniversal.com.mx', 'eluniversal.com.mx']

    def __init__(self):
        CrawlSpider.__init__(self)
        configure_logging({'LOG_FORMAT': '%(asctime)s %(levelname)s: %(message)s',
                           'LOG_FILE': 'logs/news_info_errors.log',
                           'LOG_LEVEL': logging.ERROR})

    def start_requests(self):
        base_url = 'http://activo.eluniversal.com.mx/historico/search/index.php?q=%s&editor=&tipo_contenido=texto&seccion=%s'

        keywords = ['asesinato', 'secuestro', 'extorsion', 'asalto', 'narcotrafico']
        sections = ['Naci%C3%B3n', 'Metr%C3%B3poli', 'Estados']

        starting_urls = [base_url % (a[0], a[1]) for a in itertools.product(keywords, sections)]

        for url in starting_urls:
            yield scrapy.Request(url, self.get_number_pages)

    def get_number_pages(self, response):
        # Gets the pages
        try:
            response_url = response.url
            results = response.css('div#BuscarBox > span#ContadorBusqueda::text').extract()[0]

            n = re.match("^\[(\d+) \D+\]$", results)

            if n:
                num_articles = int(n.group(1))
                start_range = range(0, num_articles, 20)
                #start_range = range(0, 20, 20)

                for i, start_r in enumerate(start_range):
                    page_string = '&start=%s&page=%s' % (start_r, i+1)
                    new_url = response_url + page_string

                    yield scrapy.Request(new_url, callback=self.get_news_links)

        except IndexError:
            print "Element Not Found"
        except:
            print "Error in get_number_pages()"

    def get_news_links(self, response):

        refer_link = response.request.headers.get('Referer', None)
        keyword = []
        section = []
        if refer_link:
            parameters_dict = parse_qs(urlparse(refer_link).query)
            keyword = parameters_dict.get('q', [])
            section = parameters_dict.get('seccion', [])

        articles_urls = response.css('div.moduloNoticia > div.ModuloDer > div.HeadNota > a::attr("href")')

        for href in articles_urls:
            art_url = href.extract()
            request = scrapy.Request(art_url, callback=self.parse_article)

            try:
                request.meta['keyword'] = keyword[0]
                request.meta['section'] = section[0]
            except IndexError:
                request.meta['keyword'] = ''
                request.meta['section'] = ''

            yield request

    def parse_article(self, response):

        news_item = NewscrawlerItem()

        note_content = response.css('div#noteContent')[0]

        # Gets the News Title
        try:
            title_container = note_content.css('h1.noteTitle::text').extract()[0]
            news_item['news_title'] = title_container.encode('utf8')
        except IndexError:
            news_item['news_title'] = ''

        # Sets the Keyword
        news_item['news_keyword'] = response.meta['keyword']

        # Sets the Section
        news_item['news_section'] = response.meta['section']

        # Gets the Author
        try:
            author_container = note_content.css('div#data-content > div#authorNote::text').extract()[0]
            #news_item['author'] = str(unidecode(author_container)).strip()
            news_item['author'] = author_container.encode('utf8')
        except IndexError:
            try:
                author_container = note_content.css('div.noteText > span#authorNote::text').extract()[0]
                news_item['author'] = author_container.encode('utf8')
            except IndexError:
                news_item['author'] = ''

        # Gets the publication Date
        try:
            p_date_container = note_content.css('div#data-content > div#dateNote > span#datePlace::text').extract()[0]
            # p_date_text = str(unidecode(p_date_container)).strip()
            news_item['publication_date'] = p_date_container.encode('utf8')
        except IndexError:
            try:
                p_date_container = note_content.css('div.noteText > span.noteInfo::text').extract()[0]
                #p_date_text = str(unidecode(p_date_container)).strip()
                news_item['publication_date'] = p_date_container.encode('utf8')
            except IndexError:
                news_item['publication_date'] = ''

        try:
            paragraph_text = []
            paragraphs = note_content.css('div.noteText > p > span#contentNote > p::text')
            for paragraph in paragraphs:
                # paragraph_pre_text = str(unidecode(paragraph.extract())).strip()
                paragraph_pre_text = paragraph.extract().encode('utf8')
                paragraph_text.append(paragraph_pre_text)

            pre_article = ' '.join(paragraph_text)
            #article = str(unidecode(pre_article)).strip()
            article = pre_article

            news_item['article'] = article
        except IndexError:
            news_item['article'] = ''

        # Articles URL
        news_item['article_url'] = response.url

        return news_item





