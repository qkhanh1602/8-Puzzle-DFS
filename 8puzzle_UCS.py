import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import heapq
import random
import time


START_DEFAULT = "531620478"
GOAL_DEFAULT = "012345678"


def string_to_state(s):
    return [
        [int(s[0]), int(s[1]), int(s[2])],
        [int(s[3]), int(s[4]), int(s[5])],
        [int(s[6]), int(s[7]), int(s[8])]
    ]


def state_to_string(state):
    return "".join(str(x) for row in state for x in row)


def clone_state(state):
    return [row[:] for row in state]


def find_zero(state):
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                return i, j
    return None


def get_neighbors(state):
    x, y = find_zero(state)

    moves = [
        ("UP", -1, 0),
        ("DOWN", 1, 0),
        ("LEFT", 0, -1),
        ("RIGHT", 0, 1)
    ]

    result = []

    for action, dx, dy in moves:
        nx = x + dx
        ny = y + dy

        if 0 <= nx < 3 and 0 <= ny < 3:
            new_state = clone_state(state)
            new_state[x][y], new_state[nx][ny] = new_state[nx][ny], new_state[x][y]
            result.append((new_state, action))

    return result


def is_valid_input(s):
    return len(s) == 9 and "".join(sorted(s)) == "012345678"


def inversion_count(s):
    arr = [int(x) for x in s if x != "0"]
    count = 0

    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                count += 1

    return count


def is_solvable(start, goal):
    return inversion_count(start) % 2 == inversion_count(goal) % 2


def misplaced_tiles(state, goal_state):
    count = 0

    for i in range(3):
        for j in range(3):
            if state[i][j] != 0 and state[i][j] != goal_state[i][j]:
                count += 1

    return count


def reconstruct_path(goal_key, parent, state_map):
    keys = []
    actions = []
    current = goal_key

    while current is not None:
        keys.append(current)
        info = parent.get(current)

        if info is None:
            break

        parent_key, action = info
        actions.append(action)
        current = parent_key

    keys.reverse()
    actions.reverse()

    return [state_map[k] for k in keys], actions


def make_trace_item(iteration, node_state, node_key, action, mode,
                    frontier_after, reached_after, children, node_cost=None):
    return {
        "iteration": iteration,
        "node": node_state,
        "node_key": node_key,
        "action": action,
        "mode": mode,
        "frontier_after": frontier_after,
        "reached_after": reached_after,
        "children": children,
        "node_cost": node_cost
    }


def preview_plain(keys, limit=8):
    data = list(keys)[:limit]
    if len(keys) > limit:
        data.append(f"... +{len(keys) - limit}")
    return data


def preview_frontier_nodes(nodes, limit=8):
    data = [node["key"] for node in list(nodes)[:limit]]
    if len(nodes) > limit:
        data.append(f"... +{len(nodes) - limit}")
    return data


def format_key_as_matrix(key):
    key = str(key)

    if " " in key:
        state_key = key[:9]
        extra = key[9:].strip()
    else:
        state_key = key[:9]
        extra = ""

    if not state_key.isdigit() or len(state_key) != 9:
        return key

    rows = []
    for i in range(0, 9, 3):
        row = state_key[i:i + 3]
        rows.append(" ".join("_" if ch == "0" else ch for ch in row))

    text = "\n".join(rows)

    if extra:
        text += f"   {extra}"

    return text


def format_key_list_as_matrices(items, limit=8):
    if not items:
        return "Rỗng"

    lines = []

    for index, item in enumerate(items[:limit], start=1):
        lines.append(f"#{index}")
        lines.append(format_key_as_matrix(item))
        lines.append("")

    if len(items) > limit:
        lines.append(f"... +{len(items) - limit} trạng thái")

    return "\n".join(lines).strip()


def preview_priority_queue(heap, limit=8):
    ordered = sorted(heap)
    data = []

    for cost, order, node in ordered[:limit]:
        data.append(f"{node['key']} g={cost}")

    if len(heap) > limit:
        data.append(f"... +{len(heap) - limit}")

    return data


def bfs_early(start, goal):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    frontier = deque([{
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START"
    }])

    reached = {start_key}
    trace = []
    nodes_expanded = 0

    while frontier:
        node = frontier.popleft()
        nodes_expanded += 1

        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                "BFS: Queue FIFO, kiểm tra child trước khi thêm frontier",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": len(node["actions"]),
                "trace": trace
            }

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)

            if child_key not in reached:
                reached.add(child_key)

                frontier.append({
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action
                })

                status = "ADD"
            else:
                status = "SKIP"

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                "BFS: Queue FIFO, kiểm tra child trước khi thêm frontier",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

    return None


def bfs_late(start, goal):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    frontier = deque([{
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START"
    }])

    reached = set()
    trace = []
    nodes_expanded = 0
    iteration = 0

    while frontier:
        node = frontier.popleft()
        iteration += 1

        children_info = []

        if node["key"] in reached:
            children_info.append({
                "state": node["state"],
                "key": node["key"],
                "action": "SKIP",
                "status": "Đã có trong reached"
            })

            if len(trace) < 1000:
                trace.append(make_trace_item(
                    iteration,
                    node["state"],
                    node["key"],
                    node["action"],
                    "BFS cách 2: lấy node ra rồi mới kiểm tra reached",
                    preview_frontier_nodes(frontier),
                    preview_plain(reached),
                    children_info
                ))

            continue

        reached.add(node["key"])
        nodes_expanded += 1

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                iteration,
                node["state"],
                node["key"],
                node["action"],
                "BFS cách 2: lấy node ra rồi mới kiểm tra reached",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": len(node["actions"]),
                "trace": trace
            }

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)

            frontier.append({
                "key": child_key,
                "state": child_state,
                "path": node["path"] + [child_state],
                "actions": node["actions"] + [action],
                "action": action
            })

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": "ADD"
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                iteration,
                node["state"],
                node["key"],
                node["action"],
                "BFS cách 2: lấy node ra rồi mới kiểm tra reached",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

    return None


def uniform_cost_search(start, goal):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    order = 0
    start_node = {
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START",
        "cost": 0
    }

    frontier = [(0, order, start_node)]
    order += 1

    frontier_best_cost = {start_key: 0}
    reached_cost = {}
    trace = []
    nodes_expanded = 0

    while frontier:
        cost, _, node = heapq.heappop(frontier)

        if frontier_best_cost.get(node["key"]) != cost:
            continue

        frontier_best_cost.pop(node["key"], None)

        if node["key"] in reached_cost and reached_cost[node["key"]] <= cost:
            continue

        reached_cost[node["key"]] = cost
        nodes_expanded += 1

        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"UCS: Priority Queue theo g(n), g(node)={cost}",
                preview_priority_queue(frontier),
                [f"{k} g={v}" for k, v in list(reached_cost.items())[:8]],
                children_info,
                node_cost=cost
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": cost,
                "trace": trace
            }

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)
            new_cost = cost + misplaced_tiles(child_state, goal)

            child_info = {
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": "",
                "cost": new_cost
            }

            if child_key in reached_cost and reached_cost[child_key] <= new_cost:
                child_info["status"] = "SKIP"
                children_info.append(child_info)
                continue

            if child_key not in frontier_best_cost or new_cost < frontier_best_cost[child_key]:
                child_node = {
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action,
                    "cost": new_cost
                }

                frontier_best_cost[child_key] = new_cost
                heapq.heappush(frontier, (new_cost, order, child_node))
                order += 1
                child_info["status"] = "ADD/UPDATE"
            else:
                child_info["status"] = "SKIP"

            children_info.append(child_info)

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                "UCS: g(child) = g(parent) + số ô sai vị trí của child",
                preview_priority_queue(frontier),
                [f"{k} g={v}" for k, v in list(reached_cost.items())[:8]],
                children_info,
                node_cost=cost
            ))

    return None


def dfs_search(start, goal):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    state_map = {start_key: start}
    parent = {start_key: None}

    frontier = [start_key]
    frontier_set = {start_key}
    reached = {start_key}
    trace = []
    nodes_expanded = 0

    while frontier:
        current_key = frontier.pop()
        frontier_set.remove(current_key)
        current_state = state_map[current_key]
        nodes_expanded += 1

        parent_info = parent[current_key]
        action_from_parent = parent_info[1] if parent_info else "START"

        children_info = []

        if current_key == goal_key:
            path, actions = reconstruct_path(current_key, parent, state_map)

            trace.append(make_trace_item(
                nodes_expanded,
                current_state,
                current_key,
                action_from_parent,
                "DFS: Stack LIFO",
                preview_plain(reversed(frontier)),
                preview_plain(reached),
                children_info
            ))

            return {
                "path": path,
                "actions": actions,
                "nodes": nodes_expanded,
                "depth": len(actions),
                "cost": len(actions),
                "trace": trace
            }

        for child_state, action in reversed(get_neighbors(current_state)):
            child_key = state_to_string(child_state)

            if child_key not in reached and child_key not in frontier_set:
                reached.add(child_key)
                frontier.append(child_key)
                frontier_set.add(child_key)
                state_map[child_key] = child_state
                parent[child_key] = (current_key, action)
                status = "PUSH"
            else:
                status = "SKIP"

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                current_state,
                current_key,
                action_from_parent,
                "DFS: Stack LIFO",
                preview_plain(list(reversed(frontier))),
                preview_plain(reached),
                children_info
            ))

    return None


def depth_limited_search(start, goal, limit, base_iteration=0):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    frontier = [{
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START",
        "depth": 0,
        "path_keys": [start_key]
    }]

    trace = []
    nodes_expanded = 0
    result = "failure"

    while frontier:
        node = frontier.pop()
        nodes_expanded += 1

        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                base_iteration + nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"IDS / DLS: limit={limit}",
                preview_plain([n["key"] for n in reversed(frontier)]),
                preview_plain(node["path_keys"]),
                children_info
            ))

            return {
                "status": "found",
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "trace": trace
            }

        if node["depth"] >= limit:
            result = "cutoff"
            children_info.append({
                "state": node["state"],
                "key": node["key"],
                "action": "CUT",
                "status": f"CUTOFF depth={node['depth']}"
            })

            if len(trace) < 1000:
                trace.append(make_trace_item(
                    base_iteration + nodes_expanded,
                    node["state"],
                    node["key"],
                    node["action"],
                    f"IDS / DLS: limit={limit}",
                    preview_plain([n["key"] for n in reversed(frontier)]),
                    preview_plain(node["path_keys"]),
                    children_info
                ))

            continue

        for child_state, action in reversed(get_neighbors(node["state"])):
            child_key = state_to_string(child_state)

            if child_key in node["path_keys"]:
                status = "SKIP cycle"
            else:
                frontier.append({
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action,
                    "depth": node["depth"] + 1,
                    "path_keys": node["path_keys"] + [child_key]
                })
                status = "PUSH"

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                base_iteration + nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"IDS / DLS: limit={limit}",
                preview_plain([n["key"] for n in reversed(frontier)]),
                preview_plain(node["path_keys"]),
                children_info
            ))

    return {
        "status": result,
        "nodes": nodes_expanded,
        "trace": trace
    }


def ids_search(start, goal, max_depth=40):
    total_nodes = 0
    all_trace = []

    for limit in range(max_depth + 1):
        result = depth_limited_search(start, goal, limit, len(all_trace))
        total_nodes += result.get("nodes", 0)
        all_trace.extend(result.get("trace", []))

        if len(all_trace) > 1000:
            all_trace = all_trace[:1000]

        if result["status"] == "found":
            return {
                "path": result["path"],
                "actions": result["actions"],
                "nodes": total_nodes,
                "depth": len(result["actions"]),
                "cost": len(result["actions"]),
                "trace": all_trace
            }

    return None


class EightPuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Solver")
        self.root.geometry("1120x720")
        self.root.configure(bg="#f7f7f7")

        self.solution_path = []
        self.solution_actions = []
        self.search_trace = []
        self.current_index = 0
        self.trace_index = 0

        self.manual_mode = False
        self.manual_state = None
        self.manual_start_state = None
        self.manual_moves = 0
        self.manual_seconds = 0
        self.manual_timer_id = None
        self.animation_id = None

        self.build_ui()
        self.draw_board(string_to_state(START_DEFAULT))
        self.render_empty_trace()

    def build_ui(self):
        self.create_header()

        self.scroll_canvas = tk.Canvas(
            self.root,
            bg="#f7f7f7",
            highlightthickness=0
        )
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(
            self.root,
            orient="vertical",
            command=self.scroll_canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")

        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.container = tk.Frame(self.scroll_canvas, bg="#f7f7f7")
        self.canvas_window = self.scroll_canvas.create_window(
            (0, 0),
            window=self.container,
            anchor="nw"
        )

        self.container.bind("<Configure>", self.update_scroll_region)
        self.scroll_canvas.bind("<Configure>", self.resize_canvas_window)

        self.root.bind_all("<MouseWheel>", self.on_mousewheel)
        self.root.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.root.bind_all("<Button-5>", self.on_mousewheel_linux)

        self.container.grid_columnconfigure(0, weight=1)

        self.title_frame = tk.Frame(self.container, bg="#f7f7f7")
        self.title_frame.pack(fill="x", padx=70, pady=(28, 18))

        tk.Label(
            self.title_frame,
            text="Home » Projects",
            bg="#f7f7f7",
            fg="#555555",
            font=("Arial", 10)
        ).pack(anchor="w")

        tk.Label(
            self.title_frame,
            text="8 Puzzle Solver",
            bg="#f7f7f7",
            fg="#222222",
            font=("Arial", 30, "bold")
        ).pack(anchor="w", pady=(16, 8))

        tk.Label(
            self.title_frame,
            text="A simple 8-puzzle solver with BFS, UCS, DFS and IDS. Inspect statistics and follow the search trace.",
            bg="#f7f7f7",
            fg="#555555",
            font=("Arial", 12),
            wraplength=760,
            justify="left"
        ).pack(anchor="w")

        tk.Frame(self.title_frame, height=1, bg="#dddddd").pack(fill="x", pady=(20, 0))

        self.main = tk.Frame(self.container, bg="#f7f7f7")
        self.main.pack(fill="x", padx=70)

        self.controls_panel = self.card(self.main, width=270, height=500)
        self.controls_panel.grid(row=0, column=0, padx=(0, 28), sticky="n")

        self.board_panel = tk.Frame(self.main, bg="#f7f7f7")
        self.board_panel.grid(row=0, column=1, padx=(0, 28), sticky="n")

        self.stats_panel = self.card(self.main, width=360, height=430)
        self.stats_panel.grid(row=0, column=2, sticky="n")

        self.build_controls()
        self.build_board()
        self.build_stats()
        self.build_trace()

    def create_header(self):
        tk.Frame(self.root, bg="#1f4542", height=7).pack(fill="x")

        header = tk.Frame(self.root, bg="#ffffff", height=58, highlightbackground="#dddddd", highlightthickness=1)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = tk.Frame(header, bg="#ffffff")
        inner.pack(fill="both", expand=True, padx=70)

        tk.Label(
            inner,
            text="8-Puzzle Solver",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(side="left")

        nav = tk.Frame(inner, bg="#ffffff")
        nav.pack(side="right")

        for text in ["Solver", "Trace", "About"]:
            tk.Label(
                nav,
                text=text,
                bg="#ffffff",
                fg="#444444",
                font=("Arial", 10)
            ).pack(side="left", padx=14)

    def update_scroll_region(self, event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def resize_canvas_window(self, event):
        self.scroll_canvas.itemconfigure(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_linux(self, event):
        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")

    def card(self, parent, width, height):
        frame = tk.Frame(
            parent,
            bg="#ffffff",
            width=width,
            height=height,
            highlightbackground="#d6d6d6",
            highlightthickness=1
        )
        frame.pack_propagate(False)
        return frame

    def build_controls(self):
        tk.Button(
            self.controls_panel,
            text="Shuffle Puzzle",
            command=self.shuffle_puzzle,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 10, "bold")
        ).pack(fill="x", padx=18, pady=(18, 18), ipady=7)

        self.start_entry = self.labeled_entry(
            self.controls_panel,
            "Initial state",
            START_DEFAULT,
            "Enter 9 characters, e.g. 012345678"
        )

        self.goal_entry = self.labeled_entry(
            self.controls_panel,
            "Goal state",
            GOAL_DEFAULT
        )

        tk.Label(
            self.controls_panel,
            text="Search algorithm",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=18, pady=(8, 5))

        self.algorithm_var = tk.StringVar(value="DFS")
        self.algorithm_box = ttk.Combobox(
            self.controls_panel,
            textvariable=self.algorithm_var,
            values=[
                "BFS Cách 1",
                "BFS Cách 2",
                "UCS",
                "DFS",
                "IDS"
            ],
            state="readonly"
        )
        self.algorithm_box.pack(fill="x", padx=18, ipady=4)

        tk.Button(
            self.controls_panel,
            text="Solve Puzzle",
            command=self.solve_puzzle,
            bg="#287bdb",
            fg="#ffffff",
            activebackground="#1f65b8",
            activeforeground="#ffffff",
            relief="flat",
            font=("Arial", 10, "bold")
        ).pack(fill="x", padx=18, pady=(18, 12), ipady=7)

        self.error_label = tk.Label(
            self.controls_panel,
            text="",
            bg="#ffffff",
            fg="#c5221f",
            font=("Arial", 9),
            wraplength=230,
            justify="left"
        )
        self.error_label.pack(anchor="w", padx=18)

        note = (
            "Quy ước: 0 là ô trống. BFS dùng Queue FIFO, UCS dùng Priority Queue, "
            "DFS dùng Stack LIFO, IDS tăng dần giới hạn độ sâu."
        )
        self.note_label = tk.Label(
            self.controls_panel,
            text=note,
            bg="#ffffff",
            fg="#555555",
            font=("Arial", 8),
            wraplength=230,
            justify="left"
        )
        self.note_label.pack(anchor="w", padx=18, pady=(12, 18))

    def labeled_entry(self, parent, label, default, help_text=None):
        tk.Label(
            parent,
            text=label,
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=18)

        if help_text:
            tk.Label(
                parent,
                text=help_text,
                bg="#ffffff",
                fg="#555555",
                font=("Arial", 8)
            ).pack(anchor="w", padx=18, pady=(0, 5))

        entry = tk.Entry(
            parent,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 10)
        )
        entry.insert(0, default)
        entry.pack(fill="x", padx=18, pady=(0, 14), ipady=6)
        return entry

    def build_board(self):
        self.board_frame = tk.Frame(
            self.board_panel,
            bg="#222222",
            highlightbackground="#222222",
            highlightthickness=8
        )
        self.board_frame.pack(pady=(0, 12))

        self.tiles = []

        for i in range(3):
            row = []
            for j in range(3):
                label = tk.Label(
                    self.board_frame,
                    text="",
                    width=4,
                    height=2,
                    bg="#f7f7f7",
                    fg="#111111",
                    font=("Arial", 28, "bold"),
                    relief="solid",
                    bd=1
                )
                label.grid(row=i, column=j, padx=3, pady=3)
                row.append(label)
            self.tiles.append(row)

        self.action_label = tk.Label(
            self.board_panel,
            text="Action: Waiting",
            bg="#f7f7f7",
            fg="#555555",
            font=("Arial", 11, "bold")
        )
        self.action_label.pack(pady=(0, 8))

        nav = tk.Frame(self.board_panel, bg="#f7f7f7")
        nav.pack()

        for text, cmd in [
            ("Prev", self.prev_step),
            ("Stop", self.stop_animation),
            ("Next", self.next_step)
        ]:
            tk.Button(
                nav,
                text=text,
                command=cmd,
                bg="#ffffff",
                fg="#222222",
                relief="solid",
                bd=1,
                font=("Arial", 10, "bold")
            ).pack(side="left", padx=5, ipadx=10, ipady=5)

        self.manual_panel = self.card(self.board_panel, width=330, height=130)
        self.manual_panel.pack(pady=(16, 0))

        tk.Label(
            self.manual_panel,
            text="Manual Mode",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(pady=(10, 8))

        row = tk.Frame(self.manual_panel, bg="#ffffff")
        row.pack()

        tk.Button(
            row,
            text="Manual Play",
            command=self.start_manual_play,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 9, "bold")
        ).pack(side="left", padx=5, ipadx=8, ipady=5)

        tk.Button(
            row,
            text="Reset",
            command=self.reset_manual_play,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 9, "bold")
        ).pack(side="left", padx=5, ipadx=8, ipady=5)

        stat = tk.Frame(self.manual_panel, bg="#ffffff")
        stat.pack(fill="x", padx=14, pady=(10, 0))

        self.moves_label = tk.Label(stat, text="Số bước\n0", bg="#f7f7f7", fg="#222222", font=("Arial", 9, "bold"))
        self.moves_label.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.time_label = tk.Label(stat, text="Thời gian\n0s", bg="#f7f7f7", fg="#222222", font=("Arial", 9, "bold"))
        self.time_label.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def build_stats(self):
        tk.Label(
            self.stats_panel,
            text="Stats",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 18, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 10))

        self.status_label = tk.Label(
            self.stats_panel,
            text="Pending user input...",
            bg="#ffffff",
            fg="#b06000",
            font=("Arial", 11, "bold")
        )
        self.status_label.pack(anchor="w", padx=18)

        self.runtime_label = self.metric_label("Runtime:")
        self.nodes_label = self.metric_label("Nodes expanded:")
        self.depth_label = self.metric_label("Search depth:")
        self.cost_label = self.metric_label("Path cost:")

        tk.Label(
            self.stats_panel,
            text="▼ Path",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", padx=18, pady=(12, 5))

        self.path_text = tk.Text(
            self.stats_panel,
            height=9,
            bg="#f7f7f7",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Consolas", 9)
        )
        self.path_text.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.path_text.insert("1.0", "Chưa có dữ liệu")
        self.path_text.configure(state="disabled")

    def metric_label(self, text):
        label = tk.Label(
            self.stats_panel,
            text=text,
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        )
        label.pack(anchor="w", padx=18, pady=(12, 0))
        return label

    def build_trace(self):
        trace_card = tk.Frame(
            self.container,
            bg="#ffffff",
            highlightbackground="#d6d6d6",
            highlightthickness=1
        )
        trace_card.pack(fill="both", expand=True, padx=70, pady=(22, 26))

        header = tk.Frame(trace_card, bg="#ffffff")
        header.pack(fill="x", padx=18, pady=(18, 12))

        tk.Label(
            header,
            text="Search Trace",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 18, "bold")
        ).pack(side="left")

        self.trace_count_label = tk.Label(
            header,
            text="Trace: 0/0",
            bg="#ffffff",
            fg="#555555",
            font=("Arial", 10)
        )
        self.trace_count_label.pack(side="right")

        table = tk.Frame(trace_card, bg="#ffffff")
        table.pack(fill="both", expand=True, padx=18)

        for col, name in enumerate(["Node", "Frontier", "Reached"]):
            tk.Label(
                table,
                text=name,
                bg="#eeeeee",
                fg="#222222",
                relief="solid",
                bd=1,
                font=("Arial", 10, "bold")
            ).grid(row=0, column=col, sticky="nsew")

        table.grid_columnconfigure(0, weight=1)
        table.grid_columnconfigure(1, weight=2)
        table.grid_columnconfigure(2, weight=1)

        self.node_text = tk.Text(table, height=12, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 9))
        self.frontier_text = tk.Text(table, height=12, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 9))
        self.reached_text = tk.Text(table, height=12, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 9))

        self.node_text.grid(row=1, column=0, sticky="nsew")
        self.frontier_text.grid(row=1, column=1, sticky="nsew")
        self.reached_text.grid(row=1, column=2, sticky="nsew")

        btns = tk.Frame(trace_card, bg="#ffffff")
        btns.pack(fill="x", padx=18, pady=12)

        tk.Button(btns, text="Prev trace", command=self.prev_trace, bg="#ffffff", relief="solid", bd=1).pack(side="left", padx=(0, 8), ipadx=8, ipady=4)
        tk.Button(btns, text="Next trace", command=self.next_trace, bg="#ffffff", relief="solid", bd=1).pack(side="left", padx=(0, 8), ipadx=8, ipady=4)
        tk.Button(btns, text="Path trace", command=self.show_solution_trace, bg="#ffffff", relief="solid", bd=1).pack(side="left", padx=(0, 8), ipadx=8, ipady=4)

        self.children_text = tk.Text(
            trace_card,
            height=7,
            bg="#f7f7f7",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Consolas", 9)
        )
        self.children_text.pack(fill="x", padx=18, pady=(0, 18))
        self.children_text.insert("1.0", "Node con sẽ hiện ở đây")
        self.children_text.configure(state="disabled")

    def draw_board(self, state):
        zero_pos = find_zero(state)

        for i in range(3):
            for j in range(3):
                value = state[i][j]
                label = self.tiles[i][j]
                label.configure(text="" if value == 0 else str(value))

                if value == 0:
                    label.configure(bg="#d9d9d9")
                else:
                    label.configure(bg="#f7f7f7")

                label.unbind("<Button-1>")

                if self.manual_mode and value != 0 and abs(i - zero_pos[0]) + abs(j - zero_pos[1]) == 1:
                    label.configure(highlightbackground="#287bdb", highlightthickness=3)
                    label.bind("<Button-1>", lambda e, x=i, y=j: self.manual_tile_click(x, y))
                else:
                    label.configure(highlightthickness=0)

        self.update_action_label()

    def update_action_label(self):
        if not self.solution_path:
            if self.manual_mode:
                self.action_label.configure(text="Action: Người chơi tự di chuyển")
            else:
                self.action_label.configure(text="Action: Waiting")
        elif self.current_index == 0:
            self.action_label.configure(text="Action: Start")
        else:
            self.action_label.configure(text=f"Action: Move {self.solution_actions[self.current_index - 1]}")

    def validate_inputs(self):
        start = self.start_entry.get().strip()
        goal = self.goal_entry.get().strip()

        self.error_label.configure(text="")

        if not is_valid_input(start) or not is_valid_input(goal):
            self.error_label.configure(text="Input phải gồm đúng 9 số từ 0 đến 8.")
            return None, None

        if not is_solvable(start, goal):
            self.error_label.configure(text="Trạng thái này không thể giải được.")
            return None, None

        return start, goal

    def solve_puzzle(self):
        self.stop_animation()
        self.stop_manual_timer()
        self.manual_mode = False

        start_str, goal_str = self.validate_inputs()
        if not start_str:
            return

        start = string_to_state(start_str)
        goal = string_to_state(goal_str)
        algo = self.algorithm_var.get()

        self.status_label.configure(text=f"Đang chạy {algo}...", fg="#b06000")
        self.root.update_idletasks()

        start_time = time.perf_counter()

        if algo == "BFS Cách 1":
            result = bfs_early(start, goal)
        elif algo == "BFS Cách 2":
            result = bfs_late(start, goal)
        elif algo == "UCS":
            result = uniform_cost_search(start, goal)
        elif algo == "DFS":
            result = dfs_search(start, goal)
        else:
            result = ids_search(start, goal)

        runtime = (time.perf_counter() - start_time) * 1000

        if result is None:
            self.status_label.configure(text="Không tìm thấy lời giải", fg="#c5221f")
            return

        self.solution_path = result["path"]
        self.solution_actions = result["actions"]
        self.search_trace = result["trace"]
        self.current_index = 0
        self.trace_index = 0

        self.runtime_label.configure(text=f"Runtime: {runtime:.3f} ms")
        self.nodes_label.configure(text=f"Nodes expanded: {result['nodes']}")
        self.depth_label.configure(text=f"Search depth: {result['depth']}")
        self.cost_label.configure(text=f"Path cost: {result['cost']}")

        self.write_path_text()
        self.draw_board(self.solution_path[0])
        self.render_trace(0)

        if len(self.solution_path) <= 100:
            self.status_label.configure(text="Đang mô phỏng lời giải...", fg="#b06000")
            self.animate_solution()
        else:
            self.status_label.configure(text="Lời giải dài, dùng Prev / Next để xem", fg="#b06000")

    def write_path_text(self):
        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")

        lines = []

        for i, state in enumerate(self.solution_path[:180]):
            if i == 0:
                lines.append("Step 0")
            else:
                lines.append(f"Step {i} - Move {self.solution_actions[i - 1]}")

            lines.append(state_to_string(state))
            lines.append("")

        if len(self.solution_path) > 180:
            lines.append(f"... còn {len(self.solution_path) - 180} step nữa")

        self.path_text.insert("1.0", "\n".join(lines))
        self.path_text.configure(state="disabled")

    def animate_solution(self):
        self.stop_animation()

        def step():
            if self.current_index < len(self.solution_path) - 1:
                self.current_index += 1
                self.draw_board(self.solution_path[self.current_index])
                self.show_solution_trace()
                self.animation_id = self.root.after(650, step)
            else:
                self.status_label.configure(text="Solved successfully!", fg="#188038")

        self.animation_id = self.root.after(650, step)

    def stop_animation(self):
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def next_step(self):
        self.stop_animation()
        if not self.solution_path:
            return

        if self.current_index < len(self.solution_path) - 1:
            self.current_index += 1
            self.draw_board(self.solution_path[self.current_index])
            self.show_solution_trace()

    def prev_step(self):
        self.stop_animation()
        if not self.solution_path:
            return

        if self.current_index > 0:
            self.current_index -= 1
            self.draw_board(self.solution_path[self.current_index])
            self.show_solution_trace()

    def render_empty_trace(self):
        self.set_text(self.node_text, "")
        self.set_text(self.frontier_text, "")
        self.set_text(self.reached_text, "")
        self.set_text(self.children_text, "Bấm Solve Puzzle để xem bảng quá trình tìm kiếm.")
        self.trace_count_label.configure(text="Trace: 0/0")

    def render_trace(self, index):
        if not self.search_trace:
            return

        index = max(0, min(index, len(self.search_trace) - 1))
        self.trace_index = index
        item = self.search_trace[index]

        node_lines = [
            f"State: {item['node_key']}",
            f"Action: {item['action']}",
            f"Iteration: {item['iteration']}"
        ]

        if item.get("node_cost") is not None:
            node_lines.append(f"g(n): {item['node_cost']}")

        node_lines.append("")
        node_lines.extend(self.format_state(item["node"]))

        self.set_text(self.node_text, "\n".join(node_lines))
        self.set_text(
            self.frontier_text,
            format_key_list_as_matrices(item.get("frontier_after", []), limit=8)
        )
        self.set_text(
            self.reached_text,
            format_key_list_as_matrices(item.get("reached_after", []), limit=8)
        )

        child_lines = [item.get("mode", "")]

        for child in item.get("children", [])[:12]:
            line = f"{child['action']:>5} | {child['status']}"

            if child.get("cost") is not None:
                line += f" | g={child['cost']}"

            child_lines.append(line)
            child_lines.append(format_key_as_matrix(child["key"]))
            child_lines.append("")

        self.set_text(self.children_text, "\n".join(child_lines))
        self.trace_count_label.configure(text=f"Trace: {self.trace_index + 1}/{len(self.search_trace)}")

    def format_state(self, state):
        return [" ".join(str(x) if x != 0 else "_" for x in row) for row in state]

    def set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def next_trace(self):
        if self.search_trace and self.trace_index < len(self.search_trace) - 1:
            self.render_trace(self.trace_index + 1)

    def prev_trace(self):
        if self.search_trace and self.trace_index > 0:
            self.render_trace(self.trace_index - 1)

    def show_solution_trace(self):
        if not self.search_trace or not self.solution_path:
            return

        key = state_to_string(self.solution_path[self.current_index])

        for i, item in enumerate(self.search_trace):
            if item["node_key"] == key:
                self.render_trace(i)
                break

    def shuffle_puzzle(self):
        self.stop_animation()
        self.stop_manual_timer()
        self.manual_mode = False

        goal_str = self.goal_entry.get().strip()

        if not is_valid_input(goal_str):
            self.error_label.configure(text="Goal không hợp lệ.")
            return

        state = string_to_state(goal_str)
        last = None
        opposite = {
            "UP": "DOWN",
            "DOWN": "UP",
            "LEFT": "RIGHT",
            "RIGHT": "LEFT"
        }

        for _ in range(14):
            neighbors = get_neighbors(state)

            if last:
                filtered = [(s, a) for s, a in neighbors if a != opposite[last]]
                if filtered:
                    neighbors = filtered

            state, last = random.choice(neighbors)

        start_str = state_to_string(state)
        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, start_str)

        self.solution_path = []
        self.solution_actions = []
        self.search_trace = []
        self.current_index = 0
        self.trace_index = 0

        self.draw_board(state)
        self.render_empty_trace()

        self.status_label.configure(text="Pending user input...", fg="#b06000")
        self.runtime_label.configure(text="Runtime:")
        self.nodes_label.configure(text="Nodes expanded:")
        self.depth_label.configure(text="Search depth:")
        self.cost_label.configure(text="Path cost:")

        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")
        self.path_text.insert("1.0", "Chưa có dữ liệu")
        self.path_text.configure(state="disabled")

    def start_manual_play(self):
        self.stop_animation()

        start_str, goal_str = self.validate_inputs()
        if not start_str:
            return

        self.manual_mode = True
        self.manual_state = string_to_state(start_str)
        self.manual_start_state = clone_state(self.manual_state)
        self.manual_moves = 0
        self.manual_seconds = 0

        self.solution_path = []
        self.solution_actions = []
        self.search_trace = []

        self.draw_board(self.manual_state)
        self.update_manual_labels()
        self.start_manual_timer()

        self.status_label.configure(text="Manual Mode", fg="#188038")
        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")
        self.path_text.insert("1.0", "Đang ở chế độ tự chơi thủ công. Người chơi tự di chuyển các ô.")
        self.path_text.configure(state="disabled")

    def reset_manual_play(self):
        if not self.manual_start_state:
            self.start_manual_play()
            return

        self.manual_mode = True
        self.manual_state = clone_state(self.manual_start_state)
        self.manual_moves = 0
        self.manual_seconds = 0
        self.draw_board(self.manual_state)
        self.update_manual_labels()
        self.start_manual_timer()

    def manual_tile_click(self, i, j):
        if not self.manual_mode or not self.manual_state:
            return

        zx, zy = find_zero(self.manual_state)

        if abs(i - zx) + abs(j - zy) != 1:
            return

        self.manual_state[zx][zy], self.manual_state[i][j] = self.manual_state[i][j], self.manual_state[zx][zy]
        self.manual_moves += 1

        self.draw_board(self.manual_state)
        self.update_manual_labels()
        self.action_label.configure(text=f"Action: Player Move {self.manual_moves}")

        if state_to_string(self.manual_state) == self.goal_entry.get().strip():
            self.manual_mode = False
            self.stop_manual_timer()
            self.status_label.configure(text="Bạn đã thắng!", fg="#188038")
            self.action_label.configure(text="Action: Goal reached!")

    def start_manual_timer(self):
        self.stop_manual_timer()

        def tick():
            if self.manual_mode:
                self.manual_seconds += 1
                self.update_manual_labels()
                self.manual_timer_id = self.root.after(1000, tick)

        self.manual_timer_id = self.root.after(1000, tick)

    def stop_manual_timer(self):
        if self.manual_timer_id:
            self.root.after_cancel(self.manual_timer_id)
            self.manual_timer_id = None

    def update_manual_labels(self):
        self.moves_label.configure(text=f"Số bước\n{self.manual_moves}")
        self.time_label.configure(text=f"Thời gian\n{self.manual_seconds}s")


if __name__ == "__main__":
    root = tk.Tk()
    app = EightPuzzleApp(root)
    root.mainloop()
