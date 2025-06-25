import requests

class NVD_API:
    BASE_URL = "https://services.nvd.nist.gov/rest/json/"
    _instance = None
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(NVD_API, cls).__new__(cls)
        return cls.instance
    

    def get_CPEs_by_keyword(self, keyword: str) -> list[str]:
        cpes_list = []
        products = requests.get(f'{NVD_API.BASE_URL}/cpes/2.0/?keywordSearch={keyword}').json()["products"]
        for product in products:
            title = product["cpe"]["titles"][0]["title"]
            cpe_name = product["cpe"]["cpeName"]
            cpes_list.append(f'{title} ({cpe_name})')
        return cpes_list
    
    def get_vulnerability_by_cpe(self, cpe_name: str):
        CVEs_list = []
        vulnerabilities = requests.get(f'{NVD_API.BASE_URL}/cves/2.0?cpeName={cpe_name}').json()["vulnerabilities"]
        for vulnerability in vulnerabilities:
            cve_details = vulnerability["cve"]
            CVEs_list.append(self.extract_returned_details_for_cve(cve_details))           
        return CVEs_list
    
    def extract_returned_details_for_cve(self, cve_details: dict) -> dict:
        cve_details_to_return = {}
        cve_details_to_return["id"] = cve_details["id"]
        cve_metrics = cve_details["metrics"]
        cve_version = "cvssMetricV31" if "cvssMetricV31" in cve_metrics else "cvssMetricV2" # use older version if I have to
        cve_details_to_return["cvss_score"] = cve_details["metrics"][cve_version][0]["cvssData"]["baseScore"]
        cve_details_to_return["description"] = list(filter(lambda x: x["lang"] == "en", cve_details["descriptions"]))[0]["value"]
        cve_details_to_return["relevantReferencesURLs"] = self.extract_exploit_github_references_urls(cve_details["references"])
        return cve_details_to_return
    
    def extract_exploit_github_references_urls(self, references: list[dict]) -> list[str]:
        return [NVD_API.slice_github_url(reference["url"]) for reference in references if "github" in reference["url"] and "Exploit" in reference["tags"]]

    @staticmethod
    def slice_github_url(url: str) -> str: # so it contains the endpoint until the repo name without additionals
        url_components = url[8:].split('/')[1:3]
        url_components.insert(0, "repos")
        return "/".join(url_components)
