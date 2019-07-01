import scrapy
import re
import time


from scrapy.linkextractors import LinkExtractor
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.http import Request, HtmlResponse

from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from scrapy.exceptions import CloseSpider

class GameItem(scrapy.Item):
    name = scrapy.Field()
    release_date = scrapy.Field()
    app_id = scrapy.Field()
    positive_reviews = scrapy.Field()
    total_reviews = scrapy.Field()
    developer = scrapy.Field()
    genres = scrapy.Field()

class GamesSpider(CrawlSpider):

    def __init__(self, *a,**kw):
        super(GamesSpider, self).__init__(*a,**kw)
        assert 'limit' in kw.keys(), 'Please pass items limit'
        limit = kw['limit']

    name = "games"
    # start_urls = ['https://store.steampowered.com/search/?sort_by=Reviews_DESC']
    start_urls = ['https://store.steampowered.com/search/?sort_by=Relevance_DESC']
    allowed_domains = ['steampowered.com']
    # css selector to get all links on starting page
    # response.css("#search_result_container a::attr(href)").getall()

    items_crawled = 0

    rules = [
        Rule(
            LinkExtractor(
                allow='/app/(\d+)/',
                restrict_css='#search_result_container'),
            callback='parse_game_info'),
        Rule(
            LinkExtractor(
                allow='page=(\d+)',
                restrict_css='.search_pagination_right'))]

    def output_format(self, name, date, pos_rev_count, rev_count, developer, gen):
        self.items_crawled +=1
        item = GameItem()
        item['name'] = name
        item['release_date'] = date
        item['app_id'] = self.id
        item['positive_reviews'] = pos_rev_count
        item['total_reviews'] = rev_count
        item['developer'] = developer
        item['genres'] = gen
        return item

    def parse_game_info(self, response):
        if self.items_crawled >= int(self.limit):
            raise CloseSpider("Scraped requested amount of items")

        try:
            self.id = re.findall('/app/(.*?)/', response.url)[-1]
        except:
            self.id = ''

        if '/agecheck/app' in response.url:
            print(f'\nAgecheck toggled for {response.url}\n ')
            # pass
            yield self.toogle_agecheck(response)

        else:
            yield self.normal_parse(response)

    def normal_parse(self, response):
        name = response.css("div.apphub_AppName::text").get()
        date = response.css("div.date::text").get()
        developer = response.css("#developers_list > a::text").get()

        rev_count = response.xpath("""//*[@id="game_highlights"]""").get()

        # genres search
        try:
            gen = re.findall("(.*?)</a>", rev_count)
            gen = [g.split("\t\t\t\t\t\t\t\t\t\t\t\t")[1] for g in gen[4:] if len(
                g.split("\t\t\t\t\t\t\t\t\t\t\t\t")) > 1]
        except:
            gen = 'No genres provided'

        # reviews amount search
        try:
            rev_count = rev_count.split(
                'data-tooltip-html="')[-1].split("user reviews for this")[0].split("%")
            pos_rev_count = int(rev_count[0])
            rev_count = rev_count[1].split(" ")[-2]
            rev_count = rev_count.replace(
                ",", "")  # chage "11,22" to "1122"
            rev_count = int(rev_count)
            pos_rev_count = int(pos_rev_count * rev_count / 100)
        except:
            print("Not enough reviews to gather data for reviews amount")
            rev_count = "Not enough reviews to get score"
            pos_rev_count = "Not enough reviews to get score"

        return self.output_format(name, date, pos_rev_count, rev_count, developer, gen)

    def toogle_agecheck(self, response):
        delay = 10
        url = response.url

        # define browser options, namely launching in background

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--lang=en")

        d = webdriver.Chrome(chrome_options=chrome_options)  # launch browser
        d.get(url)

        # pass the agecheck form selecting year to 1996
        try:
            select = Select(d.find_element_by_name("ageYear"))
            select.select_by_visible_text("1996")
            d.find_element_by_xpath(
                """//*[@id="app_agegate"]/div[1]/div[4]/a[1]""").click()
            myElem = WebDriverWait(d, delay).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.date")))
        except TimeoutException:
            print(f'Timed out waiting for age check in {response.url}')

        developer = d.find_element_by_xpath(
            """//*[@id="developers_list"]/a""").text

        # date

        try:
            date = d.find_element_by_css_selector("div.date").text
        except:
            date = 'No date provided'

        # name

        try:
            name = d.find_element_by_css_selector("div.apphub_AppName").text
        except:
            name = "No name provided"

        # reviews count

        try:
            rev_count = d.find_elements_by_xpath(
                """//div[@class="user_reviews_summary_row"]""")[-1].get_attribute("data-tooltip-html")
            rev_count = rev_count.split("user reviews for this")[0].split("%")
            pos_rev_count = int(rev_count[0])  # percentage
            rev_count = rev_count[1].split(" ")[-2]
            rev_count = rev_count.replace(",", "")  # chage "11,22" to "1122"
            rev_count = int(rev_count)
            pos_rev_count = int(pos_rev_count * rev_count / 100)

        except:
            print("Not enough reviews to gather data for reviews amount")
            rev_count = "Not enough reviews to get score"
            pos_rev_count = "Not enough reviews to get score"

        # genres search

        try:
            gen = d.find_elements_by_xpath(
                """//div[@class="glance_tags popular_tags"]/a""")
            gen = [g.text for g in gen if len(g.text) > 0]
        except:
            gen = "No genres provided"

        d.quit()

        return self.output_format(name, date, pos_rev_count, rev_count, developer, gen)
