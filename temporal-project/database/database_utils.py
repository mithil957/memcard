from config import POCKETBASE_URL, PB_APP_USER_EMAIL, PB_APP_USER_PASSWORD
import aiohttp
from async_lru import alru_cache
from typing import Any
from urllib.parse import quote
from async_lru import alru_cache
from database.tps_utils import rate_limit

import time
import asyncio

# --- HELPFUL TYPES ---
PocketBaseToken = str


# --- Helpful Functions ---
@alru_cache(maxsize=1)
async def get_pocketbase_auth_token() -> PocketBaseToken:
    async with aiohttp.ClientSession() as session:
        payload = {
            "identity": PB_APP_USER_EMAIL,
            "password": PB_APP_USER_PASSWORD,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with session.post(f'{POCKETBASE_URL}/api/collections/_superusers/auth-with-password', headers=headers, json=payload) as response:
            admin_auth_record = await response.json()
            return admin_auth_record['token']


async def get_record[T](collection_name: str,
                        record_id: str,
                        options: dict[str, Any] = {}) -> T:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'{POCKETBASE_URL}/api/collections/{collection_name}/records/{record_id}',
            headers={
                "Accept": "application/json",
                "Authorization": await get_pocketbase_auth_token(),
            },
            params=options
        ) as response:
            data = await response.json()
            return data


async def get_all_records[T](collection_name: str, options: dict[str, Any] = {}) -> list[T]:
    all_records: list[dict[str, Any]] = []
    current_page = 1
    at_end_of_items = False

    async with aiohttp.ClientSession() as session:
        while not at_end_of_items:
            params = {
                **options,
                "perPage": 30,
                "page": current_page,
                "skipTotal": "true"
            }

            async with session.get(
                f'{POCKETBASE_URL}/api/collections/{collection_name}/records',
                headers={
                    "Accept": "application/json",
                    "Authorization": await get_pocketbase_auth_token(),
                },
                params=params
            ) as response:
                data = await response.json()
                if len(data.get("items", [])) != 0:
                    all_records.extend(data["items"])
                    current_page += 1
                else:
                    at_end_of_items = True

    return all_records  # type: ignore

@rate_limit(key="pocketbase", tps=200)
async def get_first_matching_record[T](collection_name: str, options: dict[str, Any] = {}) -> T | None:
    async with aiohttp.ClientSession() as session:
        params = {
            **options,
            "perPage": 30,
            "page": 1,
            "skipTotal": "true"
        }
        async with session.get(
            f'{POCKETBASE_URL}/api/collections/{collection_name}/records',
                headers={
                    "Accept": "application/json",
                    "Authorization": await get_pocketbase_auth_token(),
            },
                params=params
        ) as response:
            data = await response.json()
            if len(data.get("items", [])) != 0:
                return data["items"][0]
            else:
                return None


def construct_file_url(record, filename_in_pb) -> str:
    parts = [
        POCKETBASE_URL,
        "api",
        "files",
        quote(record['collectionId']),
        quote(record['id']),
        quote(filename_in_pb),
    ]
    return "/".join(parts)


async def download_file(file_url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            return await response.read()


async def save_record[T](collection_name: str, record: Any) -> T:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'{POCKETBASE_URL}/api/collections/{collection_name}/records',
            headers={
                "Accept": "application/json",
                "Authorization": await get_pocketbase_auth_token(),
            },
            json=record
        ) as response:
            data = await response.json()
            return data


async def delete_record(collection_name: str, record_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.delete(
            f'{POCKETBASE_URL}/api/collections/{collection_name}/records/{record_id}',
            headers={
                "Accept": "application/json",
                "Authorization": await get_pocketbase_auth_token(),
            }
        ) as response:
            return response.status


async def update_record[T](collection_name: str, record_id: str, record: Any) -> T:
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f'{POCKETBASE_URL}/api/collections/{collection_name}/records/{record_id}',
            headers={
                "Accept": "application/json",
                "Authorization": await get_pocketbase_auth_token(),
            },
            json=record
        ) as response:
            data = await response.json()
            return data
