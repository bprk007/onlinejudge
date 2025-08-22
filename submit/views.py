from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from submit.forms import CodeSubmissionForm
from django.conf import settings
from .models import Problem
import os
import uuid
import subprocess
from pathlib import Path
from google import genai
from dotenv import load_dotenv
import resource
import signal

load_dotenv()  # loads .env into environment
api_key = os.getenv("GOOGLE_API_KEY")



@login_required
def submit(request, slug=None):
    problem = None
    output = None
    action = request.POST.get("action")
    verdicts = []
    submission = None
    prev_slug = None
    next_slug = None
    ai_rev = None

    if slug:
        problems = list(Problem.objects.order_by("id"))
        current_index = next((i for i, p in enumerate(problems) if p.slug == slug), None)

        if current_index is not None:
            if current_index > 0:
                prev_slug = problems[current_index - 1].slug
            if current_index < len(problems) - 1:
                next_slug = problems[current_index + 1].slug

        problem = get_object_or_404(Problem, slug=slug)
    
    if request.method == 'POST':
        form = CodeSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)

        if action == "run":
            # Example test case only
            #submission.input_data = problem.example_testcases[0].get("input", "")
            
            output = run_code(
                submission.language,
                submission.code,
                submission.input_data
            )
            print(output)
            print(submission.input_data)
            submission.output_data = output 
            print(output)  # ✅ save only here
            submission.save()

        elif action == "submit":
            # Hidden test cases
            test_cases = problem.test_cases
            for idx, tc in enumerate(test_cases, start=1):
                output = run_code(
                    submission.language,
                    submission.code,
                    tc["input"]
                )
                passed = (output.strip() == tc["output"].strip())
                verdicts.append({
                        "passed": passed,
                        "message": f"Test case {idx} {'passed' if passed else 'failed'}"})
                
                if not passed:
                    verdicts.append({
                        "passed": passed,
                        "message": f"Test case {idx} {'passed' if passed else 'failed'}"
                    })
                    break
            submission.save()  # ✅ don’t touch output_data

        elif action == "ai_review":
            ai_rev = ai_review(problem.description, submission.code)
            submission.save()
            return render(request, "index.html", {
                "form": form,
                "output": submission.output_data,  # ✅ always read from saved
                "problem": problem,
                "input": problem.example_testcases[0].get("input", ""),
                "verdicts": verdicts,
                "submission": submission,
                "prev_slug": prev_slug,
                "next_slug": next_slug,
                "ai_rev": ai_rev,
            })

    else:
        form = CodeSubmissionForm()

    return render(request, "index.html", {
        "form": form,
        "output": submission.output_data if submission else None,  # ✅ persists run output
        "problem": problem,
        "input": submission.input_data if submission else problem.example_testcases[0].get("input", ""),
        "verdicts": verdicts,
        "submission": submission,
        "prev_slug": prev_slug,
        "next_slug": next_slug,
    })


def set_memory_limit(memory_limit_mb=512):
    """Set memory limit before running user code"""
    try:
        mem_bytes = memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

    except Exception as e:
        
       print("")

def run_code(language, code, input_data, time_limit=2, memory_limit=128):
    print("running")
    print(input_data)
    project_path = Path(settings.BASE_DIR)
    directories = ["codes", "inputs", "outputs"]

    for directory in directories:
        dir_path = project_path / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)

    codes_dir = project_path / "codes"
    inputs_dir = project_path / "inputs"
    outputs_dir = project_path / "outputs"

    unique = str(uuid.uuid4())

    if language == "java":
        # Always name file Main.java (standard for OJ platforms)
        code_file_name = "Main.java"
    else:
        code_file_name = f"{unique}.{language}"

    input_file_name = f"{unique}.txt"
    output_file_name = f"{unique}.txt"

    code_file_path = codes_dir / code_file_name
    input_file_path = inputs_dir / input_file_name
    output_file_path = outputs_dir / output_file_name

    with open(code_file_path, "w") as code_file:
        code_file.write(code)

    with open(input_file_path, "w") as input_file:
        input_file.write(input_data)

    # Create empty output file
    open(output_file_path, "w").close()

    try:
        if language == "cpp":
            executable_path = codes_dir / unique
            compile_result = subprocess.run(
                ["clang++", str(code_file_path), "-o", str(executable_path)],
                capture_output=True
            )
            if compile_result.returncode != 0:
                return "Compilation Error:\n" + compile_result.stderr.decode()

            with open(input_file_path, "r") as input_file, \
                 open(output_file_path, "w") as output_file:
                result = subprocess.run(
                    [str(executable_path)],
                    stdin=input_file,
                    stdout=output_file,
                    timeout=time_limit,
                    preexec_fn=lambda: set_memory_limit(memory_limit)
                )
                if result.returncode == -signal.SIGKILL:
                    return "Memory Limit Exceeded"

        elif language in ("py", "python"):
            with open(input_file_path, "r") as input_file, \
                 open(output_file_path, "w") as output_file:
                result = subprocess.run(
                    ["python3", str(code_file_path)],
                    stdin=input_file,
                    stdout=output_file,
                    timeout=time_limit,
                    preexec_fn=lambda: set_memory_limit(memory_limit)
                )
                if result.returncode == -signal.SIGKILL:
                    return "Memory Limit Exceeded"

        elif language == "java":
            # Compile
            compile_result = subprocess.run(
                ["javac", str(code_file_path)],
                capture_output=True,
                cwd=codes_dir
            )
            if compile_result.returncode != 0:
                return "Compilation Error:\n" + compile_result.stderr.decode()

            # Run
            with open(input_file_path, "r") as input_file, \
                 open(output_file_path, "w") as output_file:
                result = subprocess.run(
                    ["java", "-cp", str(codes_dir), "Main"],
                    stdin=input_file,
                    stdout=output_file,
                    timeout=time_limit,
                    preexec_fn=lambda: set_memory_limit(memory_limit)
                )
                if result.returncode == -signal.SIGKILL:
                    return "Memory Limit Exceeded"

    except subprocess.TimeoutExpired:
        return "Time Limit Exceeded"

    # Read output
    with open(output_file_path, "r") as output_file:
        output_data = output_file.read()
    print(output_data)
    return output_data




@login_required
def problem_list(request):
    print("view found")
    problems = Problem.objects.all().order_by('id')
    return render(request, "problems.html", {"problems": problems})

@login_required
def problem_detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    return render(request, "submit/problem_detail.html", {"problem": problem})


def problem_detail(request, slug):
    problems = list(Problem.objects.order_by('id'))
    problem = get_object_or_404(Problem, slug=slug)
    
    index = problems.index(problem)

    prev_slug = problems[index - 1].slug if index > 0 else None
    next_slug = problems[index + 1].slug if index < len(problems) - 1 else None

    return render(request, "index.html", {
        "problem": problem,
        "prev_slug": prev_slug,
        "next_slug": next_slug,
    })


import json
from google import genai

def ai_review(question, code):
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are a code review assistant.
    Analyze the following code for the given question and return ONLY a valid JSON object with these fields:

    - time_complexity: string (worst-case Big-O notation)
    - space_complexity: string (worst-case Big-O notation)
    - correctness: string ("Correct", "Incorrect", or "Partially Correct") with short explanation
    - improvements: list of strings (each describing a code improvement)
    - potential_bugs: list of strings (possible bugs or pitfalls)
    - readability_score: integer from 1 to 10
    

    Question:
    {question}

    Code:
    {code}

    Output ONLY the JSON. No extra text.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    # Parse the returned JSON into a Python dictionary
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON returned, contact admin", "raw_output": response.text}
