Steam crawler for games' info and thier reviews' content made as a project for a university course. Some part was inspired by @prncc steam-scraper (https://github.com/prncc/steam-scraper) 

Please ensure that you have installed the requirements. For selenium, you have to download and set up an appropriate drivers for Chrome (http://chromedriver.chromium.org/getting-started) because scrapper uses this browser in selenium.

## Some important tips:
* When reading obtained results (eg games.csv) make sure that you use only comma (",") as a separator between fields as some titles may use semicolons in thier title name.
* When using run_crawler.py please note that -r option is an amount of reviews in tens; it is due to the fact that reviews are displayed in tens with every scroll
* Some games do not have amount of reviews on the game (title) page but still it is possible to scrape some reviews, however it may occur that there are not any HELPFUL reviews so the output json file will be empty
* Reviews are saved as "review_id.json" because game name can contain characters that are not supported by system encoding (eg chineese characters). Also reviews are stored in json because they consist purely of text. Their scheme looks as follows {"helpful": amount_of_marked_as_helpful, "rev_text"}.

To use this crawler to get 200 games with 100 reviews per each and store them in "output" directory simply run : python run_crawler.py -g 200 -r 10
This behaviour can be modified by changing names in the "run_crawler" script.
