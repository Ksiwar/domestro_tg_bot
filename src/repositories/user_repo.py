from bson import ObjectId
from aiogram.fsm.storage.mongo import MongoStorage
from models.user import User, Ip, Service
from config.settings import Settings

class UserRepository:
    async def aggregate_ips_and_services(collection):
        """Агрегирует данные по IP и сервисам."""
        pipeline = [
            {
                "$facet": {
                    "all_ips": [
                        {"$unwind": {
                            "path": "$data.user.ips",
                            "preserveNullAndEmptyArrays": False,
                            "includeArrayIndex": "data.user.ips.index"
                        }},
                        {"$project": {
                            "ip": "$data.user.ips.ip",
                            "name": "$data.user.ips.name",
                            "index": "$data.user.ips.index",
                            "is_available": "$data.user.ips.is_available",
                            "telegram_id": "$data.user.chat_id"
                        }},
                        {"$group": {
                            "_id": None,
                            "all_ips": {"$push": "$$ROOT"}
                        }}
                    ],
                    "all_services": [
                        {"$unwind": {
                            "path": "$data.user.service",
                            "preserveNullAndEmptyArrays": False,
                            "includeArrayIndex": "ips.index",
                            "includeArrayIndex": "data.user.service.index"
                        }},
                        {"$project": {
                            "host": "$data.user.service.host",
                            "name": "$data.user.service.name",
                            "index": "$data.user.service.index",
                            "is_available": "$data.user.service.is_available",
                            "telegram_id": "$data.user.chat_id"
                        }},
                        {"$group": {
                            "_id": None,
                            "all_services": {"$push": "$$ROOT"}
                        }}
                    ]
                }
            },
            {
                "$project": {
                    "all_ips": {
                        "$ifNull": [{"$arrayElemAt": ["$all_ips.all_ips", 0]}, []]
                    },
                    "all_services": {
                        "$ifNull": [{"$arrayElemAt": ["$all_services.all_services", 0]}, []]
                    }
                }
            }
        ]
        
        cursor = collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0] if result else {"all_ips": [], "all_services": []}

    @staticmethod
    async def update_user_status(collection, id: str, index: int, field: str, is_available: bool):
        """Обновляет статус пользователя."""
        update_query = {f"data.user.{field}.{index}.is_available": is_available}
        await collection.update_one(
            {"_id": id},
            {"$set": update_query}
        )
    
    @staticmethod
    async def get_all_users(collection):
        users = []
        projection = {"data.user": 1, "_id": 0}
        async for doc in collection.find({}, projection):
            user = doc.get('data', {}).get('user', {})
            if user is not None:
                users.append(user)
        return users

