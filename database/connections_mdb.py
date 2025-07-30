import pymongo
import logging
from info import DATABASE_URL, DATABASE_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URL)
mydb = myclient[DATABASE_NAME]
mycol = mydb['CONNECTION']


async def add_connection(group_id: int, user_id: int) -> bool:
    try:
        query = mycol.find_one(
            {"_id": user_id},
            {"_id": 0, "active_group": 0}
        )
        if query:
            group_ids = [x["group_id"] for x in query.get("group_details", [])]
            if group_id in group_ids:
                return False

        group_details = {"group_id": group_id}

        if query is None:
            data = {
                "_id": user_id,
                "group_details": [group_details],
                "active_group": group_id,
            }
            mycol.insert_one(data)
        else:
            mycol.update_one(
                {"_id": user_id},
                {
                    "$push": {"group_details": group_details},
                    "$set": {"active_group": group_id}
                }
            )
        return True
    except Exception as e:
        logger.exception(f"Failed to add connection for {user_id} → {group_id}: {e}", exc_info=True)
        return False


async def active_connection(user_id: int) -> int | None:
    try:
        query = mycol.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
        return int(query["active_group"]) if query and query.get("active_group") else None
    except Exception as e:
        logger.exception(f"Error fetching active connection for {user_id}: {e}")
        return None


async def all_connections(user_id: int) -> list[int] | None:
    try:
        query = mycol.find_one({"_id": user_id}, {"_id": 0, "active_group": 0})
        if query:
            return [x["group_id"] for x in query.get("group_details", [])]
        return None
    except Exception as e:
        logger.exception(f"Error getting all connections for {user_id}: {e}")
        return None


async def if_active(user_id: int, group_id: int) -> bool:
    try:
        query = mycol.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
        return query is not None and query.get("active_group") == group_id
    except Exception as e:
        logger.exception(f"Error checking if group {group_id} is active for {user_id}: {e}")
        return False


async def make_active(user_id: int, group_id: int) -> bool:
    try:
        update = mycol.update_one(
            {"_id": user_id},
            {"$set": {"active_group": group_id}}
        )
        return update.modified_count > 0
    except Exception as e:
        logger.exception(f"Error setting group {group_id} as active for {user_id}: {e}")
        return False


async def make_inactive(user_id: int) -> bool:
    try:
        update = mycol.update_one(
            {"_id": user_id},
            {"$set": {"active_group": None}}
        )
        return update.modified_count > 0
    except Exception as e:
        logger.exception(f"Error making all connections inactive for {user_id}: {e}")
        return False


async def delete_connection(user_id: int, group_id: int) -> bool:
    try:
        update = mycol.update_one(
            {"_id": user_id},
            {"$pull": {"group_details": {"group_id": group_id}}}
        )
        if update.modified_count == 0:
            return False

        query = mycol.find_one({"_id": user_id})
        group_details = query.get("group_details", [])
        active_group = query.get("active_group")

        if group_details:
            if active_group == group_id:
                # Make last group in list active
                new_active = group_details[-1]["group_id"]
                mycol.update_one(
                    {"_id": user_id},
                    {"$set": {"active_group": new_active}}
                )
        else:
            mycol.update_one(
                {"_id": user_id},
                {"$set": {"active_group": None}}
            )
        return True
    except Exception as e:
        logger.exception(f"Failed to delete connection {group_id} for {user_id}: {e}", exc_info=True)
        return False
