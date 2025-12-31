from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

USERS_FILE = "user.txt"
TASKS_FILE = "tasks.txt"
TASK_OVERVIEW_FILE = "task_overview.txt"
USER_OVERVIEW_FILE = "user_overview.txt"

DATE_FMT = "%d %b %Y"  # e.g. 25 Oct 2019


# ----------------- File helpers -----------------
def ensure_file(path: str) -> None:
    if not Path(path).exists():
        Path(path).write_text("", encoding="utf-8")


def read_lines(path: str) -> list[str]:
    ensure_file(path)
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]


def append_line(path: str, line: str) -> None:
    ensure_file(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")


def write_lines(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip("\n") + ("\n" if lines else ""))


# ----------------- Users -----------------
def load_users() -> dict[str, str]:
    """
    user.txt format:
    username, password
    """
    users: dict[str, str] = {}
    for ln in read_lines(USERS_FILE):
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) != 2:
            # skip bad lines instead of crashing
            continue
        u, p = parts
        if u:
            users[u] = p
    return users


def login() -> str:
    users = load_users()
    while True:
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        if username in users and users[username] == password:
            print(f"\nLogin successful. Welcome, {username}!\n")
            return username

        print("Incorrect username or password. Please try again.\n")


def reg_user(users: dict[str, str]) -> None:
    # admin-only enforced by caller
    while True:
        new_u = input("Enter a new username: ").strip()
        if not new_u:
            print("Username cannot be empty.\n")
            continue

        # prevent duplicates
        if new_u in users:
            print("That username already exists. Try a different username.\n")
            continue

        new_p = input("Enter a new password: ").strip()
        confirm = input("Confirm password: ").strip()
        if new_p != confirm:
            print("Passwords do not match. Try again.\n")
            continue

        append_line(USERS_FILE, f"{new_u}, {new_p}")
        users[new_u] = new_p
        print("User registered successfully.\n")
        return


# ----------------- Tasks -----------------
def parse_task_line(line: str) -> list[str] | None:
    # tasks.txt is comma+space separated in the project
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 6:
        return None
    return parts  # [user, title, desc, assigned, due, completed]


def load_tasks() -> list[list[str]]:
    tasks: list[list[str]] = []
    for ln in read_lines(TASKS_FILE):
        t = parse_task_line(ln)
        if t:
            tasks.append(t)
    return tasks


def task_to_line(task: list[str]) -> str:
    return ", ".join(task)


def print_task(task: list[str], number: int | None = None) -> None:
    assigned_user, title, desc, assigned_str, due_str, done = task
    prefix = f"Task {number}:\n" if number is not None else "Task:\n"
    print(prefix +
          f"Assigned to:        {assigned_user}\n"
          f"Task:               {title}\n"
          f"Task description:   {desc}\n"
          f"Date assigned:      {assigned_str}\n"
          f"Due date:           {due_str}\n"
          f"Task complete?      {done}\n")


def ask_date(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        try:
            dt = datetime.strptime(s, DATE_FMT).date()
            return dt.strftime(DATE_FMT)
        except ValueError:
            print(f"Invalid date format. Use e.g. 25 Oct 2019.\n")


def add_task(users: dict[str, str]) -> None:
    assignee = input("Who is the task assigned to (username)? ").strip()
    if assignee not in users:
        print("That username does not exist in user.txt. Register them first.\n")
        return

    title = input("Task title: ").strip()
    desc = input("Task description: ").strip()
    due_str = ask_date("Due date (e.g. 25 Oct 2019): ")

    assigned_str = date.today().strftime(DATE_FMT)
    # default complete is No
    line = f"{assignee}, {title}, {desc}, {assigned_str}, {due_str}, No"
    append_line(TASKS_FILE, line)
    print("Task added successfully.\n")


def view_all() -> None:
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.\n")
        return
    for i, t in enumerate(tasks, start=1):
        print_task(t, i)


def view_completed() -> None:
    tasks = load_tasks()
    completed = [t for t in tasks if t[5].strip().lower() == "yes"]
    if not completed:
        print("No completed tasks found.\n")
        return
    for i, t in enumerate(completed, start=1):
        print_task(t, i)


def get_valid_task_number(max_n: int) -> int:
    # optional recursion version; iterative is safer but this is fine
    s = input(f"Select task number (1-{max_n}) or -1 to return: ").strip()
    if s == "-1":
        return -1
    if not s.isdigit():
        print("Please enter a number.\n")
        return get_valid_task_number(max_n)
    n = int(s)
    if not (1 <= n <= max_n):
        print("That task number does not exist.\n")
        return get_valid_task_number(max_n)
    return n


def save_tasks(tasks: list[list[str]]) -> None:
    lines = [task_to_line(t) for t in tasks]
    write_lines(TASKS_FILE, lines)


def edit_task(task: list[str], users: dict[str, str]) -> None:
    # can only edit if not completed
    if task[5].strip().lower() == "yes":
        print("You cannot edit a completed task.\n")
        return

    while True:
        choice = input("Edit (u)sername, (d)ue date, (b)oth, or (c)ancel: ").strip().lower()
        if choice == "c":
            print("Edit cancelled.\n")
            return
        if choice not in {"u", "d", "b"}:
            print("Invalid choice.\n")
            continue

        if choice in {"u", "b"}:
            new_user = input("New assignee username: ").strip()
            if new_user not in users:
                print("That username does not exist.\n")
                continue
            task[0] = new_user

        if choice in {"d", "b"}:
            task[4] = ask_date("New due date (e.g. 25 Oct 2019): ")

        print("Task updated.\n")
        return


def mark_complete(task: list[str]) -> None:
    task[5] = "Yes"
    print("Task marked as complete.\n")


def view_mine(logged_in_user: str, users: dict[str, str]) -> None:
    tasks = load_tasks()
    my_tasks = [(idx, t) for idx, t in enumerate(tasks) if t[0] == logged_in_user]

    if not my_tasks:
        print("You have no tasks assigned to you.\n")
        return

    # show numbered tasks for THIS user
    print("\nYour tasks:\n")
    for display_num, (real_idx, t) in enumerate(my_tasks, start=1):
        print_task(t, display_num)

    # pick a task
    selection = get_valid_task_number(len(my_tasks))
    if selection == -1:
        print()
        return

    real_idx, selected_task = my_tasks[selection - 1]

    while True:
        action = input("Choose: (m)ark complete, (e)dit, (r)eturn: ").strip().lower()
        if action == "r":
            print()
            return
        if action == "m":
            mark_complete(selected_task)
            tasks[real_idx] = selected_task
            save_tasks(tasks)
            return
        if action == "e":
            edit_task(selected_task, users)
            tasks[real_idx] = selected_task
            save_tasks(tasks)
            return

        print("Invalid option.\n")


def delete_task() -> None:
    tasks = load_tasks()
    if not tasks:
        print("No tasks to delete.\n")
        return

    for i, t in enumerate(tasks, start=1):
        print_task(t, i)

    n = get_valid_task_number(len(tasks))
    if n == -1:
        print()
        return

    removed = tasks.pop(n - 1)
    save_tasks(tasks)
    print(f"Deleted task {n}: {removed[1]}\n")


# ----------------- Reports & stats -----------------
def is_overdue(task: list[str]) -> bool:
    done = task[5].strip().lower() == "yes"
    if done:
        return False
    try:
        due_dt = datetime.strptime(task[4], DATE_FMT).date()
        return due_dt < date.today()
    except ValueError:
        # if due date is corrupted, treat as not overdue
        return False


def generate_reports() -> None:
    users = load_users()
    tasks = load_tasks()

    total_tasks = len(tasks)
    completed = sum(1 for t in tasks if t[5].strip().lower() == "yes")
    uncompleted = total_tasks - completed
    overdue = sum(1 for t in tasks if is_overdue(t))

    pct_incomplete = (uncompleted / total_tasks * 100) if total_tasks else 0.0
    pct_overdue = (overdue / total_tasks * 100) if total_tasks else 0.0

    task_lines = [
        f"Total tasks: {total_tasks}",
        f"Completed tasks: {completed}",
        f"Uncompleted tasks: {uncompleted}",
        f"Overdue tasks: {overdue}",
        f"Percentage incomplete: {pct_incomplete:.2f}%",
        f"Percentage overdue: {pct_overdue:.2f}%",
    ]
    write_lines(TASK_OVERVIEW_FILE, task_lines)

    total_users = len(users)
    user_lines = [
        f"Total users: {total_users}",
        f"Total tasks: {total_tasks}",
        ""
    ]

    # per-user breakdown
    for username in users.keys():
        user_tasks = [t for t in tasks if t[0] == username]
        n_user_tasks = len(user_tasks)

        pct_of_all = (n_user_tasks / total_tasks * 100) if total_tasks else 0.0
        n_done = sum(1 for t in user_tasks if t[5].strip().lower() == "yes")
        n_not_done = n_user_tasks - n_done
        n_overdue = sum(1 for t in user_tasks if is_overdue(t))

        pct_done = (n_done / n_user_tasks * 100) if n_user_tasks else 0.0
        pct_not_done = (n_not_done / n_user_tasks * 100) if n_user_tasks else 0.0
        pct_overdue = (n_overdue / n_user_tasks * 100) if n_user_tasks else 0.0

        user_lines += [
            f"User: {username}",
            f"  Tasks assigned: {n_user_tasks}",
            f"  % of total tasks: {pct_of_all:.2f}%",
            f"  % completed: {pct_done:.2f}%",
            f"  % to be completed: {pct_not_done:.2f}%",
            f"  % overdue (not completed): {pct_overdue:.2f}%",
            ""
        ]

    write_lines(USER_OVERVIEW_FILE, user_lines)
    print("Reports generated: task_overview.txt and user_overview.txt\n")


def display_statistics() -> None:
    # If reports don't exist yet, generate them first
    if not Path(TASK_OVERVIEW_FILE).exists() or not Path(USER_OVERVIEW_FILE).exists():
        generate_reports()

    print("\n--- Task Overview ---")
    for ln in read_lines(TASK_OVERVIEW_FILE):
        print(ln)

    print("\n--- User Overview ---")
    for ln in read_lines(USER_OVERVIEW_FILE):
        print(ln)
    print()


# ----------------- Menus -----------------
def admin_menu() -> str:
    return input(
        "\nPlease select one of the following options:\n"
        "r   - register user\n"
        "a   - add task\n"
        "va  - view all tasks\n"
        "vm  - view my tasks\n"
        "vc  - view completed tasks\n"
        "del - delete a task\n"
        "gr  - generate reports\n"
        "ds  - display statistics\n"
        "e   - exit\n"
        ": "
    ).strip().lower()


def user_menu() -> str:
    return input(
        "\nPlease select one of the following options:\n"
        "a   - add task\n"
        "va  - view all tasks\n"
        "vm  - view my tasks\n"
        "e   - exit\n"
        ": "
    ).strip().lower()


def main() -> None:
    ensure_file(USERS_FILE)
    ensure_file(TASKS_FILE)

    logged_in_user = login()
    users = load_users()

    while True:
        if logged_in_user == "admin":
            choice = admin_menu()
        else:
            choice = user_menu()

        if choice == "r":
            if logged_in_user != "admin":
                print("Only admin can register users.\n")
                continue
            users = load_users()
            reg_user(users)

        elif choice == "a":
            users = load_users()
            add_task(users)

        elif choice == "va":
            view_all()

        elif choice == "vm":
            users = load_users()
            view_mine(logged_in_user, users)

        elif choice == "vc":
            if logged_in_user != "admin":
                print("Only admin can view completed tasks.\n")
                continue
            view_completed()

        elif choice == "del":
            if logged_in_user != "admin":
                print("Only admin can delete tasks.\n")
                continue
            delete_task()

        elif choice == "gr":
            if logged_in_user != "admin":
                print("Only admin can generate reports.\n")
                continue
            generate_reports()

        elif choice == "ds":
            if logged_in_user != "admin":
                print("Only admin can display statistics.\n")
                continue
            display_statistics()

        elif choice == "e":
            print("Goodbye!!!")
            break

        else:
            print("You have entered an invalid input. Please try again.\n")


if __name__ == "__main__":
    main()
