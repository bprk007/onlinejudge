import json
from submit.models import Problem

with open("problems.json", "r") as f:
    data = json.load(f)

for item in data:
    problem, created = Problem.objects.get_or_create(
        slug=item["slug"],
        defaults={
            "title": item["title"],
            "difficulty": item["difficulty"],
            "description": item["description"],
            "example_input": item["example_input"],
            "test_cases": item["test_cases"]
        }
    )
    print(f"{'Created' if created else 'Skipped'}: {problem.title}")
