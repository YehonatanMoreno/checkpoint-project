from typing import List
from functools import reduce
from pydantic import BaseModel

from apis.github_api import GITHUB_API, Repository


class CVE(BaseModel):
    cve_id: str
    severity: float
    description: str
    relevant_repositories_urls: List[str] = []
    relevant_repositories_list: List[Repository] = []
    relevant_repositories: str = ""
    
    def set_relevant_repositories(self) -> None:
        print(f"relevant_repositories_urls: {self.relevant_repositories_urls}")
        if len(self.relevant_repositories_urls) > 0:
            print("fetching git repos!!")
            self.relevant_repositories_list = [GITHUB_API.get_repository_details(url) for url in self.relevant_repositories_urls]
            print(self.relevant_repositories_list)
            self.relevant_repositories_list.sort()
            repositories_details = [str(repo) for repo in self.relevant_repositories_list]
            print(repositories_details)
            self.relevant_repositories = reduce(lambda a, b: a + '\n' + b, repositories_details)
            print(self.relevant_repositories)