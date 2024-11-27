# %%
from bs4 import BeautifulSoup
import requests
from collections import deque
from html2text import HTML2Text
import os
import hashlib
import re
import json
from urllib.parse import urljoin, urlparse, unquote
import fnmatch
import time


STARTING_URL = "https://www.fairfaxcounty.gov/plan2build"
BASE_DOMAIN = "https://www.fairfaxcounty.gov/"
STORE_DIR = "D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\web_scraping_data"


excluding_tags = [
    "header",
    "footer",
    "nav",
    "aside",
    ".header",
    ".top",
    ".navbar",
    "#header",
    ".footer",
    ".bottom",
    "#footer",
    ".sidebar",
    ".side",
    ".aside",
    "#sidebar",
    ".modal",
    ".popup",
    "#modal",
    ".overlay",
    ".ad",
    ".ads",
    ".advert",
    "#ad",
    ".lang-selector",
    ".language",
    "#language-selector",
    ".social",
    ".social-media",
    ".social-links",
    "#social",
    ".menu",
    ".navigation",
    "#nav",
    ".breadcrumbs",
    "#breadcrumbs",
    "#search-form",
    ".search",
    "#search",
    ".share",
    "#share",
    ".widget",
    "#widget",
    ".cookie",
    "#cookie"
]


def matches_pattern(url, include_paths):
        """
        Check if a URL matches any of the specified path patterns.
        
        Args:
            url (str): URL to check
        
        Returns:
            bool: True if URL matches any pattern, False otherwise
        """
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Decode the path to handle URL-encoded characters
        path = unquote(parsed_url.path.strip('/'))
        
        # Check against each pattern
        for pattern in include_paths:
            # Use fnmatch for flexible pattern matching
            if fnmatch.fnmatch(path, pattern) or \
               fnmatch.fnmatch(path, f"{pattern}/*"):
                return True
        
        return False

def clean_filename(title: str, url: str, max_length=100) -> str:
    # Step 1: Replace invalid characters in the title
    cleaned_title = re.sub(r'[<>:"/\\|?*]', '_', title)  # Replace invalid characters
    cleaned_title = cleaned_title.strip()  # Strip leading/trailing spaces

    # Step 2: Limit the length of the filename
    # if len(cleaned_title) > max_length:
    #     cleaned_title = cleaned_title[:max_length]

    # Step 3: Optionally, fallback to URL if title is empty or too short
    
    # if not cleaned_title or len(cleaned_title) < 5:
        # Hash the URL to generate a unique filename
    cleaned_title = hashlib.md5((title + url).encode('utf-8')).hexdigest()[:max_length]

    return cleaned_title

def save_to_doc(markdown, metadata):
  

  filename = f"{clean_filename(metadata.get('title', ''), metadata.get('url'))}" + '.json'
  file_path = os.path.join(STORE_DIR, filename)
  with open(file_path, "w") as f:
    json.dump({
      "page_content": markdown,
      "metadata": metadata
    }, f, indent=4)
    
  print(f"=> successfully saved to: {filename}\n")
  

def scrape_page(response, include_paths=None):
  # if pdf file
  if response.headers.get('content-type', '').startswith('application/pdf'):
    return
  
  soup = BeautifulSoup(response.text, 'html.parser')
  
  # specific to fairfaxcounty.gov This gets the main content only
  page_content = soup.find('div', {'class': "pagecontent"})

  # Remove unnecessary tags
  for tag in page_content.find_all(excluding_tags):
    tag.decompose()

  html_converter = HTML2Text()
  html_converter.ignore_images = True
  html_converter.ignore_links = True
  html_converter.mark_code = True
  html_converter.body_width = 0
  markdown = html_converter.handle(str(page_content))
  
  metadata = {
    'url': response.url,
    'title': soup.title.string if soup.title else 'No title',
    'description': soup.find('meta', {'name': 'description'})['content'] if soup.find('meta', {'name': 'description'}) else 'No description',
    'keywords': soup.find('meta', {'name': 'keywords'})['content'] if soup.find('meta', {'name': 'keywords'}) else 'No keywords',
  }

  save_to_doc(markdown, metadata)
  
  is_curr_external = urlparse(response.url).netloc != urlparse(STARTING_URL).netloc
  links = []
  for a_tag in page_content.find_all('a', href=True):
    link = a_tag['href']
    if not link or link.startswith('#'):
      continue
    
    link = urljoin(BASE_DOMAIN, a_tag['href'])
    # If current is already external link, skip the next external links
    if is_curr_external and urlparse(link).netloc != urlparse(STARTING_URL).netloc:
      continue
    
    # skip when include paths are not matched
    if include_paths and not matches_pattern(link, include_paths):
        continue
    
    links.append(link)
    
  return links

def download_pdf(response):
  filename = os.path.basename(urlparse(response.url).path)
  pdf_dir = STORE_DIR + '\\pdf'
  local_path = os.path.join(pdf_dir, filename)
  with open(local_path, 'wb') as file:
    file.write(response.content)


def crawl_url(starting_url, max_size=5, depth=2, include_paths=None):
  
  include_paths = [path.strip('/') for path in include_paths] if include_paths else None
  visited = set([starting_url]) 
  url_queue = deque([(starting_url, 0)])
  scraped = []
  
  while url_queue and len(scraped) < max_size:
    curr_url, curr_depth = url_queue.popleft()
    
    if depth > 0 and curr_depth > depth:
      break
    
    try:
      print(f"scraping: {curr_url}")

      # pdf file download

      response = requests.get(curr_url)
      if response.status_code == 200:
        if curr_url.endswith('.pdf'):
          download_pdf(response)
          continue
        next_links = scrape_page(response, include_paths)
        scraped.append(curr_url)
        for link in next_links:
          if link not in visited:
            visited.add(link)
            url_queue.append((link, curr_depth + 1))
            
            
    except Exception as e:
      print(f"Failed while crawling {curr_url}: {e}")
    
    finally:
      time.sleep(.5)
  
  return scraped

starting_url = STARTING_URL
max_size = 5
depth = 2

# %%
include_paths = [
  "/plan2build/*",
  '/landdevelopment/*',
  'planning-development/*'
]

crawl_url(starting_url=starting_url, max_size=300, depth=8, include_paths=include_paths)


# %%
## THINGS TO IMPROVE
# - I can print number of sites scanned at the end (Successful, Error, Filetype)
# - Maybe, I can add DB to store the all the scraped information
# - I can scrape then store that directly into a vectorstore
# - When converting to markdown, I could leave the links in. This was maybe the LLM will pick up the links also.
# - Make scrape_page asynchronous
# - Store files to S3
# - Add AI agent to check if the document is relevant for this project
# - Store metadata to pdf (original pdf url, original webpage pdf is crawled from)
# - Make it into a class