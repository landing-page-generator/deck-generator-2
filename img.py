import requests
import os


def get_image_from_pexels(prompt):
    pexels_api_key = os.environ.get("PEXELS_API_KEY")

    headers = {
        "Authorization": pexels_api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",  # to avoid 403 Forbidden
    }

    params = {"query": prompt, "per_page": 1}
    url = "https://api.pexels.com/v1/search"
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if data["total_results"] > 0:
        photo = data["photos"][0]
        image_url = photo["src"]["original"]
        return image_url
    return ""
