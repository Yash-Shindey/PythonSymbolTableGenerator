import datetime
import math
from typing import List, Dict, Tuple, Optional

class Employee:
    def __init__(self, name: str, id: int):
        self.name: str = name
        self.id: int = id

    def get_info(self) -> str:
        return f"Employee Name: {self.name}, ID: {self.id}"

def calculate_distances(points: List[Tuple[float, float]]) -> List[float]:
    """Calculate distances from the origin for a list of points."""
    return [math.sqrt(x**2 + y**2) for x, y in points]

def log_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"Function {func.__name__} with args {args} and kwargs {kwargs} returned {result}")
        return result
    return wrapper

@log_decorator
def factorial(n: int) -> int:
    """Compute the factorial of a number with a logging decorator."""
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

def get_time() -> str:
    """Returns the current time formatted as a string."""
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

def process_data(data: Dict[str, List[int]]) -> Dict[str, int]:
    """Process a dictionary of data to sum up lists of integers."""
    return {key: sum(values) for key, values in data.items()}

if __name__ == "__main__":
    emp = Employee("John Doe", 1001)
    print(emp.get_info())

    points = [(1.0, 2.0), (3.0, 4.0)]
    distances = calculate_distances(points)
    print("Distances from origin:", distances)

    print("Factorial of 5:", factorial(5))
    print("Current Time:", get_time())

    data = {"group1": [1, 2, 3], "group2": [4, 5, 6]}
    results = process_data(data)
    print("Processed Data:", results)
