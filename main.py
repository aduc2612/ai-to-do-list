import json
import uuid
from dataclasses import dataclass
from langchain.tools import tool


from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from dataclasses import dataclass


@dataclass
class Task:
    title: str
    due_date: str

DATABASE_FILE = "data.json"

def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    return data

def write_json(file_path, updated_data):
    with open(file_path, 'w') as file:
        json.dump(updated_data, file)
    return True

def generate_id():
    return str(uuid.uuid4())

@tool
def create_task(title: str, due_date : str=""):
    """
    Use this to create a new task in the to-do list.
    Returns the ID of the created task if successful, else return False.
    """
    if not title:
        return False
    new_id = generate_id()
    new_task = {
        "id": new_id,
        "title": title,
        "due_date": due_date,
    }
    database = read_json(DATABASE_FILE)
    database.append(new_task)
    write_json(DATABASE_FILE, database)
    return new_id

@tool
def get_tasks() -> list:
    """
    Use this to retrieve all current tasks. 
    Always call this before updating or deleting to get the correct IDs.
    Returns the database in list format
    """
    database = read_json(DATABASE_FILE)
    return database

@tool
def update_task(task_id : str, **updates) -> bool:
    """
    Use this to update information about a task
    Returns True if the action is successful, else False
    """
    database = read_json(DATABASE_FILE)
    if len(database) == 0:
        return False
    for i in range(len(database)):
        if database[i]['id'] != task_id:
            continue
        allowed_fields = {"title", "due_date"}
        for key, value in updates.items():
            if key in allowed_fields:
                database[i][key] = value
        return write_json(DATABASE_FILE, database)
    return False

@tool
def delete_task(task_id : str) -> bool:
    """
    Deletes a task given its unique integer ID.
    Returns True if successful, else returns False
    """
    database = read_json(DATABASE_FILE)
    for i in range(len(database)):
        if database[i]['id'] != task_id:
            continue
        del database[i]
        return write_json(DATABASE_FILE, database)
    return False


SYSTEM_PROMPT = """
You are a precise To-Do List Assistant.
When the user asks to do something with a task, always confirm if the action was successful.
Never show the ID to the user.
Keep everything concise, straight to the point.
When the user finishes a task, delete it.
"""

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-20b"
)

agent = create_agent(
    model = model,
    tools = [create_task, get_tasks, update_task, delete_task],
    system_prompt = SYSTEM_PROMPT
)

def ask_agent(query: str):
    inputs = {"messages": [("user", query)]}
    for s in agent.stream(inputs, stream_mode="values"):
        message = s["messages"][-1]
        if hasattr(message, "content"):
            print(message.content)

ask_agent("I have to watch Diddy vs Epstein")
