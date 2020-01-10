import os
import pprint
from pymongo import MongoClient
import requests
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Get request object and check for status
def get_requests(url):
    """
    Parameters
    ----------

    Returns
    -------
    
    """    
    r = requests.get(url)
    try:
        r.raise_for_status()
    except Exception as exc:
        print(f'request error: {exc}')
    return r


# scrape list of city names from yelp.com/city
def scrape_cities(r):
    soup = BeautifulSoup(r.text, 'html.parser')
    ca_tag = soup.find('h4', text='CA')
    city_links = []
    for tag in ca_tag.next_sibling.children:
        city_links.append(tag.find('a').attrs['href'].split('/')[2])
    return city_links


# make "store link" scraper function
def scrape_stores(r, limit):
    all_links = [] 
    count = 0    
    while True:     
        soup = BeautifulSoup(r.text, 'html.parser')
        # find the link to the next page 
        # uniquely identify the "next" page link from all other page links: using regex on class attr
        try:
            next_link = soup.find('a', class_=re.compile("next-link")).attrs['href'] 
        except: # if .find() is empty, .attrs['href'] will throw a NoneType error. If so, Break
            print(f'next_tag NOT FOUND: {r.url}\n')
            break

        # find all store links on current page
        # add to master list (all_links)
        # use next_link to request the next page to scrape
        try:
            store_links = [tag.attrs['href'] for tag in soup.find_all('a', href=re.compile("/biz/")) if not tag.text]
            all_links.extend([link.split('?')[0] for link in store_links]) # clean URL before extend
            print(f'Scraped {len(store_links)} links')
            r = requests.get('https://www.yelp.com'+next_link)
            count += 1
        except Exception as exc: # catch potential errors from tag.attrs['href']
            print(f'Error: {exc}')      
            break

        if count >  limit: break # infinite loop safety

    print('Total links scraped:', len(all_links))
    print('Saving to file..')
    with open('master_list.txt', 'a') as f:
        f.writelines([link+'\n' for link in all_links])

    return all_links 

# refactored methods
def section_idx(driver, section_name=None):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    main_div = soup.find('div', class_="lemon--div__373c0__1mboc stickySidebar--heightContext__373c0__133M8 tableLayoutFixed__373c0__12cEm arrange__373c0__UHqhV u-space-b6 u-padding-b4 border--bottom__373c0__uPbXS border-color--default__373c0__2oFDT")
    section_tags = main_div.find('div').find_all('section')
    section_names = [tag.find('div').find('div').text for tag in section_tags]
    if section_name:
        return (section_names.index(section_name)+1, section_names)
    else: 
        return section_names
    
def store_name(soup):
    try:
        return soup.find('h1').text
    except:
        print('no name found')
        return None

def star_rating(soup):
    try:
        return soup.find('div', class_=re.compile('i-stars--large'))\
                .attrs['aria-label']\
                .split(' ')[0]
    except:
        print('no rating found')
        return None

def total_reviews(soup):
    try:  
        return soup.find('p', class_='lemon--p__373c0__3Qnnj text__373c0__2pB8f text-color--mid__373c0__3G312 text-align--left__373c0__2pnx_ text-size--large__373c0__1568g')\
                .text.split(' ')[0]
    except:
        print('no reviews found')
        return None

def address(soup):
    try:
        street, city, state, zipcode = [tag.text for tag in soup.find('address').find_all('span')]
        return {'street':street, 'city':city, 'state':state, 'zipcode':zipcode}
    except:
        print('no address found')
        return None 

def price(soup):
    try:
        return soup.find("span", class_="lemon--span__373c0__3997G text__373c0__2pB8f text-color--normal__373c0__K_MKN text-align--left__373c0__2pnx_ text-bullet--after__373c0__1ZHaA text-size--large__373c0__1568g").text
    except: 
        print('no price found')
        return None

# clean reviews
def clean_string(string):
    return ' '.join([''.join([c for c in word if c.isalnum()]) for word in string.split()])
 

# grab amenities data using selenium
def amenities(driver):
    try:
        idx, _ = section_idx(driver, 'Amenities')
        # click "show more" to reveal hidden html
        button = driver.find_elements_by_xpath(f'//*[@id="wrap"]/div[3]/div/div[1]/div[3]/div/div/div[2]/div[1]/section[{idx}]/div[2]/a')
        driver.execute_script("arguments[0].click();", button[0])
    except:
        pass
    
    # get amenities and create dictionary
    try:
        xpath = f'//*[@id="wrap"]/div[3]/div/div[1]/div[3]/div/div/div[2]/div[1]/section[{idx}]/div[2]/div'
        ameneties = driver.find_elements_by_xpath(xpath)
        ameneties_dict = {}
        for a in ameneties[0].text.split('\n'):
            key_name = " ".join(a.split(' ')[:-1])
            key_value = a.split(' ')[-1]
            ameneties_dict[key_name] = key_value
        return ameneties_dict
    except:
        print('no amenities found')
        return None


def highlights(driver):
    try:
        idx, _ = section_idx(driver, 'Review Highlights') #find which section number
        button = driver.find_elements_by_xpath(f'//*[@id="wrap"]/div[3]/div/div[1]/div[3]/div/div/div[2]/div[1]/section[{idx}]/div[2]/a')
        driver.execute_script("arguments[0].click();", button[0])
    except:
        pass 
    try:    
        review_section = f'//*[@id="wrap"]/div[3]/div/div[1]/div[3]/div/div/div[2]/div[1]/section[{idx}]'
        review_tags = driver.find_element_by_xpath(review_section)
        reviews = review_tags.text.split('\n')
        return [clean_string(text) for text in reviews[1:]]
    except:
        print('no info found')
        return None
    


def about(driver):
    try:
        idx, _ = section_idx(driver, 'About the Business')
        open_button = driver.find_elements_by_xpath(f'//*[@id="wrap"]/div[3]/div/div[1]/div[3]/div/div/div[2]/div[1]/section[{idx}]/div[2]/a')
        driver.execute_script("arguments[0].click();", open_button[0])
    except:
        pass
    try:
        pop_up = driver.find_elements_by_xpath(f'//*[@id="wrap"]/div[3]/div/div[1]/div[3]/div/div/div[2]/div[1]/section[{idx}]/div[2]/div[2]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div/div/p')
        text = "".join([p.text for p in pop_up])
        return text
    except:
        print('no about section')
        return None

# delete duplicates from master list of all store links
def drop_duplicates(links):
    return set(links)

def scrape_page(url, driver):
    driver.get(url)
    # captcha
    if driver.current_url.startswith('https://www.yelp.com/visit_captcha'):
        print('DAMN YOU CAPTCHA!!!')
        if input('Solve problem and press "y" to continue \n') == 'y':
                driver = webdriver.Chrome()
                driver.get(url)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    sections= section_idx(driver)
         
    document = {
    'name':store_name(soup),
    'ratings':star_rating(soup),
    'review_count':total_reviews(soup),
    'price_rating':price(soup),
    'address_dict':address(soup),
    'amenities_dict':amenities(driver),
    'highlight_revs':highlights(driver),
    'about_info':about(driver),
    'sections_list': sections
    }
    print(document)
    

    return document

def scrape_insert_db(master_list, table, chrome_options):
    driver = webdriver.Chrome(options=chrome_options)
    for i, store in enumerate(master_list):
        url = "https://www.yelp.com"+store
        try:
            document = scrape_page(url, driver)
            table.insert_one(document)
            print('\ninsert complete :)')
            print(f'count: {i} \n')
        except: 
            print('\ninsert fail :(')
            print(f'count: {i} \n')


# scrape cities from yelp.com/cities
#url = "https://www.yelp.com/city"
#r = get_requests(url)
#city_links = scrape_cities(r)

# city_links = [#'anaheim-ca-us', 
#               'bakersfield', 
#               'berkeley', 
#               'chula-vista-ca-us', 
#               'concord-ca-us', 
#               'davis', 
#               'elk-grove-ca-us', 
#               'escondido-ca-us', 
#               'fairfield-ca-us', 
#               'fullerton-ca-us', 
#               'hollywood-ca-us', 
#               'lancaster-ca-us', 
#               'la', 
#               'modesto-ca-us', 
#               'moreno-valley-ca-us', 
#               'oakland', 
#               'north-county-san-diego', 
#               'pasadena-ca-us', 
#               'rancho-cucamonga-ca-us', 
#               'richmond-ca-us', 
#               'riverside-ca-us', 
#               'roseville-ca-us', 
#               'sacramento', 
#               'san-bernardino-ca-us', 
#               'san-diego', 
#               'sf', 
#               'san-jose', 
#               'santa-ana-ca-us',
#               'santa-clarita-ca-us', 
#               'simi-valley-ca-us', 
#               'sunnyvale-ca-us', 
#               'torrance-ca-us', 
#               'west-covina-ca-us']

# for each city, search all three parameters and scrape store links
# master_list = []
# for city in city_links:
#     for sortby in ['rating', 'review_count', 'recommended']:
#         try:
#             url = f"https://www.yelp.com/search?find_desc=Coffee%20%26%20Tea&find_loc={city}&sortby={sortby}"
#             r = get_requests(url)
#             if r.url.startswith('https://www.yelp.com/visit_captcha'):
#                 print('DAMN YOU CAPTCHA!!!')
#                 if input('Solve problem and press "y" to continue \n') == 'y':
#                     continue           
#             store_links = scrape_stores(r, 1000)
#             master_list.extend(store_links)
#         except:
#             if input('something happened..press "y" to cont \n') == 'y':
#                 continue

with open('data/master_list_clean.txt', 'r') as f:
    master_list = [line.strip('\n') for line in f.readlines()]

master_list = master_list[10500:] # checkpoint
#headless chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")

# start mongo server
local_client = MongoClient()
db = local_client.yelp
homepages4 = db.homepages4

# for each store, scrape data and output dictionary

scrape_insert_db(master_list, homepages4, chrome_options)

local_client.close()