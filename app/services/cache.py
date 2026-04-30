import json
from datetime import datetime, timezone

import aiosqlite

from app.core.config import Settings


class RoadmapCache:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def init(self) -> None:
        async with aiosqlite.connect(self.settings.sqlite_db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS roadmap_cache (
                    normalized_skill TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    roadmap_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    PRIMARY KEY (normalized_skill, request_hash)
                )
                """
            )
            await db.commit()

    async def get(self, normalized_skill: str, request_hash: str) -> dict | None:
        if not self.settings.enable_cache:
            return None
        await self.init()
        async with aiosqlite.connect(self.settings.sqlite_db_path) as db:
            cursor = await db.execute(
                "SELECT roadmap_json FROM roadmap_cache WHERE normalized_skill = ? AND request_hash = ?",
                (normalized_skill, request_hash),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        data.setdefault("metadata", {})["cached"] = True
        return data

    async def set(self, normalized_skill: str, request_hash: str, roadmap: dict, model_used: str) -> None:
        if not self.settings.enable_cache:
            return
        await self.init()
        to_store = json.loads(json.dumps(roadmap))
        to_store.setdefault("metadata", {})["cached"] = False
        async with aiosqlite.connect(self.settings.sqlite_db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO roadmap_cache
                (normalized_skill, request_hash, roadmap_json, created_at, model_used)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    normalized_skill,
                    request_hash,
                    json.dumps(to_store),
                    datetime.now(timezone.utc).isoformat(),
                    model_used,
                ),
            )
            await db.commit()
