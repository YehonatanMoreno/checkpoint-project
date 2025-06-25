import requests

class GITHUB_API:
    BASE_URL = "https://api.github.com"
    _instance = None
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GITHUB_API, cls).__new__(cls)
        return cls.instance
    
    def get_repository_details(self, repo_url: str) -> dict:
        repo_details = requests.get(f'{GITHUB_API.BASE_URL}/{repo_url}').json()
        return {
            "stars": repo_details["stargazers_count"],
            "forks": repo_details["forks"]
        }
