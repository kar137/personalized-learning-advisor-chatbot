def format_list(items: list) -> str:
    return "\n".join([f"- {item}" for item in items])

def format_courses(courses: list) -> str:
    return "\n".join([f"- {c['title']} ({c['platform']}) [{c['level']}]" for c in courses])
