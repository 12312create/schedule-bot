import time
import random
import logging
from typing import List, Optional, Any, Tuple
logger = logging.getLogger(__name__)

def bubble_sort(arr: List[Any], key=None, reverse: bool = False) -> List[Any]:
    arr = arr.copy()
    n = len(arr)
    comparisons = 0
    swaps = 0
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            comparisons += 1
            val_j = key(arr[j]) if key else arr[j]
            val_j1 = key(arr[j + 1]) if key else arr[j + 1]
            should_swap = (val_j > val_j1) if not reverse else (val_j < val_j1)
            if should_swap:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swaps += 1
                swapped = True

        if not swapped:
            break

    logger.debug(f"BubbleSort: n={n}, comparisons={comparisons}, swaps={swaps}")
    return arr

def quick_sort(arr: List[Any], key=None, reverse: bool = False) -> List[Any]:
    if len(arr) <= 1:
        return arr.copy()

    mid = len(arr) // 2
    pivot = arr[mid]
    pivot_val = key(pivot) if key else pivot

    less = []
    equal = []
    greater = []

    for item in arr:
        val = key(item) if key else item
        if val < pivot_val:
            less.append(item)
        elif val == pivot_val:
            equal.append(item)
        else:
            greater.append(item)

    if not reverse:
        return quick_sort(less, key, reverse) + equal + quick_sort(greater, key, reverse)
    else:
        return quick_sort(greater, key, reverse) + equal + quick_sort(less, key, reverse)

def linear_search(arr: List[Any], target: Any, key=None) -> int:

    for i, item in enumerate(arr):
        val = key(item) if key else item
        if val == target:
            logger.debug(f"LinearSearch: found at index {i} after {i + 1} comparisons")
            return i
    logger.debug(f"LinearSearch: '{target}' not found after {len(arr)} comparisons")
    return -1

def linear_search_all(arr: List[Any], target: Any, key=None) -> List[int]:
    indices = []
    for i, item in enumerate(arr):
        val = key(item) if key else item
        if val == target:
            indices.append(i)
    return indices

def linear_search_contains(arr: List[Any], keyword: str, key=None) -> List[Any]:
    results = []
    keyword_lower = keyword.lower()
    for item in arr:
        val = str(key(item) if key else item).lower()
        if keyword_lower in val:
            results.append(item)
    return results

def binary_search(arr: List[Any], target: Any, key=None) -> int:
    left, right = 0, len(arr) - 1
    iterations = 0
    while left <= right:
        iterations += 1
        mid = (left + right) // 2
        mid_val = key(arr[mid]) if key else arr[mid]

        if mid_val == target:
            logger.debug(f"BinarySearch: found at index {mid} after {iterations} iterations")
            return mid
        elif mid_val < target:
            left = mid + 1
        else:
            right = mid - 1

    logger.debug(f"BinarySearch: not found after {iterations} iterations")
    return -1

def binary_search_leftmost(arr: List[Any], target: Any, key=None) -> int:
    left, right = 0, len(arr)
    while left < right:
        mid = (left + right) // 2
        mid_val = key(arr[mid]) if key else arr[mid]
        if mid_val < target:
            left = mid + 1
        else:
            right = mid
    return left if left < len(arr) else -1

def sort_schedule_by_time(schedule: List[dict]) -> List[dict]:
    return quick_sort(schedule, key=lambda x: x.get("time_start", "00:00"))

def sort_schedule_bubble(schedule: List[dict]) -> List[dict]:
    return bubble_sort(schedule, key=lambda x: x.get("time_start", "00:00"))

def search_subject(schedule: List[dict], subject_name: str) -> List[dict]:
    return linear_search_contains(schedule, subject_name, key=lambda x: x.get("subject", ""))

def search_teacher(schedule: List[dict], teacher_name: str) -> List[dict]:
    return linear_search_contains(schedule, teacher_name, key=lambda x: x.get("teacher", ""))

def find_lesson_by_time(sorted_schedule: List[dict], time_str: str) -> int:
    return binary_search(sorted_schedule, time_str, key=lambda x: x.get("time_start", ""))

def benchmark_sorting(sizes: List[int] = None) -> dict:
    if sizes is None:
        sizes = [10, 100, 500, 1000]

    results = {}
    print("\n" + "=" * 65)
    print(f"{'Алгоритм':<20} {'n':>6} {'Время (сек)':>15} {'Сложность':>12}")
    print("=" * 65)

    for n in sizes:
        data = [random.randint(1, 10000) for _ in range(n)]
        results[n] = {}
        arr_copy = data.copy()
        t_start = time.perf_counter()
        bubble_sort(arr_copy)
        t_bubble = time.perf_counter() - t_start
        results[n]["bubble"] = t_bubble
        print(f"{'Bubble Sort':<20} {n:>6} {t_bubble:>15.6f} {'O(n²)':>12}")
        arr_copy = data.copy()
        t_start = time.perf_counter()
        quick_sort(arr_copy)
        t_quick = time.perf_counter() - t_start
        results[n]["quick"] = t_quick
        print(f"{'Quick Sort':<20} {n:>6} {t_quick:>15.6f} {'O(n log n)':>12}")

        arr_copy = data.copy()
        t_start = time.perf_counter()
        sorted(arr_copy)
        t_builtin = time.perf_counter() - t_start
        results[n]["builtin"] = t_builtin
        print(f"{'Python sorted()':<20} {n:>6} {t_builtin:>15.6f} {'O(n log n)':>12}")
        print("-" * 65)

    return results

def benchmark_searching(n: int = 1000) -> dict:
    data = sorted([random.randint(1, n * 10) for _ in range(n)])
    target = data[n // 2]  # Элемент в середине

    results = {}
    print(f"\n--- Поиск: n={n}, target={target} ---")

    t_start = time.perf_counter()
    for _ in range(100):
        linear_search(data, target)
    t_linear = (time.perf_counter() - t_start) / 100
    results["linear"] = t_linear
    print(f"Linear Search:  {t_linear:.8f} сек | O(n)")

    t_start = time.perf_counter()
    for _ in range(100):
        binary_search(data, target)
    t_binary = (time.perf_counter() - t_start) / 100
    results["binary"] = t_binary
    print(f"Binary Search:  {t_binary:.8f} сек | O(log n)")

    if t_linear > 0:
        speedup = t_linear / t_binary if t_binary > 0 else float("inf")
        print(f"Binary ускорение: {speedup:.1f}x быстрее Linear")

    return results

def print_big_o_analysis():
    print("\n" + "=" * 75)
    print("   АНАЛИЗ СЛОЖНОСТИ АЛГОРИТМОВ (Big-O Notation)")
    print("=" * 75)
    table = [
        ("Bubble Sort", "O(n)", "O(n²)", "O(n²)", "O(1)"),
        ("Quick Sort", "O(n log n)", "O(n log n)", "O(n²)", "O(log n)"),
        ("Linear Search", "O(1)", "O(n)", "O(n)", "O(1)"),
        ("Binary Search", "O(1)", "O(log n)", "O(log n)", "O(1)"),
    ]
    header = f"{'Алгоритм':<18} {'Лучший':>12} {'Средний':>12} {'Худший':>12} {'Память':>10}"
    print(header)
    print("-" * 75)
    for row in table:
        print(f"{row[0]:<18} {row[1]:>12} {row[2]:>12} {row[3]:>12} {row[4]:>10}")
    print("=" * 75)

if __name__ == "__main__":
    print_big_o_analysis()
    benchmark_sorting([10, 50, 100])
    benchmark_searching(500)
    demo_schedule = [
        {"time_start": "10:00", "subject": "Python программалау", "teacher": "Сапакова С.З."},
        {"time_start": "08:00", "subject": "SQL кіріспе", "teacher": "Козина Л.А."},
        {"time_start": "12:10", "subject": "Физика", "teacher": "Ерназаров Т.И."},
        {"time_start": "20:30", "subject": "SQL СОӨЖ", "teacher": "—"},
    ]

    print("\n--- Сортировка расписания (Quick Sort) ---")
    sorted_sched = sort_schedule_by_time(demo_schedule)
    for s in sorted_sched:
        print(f"  {s['time_start']} — {s['subject']}")

    print("\n--- Поиск предмета (Linear Search) ---")
    found = search_subject(demo_schedule, "python")
    for f in found:
        print(f"  Найдено: {f['subject']} у {f['teacher']}")

    print("\n--- Бинарный поиск пары по времени ---")
    idx = find_lesson_by_time(sorted_sched, "10:00")
    if idx >= 0:
        print(f"  Найдено на индексе {idx}: {sorted_sched[idx]['subject']}")