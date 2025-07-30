import pymongo
import logging
from info import DATABASE_URL, DATABASE_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URL)
mydb = myclient[DATABASE_NAME]
mycol = mydb['CONNECTION']


async def add_connection(group_id: str, user_id: str) -> bool:
    try:
        user_data = mycol.find_one({"_id": user_id}, {"_id": 0, "active_group": 0})

        # Check for duplicate
        if user_data:
            group_ids = [x["group_id"] for x in user_data.get("group_details", [])]
            if group_id in group_ids:
                return False

        group_details = {"group_id": group_id}

        if not user_data:
            # New user
            data = {
                "_id": user_id,
                "group_details": [group_details],
                "active_group": group_id
            }
            mycol.insert_one(data)
        else:
            # Existing user, update
            mycol.update_one(
                {"_id": user_id},
                {
                    "$push": {"group_details": group_details},
                    "$set": {"active_group": group_id}
                }
            )
        return True

    except Exception as e:
        logger.exception(f"add_connection error: {e}")
        return False


async def active_connection(user_id: str) -> int | None:
    query = mycol.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
    return int(query["active_group"]) if query and query.get("active_group") else None


async def all_connections(user_id: str) -> list[str] | None:
    query = mycol.find_one({"_id": user_id}, {"_id": 0, "active_group": 0})
    if query:
        return [x["group_id"] for x in query.get("group_details", [])]
    return None


async def if_active(user_id: str, group_id: str) -> bool:
    query = mycol.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
    return bool(query and query.get("active_group") == group_id)


async def make_active(user_id: str, group_id: str) -> bool:
    try:
        result = mycol.update_one({"_id": user_id}, {"$set": {"active_group": group_id}})
        return result.modified_count > 0
    except Exception as e:
        logger.exception(f"make_active error: {e}")
        return False


async def make_inactive(user_id: str) -> bool:
    try:
        result = mycol.update_one({"_id": user_id}, {"$set": {"active_group": None}})
        return result.modified_count > 0
    except Exception as e:
        logger.exception(f"make_inactive error: {e}")
        return False


async def delete_connection(user_id: str, group_id: str) -> bool:
    try:
        result = mycol.update_one(
            {"_id": user_id},
            {"$pull": {"group_details": {"group_id": group_id}}}
        )

        if result.modified_count == 0:
            return False

        user_data = mycol.find_one({"_id": user_id}, {"_id": 0})

        # Update active group
        group_details = user_data.get("group_details", [])
        if group_details:
            if user_data.get("active_group") == group_id:
                last_group = group_details[-1]["group_id"]
                mycol.update_one({"_id": user_id}, {"$set": {"active_group": last_group}})
        else:
            mycol.update_one({"_id": user_id}, {"$set": {"active_group": None}})

        return True

    except Exception as e:
        logger.exception(f"delete_connection error: {e}")
        return False
