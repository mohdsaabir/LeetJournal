from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import re
import requests
from .models import Question, Tag, DIFFICULTY_CHOICES, UserProblem
from django.contrib.auth.models import User



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





def question_detail_view(request, pk):
    question = get_object_or_404(Question, pk=pk)
    # You can later pass code snippets, optimized code, and notes here too
    return render(request, "journal/question_detail.html", {"question": question})



def all_solved_view(request):
    questions = Question.objects.all()  # or filter by solved status if you have it
    return render(request, "journal/all_solved.html", {"questions": questions})
