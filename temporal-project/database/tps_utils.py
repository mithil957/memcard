import asyncio
import time
import functools
from typing import Literal

TPS_STATE = {}

TpsKey = Literal["embedding", "baml", "pocketbase"]

def rate_limit(key: TpsKey, tps: int):
    if tps <= 0:
        raise ValueError("TPS must be positive")
    if not key:
        raise ValueError("Key must be a non-empty string")
    
    min_interval = 1.0 / tps

    if key not in TPS_STATE:
        TPS_STATE[key] = {
            'lock': asyncio.Lock(),
            'last_call_time': 0.0,
            'min_interval': min_interval,
        }
    else:
        TPS_STATE[key]['min_interval'] = min_interval

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            state = TPS_STATE[key]
            lock = state['lock']

            async with lock:
                effective_min_interval = state['min_interval']
                current_time = time.monotonic()
                time_since_last_call = current_time - state['last_call_time']

                if time_since_last_call < effective_min_interval:
                    await asyncio.sleep(effective_min_interval - time_since_last_call)
                
                state['last_call_time'] = time.monotonic()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator