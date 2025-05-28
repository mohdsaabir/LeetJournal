import requests
import re

def extract_slug(url):
    match = re.search(r'leetcode\.com/problems/([^/]+)/?', url)
    return match.group(1) if match else None

def fetch_leetcode_data(slug):
    query = """
    query getQuestionDetail($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionFrontendId   # the “#” number you see on the problem list
        title
        titleSlug
        difficulty
        content              # the full problem statement in HTML
        tags: topicTags {
          name
        }
        likes
        dislikes
        isPaidOnly
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

if __name__ == "__main__":
    leetcode_url = input("Enter LeetCode question URL: ").strip()
    slug = extract_slug(leetcode_url)

    if not slug:
        print("Invalid LeetCode URL")
    else:
        q = fetch_leetcode_data(slug)
        if not q:
            print("Failed to fetch data.")
        else:
            print(f"\n--- Question #{q['questionFrontendId']} – {q['title']} ---")
            print(f"Slug      : {q['titleSlug']}")
            print(f"Difficulty: {q['difficulty']}")
            print(f"Paid Only : {q['isPaidOnly']}")
            print(f"Likes     : {q['likes']}   Dislikes: {q['dislikes']}")
            print("Tags      :", ", ".join(tag["name"] for tag in q["tags"]))
            print("\n--- Problem Statement (HTML) ---")
            print(q["content"])
