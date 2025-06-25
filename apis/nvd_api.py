from typing import List
from functools import reduce
from pydantic import BaseModel

from apis.api_template import APITemplate
from apis.github_api import GITHUB_API, Repository


class CVE(BaseModel):
    cve_id: str
    severity: float
    description: str
    relevant_repositories_urls: List[str] = []
    relevant_repositories_list: List[Repository] = []
    relevant_repositories: str = ""
    
    def set_relevant_repositories(self) -> None:
        if len(self.relevant_repositories) > 0:
            self.relevant_repositories_list = [GITHUB_API.get_repository_details(url) for url in self.relevant_repositories_urls]
            self.relevant_repositories_list.sort()
            repositories_details = [str(repo) for repo in self.relevant_repositories]
            self.relevant_repositories_string = reduce(lambda a, b: a + b + '\n', repositories_details)


class NVD_API(APITemplate):
    BASE_URL = "https://services.nvd.nist.gov/rest/json"

    @classmethod
    def get_CPEs_by_keyword(cls, keyword: str) -> List[str]:
        cpes_list = []
        products = super().get(f'cpes/2.0/?keywordSearch={keyword}').json()["products"]
        for product in products:
            title = product["cpe"]["titles"][0]["title"]
            cpe_name = product["cpe"]["cpeName"]
            cpes_list.append(f'{title} ({cpe_name})')
        return cpes_list
    
    @classmethod
    def get_vulnerability_by_cpe_and_severity(cls, cpe_name: str, min_severity: float = 0) -> List[CVE]:
        CVEs_list: List[CVE] = []
        vulnerabilities = super().get(f'cves/2.0?cpeName={cpe_name}').json()["vulnerabilities"]
        for vulnerability in vulnerabilities:
            cve_details = vulnerability["cve"]
            CVEs_list.append(CVE(**cls.__extract_returned_details_for_cve(cve_details)))
        return list(filter(lambda cve: cve.severity >= min_severity, CVEs_list))
    
    @classmethod
    def __extract_returned_details_for_cve(cls, cve_details: dict) -> dict:
        cve_details_to_return = {}
        cve_details_to_return["cve_id"] = cve_details["id"]
        cve_metrics = cve_details["metrics"]
        cve_version = "cvssMetricV31" if "cvssMetricV31" in cve_metrics else "cvssMetricV2" # use older version if I have to
        cve_details_to_return["severity"] = cve_details["metrics"][cve_version][0]["cvssData"]["baseScore"]
        cve_details_to_return["description"] = list(filter(lambda x: x["lang"] == "en", cve_details["descriptions"]))[0]["value"]
        cve_details_to_return["relevant_repositories_urls"] = cls.__extract_exploit_github_references_urls(cve_details["references"])
        return cve_details_to_return
    
    @classmethod
    def __extract_exploit_github_references_urls(cls, references: List[dict]) -> List[str]:
        return [cls.__slice_github_url(reference["url"]) for reference in references if "github" in reference["url"] and "tags" in reference and "Exploit" in reference["tags"]]

    @classmethod
    def __slice_github_url(cls, url: str) -> str: # so it contains the endpoint until the repo name without additionals
        url_components = url[8:].split('/')[1:3]
        url_components.insert(0, "repos")
        return "/".join(url_components)
