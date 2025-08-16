from datetime import datetime, timedelta
from pathlib import Path
import secrets
from typing import Optional
import aiofiles
from aiofiles import os as aio_os

DATA_FILE_EXT = ".dat"
EXPIRATION_FILE_EXT = ".exp"


class DiskStorageBackend:
    def __init__(self, storage_path: Path, timeout_seconds: int):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds

    async def store_data(self, data: bytes) -> str:
        code = await self._ensure_unique_code()
        expiration_time = datetime.now() + timedelta(seconds=self.timeout_seconds)

        async with aiofiles.open(self._data_file(code), mode="wb") as f:
            await f.write(data)
        async with aiofiles.open(self._expiration_file(code), mode="w") as f:
            await f.write(expiration_time.isoformat())

        return code

    async def retrieve_data(self, code: str) -> Optional[bytes]:
        if not await self._exists(code):
            return None
        async with aiofiles.open(self._data_file(code), mode="rb") as f:
            return await f.read()

    async def delete_data(self, code: str) -> None:
        await aio_os.remove(self._data_file(code))
        await aio_os.remove(self._expiration_file(code))

    def _data_file(self, code: str) -> Path:
        return self.storage_path / f"{code}{DATA_FILE_EXT}"

    def _expiration_file(self, code: str) -> Path:
        return self.storage_path / f"{code}{EXPIRATION_FILE_EXT}"

    def _generate_human_readable_code(self) -> str:
        vowels = "aeiou"
        consonants = "bcdfghjklmnpqrstvwxyz"

        code = ""
        for i in range(6):
            if i % 2 == 0:
                code += secrets.choice(consonants)
            else:
                code += secrets.choice(vowels)

        code += str(secrets.randbelow(100)).zfill(2)
        return code

    async def _exists(self, code: str) -> bool:
        expiration_file = self._expiration_file(code)
        if not await aio_os.path.exists(expiration_file):
            return False

        async with aiofiles.open(expiration_file, mode="r") as f:
            expiration = await f.read()
            expiration_time = datetime.fromisoformat(expiration.strip())

        if expiration_time < datetime.now():
            await self.delete_data(code)
            return False
        return True

    async def _ensure_unique_code(self) -> str:
        max_attempts = 100
        for _ in range(max_attempts):
            code = self._generate_human_readable_code()
            exists = await self._exists(code)
            if not exists:
                return code

        raise Exception("Unable to generate unique code")
