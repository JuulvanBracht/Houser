from http.server import BaseHTTPRequestHandler
import supabase
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Fetch watchlist data from Supabase
        watchlist = supabase_client.table("watchlist").select("*").execute()
        if watchlist.error:
            self.send_error(500, str(watchlist.error))
            return

        results = []
        for item in watchlist.data:
            watchlist_id = item["id"]
            street_name = item["street_name"]
            city_name = item["city_name"]

            # Scrape Funda website for listings on this street in the city
            funda_url = f"https://www.funda.nl/en/koop/{city_name}/straat-{street_name.replace(' ', '-')}/"
            response = requests.get(funda_url)
            if response.status_code != 200:
                continue  # Skip this entry if Funda scraping fails

            soup = BeautifulSoup(response.content, "html.parser")
            properties = soup.find_all("div", class_="search-result")  # Adjust class based on Funda structure

            for prop in properties:
                # Extract details (adjust based on Funda HTML structure)
                address = prop.find("h2", class_="search-result__header-title").text.strip()
                status = prop.find("span", class_="search-result-label").text.strip() if prop.find("span", class_="search-result-label") else "Available"
                price = prop.find("span", class_="search-result-price").text.strip()
                scanned_at = datetime.utcnow().isoformat()

                # Append result to list
                results.append({
                    "watchlist_id": watchlist_id,
                    "address": address,
                    "status": status,
                    "price": price,
                    "scanned_at": scanned_at
                })

        # Insert results into Supabase `scan_results` table
        if results:
            insert_response = supabase_client.table("scan_results").insert(results).execute()
            if insert_response.error:
                self.send_error(500, str(insert_response.error))
                return

        # Send a success response
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes('{"status": "success", "message": "Scan completed!"}', "utf-8"))
