from pydantic import BaseModel


class Repository(BaseModel):
    name: str
    stars_count: int
    forks_count: int
        
    def __str__(self) -> str:
        return f"• {self.name} (stars_count: {self.stars_count}, forks: {self.forks_count})"
    
    def __lt__(self, other: "Repository") -> bool: # in order to be able to sort
        if self.stars_count < other.stars_count:
            return True
        if self.stars_count == other.stars_count:
            return self.forks_count < other.forks_count
        return False
