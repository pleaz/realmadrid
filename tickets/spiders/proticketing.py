# -*- coding: utf-8 -*-
from scrapy_splash import SplashRequest
import scrapy
import json
import logging


class ProticketingSpider(scrapy.Spider):
    name = 'proticketing'
    allowed_domains = ['proticketing.com']
    event = None
    seats = None
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'TELNETCONSOLE_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'upgrade-insecure-requests': '1',
            'OB-channel': 'realmadrid_tickets',
            'OB-language': 'es_ES'
        },
        'SPLASH_URL': 'http://0.0.0.0:8050',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810
        },
        'SPLASH_COOKIES_DEBUG': False,
        'COOKIES_DEBUG': False
    }

    def start_requests(self):
        yield scrapy.Request('https://proticketing.com/api/v1/venues/' + self.event)

    def parse(self, response):
        sectors = json.loads(response.body_as_unicode())
        for sector in sectors['linkList']:
            if sector['availability'] > 0:
                try:
                    seats_ar
                except NameError:
                    yield scrapy.Request(
                        response.urljoin(
                            '' + 'https://proticketing.com/api/v1/venues/' + self.event + '?actualView=' + str(
                                sector['target'])),
                        callback=self.parse_sector
                    )

    def parse_sector(self, response):
        sectors = json.loads(response.body_as_unicode())
        for sector in sectors['linkList']:
            if sector['availability'] > 0:
                try:
                    seats_ar
                except NameError:
                    yield scrapy.Request(
                        response.urljoin(
                            '' + 'https://proticketing.com/api/v1/venues/' + self.event + '?actualView=' + str(
                                sector['target'])),
                        callback=self.parse_seats,
                    )

    def parse_seats(self, response):
        seats = json.loads(response.body_as_unicode())['svgSeatListToSend']
        for index, seat in enumerate(seats):
            column = int(seat['column'])
            row = int(seat['row'])
            # if column == 17 and row == 7:
            global cont
            cont = True
            items = []
            if column % 2 == 0:
                even = True
            else:
                even = False
            for x in range(1, int(self.seats)+1):
                prev = seats[index-(x-1)]
                if prev is None:
                    # logging.warning(1)
                    cont = False
                    break
                if prev['status'] != 1:
                    # logging.warning(2)
                    cont = False
                    break
                if int(prev['row']) != row:
                    # logging.warning(3)
                    cont = False
                    break
                if (int(prev['column']) % 2 == 0) != even:
                    # logging.warning(4)
                    cont = False
                    break
                items.append(prev)

            if cont is False:
                continue
            else:
                # logging.warning(items)
                # yield {item['id']: item for item in items}
                global seats_ar
                seats_ar = []
                for it in items:
                    seats_ar.append(it.get('databaseId'))
                script = """
                            function main(splash)
                                assert(splash:go(splash.args.url))
                                return {
                                    cookies = splash:get_cookies()
                                }
                            end
                        """
                yield SplashRequest('https://proticketing.com/realmadrid_tickets/en_US/entradas/evento/14889/session/' +
                                    self.event + '/select',
                                    self.parse_result,
                                    endpoint='execute',
                                    args={'lua_source': script})
                break

    def parse_result(self, response):
        global session
        for cookie in response.cookiejar:
            if cookie.name == 'JSESSIONID':
                session = cookie.value
        req = scrapy.Request('https://proticketing.com/api/v2/cart/seats',
                             method='POST',
                             body=json.dumps({"sessionId": self.event, "seats": seats_ar}),
                             headers={'Content-Type': 'application/json',
                                      'OB-channel': 'realmadrid_tickets',
                                      'OB-language': 'es_ES'},
                             callback=self.final)
        req.cookies['JSESSIONID'] = session
        yield req

    @staticmethod
    def final(response):
        answer = json.loads(response.body_as_unicode())
        if 'cart' in answer:
            yield dict({'JSESSIONID': session})
        else:
            logging.warning(response)
