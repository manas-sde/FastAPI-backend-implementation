# FastAPI creates fastapi app instance
# HTTPException will be used for throwing HTTP exception
# Query is a FastAPI class which is used to declare query parameters for an endpoint.
from fastapi import FastAPI, HTTPException, Query

# BaseModel is a Pydantic class which is used to declare the structure of the request and response data in the API.
from pydantic import BaseModel

# For establishing connection with Mongo cluster
from pymongo import MongoClient

# UpdateOne will be used for combining multiple update query
from pymongo.operations import UpdateOne

# For converting id to mongo object id
from bson.objectid import ObjectId

# List will be used to declare list data type
# Optinal is a type hint from the typing module which is used to declare an optional field in a Pydantic model.
from typing import List, Optional



# Creates a FastAPI instance
app = FastAPI()

# Creates a MongoClient instance and connects to MongoDB server at the specified URI
client = MongoClient('mongodb://localhost:27017/')  

# Selects the database named 'mydatabase' from the MongoClient instance
db = client['cosmoDB'] 



# User class represents User's collection strtucture which store user detail such as name and email.
class User(BaseModel):
    name: str
    email: str

# Org class represent Organization's collection structure.
class Org(BaseModel):
    name: str

# Permission classs represents structure of Permission collection which store user_id, organization name and role granted(READ, WRITE, ADMIN)
class Permission(BaseModel):
    user_id: str
    org_name: str
    role: str




#----------------- User route starts ---------------


# Endpoint for creating a new user
'''
Payload
    - name
    - email
Response
    - id (id of last inserted user)
'''
@app.post("/users", tags=["users"])
def create_user(user: User):
    result = db.users.insert_one(user.dict())
    return {
        "id": str(result.inserted_id)
        }





# Endpoint for getting all list of users
# Filter available by name
'''
Payload
    - limit (Maximum number of users required in response)
    - offset 
    - name (string displaying name required in filter)
Response
    - count (Total number of such users fetched from database) (In case of filter it only counts number of user whose name contains filter value)
    - data (type:dict)
        - id (user id)
        - name (user name)
        - email (user email)
'''
@app.get("/users", tags=["users"])
def list_users(limit: int = 10, offset: int = 0, name: Optional[str] = None):
    query = {}
    if name:
        query = {"name": {"$regex": name, "$options": "i"}}
    users = db.users.find(query).skip(offset).limit(limit)
    count = db.users.count_documents(query)
    data = []
    for user in users:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        data.append({
            "id" : user["_id"],
            "name" : user["name"],
            "email" : user["email"]
        })
    
    return {"count": count, "data": data}




# Endpoint for fetching single user
'''
Paramater (as url slug)
    - user_id (id of requested user)

Response
    - id (user id)
    - name (user name)
    - email (user email)
'''
@app.get("/users/{user_id}", tags=["users"])
def get_user(user_id: str):
    user = db.users.find_one({"_id": ObjectId(user_id)})

    # Validating if user exist or not
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return {
        "id" : user["_id"],
        "name" : user["name"],
        "email" : user["email"]
    }

#----------- User route ends --------------------------




#----------- Organization route starts ----------------


# Endpoint for creating a new organization 

'''
Payload
    - org (type: dict)
        - name (name of organization)

Response
    - id (id of last inserted organisation)

'''
@app.post("/orgs", tags=["orgs"])
def create_org(org: Org):
    if db.orgs.find_one({"name": org.name}):
        raise HTTPException(status_code=400, detail="Org already exists")
    result = db.orgs.insert_one(org.dict())
    return {"id": str(result.inserted_id)}





# Endpoint for getting all list of organisation

# Filter available by name
'''
Payload
    - limit (Maximum number of users required in response)
    - offset 
    - name (string displaying name required in filter)
Response
    - count (Total number of organisation fetched from database) (In case of filter it only counts number of organisation whose name contains filter value)
    - data (type:dict)
        - name (organisation name)
'''
@app.get("/orgs", tags=["orgs"])
def list_orgs(limit: int = 10, offset: int = 0, name: Optional[str] = None):
    query = {}
    if name:
        query = {"name": {"$regex": name, "$options": "i"}}
    orgs = db.orgs.find(query).skip(offset).limit(limit)
    count = db.orgs.count_documents(query)
    data = []
    
    for org in orgs:
        org.pop("_id")
        data.append(org)
    
    return {"count": count, "data": data}





# Endpoint for allocating/updating permission to a user
'''
Payload
    - permissions (type:list)
        - Each element of this list will be a dict of permission type object which contains
            - user_id (id of user)
            - org_name (name of organisation)
            - role ("READ", "WRITE", "ADMIN")
Response
    - count (number of permission record inserted/updated)
'''
@app.post("/permissions", tags=["permissions"])
def update_permissions(permissions: List[Permission]):


    # Define list of PyMongo operations to perform in bulk
    operations = []
    for permission in permissions:

        # User id validation
        if not db.users.find_one({"_id": ObjectId(permission.user_id)}):
            raise HTTPException(status_code=400, detail="User not found")
        
        # Organisation name validation
        if not db.orgs.find_one({"name": permission.org_name}):
            raise HTTPException(status_code=400, detail="Org not found")
        
        # Role type validation
        if not permission.role in ["READ", "WRITE", "ADMIN"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        

        filter_query = {"user_id": permission.user_id, "org_name": permission.org_name}
        update_query = {"$set": {"role": permission.role}}
        operations.append(UpdateOne(filter_query, update_query, upsert=True))


    # Execute bulk write operation
    result = db.permissions.bulk_write(operations)

    # Return number of permissions created or modified
    return{
        "count" : result.upserted_count
    }






# Endpoint for removing permission of any user
'''
Payload
    - user_id (user id)
    - org_name (name of organisation)
    - role ("READ","WRITE","ADMIN")
Reposnse
    - deleted_count (count of records deleted successfully)
'''
@app.delete("/permissions", tags=["permissions"])
def delete_permissions(permissions: List[Permission]):     
    permissions_list = []

    for permission in permissions:
        # Converting all permission type object to dict
        permissions_list.append(permission.__dict__)

    # Using or operator for all permission to be deleted with a single mongo connection   
    result = db.permissions.delete_many({"$or":permissions_list})

    if result.deleted_count == 0:
        message = "No user with given permission exists"
    else:
        message = f"{result.deleted_count} permissions successfully removed"

    # returning count of deleted records
    return {
        "deleted_count": result.deleted_count,
        "message" : message
    }