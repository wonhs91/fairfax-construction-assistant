# %%
from firecrawl import FirecrawlApp
from langchain_core.documents import Document

app = FirecrawlApp(api_key="sample bearer token", api_url="http://localhost:3002")

# scrape_status = app.scrape_url(
#   'https://firecrawl.dev', 
#   params={'formats': ['markdown']}
# )
# %%
import os
import re
import json
import hashlib


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

store_dir = "D:\\projects\\AIprojects\\fairfax-construction-assistant\\service\\consultation_company\\vectorstores\\web_scraping_data"

os.makedirs(store_dir, exist_ok=True)

  # Define event handlers   
def on_document(detail):
    print(f"working on: {detail["metadata"].get("title")}")
    
    page_content = (
        detail.get("markdown") or detail.get("html") or detail.get("rawHtml", "")
    )
    metadata = detail.get("metadata", {})
    
    print(f"scraping: {metadata.get('sourceURL')}")
    doc_dict = {
      "page_content": page_content,
      "metadata": metadata
    }
    
    filename = f"{clean_filename(metadata.get('title', ''), metadata.get('url'))}" + '.json'
    file_path = os.path.join(store_dir, filename)
    with open(file_path, "w") as f:
      json.dump(doc_dict, f, indent=4)
      
    print(f"scraping successfully saved to: {filename}")


    print("\n")
    print("===" * 25)
    print("\n")

def on_error(detail):
    print("ERR", detail['error'])
    

    print("\n")
    print("###" * 25)
    print("\n")
    
def on_done(detail):
    print("DONE", detail['status'])
    
    print("\n")
    print("---" * 25)
    print("\n")

    # Function to start the crawl and watch process
async def start_crawl_and_watch():
    # Initiate the crawl job and get the watcher
    watcher = app.crawl_url_and_watch(
      'https://www.fairfaxcounty.gov/', 
      params={
          "limit": 100,
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
            "topics/property-and-housing/*",
          ]
        }
    )

    # Add event listeners
    watcher.add_event_listener("document", on_document)
    watcher.add_event_listener("error", on_error)
    watcher.add_event_listener("done", on_done)
    print(f"\n\n**********\n\nID: {watcher.id}\n\n**********\n\n")
    # Start the watcher
    try:
        # Try to start the watcher connection
        await watcher.connect()

    except Exception as e:
        # If the message size is too large, catch the error and skip this chunk
        print(f"Failed to connect: {e}. Skipping this chunk...")
        # You can choose to log this or handle it differently

import asyncio
if __name__ == "__main__":
  asyncio.run(start_crawl_and_watch())