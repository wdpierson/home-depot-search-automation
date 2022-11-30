import scrapy
import os
import json
import re


class HomeDepotSpider(scrapy.Spider):
    name = "home_depot"
    base_url = 'https://www.homedepot.com'

    def __init__(self, search_items=None, *args, **kwargs):
        super(HomeDepotSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://www.homedepot.com/s/' + arg.replace('/', '%2f') for arg in search_items.split(',')]
        print(str(self.start_urls))

        #  Clear out any data in items.json before starting
        with open("C:\\Users\\" + os.environ["username"] + "\\Desktop\\items.json", mode='a+') as f:
            f.seek(0)
            f.truncate()

    def parse(self, response):
        search_item = str(response.url)[str(response.url).rfind('/') + 1:]  # Everything after last /
        search_item = search_item.replace('%2f', '/').replace('%20', ' ')  # Decode UTF-8 (str.decode doesn't work)

        if '/p/' in str(response.url):  # Certain items take you directly to product.
            search_item = response.request.meta['redirect_urls'][0]
            search_item = search_item[search_item.rfind('/') + 1:]

        result = [{'search_item': search_item}]  # Concurrency -> can't guarantee order -> use this to label results

        for i in range(1, 4):
            xpath_str = '//section[@id="browse-search-pods-1"]/div[' + str(i) + ']'

            if '/p/' in str(response.url):  # Certain items take you directly to product
                item_name = response.xpath('//h1[@class="product-details__title"]/text()').get()
                item_price = response.xpath('//div[@class="price-format__large price-format__main-price"]/span/text()').getall()
                item_uom = None  # TODO figure out UOM for links that go directly to item (need an example...)
            else:   # Most searches should land here, a search result screen with multiple items
                item_name = " ".join(response.xpath(xpath_str + '//h3/span/text()').getall())
                item_price = response.xpath(xpath_str + '//div[@class=\'price\']//span/text()').getall()
                item_uom = response.xpath(xpath_str + '//span[@class=\'price__uom\']/text()').get()

            item_price = "".join(item_price[:2] + ["."] + item_price[2:]).strip()
            if item_uom is not None:  # Divide price by number in package (round to 2 decimals)
                if "\u00a2." in item_price:  # Remove cent
                    item_price = item_price[:len(item_price) - 2]
                package_size = re.search(r'\((\d+)-', str(item_name))
                if package_size:
                    item_price = "$" + str(round(float(item_price[1:]) / float(package_size.group(1)), 2))

            result.append({
                'result_num': i,
                'item_uom': item_uom,
                'item_name': item_name,
                'item_price': item_price,
                'debug': (response.xpath('//div[@id="header"]//div[@class="MyStore__store"]').get())
            })

        with open("C:\\Users\\" + os.environ["username"] + "\\Desktop\\items.json", mode='a+') as f:
            json_object = json.dumps(result, indent=4)
            f.writelines(json_object)

