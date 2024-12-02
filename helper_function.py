import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from modeling import train_model, predict_model
import sys
import cgi
import urllib
import json
import time
import pprint
isPython2 = sys.hexversion < 0x03000000
if isPython2:
	import urllib2
else:
	import urllib.request
	import urllib.error
import openai
from openai import OpenAI

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("API_KEY_PAGESPEED")

def get_pagespeed_scores(url, strategy="mobile", categories=None):
    """
    Fetch scores for specified categories from Google PageSpeed Insights API.

    Args:
        url (str): The URL to analyze.
        strategy (str): The strategy to use ("mobile" or "desktop"). Default is "mobile".
        categories (list): List of categories to fetch. Default is ["performance", "accessibility", "best-practices", "seo"].

    Returns:
        dict: Dictionary containing scores for each category, or None if not available.
    """
    if categories is None:
        categories = ["performance", "accessibility", "best-practices", "seo"]
    
    all_category_data = {}
    for category in categories:
        endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        params = {
            "url": url,
            "strategy": strategy,
            "category": category,
            "key": API_KEY
        }
        response = requests.get(endpoint, params=params)
        data = response.json()

        if 'error' in data:
            print(f"API Error for category '{category}': {data['error']}")
            all_category_data[category] = None  # Set None for errors
        else:
            category_data = data.get('lighthouseResult', {}).get('categories', {}).get(category, None)
            if category_data:
                all_category_data[category] = category_data.get('score', None)  # Get only the score

    # Convert scores to percentages
    all_category_data = {k: (v * 100 if v is not None else None) for k, v in all_category_data.items()}
    return all_category_data

#scrapping
# Fungsi untuk request ke URL
def request_web(url, endpoint=""):
    try:
        file_url = f"{url}/{endpoint}" 
        response = requests.get(file_url, timeout=10)
        response.raise_for_status()  # Raise HTTPError untuk status code yang buruk
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat mengambil data dari URL: {e}")
        return None

# def make_soup(url):
#     response = request_web(url, "")
#     if response:
#         soup = BeautifulSoup(response.text, "html.parser")
#         return soup
#     else:
#         print(f"Could not create soup for {url}")
#         return None

# Fungsi untuk ekstrak meta tags
def extract_meta_tags(soup):
    meta_data = {}
    meta_description = soup.find("meta", attrs={"name": "description"})
    meta_data["description"] = meta_description["content"] if meta_description else "Tidak ditemukan"

    meta_keywords = soup.find("meta", attrs={"name": "keywords"})
    meta_data["keywords"] = meta_keywords["content"] if meta_keywords else "Tidak ditemukan"

    title_tag = soup.find("title")
    meta_data["title"] = title_tag.get_text().strip() if title_tag else "Tidak ditemukan"

    meta_robots = soup.find("meta", attrs={"name": "robots"})
    meta_data["robots"] = "Yes" if meta_robots else "No"

    # Menentukan status Open Graph Tag
    og_tags = ["og:title", "og:description", "og:image", "og:url"]
    # Cek apakah ada minimal satu tag yang ditemukan
    og_status = "Implemented" if any(soup.find("meta", attrs={"property": tag}) for tag in og_tags) else "Not Implemented"
    # Menyimpan status og_tag dalam meta_data
    meta_data["og_tag"] = og_status

    meta_canonical = soup.find("link", attrs={"rel": "canonical"})
    meta_data["canonical"] = "Yes" if meta_canonical else "No"

    meta_google_site_verification = soup.find("meta", attrs={"name": "google-site-verification"})
    meta_data["google_site_verification"] = "Yes" if meta_google_site_verification else "No"

    return meta_data

# Fungsi untuk ekstrak heading tags
def extract_headings(soup):
    headings_count = {}
    for level in range(1, 7):  # H1 hingga H6
        tag = f"h{level}"
        # Menghitung jumlah heading pada setiap level H1, H2, H3, ..., H6
        headings_count[f'h{level}_count'] = len(soup.find_all(tag))
    return headings_count

# Fungsi untuk menghitung jumlah kata
def count_words(soup):
    body_text = soup.body.get_text() if soup.body else ""
    words = body_text.split()
    return len(words)

# Fungsi untuk cek sitemap
def cek_sitemap(url):
    response = request_web(url, "sitemap.xml")
    if response and response.status_code == 200:
        return "Yes"
    else:
        return "No"

# Fungsi untuk cek robots.txt
def cek_robots(url):
    response = request_web(url, "robots.txt")
    if response and response.status_code == 200:
        return "Yes"
    else:
        return "No"

# Jika perlu menambahkan fungsi `find_favicon`, definisikan juga di sini.
def find_favicon(soup):
    favicon_link = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
    if favicon_link:
        return "Yes"
    else:
        return "No"

def scrape_metatags_and_structure(url):
    # Mengambil halaman dan membuat BeautifulSoup
    soup = request_web(url)
    if not soup:
        return None  # Jika halaman tidak dapat diambil, return None

    # 1. Mengekstrak Meta Tags
    meta_tags = extract_meta_tags(soup)
    og_status = meta_tags["og_tag"]  # Tidak perlu memproses lebih lanjut, sudah berisi "Implemented" atau "Not Implemented"

    # 2. Mengekstrak Heading Tags (H1 hingga H6)
    headings = extract_headings(soup)

    # 3. Menghitung Jumlah Kata
    word_count = count_words(soup)

    # 4. Mengecek Sitemap dan Robots.txt
    sitemap_status = cek_sitemap(url)  # Mengembalikan 1 jika ada, 0 jika tidak
    robots_status = cek_robots(url)    # Mengembalikan 1 jika ada, 0 jika tidak

    # 5. Mencari Favicon
    favicon = find_favicon(soup)

    # Menghitung Meta Title dan Description Count
    meta_title_count = 1 if meta_tags["title"] != "Tidak ditemukan" else 0
    meta_description_count = 1 if meta_tags["description"] != "Tidak ditemukan" else 0
    meta_keywords_count = 1 if meta_tags["keywords"] != "Tidak ditemukan" else 0
    meta_robots_count = 1 if meta_tags["robots"] != "Tidak ditemukan" else 0

    # 6. Mengembalikan semua data dalam bentuk dictionary
    data = {
        "Meta title": meta_tags["title"],
        "Meta title count": meta_title_count,
        "Meta description": meta_tags["description"],
        "Meta description count": meta_description_count,
        "H1 count": headings["h1_count"],
        "H2 count": headings["h2_count"],
        "H3 count": headings["h3_count"],
        "H4 count": headings["h4_count"],
        "H5 count": headings["h5_count"],
        "H6 count": headings["h6_count"],
        "Meta robots": meta_tags["robots"],
        "Meta keywords": meta_tags["keywords"],
        "Open Graph Status": og_status,  # Status Open Graph langsung
        "Canonical Tag Present": meta_tags["canonical"],
        "Sitemap Present": sitemap_status,  # 1 jika ditemukan, 0 jika tidak
        "Robots.txt Present": robots_status,  # 1 jika ditemukan, 0 jika tidak
        "Google Search Console Connected": meta_tags["google_site_verification"],
        "Favicon Present": favicon,
        "Word Count": word_count,
    }

    return data

# Fungsi untuk melatih model dengan data pelatihan
def train_seo_model(X_train, y_train):
    """
    Melatih model SEO berdasarkan data pelatihan.
    Args:
        X_train (list): Data fitur pelatihan.
        y_train (list): Label target pelatihan.
    """
    trained_model = train_model(X_train, y_train)
    return trained_model

#Fungsi untuk melakukan prediksi dan menghasilkan hasil
def predict_seo_structure(url):
    """
    Melakukan prediksi untuk kolom Structure berdasarkan input.
    Args:
        input_list (list): Data fitur untuk prediksi.
    Returns:
        float: Prediksi nilai Structure
    """
    #ambil nilai pagespeed
    ps = get_pagespeed_scores(url, strategy="mobile", categories=None)
    scrap = scrape_metatags_and_structure(url)
    input_list = [
        ps['accessibility'],
        ps['seo'],
        ps['best-practices'],
        ps['performance'],
        scrap['H5 count'],
        1 if scrap['Meta robots']=="Yes" else 0,
        scrap['Word Count']
    ]
    structure_value = predict_model(input_list)
    return structure_value

"""#**Clasification Grade and Mobile friendly**"""
#Pengkategorian grade
def grade_category(url):
  structure_value = predict_seo_structure(url)
  ps = get_pagespeed_scores(url, strategy="mobile", categories=None)
  performance_score = ps['performance']
  grade = (structure_value + performance_score) /2
  if grade >= 90:
      grade_category = "A"
  elif grade >= 50:
      grade_category = "B"
  else:
      grade_category = "C"

  return grade_category

def mobile_friendly(url):
  ps = get_pagespeed_scores(url, strategy="mobile", categories=None)
  performance_score = ps['performance']
  if performance_score >= 75:
    return "Yes"
  else:
    return "No"
  
"""#**Siteliner Function**"""

#!/usr/bin/python
#list library di atas

#	Python sample code for Siteliner Premium API
#
#	Compatible with Python 2.4 or later
#
#	You may install, use, reproduce, modify and redistribute this code, with or without
#	modifications, subject to the general Terms and Conditions on the Siteliner website.
#
#	For any technical assistance please contact us via our website.
#
#	5-Aug-2020: First version
#
#	Siteliner (c) Indigo Stream Technologies 2020 - https://www.siteliner.com/
#
#
#	Instructions for use:
#
#	1. Set the constants SITELINER_USERNAME and SITELINER_API_KEY below to your details.
#	2. Call the appropriate API function, following the examples below .
#	3. Use print_r to discover the structure of the output.
#	4. To run the example provided, please uncomment and edit the lines below.
#	   NOTE: Each scanned page and API request for scan results costs 1c

#SITELINER_RUN_EXAMPLES=True
#SITELINER_ROOT_URL="http://www.example.com/"
#SITELINER_MAX_PAGES=100

#	Error handling:
#
#	* If a call failed completely (e.g. curl failed to connect), functions return false.
#	* If the API returned an error, the response array will contain an 'error' element.


# A. Constants you need to change
load_dotenv('./api_key.env')
siteliner_username = os.getenv('SITELINER_USERNAME')
siteliner_api_key = os.getenv('SITELINER_API_KEY')
SITELINER_USERNAME = siteliner_username
SITELINER_API_KEY = siteliner_api_key
if not SITELINER_USERNAME:
    raise ValueError("SITELINER_USERNAME is missing in the environment variables")
if not SITELINER_API_KEY:
    raise ValueError("SITELINER_API_KEY is missing in the environment variables")


SITELINER_API_URL = "https://www.siteliner.com/api/"

#	B. Functions for you to use

def siteliner_get_account_summary(count=100, start=1):
	return siteliner_api_call('account',{'count':count,'start':start})

def siteliner_start_scan(rooturl, maxpages, parameters=None):
# any optional API parameters should be provided to the function in the format specified by the API documentation
#
# Example:
#
# siteliner_start_scan("http://www.example.com", 100,
#                      {"scanmode":"excludedirs",
#                       "excludedirs":"sports/\nbusiness/banking/"
#                       })
    params={'rooturl':rooturl,'maxpages':maxpages}
    if parameters is not None:
        for key in parameters:
            params[key] = parameters[key]

    return siteliner_api_call('start',params,True)

def siteliner_pause_scan(scan):
    return siteliner_api_call('pause',{'scan':scan},True)

def siteliner_resume_scan(scan):
	return siteliner_api_call('resume',{'scan':scan},True)

def siteliner_cancel_scan(scan):
	return siteliner_api_call('cancel',{'scan':scan},True)

def siteliner_get_scan_status(scan):
	return siteliner_api_call('status',{'scan':scan})

def siteliner_get_scan_summary(scan):
	return siteliner_api_call('sitesummary',{'scan':scan})

def siteliner_get_analyzed_pages(scan, count=100, start=1):
	return siteliner_api_call('siteanalyzed',{'scan':scan,'count':count,'start':start})

def siteliner_get_skipped_pages(scan, count=100, start=1):
	return siteliner_api_call('siteskipped',{'scan':scan,'count':count,'start':start})

def siteliner_get_duplicate_pages(scan, count=100, start=1):
	return siteliner_api_call('siteduplicate',{'scan':scan,'count':count,'start':start})

def siteliner_get_broken_link_pages(scan, count=100, start=1):
	return siteliner_api_call('sitebroken',{'scan':scan,'count':count,'start':start})

def siteliner_get_related_domains(scan, count=100, start=1):
	return siteliner_api_call('siterelateddomain',{'scan':scan,'count':count,'start':start})

def siteliner_get_page_duplicates(scan, page, count=100, start=1):
	return siteliner_api_call('pageduplicate',{'scan':scan,'page':page,'count':count,'start':start})

def siteliner_get_page_int_links_in(scan, page, count=100, start=1):
	return siteliner_api_call('pagelinkin',{'scan':scan,'page':page,'count':count,'start':start})

def siteliner_get_page_int_links_out(scan, page, count=100, start=1):
	return siteliner_api_call('pagelinkout',{'scan':scan,'page':page,'count':count,'start':start})

def siteliner_get_page_ext_links_out(scan, page, count=100, start=1):
	return siteliner_api_call('pageexternal',{'scan':scan,'page':page,'count':count,'start':start})

def siteliner_get_related_links_in(scan, url, count=100, start=1):
	return siteliner_api_call('relatedlinkin',{'scan':scan,'url':url,'count':count,'start':start})


# C. Functions used internally

def siteliner_api_call(operation, params={}, post=False):
    urlparams={}
    urlparams['user'] = SITELINER_USERNAME
    urlparams['key'] = SITELINER_API_KEY
    if post:
        urlparams['command'] = operation
    else:
        urlparams['report'] = operation

    if post:
        if isPython2:
            postdata = urllib.urlencode(params)
        else:
            postdata = urllib.parse.urlencode(params)
    else:
        postdata = None
        urlparams.update(params)

    uri = SITELINER_API_URL + '?'

    request = None
    if isPython2:
        uri += urllib.urlencode(urlparams)
        if postdata is None:
            request = urllib2.Request(uri)
        else:
            request = urllib2.Request(uri, postdata.encode("UTF-8"))
    else:
        uri += urllib.parse.urlencode(urlparams)
        if postdata is None:
            request = urllib.request.Request(uri)
        else:
            request = urllib.request.Request(uri, postdata.encode("UTF-8"))

    try:
        response = None
        if isPython2:
            response = urllib2.urlopen(request)
        else:
            response = urllib.request.urlopen(request)
        res = response.read()
        result = json.loads(res)
        if 'error' in result.keys():
            print("API returned error: "+result['error'])
            return None
        return result
    except Exception:
        e = sys.exc_info()[1]
        print(e.args[0])

    return None

def format_plural_string(count,text):
    result='No '+text+'s'
    if count > 0:
        if count==1:
            result='1 ' + text
        else:
            result=str(count) + ' ' + text + 's'
    return result

#	E. Example

def siteliner_run_example(rooturl, maxpages):

    print("\nStarting scan for "+rooturl)

    scan_info=siteliner_start_scan(rooturl,maxpages)
    if scan_info is None:
        sys.exit()

    scan=scan_info['scan']
    print("Scan successfully started, scan ID: "+scan)

    while(scan_info['status'] != 'completed'):
        time.sleep(10)
        scan_info=siteliner_get_scan_status(scan)
        if scan_info is None:
            sys.exit()
        print(format_plural_string(scan_info['found'],"page")+" found so far, "+format_plural_string(scan_info['retrieved'],"page")+" retrieved")

    summary=siteliner_get_scan_summary(scan)
    if summary is None:
        sys.exit()

    print("\nScan completed successfully, summary:")
    print(json.dumps(summary, indent=4))

    analyzed=siteliner_get_analyzed_pages(scan,5)
    if analyzed is None:
        sys.exit()

    print("\n"+format_plural_string(len(analyzed['results']), 'most prominent page'))
    print(json.dumps(analyzed, indent=4))

    home_links_in=siteliner_get_page_int_links_in(scan,"/",5)
    if home_links_in is None:
        sys.exit()

    if home_links_in['resultcount'] > 0:
        print("\n"+format_plural_string(len(home_links_in['results']), 'most prominent page')+" with most links to home page:")
        print(json.dumps(home_links_in, indent=4))
    else:
        print("\nNo pages found with links to home page");
    print("\n")
    return summary


if 'SITELINER_RUN_EXAMPLES' in globals() and SITELINER_RUN_EXAMPLES:
    siteliner_run_example(SITELINER_ROOT_URL,SITELINER_MAX_PAGES)

"""# **LLM Model (Blm testing)**"""
load_dotenv('./api_key.env')
api_key = os.getenv('API_KEY_OPENAI')
if not api_key:
    raise ValueError("API_KEY_OPENAI is missing in the environment variables")

client = OpenAI(
     api_key = api_key
)


def generate_notes(url, maxpages):
    all_category_data = get_pagespeed_scores(url, strategy="mobile", categories=None)
    data = scrape_metatags_and_structure(url)
    structure_value = predict_seo_structure(url)
    grade_category = grade_category(url)
    mobile = mobile_friendly(url)
    siteliner = siteliner_run_example(url, maxpages)
    all_data = {
        "URL" : url,
        "Structure" : structure_value,
        "Grade" : grade_category,
        #pagespeed result
        "Performance" : all_category_data['performance'],
        "Accessibility" : all_category_data['accessibility'],
        "Best Practices" : all_category_data['best-practices'],
        "SEO": all_category_data['seo'],
        #content analysis
        "Mobile Friendly" : mobile,
        "Broken Link Count " : siteliner['brokenlinks'],
        "Duplicate Count Percentage" : siteliner['duplicate'],
        "Common Count Percentage" : siteliner['common'],
        "Unique Count Percentage" : siteliner['unique'],
        #metatag data
        "Meta title" : data["Meta title"],
        "Meta title count": data["Meta title count"],
        "Meta description" : data["Meta description"],
        "Meta description count" : data["Meta description count"],
        "H1 count": data["H1 count"],
        "H2 count" : data["H2 count"],
        "H3 count" : data["H3 count"],
        "H4 count" : data["H4 count"],
        "H5 count" : data["H5 count"],
        "H6 count" : data["H6 count"],
        "Meta robots" : data["Meta robots"],
        "Meta keywords" : data["Meta keywords"],
        "Open Graph Status" : data["Open Graph Status"],
        "Canonical Tag Present" : data["Canonical Tag Present"],
        "Sitemap Present" : data["Sitemap Present"],
        "Robots.txt Present" : data["Robots.txt Present"],
        "Google Search Console Connected" : data["Google Search Console Connected"],
        "Favicon Present" : data["Favicon Present"]
    }
    META_PROMPT = f"""
    Berikut adalah data hasil audit SEO untuk sebuah website:

    {all_data}

    Tolong:
    1. Identifikasi masalah utama dalam aspek SEO.
    2. Berikan rekomendasi untuk meningkatkan skor dan performa SEO.
    3. Berikan saran terkait hasil prediksi grade SEO.
    """
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": META_PROMPT,
            },
            {
                "role": "user",
                "content": "berdasarkan data tersebut buat catatan mendetail yang berisi analisis permasalahan dan jangan berikan rekomendasi sama sekali,:\n",
            },
        ],
    )

    return completion.choices[0].message.content

def generate_recommendation(url, maxpages):
    all_category_data = get_pagespeed_scores(url, strategy="mobile", categories=None)
    data = scrape_metatags_and_structure(url)
    structure_value = predict_seo_structure(url)
    grade_category = grade_category(url)
    mobile = mobile_friendly(url)
    siteliner = siteliner_run_example(url, maxpages)
    all_data = {
        "URL" : url,
        "Structure" : structure_value,
        "Grade" : grade_category,
        #pagespeed result
        "Performance" : all_category_data['performance'],
        "Accessibility" : all_category_data['accessibility'],
        "Best Practices" : all_category_data['best-practices'],
        "SEO": all_category_data['seo'],
        #content analysis
        "Mobile Friendly" : mobile,
        "Broken Link Count " : siteliner['brokenlinks'],
        "Duplicate Count Percentage" : siteliner['duplicate'],
        "Common Count Percentage" : siteliner['common'],
        "Unique Count Percentage" : siteliner['unique'],
        #metatag data
        "Meta title" : data["Meta title"],
        "Meta title count": data["Meta title count"],
        "Meta description" : data["Meta description"],
        "Meta description count" : data["Meta description count"],
        "H1 count": data["H1 count"],
        "H2 count" : data["H2 count"],
        "H3 count" : data["H3 count"],
        "H4 count" : data["H4 count"],
        "H5 count" : data["H5 count"],
        "H6 count" : data["H6 count"],
        "Meta robots" : data["Meta robots"],
        "Meta keywords" : data["Meta keywords"],
        "Open Graph Status" : data["Open Graph Status"],
        "Canonical Tag Present" : data["Canonical Tag Present"],
        "Sitemap Present" : data["Sitemap Present"],
        "Robots.txt Present" : data["Robots.txt Present"],
        "Google Search Console Connected" : data["Google Search Console Connected"],
        "Favicon Present" : data["Favicon Present"]
    }
    META_PROMPT = f"""
    Berikut adalah data hasil audit SEO untuk sebuah website:

    {all_data}

    Tolong:
    1. Identifikasi masalah utama dalam aspek SEO.
    2. Berikan rekomendasi untuk meningkatkan skor dan performa SEO.
    3. Berikan saran terkait hasil prediksi grade SEO.
    """
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": META_PROMPT,
            },
            {
                "role": "user",
                "content": "berdasarkan data tersebut buat rekomendasi yang actionable, berisi langkah - langkah yang dapat dilakukan:\n",
            },
        ],
    )

    return completion.choices[0].message.content