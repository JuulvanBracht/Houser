from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os
from supabase import create_client, Client

# Supabase environment variables from Vercel
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and KEY must be set as environment variables.")

# Supabase client setup
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI app setup
app = FastAPI()

# Pydantic models
class WatchlistRequest(BaseModel):
    street_name: str
    city_name: str

class WatchlistResponse(BaseModel):
    id: int
    street_name: str
    city_name: str

# CRUD operations for Watchlist

# Create a new watchlist entry
@app.post("/watchlist/add", response_model=WatchlistResponse)
def add_watchlist_item(item: WatchlistRequest):
    # Check if the entry already exists
    existing_item = supabase.table("watchlist").select("*").eq("street_name", item.street_name).eq("city_name", item.city_name).execute()
    if existing_item.data:
        raise HTTPException(status_code=400, detail="Entry already exists in the watchlist")

    # Insert the new watchlist item
    new_item = {
        "street_name": item.street_name,
        "city_name": item.city_name
    }
    response = supabase.table("watchlist").insert(new_item).execute()
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Failed to add item to the watchlist")
    return response.data[0]

# Retrieve all watchlist entries
@app.get("/watchlist/", response_model=list[WatchlistResponse])
def list_watchlist():
    response = supabase.table("watchlist").select("*").execute()
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to retrieve watchlist entries")
    return response.data

# Update an existing watchlist entry
@app.put("/watchlist/update/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist_item(watchlist_id: int, item: WatchlistRequest):
    # Check if the entry exists
    existing_item = supabase.table("watchlist").select("*").eq("id", watchlist_id).execute()
    if not existing_item.data:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")

    # Update the watchlist item
    updated_item = {
        "street_name": item.street_name,
        "city_name": item.city_name
    }
    response = supabase.table("watchlist").update(updated_item).eq("id", watchlist_id).execute()
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to update watchlist entry")
    return response.data[0]

# Delete a watchlist entry
@app.delete("/watchlist/delete/{watchlist_id}")
def delete_watchlist_item(watchlist_id: int):
    # Check if the entry exists
    existing_item = supabase.table("watchlist").select("*").eq("id", watchlist_id).execute()
    if not existing_item.data:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")

    # Delete the watchlist item
    response = supabase.table("watchlist").delete().eq("id", watchlist_id).execute()
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to delete watchlist entry")
    return {"detail": "Watchlist entry deleted successfully"}

# Example route for health check
@app.get("/health")
def health_check():
    return {"status": "ok"}