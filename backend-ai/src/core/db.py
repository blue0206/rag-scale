from ..db.mongo import users_collection


async def setup_db_index():
    """
    This function creates an index on the users collection for the username field.
    """

    await users_collection.create_index("username", unique=True)
    print("Database index on 'username' field created successfully.")
