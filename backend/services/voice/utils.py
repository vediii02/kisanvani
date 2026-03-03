import asyncio
from typing import AsyncIterator, Any

async def merge_async_iters(*iters: AsyncIterator) -> AsyncIterator[Any]:
    """Merge multiple async iterators into a single stream."""
    queue = asyncio.Queue()

    async def _drain(it: AsyncIterator):
        try:
            async for item in it:
                await queue.put(item)
        except Exception as e:
            await queue.put(e)
        finally:
            await queue.put(None)

    tasks = [asyncio.create_task(_drain(it)) for it in iters]
    active_tasks = len(tasks)

    try:
        while active_tasks > 0:
            item = await queue.get()
            if item is None:
                active_tasks -= 1
            elif isinstance(item, Exception):
                print(f"[Merge Error] {item}")
            else:
                yield item
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
