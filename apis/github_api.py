from typing import List
from pydantic import BaseModel

from apis.api_template import APITemplate


class Repository(BaseModel):
    name: str
    stars: int
    forks: int
    
    def __init__(self, name, stars, forks) -> None:
        self.name = name
        self.stars = stars
        self.forks = forks
        
    def __str__(self) -> str:
        return f"-{self.name} (stars: {self.stars}, forks: {self.forks})"
    
    def __lt__(self, other: "Repository") -> bool:
        if self.stars < other.stars:
            return True
        if self.stars == other.stars:
            return self.forks < other.forks
        return False
class GITHUB_API(APITemplate):
    BASE_URL = "https://api.github.com"
    
    @classmethod
    def get_repository_details(cls, repo_url: str) -> Repository:
        repo_details = super().get(repo_url).json()
        return Repository(repo_url.split('/')[-1], repo_details["stargazers_count"], repo_details["forks"])
