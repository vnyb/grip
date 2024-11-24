import inspect
from typing import List, Set

class _Empty:
    pass

SPECIAL_MEMBERS = {*dir(_Empty), "__annotations__"}

def listattr(obj) -> List[str]:
    return [
        name for name, _ in inspect.getmembers(obj, lambda m:not(inspect.isroutine(m)))
        if name not in SPECIAL_MEMBERS
    ]
