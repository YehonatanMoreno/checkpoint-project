from apis.api_template import APITemplate


class GITHUB_API(APITemplate):
    BASE_URL = "https://api.github.com"
    
    @classmethod
    def get_repository_details(cls, repo_url: str) -> dict:
        repo_details = super().get(repo_url).json()
        return {
            "stars": repo_details["stargazers_count"],
            "forks": repo_details["forks"]
        }

    @staticmethod
    def sort_repos_by_poularity(repos: list[dict]) -> list[dict]:
        return sorted(repos, key=lambda repo: (repo["stars"], repo["forks"]), reverse=True)
    
    