import math


def _hungarian(rows, real_cols, tie_costs):
    """Solve rows <= real_cols, allowing rows to use dummy columns."""
    row_count = len(rows)
    column_count = real_cols + row_count
    costs = []
    for row_index, row in enumerate(rows):
        encoded = []
        for column_index, value in enumerate(row):
            encoded.append(
                (math.inf, 0, 0)
                if math.isinf(value)
                else (0, value, tie_costs[row_index][column_index])
            )
        encoded.extend([(1, 0, 0)] * row_count)
        costs.append(encoded)

    # Triples compare lexicographically: first minimize dummy assignments,
    # then actual cost, then the assignment vector encoded in tie_costs.
    zero = (0, 0, 0)
    u = [zero] * (row_count + 1)
    v = [zero] * (column_count + 1)
    matched = [0] * (column_count + 1)
    way = [0] * (column_count + 1)

    for row_number in range(1, row_count + 1):
        matched[0] = row_number
        column = 0
        minimum = [(math.inf, 0, 0)] * (column_count + 1)
        used = [False] * (column_count + 1)

        while True:
            used[column] = True
            row = matched[column]
            delta = (math.inf, 0, 0)
            next_column = 0
            for candidate in range(1, column_count + 1):
                if used[candidate]:
                    continue
                value = costs[row - 1][candidate - 1]
                current = (
                    value[0] - u[row][0] - v[candidate][0],
                    value[1] - u[row][1] - v[candidate][1],
                    value[2] - u[row][2] - v[candidate][2],
                )
                if current < minimum[candidate]:
                    minimum[candidate] = current
                    way[candidate] = column
                if minimum[candidate] < delta:
                    delta = minimum[candidate]
                    next_column = candidate

            for candidate in range(column_count + 1):
                if used[candidate]:
                    matched_row = matched[candidate]
                    u[matched_row] = (
                        u[matched_row][0] + delta[0],
                        u[matched_row][1] + delta[1],
                        u[matched_row][2] + delta[2],
                    )
                    v[candidate] = (
                        v[candidate][0] - delta[0],
                        v[candidate][1] - delta[1],
                        v[candidate][2] - delta[2],
                    )
                else:
                    minimum[candidate] = (
                        minimum[candidate][0] - delta[0],
                        minimum[candidate][1] - delta[1],
                        minimum[candidate][2] - delta[2],
                    )

            column = next_column
            if matched[column] == 0:
                break

        while column:
            previous = way[column]
            matched[column] = matched[previous]
            column = previous

    assignment = [None] * row_count
    for column in range(1, real_cols + 1):
        if matched[column]:
            assignment[matched[column] - 1] = column - 1
    return assignment


def min_cost_assignment(cost) -> list[int | None]:
    """Return each worker's task index, or None when no finite pair is used."""
    worker_count = len(cost)
    if not worker_count:
        return []
    task_count = len(cost[0])
    if any(len(row) != task_count for row in cost):
        raise ValueError("cost must be rectangular")
    if not task_count:
        return [None] * worker_count

    base = task_count + 1
    if worker_count <= task_count:
        weights = [base ** (worker_count - 1 - worker)
                   for worker in range(worker_count)]
        tie_costs = [[task * weights[worker] for task in range(task_count)]
                      for worker in range(worker_count)]
        return _hungarian(cost, task_count, tie_costs)

    # Transpose so the Hungarian core always has no more rows than columns.
    transposed = [[cost[worker][task] for worker in range(worker_count)]
                  for task in range(task_count)]
    weights = [base ** (worker_count - 1 - worker)
               for worker in range(worker_count)]
    tie_costs = [[(task - task_count) * weights[worker]
                  for worker in range(worker_count)]
                 for task in range(task_count)]
    task_to_worker = _hungarian(transposed, worker_count, tie_costs)
    assignment = [None] * worker_count
    for task, worker in enumerate(task_to_worker):
        if worker is not None:
            assignment[worker] = task
    return assignment


def demo():
    import itertools
    import time

    assert min_cost_assignment([[4, 1, 3], [2, 0, 5], [3, 2, 2]]) == [1, 0, 2]
    assert min_cost_assignment([[0, 0], [0, 0]]) == [0, 1]
    assert min_cost_assignment([[4, 1], [2, 3], [0, 5]]) == [1, None, 0]
    assert min_cost_assignment([[4, 1, 9], [2, 0, 5]]) == [1, 0]
    assert min_cost_assignment([
        [math.inf, 2, math.inf],
        [math.inf, math.inf, math.inf],
        [1, math.inf, math.inf],
    ]) == [1, None, 0]

    seed = 0xC0FFEE
    for _ in range(200):
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        size = 1 + seed % 6
        matrix = []
        for _ in range(size):
            row = []
            for _ in range(size):
                seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
                row.append(seed % 17 - 8)
            matrix.append(row)

        got = min_cost_assignment(matrix)
        got_cost = sum(matrix[row][column] for row, column in enumerate(got))
        brute_cost = math.inf
        for permutation in itertools.permutations(range(size)):
            candidate = sum(matrix[row][permutation[row]] for row in range(size))
            if candidate < brute_cost:
                brute_cost = candidate
        assert got_cost == brute_cost
        assert got == min_cost_assignment(matrix)

    matrix = [[(row * 17 + column * 11) % 101
               for column in range(80)] for row in range(12)]
    start = time.perf_counter()
    for _ in range(100):
        min_cost_assignment(matrix)
    elapsed = (time.perf_counter() - start) / 100
    print("12x80: %.6f s/call" % elapsed)


if __name__ == "__main__":
    demo()
