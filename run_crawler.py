import scrapy, argparse, time, os, shutil

from scrapy.utils.project import get_project_settings
from helper_funcs import run_rev_spider, run_game_spider, get_start_values

parser = argparse.ArgumentParser(description='Steam scraper params')
parser.add_argument('-g', '--games_limit', help="Number of scraped games",
                        type=int, default=10)
parser.add_argument('-r', '--rev_limit', help="Number of 10s scraped reviews for each game (scraper gets reviews as multiplicity of 10)",
                        type=int, default=1)

args = parser.parse_args()
games_limit = args.games_limit
rev_limit = args.rev_limit

print(f"Scraping {games_limit} games and for each {10*rev_limit} reviews")

output_dir = 'output/'
ext_game = 'csv'
ext_rev = 'json'
name = 'games'

name = output_dir + name

tic = time.time()

settings = get_project_settings()

settings.update({'FEED_FORMAT': ext_game})
settings.update({'FEED_URI': name + '.' + ext_game})
# settings.update({'CLOSESPIDER_ITEMCOUNT': 3})

if os.path.isfile(name+"."+ext_game):
    os.remove(name+"."+ext_game)
    shutil.rmtree(output_dir+'reviews')


run_game_spider(games_limit, settings)
print(f'\nGame info downloaded to file {name}.{ext_game}\n')

ids, names = get_start_values(name+"."+ext_game)

for i, id in enumerate(ids):
    settings = get_project_settings()
    settings.update({'FEED_FORMAT': ext_rev})
    settings.update({'FEED_URI': output_dir+"reviews/"+str(id) + '.' + ext_rev})
    settings.update({'CLOSESPIDER_ITEMCOUNT': rev_limit})
    run_rev_spider(id, settings)
    print(f"""\nReviews info for "{names[i]}" downloaded to file {output_dir}reviews/{id}.{ext_rev}\n""")

tac = time.time()

print(f"Whole scrapping took {tac - tic} seconds")
