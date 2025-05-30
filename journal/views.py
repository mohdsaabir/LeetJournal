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




def home_view(request):

    # login not implemented so far so just a shortcut change when login is implemented
    user=User.objects.get(username='testuser')

    recent_questions = UserProblem.objects.filter(user=user).order_by('-last_solved')[:3]

    total_solved = UserProblem.objects.filter(user=user).count()

    total_revision = UserProblem.objects.filter(mark_for_revision=True).count()  # or adjust accordingly

    return render(request, "home.html", {
        "recent_questions": recent_questions,
        "total_solved": total_solved,
        "total_revision": total_revision,
    })






def question_detail(request, pk):
    user = User.objects.get(username='testuser')
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


def all_solved_view(request):
    user = User.objects.get(username='testuser')
    date_str = request.GET.get('date')
    questions_solved = UserProblem.objects.filter(user=user).order_by('-last_solved')

   
    if date_str:
        # Filter by date (assuming last_solved is a DateTimeField)
        questions_solved = questions_solved.filter(last_solved=parse_date(date_str))

    return render(request, "all_solved.html", {"solved_problems": questions_solved})



def new_entry_view(request):
    user = User.objects.get(username='testuser')

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






def calendar_dates(request):
    # Get distinct solved dates
    dates = UserProblem.objects.values_list('last_solved', flat=True).distinct()
    # Format dates to string 'YYYY-MM-DD'
    date_strings = [d.strftime('%Y-%m-%d') for d in dates if d]
    return JsonResponse({'dates': date_strings})



def calendar_data(request):
    """
    Return JSON list of questions solved on the requested date.
    Expects ?date=yyyy-mm-dd as GET param.
    """
    user = User.objects.get(username = 'testuser')
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






def revision_question(request):

    user=User.objects.get(username = 'testuser')

    revision_ques = UserProblem.objects.filter(user=user, mark_for_revision=True).order_by('-last_solved')

    print(revision_ques)

    
    
    return render(request , "revised.html", {"revision_ques": revision_ques})





