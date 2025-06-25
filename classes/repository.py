from pydantic import BaseModel


class Repository(BaseModel):
    name: str
    stars: int
    forks: int
        
    def __str__(self) -> str:
        return f"• {self.name} (stars: {self.stars}, forks: {self.forks})"
    
    def __lt__(self, other: "Repository") -> bool:
        if self.stars < other.stars:
            return True
        if self.stars == other.stars:
            return self.forks < other.forks
        return False
