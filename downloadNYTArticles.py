import requests, bs4, os, errno, time, datetime, re

def download_page(url):
    try:
        page = requests.get(url, timeout=10.0)
    except requests.exceptions.Timeout:
        print('Timeout\n')
        return None
    except requests.exceptions.ConnectionError:
        print('ConnectionError\n')
        time.sleep(120)
        return None
    except requests.exceptions.HTTPError:
        print('HTTPError\n')
        return None
    except requests.exceptions.TooManyRedirects:
        print('TooManyRedirects\n')
        return None
    else:
        return page


def main():

    max_attempts = 10

    r_unwanted = re.compile('[\n\t\r]')

    urls_to_articles = []

    if not os.path.exists('articles/'):
        try:
            os.makedirs('articles/')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # STEP 1. BUILD THE LIST OF URLS TO ARTICLES
    if not os.path.exists('urls_to_articles.txt'):

        for year in range(2010, datetime.datetime.now().year + 1):

            catalog_page_by_years = 'http://spiderbites.nytimes.com/free_%s/index.html&#39; % (year)'

            links_to_parts = []

            attempts = 0

            print('Year: ', year)

            with open('logfile.log', 'w') as f:
                f.write('STEP 1. Year: ' + str(year) + '\n')

            catalog_page = download_page(catalog_page_by_years)

            while not (catalog_page or attempts > max_attempts):
                catalog_page = download_page(catalog_page_by_years)
                attempts += 1

            if catalog_page:
                catalog_page = bs4.BeautifulSoup(catalog_page.text, "lxml")
                if year > 1995:
                    links_to_parts.append(['http://spiderbites.nytimes.com%s&#39; % (el.get('href'))' for el in catalog_page.select('body > div > div > div > div > div > div > ul > li > a')''])
                else:
                    links_to_parts.append(['http://spiderbites.nytimes.com/free_%s/%s&#39; % (year, el.get('href')) for el in catalog_page.select('body > div > div > div > div > div > div > ul > li > a')'])

            links_to_parts = [item for sublist in links_to_parts for item in sublist]

            for link_to_parts in links_to_parts:

                attempts = 0

                parts_page = download_page(link_to_parts)

                while not (parts_page or attempts > max_attempts):
                    parts_page = download_page(link_to_parts)
                    attempts += 1

                if parts_page:
                    parts_page = bs4.BeautifulSoup(parts_page.text, "lxml")
                    urls_to_articles.append([el.get('href') for el in parts_page.select('body > div > div > div > div > ul > li > a')])

        urls_to_articles = [item for sublist in urls_to_articles for item in sublist]

        # Backing up the list of URLs
        with open('urls_to_articles.txt', 'w') as output:
            for u in urls_to_articles:
                output.write('%s\n' % (u.strip()))

    # STEP 2. DOWNLOAD ARTICLES
    # If, at some point, Step 2 is interrupted due to unforeseen
    # circumstances (power outage, loss of internet connection), replace the number
    # (value of the variable url_num) below with the one you will find in the logfile.log
    url_num = 0

    if os.path.exists('urls_to_articles.txt') and len(urls_to_articles) == 0:
        with open('urls_to_articles.txt', 'r') as f:
            urls_to_articles = f.read().splitlines()

    print('Number of articles that are about to be downloaded: ', len(urls_to_articles))

    for url in urls_to_articles[url_num:]:

        if len(url) > 34:

            attempts = 0

            if url_num % 1000 == 0:

                print('Downloading article #', url_num, ' from ', url)

                with open('logfile.log', 'w') as f:
                    f.write('STEP 2. Downloading article #' + str(url_num) + ' from ' + url + '\n')

            article_page = download_page(url)

            while not (article_page or attempts > max_attempts):
                article_page = download_page(url)
                attempts += 1

            if article_page:
                article_page = bs4.BeautifulSoup(article_page.text, "lxml")

                title = [el.getText() for el in article_page.find_all(class_="articleHeadline")]
                if len(title) > 0:
                    title = title[0]
                else:
                    title = [el.getText() for el in article_page.find_all(class_="headline")]

                    if len(title) > 0:
                        title = title[0]
                    else:
                        title = ""

                dateline = [el.getText() for el in article_page.find_all(class_="dateline")]
                if len(dateline) > 0:
                    dateline = dateline[0]
                else:
                    dateline = ""

                byline = [el.getText().strip() for el in article_page.find_all(class_="byline")]
                if len(byline) > 0:
                    byline = ' '.join(byline)
                else:
                    byline = ""

                body = [el.getText() for el in article_page.find_all(class_="articleBody")]
                if len(body) > 0:
                    body = '\n'.join(body)
                    body = r_unwanted.sub("", body)
                    body = re.sub(' +', ' ', body)

                    with open('articles/' + str(url_num) + url.split('/')[-1] + '.txt', 'w') as output:
                        output.write('(c) ' + str(datetime.datetime.now().year) + ' The New York Times Company\n')
                        output.write(url + '\n')
                        output.write(title + '\n')
                        output.write(dateline + '\n')
                        output.write(byline + '\n')
                        output.write('\n' + body)
                else:

                    body = [el.getText() for el in article_page.find_all(class_="story-body-text")]

                    if len(body) > 0:
                        body = '\n'.join(body)
                        body = r_unwanted.sub("", body)
                        body = re.sub(' +', ' ', body)

                        with open('articles/' + str(url_num) + url.split('/')[-1] + '.txt', 'w') as output:
                            output.write('(c) ' + str(datetime.datetime.now().year) + ' The New York Times Company\n')
                            output.write(url + '\n')
                            output.write(title + '\n')
                            output.write(dateline + '\n')
                            output.write(byline + '\n')
                            output.write('\n' + body)
        url_num += 1


if __name__ == '__main__':
    """
    The main function is called when nytimes.py is run from the command line
    """

    main()