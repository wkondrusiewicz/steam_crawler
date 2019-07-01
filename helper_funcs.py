import pandas as pd

from steam_crawler.steam_crawler.spiders import games, reviews

from scrapy.crawler import CrawlerProcess, CrawlerRunner, Crawler
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings
from twisted.internet import reactor
from multiprocessing import Process, Queue

def get_start_values(path):
    df = pd.read_csv(path)
    ids = df.app_id.values
    names = df.name.values
    return ids, names


def run_rev_spider(id,settings):
    def f(q):
        try:
            runner = CrawlerRunner(settings)
            spider = reviews.ReviewsSpider(id=id)
            deferred = runner.crawl(spider, id=id)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)
    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result


def run_game_spider(limit, settings):
    def f(q):
        try:
            runner = CrawlerRunner(settings)
            spider = games.GamesSpider(limit=limit)
            deferred = runner.crawl(spider, limit=limit)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)
    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result
