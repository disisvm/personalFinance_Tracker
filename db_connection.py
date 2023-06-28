from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
import os

# ----------- DB Connection -------------
load_dotenv(find_dotenv())

password = os.environ.get("mongo_pwd")

# Create the connection string for MongoDB using the provided password
connection_string = f"mongodb+srv://kvenkatamanish:{password}@manish.9cdaxh3.mongodb.net/"

# Create a MongoClient object with the connection string
client = MongoClient(connection_string)

# Access the "personalFinance_Tracker" database
db = client.personalFinance_Tracker