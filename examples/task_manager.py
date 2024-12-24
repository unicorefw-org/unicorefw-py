#!/usr/bin/env python3
##############################################################################
# examples/task_manager.py - Simple Task Manager Example                     #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info                #
#                                                                            #
# This file is part of UniCoreFW. You can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by                   #
# the Free Software Foundation.                                              #
# You should have received a copy of the [BSD-3-Clause] license              #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.           #
##############################################################################

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from unicorefw import UniCoreFW  # Now you can import Unicore as usual

# Define a list of tasks
tasks = [
    {"title": "Buy groceries", "priority": "high", "completed": False},
    {"title": "Write report", "priority": "medium", "completed": False},
    {"title": "Pay bills", "priority": "low", "completed": True},
    {"title": "Schedule meeting", "priority": "medium", "completed": True},
    {"title": "Read book", "priority": "low", "completed": False},
]

# Assign unique IDs to each task using `uniqueId`
for task in tasks:
    task["id"] = UniCoreFW.unique_id("task_")

# Display all tasks
print("\nAll Tasks with Unique IDs:")
for task in tasks:
    print(task)

# 1. Filter out completed tasks
incomplete_tasks = UniCoreFW.filter(tasks, lambda t: not t["completed"])
print("\nIncomplete Tasks:")
for task in incomplete_tasks:
    print(task)

# 2. Sort tasks by priority
sorted_tasks = UniCoreFW.sort_by(tasks, lambda t: t["priority"])
print("\nTasks Sorted by Priority:")
for task in sorted_tasks:
    print(task)

# 3. Group tasks by priority
grouped_tasks = UniCoreFW.group_by(tasks, lambda t: t["priority"])
print("\nTasks Grouped by Priority:")
for priority, tasks in grouped_tasks.items():
    print(f"Priority {priority}:")
    for task in tasks:
        print(f"  {task['title']} (ID: {task['id']})")

# 4. Map task titles to a list
task_titles = UniCoreFW.map(tasks, lambda t: t["title"])
print("\nTask Titles:")
print(task_titles)

# 5. Reduce to count the number of low-priority tasks
low_priority_count = UniCoreFW.reduce(
    tasks, lambda count, t: count + 1 if t["priority"] == "low" else count, 0
)
print("\nNumber of Low-Priority Tasks:")
print(low_priority_count)

# 6. Generate a unique identifier for a new task
new_task_id = UniCoreFW.unique_id("task_")
print("\nUnique ID for New Task:")
print(new_task_id)

# 7. Use debounce to simulate an auto-save function (here, we'll just demonstrate by calling it twice quickly)
import time


def auto_save():
    print("Auto-save triggered.")


debounced_save = UniCoreFW.debounce(auto_save, 1000)  # 1000ms delay
print("\nAuto-Save Simulation:")
debounced_save()
time.sleep(0.5)  # Calling within debounce time to test delay
debounced_save()  # This call should be ignored due to debounce

time.sleep(1.5)  # Wait to let debounce reset
debounced_save()  # This call should go through
