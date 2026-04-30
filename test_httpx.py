import asyncio
import httpx

async def f():
    try:
        async with httpx.AsyncClient(timeout=0.001) as c:
            await c.get('https://8.8.8.8')
    except Exception as e:
        print("str:", repr(str(e)))
        
asyncio.run(f())
