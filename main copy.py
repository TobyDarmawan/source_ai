import subprocess
import re
import argparse
import typing
from pathlib import Path
import json
import openai
import anthropic

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

antropic_client = anthropic.Client(api_key="your_key")

arxiv_collection = None
class Recommendation:
  # The recommendation class contains 3 properties:
  # - The metadata of the recommendation (Title, Author, Year)
  # - The content of the recommendation
  # - The path to the recommendation file.
  def __init__(
      self, 
      content: str, 
      metadata: dict = None, 
      path: str = "",
  ):
    self.metadata = metadata
    self.content = content
    self.path = path

recs2 = [
  Recommendation(
    metadata = 
    {"Title": "The Innovator's Dilemma", "Author": "Clayton M. Christensen", "Year": 1997},
    content = "Classic book on innovation", 
    path = "The Innovator's Dilemma",
),
Recommendation(
    metadata = 
    {"Title": "The E-Myth Revisited", "Author": "Michael E. Gerber", "Year": 1995},
    content = "Great book on entrepreneurship", 
    path = "The E-Myth Revisited",
),
Recommendation(
    metadata = 
    {"Title": "The $100 Startup", "Author": "Chris Guillebeau", "Year": 2012},
    content = "Inspiring book for small business owners", 
    path = "The $100 Startup",
),
Recommendation(
    metadata = 
    {"Title": "Crushing It!", "Author": "Gary Vaynerchuk", "Year": 2018},
    content = "Motivational book on personal branding", 
    path = "Crushing It!",
),
Recommendation(
    metadata = 
    {"Title": "The 4-Hour Workweek", "Author": "Tim Ferriss", "Year": 2007},
    content = "Interesting ideas on productivity and lifestyle design", 
    path = "The 4-Hour Workweek",
),
Recommendation(
    metadata = 
    {"Title": "Think and Grow Rich", "Author": "Napoleon Hill", "Year": 1937},
    content = "Classic self-help book", 
    path = "Think and Grow Rich",
),
Recommendation(
    metadata = 
    {"Title": "Rich Dad Poor Dad", "Author": "Robert Kiyosaki", "Year": 1997},
    content = "Insightful book on personal finance", 
    path = "Rich Dad Poor Dad",
),
Recommendation(
    metadata = 
    {"Title": "The Power of Now", "Author": "Eckhart Tolle", "Year": 1997},
    content = "Thought-provoking book on spirituality and mindfulness", 
    path = "The Power of Now",
),
Recommendation(
    metadata = 
    {"Title": "The Alchemist", "Author": "Paulo Coelho", "Year": 1988},
    content = "Inspirational novel about following your dreams", 
    path = "The Alchemist",
),
]

def input_user_idea():
  # Get user input
  user_idea = input("What is your idea? \n")

  # Print user input
  with open("idea.md", "w") as file:
    file.write(user_idea + "\n")
  print("Your idea is: " + user_idea)

  # Return user input
  return user_idea

def create_recommendations_page(idea_file: str, recs: typing.List[Recommendation]):
  for rec in recs:
    with open(rec.path, "w") as file:
      file.write(f"# Title:\n{rec.metadata['Title']}\n")
      # file.write(f"# Submitter:\n{rec.metadata['Author']}\n")
      # file.write(f"# Date:\n{rec.metadata['Year']}\n")
      file.write("# Summary\n")
      file.write(rec.content.lstrip())
  with open(idea_file, "a") as file:
    file.write("\n## Recommendations \n")
    for rec in recs:
      file.write(f"[[{rec.path}]]\n")
  

def copy_contents(source_file: str, destination_file: str):
  with open(destination_file, 'a') as f1:
    for line in open(source_file):
      f1.write(line)

def delete_from_heading(file_path: str):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            if line.strip() == "## Recommendations":
                break
            file.write(line)

# def get_recommendations():
  # # uri = "mongodb+srv://yashkap:SOURCEAIPWD@arxiv-db.lumuebx.mongodb.net/?retryWrites=true&w=majority&appName=arxiv-db"
  # uri = "mongodb+srv://yashkap:SOURCEAIPWD@source-ai.vcjts.mongodb.net/?retryWrites=true&w=majority&appName=source-ai"
  # # Create a new client and connect to the server
  # client = MongoClient(uri, server_api=ServerApi('1'))
  # db = client['source-ai']
  # arxiv_collection = db['arxiv2']
  # entries = arxiv_collection.find({},{ "_id": 0}).limit(10)
  # recs = []
  # index = 0
  # for index, data in enumerate(entries):
  #   rec = Recommendation(
  #       content= data["abstract"], 
  #       metadata= {
  #         "Title": re.sub('\s+', ' ', data["title"].strip()), 
  #         "Author": data["submitter"], 
  #         "Year": data["update_date"]
  #       }, 
  #       path=f"rec_{index}.md",
  #   )
  #   recs.append(rec)
  # return recs
  

openai.api_key = "your_key"

EMBEDDING_MODEL = "text-embedding-3-small"

def get_embedding(text):
    """Generate an embedding for the given text using OpenAI's API."""

    # Check for valid input
    if not text or not isinstance(text, str):
        return None

    try:
        # Call OpenAI API to get the embedding
        embedding = openai.embeddings.create(input=text, model=EMBEDDING_MODEL).data[0].embedding
        return embedding
    except Exception as e:
        print(f"Error in get_embedding: {e}")
        return None

def vector_search(user_query, collection):
    """
    Perform a vector search in the MongoDB collection based on the user query.

    Args:
    user_query (str): The user's query string.
    collection (MongoCollection): The MongoDB collection to search.

    Returns:
    list: A list of matching documents.
    """

    # Generate embedding for the user query
    query_embedding = get_embedding(user_query)
    print(len(query_embedding))

    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    # Define the vector search pipeline
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 50,  # Number of candidate matches to consider
                "limit": 5,  # Return top 5 matches
            }
        },
        {
            "$project": {
                "_id": 0,  # Exclude the _id field
                "embedding": 0,  # Exclude the embedding field
                "score": {
                    "$meta": "vectorSearchScore"  # Include the search score
                }
            }
        }
    ]

    # Execute the search
    results = collection.aggregate(pipeline)
    return list(results)



def handle_user_query(query, collection):

  get_knowledge = vector_search(query, collection)

  search_result = ''
  search_result_dict = {}
  it = 0
  for result in get_knowledge:
    search_result += (
        f"Title: {result.get('title', 'N/A')}, "
        f"Abstract: {result.get('abstract', 'N/A')}, "
        f"Date: {result.get('update_date', 'N/A')}, \n"
    )

  response = antropic_client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    system="You are an academic researcher with access to some research articles and information. Use the information you are given to provide supplemental information taking recency into account.",
    messages=[
        {"role": "user", "content": "Answer this user query: " + query + " with the following papers for context: " + search_result + ". In this format: {\"Idea\": idea, \"Title\": title}"}
    ]
  )

  return (response.content[0].text), search_result

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("path")
  args = parser.parse_args()

  target_dir = Path(args.path)
  # subprocess.Popen('rm *.md', shell=True)

  # uri = "mongodb+srv://yashkap:SOURCEAIPWD@arxiv-db.lumuebx.mongodb.net/?retryWrites=true&w=majority&appName=arxiv-db"
  uri = "mongodb+srv://yashkap:SOURCEAIPWD@source-ai.vcjts.mongodb.net/?retryWrites=true&w=majority&appName=source-ai"
  # Create a new client and connect to the server
  client = MongoClient(uri, server_api=ServerApi('1'))
  db = client['source-ai']
  arxiv_collection = db['arxiv2']

  # entries = arxiv_collection.find({},{ "_id": 0}).limit(10)
  # recs = []
  # index = 0
  # for index, data in enumerate(entries):
  #   rec = Recommendation(
  #       content= data["abstract"], 
  #       metadata= {
  #         "Title": re.sub('\s+', ' ', data["title"].strip()), 
  #         "Author": data["submitter"], 
  #         "Year": data["update_date"]
  #       }, 
  #       path=f"rec_{index}.md",
  #   )
  #   recs.append(rec)
  # return recs

  
  # idea = None
  # with open(target_dir, "w") as file:
  #   # Read each line in the file
  idea = open(target_dir, "r").read()
  # idea = "retrieval augmented generation with long form media content"
  query = "Give me the top 10 ideas for " + idea + " solely as a python list."
  response, source_information = handle_user_query(query, arxiv_collection)
  
  response = response[response.find("["):]
  response_json = json.loads(response)


  
  recs = []
  for index, data in enumerate(response_json):
    rec = Recommendation(
        content= data["Idea"], 
        metadata= {
          "Title": data["Title"]
        },
        path=f"rec_{index}.md", 
    )
    recs.append(rec)

  create_recommendations_page(recs=recs, idea_file=target_dir)

  
  # recs = get_recommendations()
  # create_recommendations_page(recs=recs, idea_file=target_dir)


  # delete_from_heading(target_dir)
  # create_recommendations_page(recs=recs, idea_file=target_dir)
