import logging
import time

from fastapi import Request

logger = logging.getLogger(__name__)

class CounterMW:
    def middle_ware_prueba(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000000
        logger.info(f"process time {process_time:.3f} ms")
        return response