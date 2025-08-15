import json
from submit.models import Problem

# Optional: delete all problems before import
Problem.objects.all().delete()
print("Deleted all existing problems.")

with open("problems.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    problem, created = Problem.objects.get_or_create(
        slug=item["slug"],
        defaults={
            "title": item["title"],
            "difficulty": item["difficulty"],
            "description": item["description"],
            "example_testcases": item["example_testcases"],
            "test_cases": item["test_cases"],
            "constraints": item["constraints"],
            "boilerplate": item["boilerplate"],
        }
    )
    print(f"{'Created' if created else 'Skipped'}: {problem.title}")
