"""One-time codes for signup, login and password reset.

A code lives in Redis for ten minutes, or in process memory when Redis is not configured.
Every wrong guess is counted, and the fifth wrong guess deletes the code, so a six-digit
code cannot be brute-forced while it is valid. Issuing a new code clears the count.
"""

import secrets

from redis.asyncio import Redis

CODE_TTL_SECONDS = 600
MAX_FAILED_ATTEMPTS = 5


def new_code() -> str:
    """A six-digit code from the secrets module, which is safe for authentication."""
    return f"{secrets.randbelow(1_000_000):06d}"


class OneTimeCodes:
    """The codes of one kind, keyed by email under a Redis key prefix."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self._codes: dict[str, str] = {}
        self._failures: dict[str, int] = {}

    def _code_key(self, email: str) -> str:
        return f"{self.prefix}{email}"

    def _failures_key(self, email: str) -> str:
        return f"{self.prefix}failures:{email}"

    async def issue(self, redis: Redis | None, email: str) -> str:
        code = new_code()
        if redis is not None:
            await redis.setex(self._code_key(email), CODE_TTL_SECONDS, code)
            await redis.delete(self._failures_key(email))
        else:
            self._codes[email] = code
            self._failures.pop(email, None)
        return code

    async def current(self, redis: Redis | None, email: str) -> str | None:
        if redis is None:
            return self._codes.get(email)
        raw = await redis.get(self._code_key(email))
        if isinstance(raw, bytes):
            return raw.decode()
        return str(raw) if raw else None

    async def record_failure(self, redis: Redis | None, email: str) -> None:
        """Count a wrong guess, and delete the code once the guesses run out."""
        if redis is not None:
            failures = await redis.incr(self._failures_key(email))
            await redis.expire(self._failures_key(email), CODE_TTL_SECONDS)
        else:
            failures = self._failures.get(email, 0) + 1
            self._failures[email] = failures
        if int(failures) >= MAX_FAILED_ATTEMPTS:
            await self.consume(redis, email)

    async def consume(self, redis: Redis | None, email: str) -> None:
        if redis is not None:
            await redis.delete(self._code_key(email), self._failures_key(email))
        else:
            self._codes.pop(email, None)
            self._failures.pop(email, None)
