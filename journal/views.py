from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import re
import requests
from .models import Question, Tag, DIFFICULTY_CHOICES, UserProblem
from django.contrib.auth.models import User
from django.http import JsonResponse
from datetime import date
from django.utils.timezone import localdate
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.contrib.auth.decorators import login_required


def extract_slug(url):
    match = re.search(r'leetcode\.com/problems/([^/]+)/?', url)
    return match.group(1) if match else None

def fetch_leetcode_data(slug):
    query = """
    query getQuestionDetail($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionFrontendId
        title
        titleSlug
        difficulty
        content
        tags: topicTags {
          name
        }
      }
    }
    """
    variables = {"titleSlug": slug}
    url = "https://leetcode.com/graphql"

    resp = requests.post(
        url,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"}
    )
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["question"]

@csrf_exempt
def fetch_and_store_question(request):
    if request.method == "GET":
        # Show a simple form to input URL
        return HttpResponse("""
            <form method="POST">
              <label>LeetCode URL: <input type="url" name="url" required></label>
              <button type="submit">Fetch Question</button>
            </form>
        """, content_type="text/html")

    if request.method == "POST":
        leetcode_url = request.POST.get("url")
        slug = extract_slug(leetcode_url)

        if not slug:
            return HttpResponse("Invalid LeetCode URL", status=400)

        try:
            qdata = fetch_leetcode_data(slug)
        except Exception as e:
            return HttpResponse(f"Failed to fetch data: {str(e)}", status=500)

        # Save or update Question and Tags
        question_no = int(qdata["questionFrontendId"])
        difficulty = qdata["difficulty"]

        question, created = Question.objects.get_or_create(
            question_no=question_no,
            defaults={
                "title": qdata["title"],
                "link": f"https://leetcode.com/problems/{slug}/",
                "leetcode_difficulty": difficulty,
                "problem_statement_html": qdata["content"],  # raw HTML
            },
        )
        if not created:
            # Update existing fields
            question.title = qdata["title"]
            question.leetcode_difficulty = difficulty
            question.link = f"https://leetcode.com/problems/{slug}/"
            question.problem_statement_html = qdata["content"]
            question.save()

        # Handle tags
        tag_names = [tag["name"] for tag in qdata["tags"]]
        question.tags.clear()
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            question.tags.add(tag)

        # Return a simple HTML page showing question info
        html_response = f"""
        <h1>Question #{question.question_no} - {question.title}</h1>
        <p><strong>Difficulty:</strong> {question.leetcode_difficulty}</p>
        <p><strong>Link:</strong> <a href="{question.link}" target="_blank">{question.link}</a></p>
        <h2>Problem Statement</h2>
        <div>{question.problem_statement_html}</div>
        <h3>Tags:</h3>
        <ul>
          {''.join(f'<li>{t.name}</li>' for t in question.tags.all())}
        </ul>
        <a href="">Fetch another question</a>
        """

        return HttpResponse(html_response, content_type="text/html")



@login_required
def home_view(request):

    # login not implemented so far so just a shortcut change when login is implemented
    user = request.user
    print("User authenticated?", request.user.is_authenticated)
    recent_questions = UserProblem.objects.filter(user=user).order_by('-last_solved')[:3]

    total_solved = UserProblem.objects.filter(user=user).count()

    total_revision = UserProblem.objects.filter(user=user,mark_for_revision=True).count()  # or adjust accordingly

    return render(request, "home.html", {
        "recent_questions": recent_questions,
        "total_solved": total_solved,
        "total_revision": total_revision,
    })





@login_required
def question_detail(request, pk):
    user = request.user
    user_problem = get_object_or_404(UserProblem, pk=pk, user=user)

    if request.method == 'POST':
        user_problem.my_solution = request.POST.get('my_solution', '')
        user_problem.optimized_solution = request.POST.get('optimized_solution', '')
        user_problem.note = request.POST.get('note', '')

        # Save revision checkbox: present in POST only if checked
        user_problem.mark_for_revision = 'revision' in request.POST

        if 'delete_note_image' in request.POST:
            if user_problem.note_image:
                user_problem.note_image.delete(save=False)
                user_problem.note_image = None

        # ✅ Handle new image upload (after deletion check)
        if 'note_image' in request.FILES:
            user_problem.note_image = request.FILES['note_image']

        # Save user difficulty from dropdown
        user_problem.user_difficulty = request.POST.get('user_difficulty', '')

        user_problem.save()
        return redirect('question_detail', pk=pk)  # redirect to same page to prevent resubmission

    return render(request, 'question_detail.html', {
        'user_problem': user_problem
    })


@login_required
def all_solved_view(request):
    user = request.user
    q = request.GET.get("q", "")
    difficulty = request.GET.get("difficulty", "")
    tag = request.GET.get("tags", "")  # Only single tag since dropdown is not multiple

    solved_problems = UserProblem.objects.filter(user=user)

    if q:
        solved_problems = solved_problems.filter(
            Q(question__title__icontains=q) | Q(question__question_no__icontains=q)
        )

    if difficulty:
        solved_problems = solved_problems.filter(question__leetcode_difficulty=difficulty)

    if tag:  # Only filter if tag is not empty
        solved_problems = solved_problems.filter(question__tags=tag)

    date_str = request.GET.get("date", "")
    if date_str:
        solved_problems = solved_problems.filter(last_solved=date_str)

    all_tags = Tag.objects.all()

    context = {
        "solved_problems": solved_problems,
        "all_tags": all_tags,
        "filter_q": q,
        "filter_difficulty": difficulty,
        "filter_tags": [int(tag)] if tag else [],
        "filters_applied": bool(q or difficulty or tag),
    }
    if request.GET.get("ajax") == "1":
        # Render only the list items for AJAX
        return render(request, "solved_list.html", {"solved_problems": solved_problems})

    return render(request, "all_solved.html", context)  # Replace with your actual template



@login_required
def new_entry_view(request):
    user = request.user

    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        if url:
            slug = extract_slug(url)

            if not slug:
                return JsonResponse({"status": "error", "message": "Invalid URL"}, status=400)

            try:
                qdata = fetch_leetcode_data(slug)
                if not qdata:
                    return JsonResponse({
                        "status": "error",
                        "message": "Question data could not be fetched. Please check the URL."
                    }, status=400)
            except Exception as e:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Failed to fetch data: {str(e)}"
                    }, status=500)


            question_no = int(qdata["questionFrontendId"])
            difficulty = qdata["difficulty"]

            question, created = Question.objects.get_or_create(
                question_no=question_no,
                defaults={
                    "title": qdata["title"],
                    "link": f"https://leetcode.com/problems/{slug}/",
                    "leetcode_difficulty": difficulty,
                    "problem_statement_html": qdata["content"],
                },
            )
            if not created:
                question.title = qdata["title"]
                question.leetcode_difficulty = difficulty
                question.link = f"https://leetcode.com/problems/{slug}/"
                question.problem_statement_html = qdata["content"]
                question.save()

            tag_names = [tag["name"] for tag in qdata["tags"]]
            question.tags.clear()
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                question.tags.add(tag)

            user_problem, _ = UserProblem.objects.get_or_create(
                user=user,
                question=question,
                defaults={"last_solved": date.today(), "mark_for_revision": False}
            )

            return JsonResponse({
                "status": "success",
                "message": "Question added successfully!",
                "redirect_url": f"/question/{user_problem.pk}/"  # or use reverse()
            })

        return JsonResponse({"status": "error", "message": "No URL provided"}, status=400)

    return render(request, "home.html", {"user": user})





@login_required
def calendar_dates(request):
    user=request.user
    # Get distinct solved dates
    dates = UserProblem.objects.filter(user=user).values_list('last_solved', flat=True).distinct()
    # Format dates to string 'YYYY-MM-DD'
    date_strings = [d.strftime('%Y-%m-%d') for d in dates if d]
    return JsonResponse({'dates': date_strings})


@login_required
def calendar_data(request):
    """
    Return JSON list of questions solved on the requested date.
    Expects ?date=yyyy-mm-dd as GET param.
    """
    user = request.user
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse({"questions": []})

    try:
        # Parse date string
        from datetime import datetime
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"questions": []})

    # Query questions solved by the user on this date
    user_questions = UserProblem.objects.filter(user=user, last_solved=selected_date).select_related('question')

    questions_data = []
    for uq in user_questions:
        questions_data.append({
            "id": uq.question.id,
            "question_no": uq.question.question_no,
            "title": uq.question.title,
            "date": uq.last_solved.strftime("%Y-%m-%d"),
        })

   

    return JsonResponse({"questions": questions_data})





@login_required
def revision_question(request):
    user=request.user
    revision_ques = UserProblem.objects.filter(user=user, mark_for_revision=True).order_by('-last_solved')

    print(revision_ques)

    
    
    return render(request , "revised.html", {"revision_ques": revision_ques})




@login_required
def live_search(request):
    user = request.user  # Replace with actual user retrieval logic
    query = request.GET.get("q", "").strip()
    if request.GET.get("ajax") == "1":
        if query:
            # Try to interpret query as int for question_no
            try:
                query_int = int(query)
            except ValueError:
                query_int = None

            # Step 1: Get matching Question IDs by title or question_no
            q_filter = Q(title__icontains=query)
            if query_int is not None:
                q_filter |= Q(question_no=query_int)

            matching_questions = Question.objects.filter(q_filter)
            matching_ids = matching_questions.values_list('id', flat=True)

            # Step 2: Filter UserProblem for this user and those questions
            user_problems = UserProblem.objects.filter(
                user=user,
                question_id__in=matching_ids
            ).select_related('question')[:5]

            # Step 3: Format results
            results = [{
                "id": up.id,
                "title": up.question.title,
                "question_no": up.question.question_no,
            } for up in user_problems]

            return JsonResponse({"results": results})

        return JsonResponse({"results": []})

    return JsonResponse({"error": "Invalid request"}, status=400)
