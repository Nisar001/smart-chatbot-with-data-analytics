import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://app:app@postgres:5432/smart_chatbot",
)


async def wait_for_db(max_attempts: int = 30, delay_seconds: int = 2) -> None:
    engine = create_async_engine(DATABASE_URL, future=True)

    try:
        for attempt in range(1, max_attempts + 1):
            try:
                async with engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
                print("PostgreSQL is ready.")
                return
            except Exception as exc:
                print(f"Attempt {attempt}/{max_attempts}: PostgreSQL not ready yet: {exc}")
                await asyncio.sleep(delay_seconds)
    finally:
        await engine.dispose()

    raise RuntimeError("PostgreSQL did not become available in time.")


if __name__ == "__main__":
    asyncio.run(wait_for_db())
