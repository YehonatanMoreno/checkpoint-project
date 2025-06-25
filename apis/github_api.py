import logging

from apis.api_template import APITemplate
from classes.repository import Repository


logging.basicConfig(level=logging.DEBUG)

class GITHUB_API(APITemplate):
    BASE_URL = "https://api.github.com"
    
    @classmethod
    def get_repository_details(cls, repo_url: str) -> Repository:
        logging.info(f"Requesting github for repo details: {repo_url}")
        repo_details = super().get(repo_url).json()
        return Repository(name=repo_url.split('/')[-1], stars=repo_details["stargazers_count"], forks=repo_details["forks"])
