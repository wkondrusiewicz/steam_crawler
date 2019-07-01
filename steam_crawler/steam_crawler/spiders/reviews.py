import scrapy
from scrapy.http import FormRequest, Request, Response

from selenium import webdriver
from selenium.webdriver.support.ui import Select ,WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import time, re

def strip_review_text(data, beg='\r\n\t\t\t\t\t\t\t\t\t\t\t\t', end='\t\t\t</div>'):
    data = data.split(beg)[1].split(end)[0]
    p  = re.compile(r'<.*?>')
    data = p.sub('',data)
    data = data.encode('ascii','ignore').decode('utf-8')
    return data

def strip_review_text_with_selenium(data):
    data = data.encode("ascii","ignore").decode("utf-8")
    data = "".join(data.split("\n")[1:])
    return data

def strip_helpful(data):
    data = data.split(" people found ")[0]
    return data


class ReviewsSpider(scrapy.Spider):
    name = "reviews"

    #overriding __init__ to add possibility to pass id as an argument

    def __init__(self, *a,**kw):
        super(ReviewsSpider, self).__init__(*a,**kw)
        assert 'id' in kw.keys(), 'Please pass id'
        id = kw['id']
        path ='https://steamcommunity.com/app/'+str(id) +'/reviews/?browsefilter=toprated&p=1'
        self.start_urls = [path]

    def parse(self, response):

        if response.xpath("//*[contains(text(), 'View Page')]"):
            print('\n\t\tAdult content detected\n')
            yield self.parse_with_adult_content(response)
        else:
            rev_text = response.css("div .apphub_CardTextContent").getall()

            rev_text = [strip_review_text(rt) for rt in rev_text] #striped reviews text

            helpful = response.css("div.found_helpful").getall()
            helpful = [strip_helpful(strip_review_text(h,beg='\r\n\t\t\t\t', end='\t\t\t')) for h in helpful] #striped "marked as helpful" reviews

            revs_with_help = [{"helpful": h, "rev_text" : rt} for (h,rt) in zip(helpful, rev_text)]

            #to handle infinite scrolling we have to fill up a form
            yield {"reviews": revs_with_help, "reviews_amount": len(rev_text)}

            form = response.xpath('//form[contains(@id,"MoreContentForm")]')

            if form:
                url = form.xpath('@action').get() #CHANGED EXTRACT TO GET
                names = form.xpath('input/@name').getall()
                values = form.xpath('input/@value').getall()

                formdata = dict(zip(names, values))
                yield FormRequest(
                url=url,
                method='GET',
                formdata=formdata,
                callback=self.parse,
                )


    def parse_with_adult_content(self, response):

        chrome_options = Options()
        chrome_options.headless = True
        chrome_options.add_argument("--lang=en")

        d = webdriver.Chrome(chrome_options=chrome_options)

        d.get(response.url)
        d.find_element_by_xpath("""//*[@id="age_gate_btn_continue"]/span""").click() #click View Page

        #after clicking "View Page" proceed to reviews
        new_url = response.url+'/reviews/?browsefilter=toprated&p=1'
        d.get(new_url)

        #loop is used to scroll many times
        for i in range(int(self.settings.attributes['CLOSESPIDER_ITEMCOUNT'].value)-1):
            d.execute_script("window.scrollTo(0, document.body.scrollHeight);") #scroll to bottom to load up more reviews
            time.sleep(8) #wait for page to load


        rev_text = d.find_elements_by_css_selector("div .apphub_CardTextContent") #raw reviews text
        helpful = d.find_elements_by_css_selector("div.found_helpful") #raw "marked as helpful" content

        rev_text = [strip_review_text_with_selenium(rt.text) for rt in rev_text]
        helpful = [strip_helpful(h.text) for h in helpful]

        revs_with_help = [{"helpful": h, "rev_text" : rt} for (h, rt) in zip(helpful, rev_text)]

        d.quit()
        return {"reviews": revs_with_help, "reviews_amount": len(rev_text)}
