import logging
from typing import List

from classes.cve import CVE
from apis.api_template import APITemplate


class NVD_API(APITemplate):
    BASE_URL = "https://services.nvd.nist.gov/rest/json"

    @classmethod
    def get_CPEs_by_keyword(cls, keyword: str) -> List[str]:
        logging.info(f"Requesting NVD for CPEs by the keyword: {keyword}")
        cpes_list = []
        products = super().get(f'cpes/2.0/?keywordSearch={keyword}').json()["products"]
        for product in products:
            title = product["cpe"]["titles"][0]["title"]
            cpe_name = product["cpe"]["cpeName"]
            cpes_list.append(f'{title} ({cpe_name})')
        return cpes_list
    
    @classmethod
    def get_vulnerabilities_by_cpe_and_severity(cls, cpe_name: str, min_severity: float = 0) -> List[CVE]:
        logging.info(f"Requesting NVD for CVEs by the CPE: {cpe_name} and with min severity of: {min_severity}")
        CVEs_list: List[CVE] = []
        vulnerabilities = super().get(f'cves/2.0?cpeName={cpe_name}').json()["vulnerabilities"]
        for vulnerability in vulnerabilities:
            cve_details = vulnerability["cve"]
            cve = CVE(**cls.__extract_returned_details_for_cve(cve_details))
            print(cve)
            if (cve.severity >= min_severity):
                CVEs_list.append(cve)
        return CVEs_list
    
    @staticmethod
    def __extract_returned_details_for_cve(cve_details: dict) -> dict:
        cve_details_to_return = {}
        cve_details_to_return["cve_id"] = cve_details["id"]
        cve_metrics = cve_details["metrics"]
        cve_version = "cvssMetricV31" if "cvssMetricV31" in cve_metrics else "cvssMetricV2" # use older version if I have to
        cve_details_to_return["severity"] = cve_details["metrics"][cve_version][0]["cvssData"]["baseScore"]
        whole_description = list(filter(lambda x: x["lang"] == "en", cve_details["descriptions"]))[0]["value"]
        cve_details_to_return["description"] = NVD_API.__extract_first_sentence_from_description(whole_description)
        cve_details_to_return["relevant_repositories_urls"] = NVD_API.__extract_exploit_github_references_urls(cve_details["references"])
        return cve_details_to_return
    
    @staticmethod
    def __extract_first_sentence_from_description(description: str) -> str: 
        """
        asuming a sentence is a non numeric string followed by a dot
        """ 
        for i in range(1, len(description) - 1):
            if description[i] == "." and not description[i - 1].isnumeric():
                print(i)
                return description[:i + 1]
        return description
    
    @staticmethod
    def __extract_exploit_github_references_urls(references: List[dict]) -> List[str]:
        return list(set([NVD_API.__slice_github_url(reference["url"]) for reference in references
                if "github" in reference["url"] and "tags" in reference and "Exploit" in reference["tags"]]))

    @staticmethod
    def __slice_github_url(url: str) -> str: # so it contains the endpoint until the repo name without additionals
        url_components = url[8:].split('/')[1:3]
        url_components.insert(0, "repos")
        return "/".join(url_components)
    
    @classmethod
    def get_cve_by_id(cls, ide: str):
        res = super().get(f'cves/2.0?cveId={ide}')
        return list(filter(lambda x: x["lang"] == "en", res.json()['vulnerabilities'][0]['cve']['descriptions']))[0]["value"]


# def func(description):
#     for i in range(1, len(description) - 1):
#             if description[i] == "." and not description[i - 1].isnumeric():
#                 print(i)
#                 return description[:i + 1]
#     return description
# print(func("Unspecified vulnerability in the benchmark reporting system in Google Web Toolkit (GWT) before 1.4.61 has unknown impact and attack vectors, possibly related to cross-site scripting (XSS)."))