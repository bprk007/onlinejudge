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

@login_required
def submit(request, slug=None):
    problem = None
    output = None
    action = request.POST.get("action")
    verdicts = []
    if slug:
        problem = get_object_or_404(Problem, slug=slug)

    if request.method == 'POST':
        form = CodeSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save()
        if action == "run":
            
                submission.input_data = problem.example_input
                output = run_code(
                    submission.language,
                    submission.code,
                    submission.input_data
                )
                submission.output_data = output
                submission.save()

        elif action == "submit":
            test_cases = problem.test_cases
            
            for idx,tc in enumerate(test_cases,start=1):
                output = run_code(
                    submission.language,
                    submission.code,
                    tc["input"]
                )
                passed = (output.strip() == tc["expected_output"].strip())
                verdicts.append({
                    "passed" : passed,
                    "message": f"Test case {idx} {'passed' if passed else 'failed'}"
                })


    else:
        form = CodeSubmissionForm()

    return render(request, "index.html", {
        "form": form,
        "output": output,
        "problem": problem,
        "input":problem.example_input,
        "verdicts":verdicts,
        "submission":submission
    })


def run_code(language,code,input_data):
    print("running")
    project_path = Path(settings.BASE_DIR)
    directories = ["codes", "inputs",   "outputs"]

    for directory in directories:
        dir_path = project_path / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)

    codes_dir = project_path / "codes"
    inputs_dir = project_path / "inputs"
    outputs_dir = project_path / "outputs"

    unique = str(uuid.uuid4())

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

    with open(output_file_path, "w") as output_file:
        pass  # This will create an empty file

    if language == "cpp":
        executable_path = codes_dir / unique
        compile_result = subprocess.run(
            ["clang++", str(code_file_path), "-o", str(executable_path)]
        )
        if compile_result.returncode == 0:
            with open(input_file_path, "r") as input_file:
                with open(output_file_path, "w") as output_file:
                    subprocess.run(
                        [str(executable_path)],
                        stdin=input_file,
                        stdout=output_file,
                    )
    elif language == "py" or "python":
        # Code for executing Python script
        with open(input_file_path, "r") as input_file:
            with open(output_file_path, "w") as output_file:
                subprocess.run(
                    ["python3", str(code_file_path)],
                    stdin=input_file,
                    stdout=output_file,
                )

    # Read the output from the output file
    with open(output_file_path, "r") as output_file:
        output_data = output_file.read()

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