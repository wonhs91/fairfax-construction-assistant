# %%
from langchain_community.document_loaders.firecrawl import FireCrawlLoader

loader = FireCrawlLoader(
  # url="https://www.fairfaxcounty.gov",
  url="https://www.fairfaxcounty.gov",
  api_url="http://localhost:3002",
  api_key="dontneedone",
  mode="crawl",
  params={
    "limit": 1000,
    # "maxDepth": 3,
    "ignoreSitemap": True,
    "allowBackwardLinks": False,
    "scrapeOptions": {
      "formats": ["markdown"],
      "onlyMainContent": True
    },
    "includePaths": [

      "plan2build/*",
      "landdevelopment/*",
      "planning-development/*",
      "topics/business-construction/*",
      "topics/land-use-and-planning/*",
      "topics/property-and-housing/*"
    ],
    "scrapeOptions": {
      "waitFor": 1000
    }
  }
)

# %%
import os
import re
import json
import hashlib


def clean_filename(title: str, url: str, max_length=100) -> str:
    # Step 1: Replace invalid characters in the title
    cleaned_title = re.sub(r'[<>:"/\\|?*]', '_', title)  # Replace invalid characters
    cleaned_title = cleaned_title.strip()  # Strip leading/trailing spaces

    # # Step 2: Limit the length of the filename
    # if len(cleaned_title) > max_length:
    #     cleaned_title = cleaned_title[:max_length]

    # # Step 3: Optionally, fallback to URL if title is empty or too short
    
    # if not cleaned_title or len(cleaned_title) < 5:
    #     # Hash the URL to generate a unique filename
    cleaned_title = hashlib.md5((title + url).encode('utf-8')).hexdigest()[:max_length]

    return cleaned_title

store_dir = "D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\web_scraping_data"

os.makedirs(store_dir, exist_ok=True)

for doc in loader.lazy_load():
  try: 
    print(f"scraping: {doc.metadata.get('sourceURL')}")
    doc_dict = {
      "page_content": doc.page_content,
      "metadata": doc.metadata
    }
    
    filename = f"{clean_filename(doc.metadata.get('title'), doc.metadata.get('url'))}" + '.json'
    file_path = os.path.join(store_dir, filename)
    with open(file_path, "w") as f:
      json.dump(doc_dict, f, indent=4)
      
    print(f"scraping successfully saved to: {filename}")
    
  except Exception as e:
    print(f"Error scraping {doc.metadata.get('sourceURL')}: {e}")
    continue
