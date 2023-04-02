from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import pathlib
import re
import time
import json

skippedRepo = ["InfiniteSynthesis", "personal-website", "blog-comment"]

root = pathlib.Path(__file__).parent.resolve()

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {}Start \-\->.*<!\-\- {}End \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {}Start -->{}<!-- {}End -->".format(marker, chunk, marker)
    return r.sub(chunk, content)

def fetch_blog():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get("https://shenyu-official.icu/#/info")
    time.sleep(5)
    preText = driver.find_element(by=By.TAG_NAME, value='pre').get_attribute("innerText")

    blogInfo = json.loads(preText)
    blogInfo = sorted(blogInfo, key=lambda item: item.get("lastModify", 0), reverse=True)[:5]

    return [
        {
            "title": item["title"],
            "url": "https://shenyu-official.icu/#/blog/" + item["blogid"],
            "updated_at": item["lastModify"],
        }
        for item in blogInfo
    ]

def fetch_repo():
    githubRepoApi = "https://api.github.com/users/InfiniteSynthesis/repos"
    repoInfo = requests.get(githubRepoApi).json()
    repoInfo = [item for item in repoInfo if not (item["name"] in skippedRepo or item["archived"] == "true")]
    repoInfo = sorted(repoInfo, key=lambda item: item.get("pushed_at", 0), reverse=True)[:5]

    return [
        {
            "name": item["name"],
            "url": item["html_url"],
            "updated_at": item["pushed_at"][:10]
        }
        for item in repoInfo
    ]

if __name__ == "__main__":
    readme = root / "README.md"

    readme_contents = readme.open().read()

    blogInfo = fetch_blog()
    blogInfoMd = "\n\n".join(
        ["[**{title}**]({url}) - {updated_at}".format(**item) for item in blogInfo]
    )
    rewritten = replace_chunk(readme_contents, "OnMyBlog", blogInfoMd)

    repoInfo = fetch_repo()
    repoInfoMd = "\n\n".join(
        ["[**{name}**]({url}) - {updated_at}".format(**item) for item in repoInfo]
    )
    rewritten = replace_chunk(rewritten, "RecentUpdate", repoInfoMd)

    readme.open("w").write(rewritten)
