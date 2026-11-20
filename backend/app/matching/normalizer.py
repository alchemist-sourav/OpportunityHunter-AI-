from __future__ import annotations

from typing import Any

SKILL_ALIASES: dict[str, str] = {
    # JavaScript ecosystem
    "js": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "jsx": "javascript",
    "node": "node.js",
    "nodejs": "node.js",
    "expressjs": "express",
    "nextjs": "next.js",
    "next.js": "next.js",
    "reactjs": "react",
    "vuejs": "vue",
    "angularjs": "angular",
    # Python ecosystem
    "py": "python",
    "django-rest-framework": "django rest framework",
    "drf": "django rest framework",
    "flask-restful": "flask restful",
    "fastapi": "fastapi",
    "pandas": "pandas",
    "numpy": "numpy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pytorch": "pytorch",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "keras": "keras",
    # Databases
    "postgres": "postgresql",
    "psql": "postgresql",
    "mysql": "mysql",
    "maria": "mariadb",
    "mongo": "mongodb",
    "redis": "redis",
    "dynamodb": "dynamodb",
    "es": "elasticsearch",
    "elastic": "elasticsearch",
    # Cloud & DevOps
    "aws": "aws",
    "gcp": "google cloud platform",
    "azure": "microsoft azure",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "docker": "docker",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "github-actions": "github actions",
    "gitlab-ci": "gitlab ci",
    "jenkins": "jenkins",
    "terraform": "terraform",
    "tf": "terraform",
    "ansible": "ansible",
    # ML/AI
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "llm": "large language models",
    "genai": "generative ai",
    # Languages
    "c++": "cpp",
    "c#": "csharp",
    "csharp": "csharp",
    "golang": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala",
    # Web
    "html": "html",
    "css": "css",
    "scss": "scss",
    "sass": "sass",
    "tailwind": "tailwind css",
    "bootstrap": "bootstrap",
    # Testing
    "jest": "jest",
    "pytest": "pytest",
    "cypress": "cypress",
    "playwright": "playwright",
    "selenium": "selenium",
    # Other
    "git": "git",
    "sql": "sql",
    "nosql": "nosql",
    "rest": "rest api",
    "graphql": "graphql",
    "grpc": "grpc",
    "microservices": "microservices",
    "serverless": "serverless",
    "api": "api design",
    "oauth": "oauth",
    "oauth2": "oauth2",
    "jwt": "jwt",
    "ssl": "ssl/tls",
    "tls": "ssl/tls",
}

SKILL_CATEGORIES: dict[str, set[str]] = {
    "programming_languages": {
        "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#", "ruby",
        "php", "swift", "kotlin", "scala", "sql", "html", "css",
    },
    "frameworks": {
        "react", "vue", "angular", "svelte", "next.js", "django", "flask", "fastapi",
        "express", "spring", "rails", "laravel", "node.js", "angular",
    },
    "databases": {
        "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch",
        "dynamodb", "cassandra", "mariadb",
    },
    "cloud": {
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
    },
    "ml_ai": {
        "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn",
        "keras", "nlp", "computer vision", "llm", "generative ai",
    },
    "devops": {
        "docker", "kubernetes", "terraform", "ansible", "ci/cd", "github actions",
        "gitlab ci", "jenkins", "terraform",
    },
    "testing": {
        "jest", "pytest", "cypress", "playwright", "selenium",
    },
    "soft_skills": {
        "communication", "teamwork", "problem solving", "leadership", "agile", "scrum",
    },
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill string to its canonical form."""
    if not skill:
        return ""
    skill = skill.strip().lower()
    # Remove special characters except +, #, .
    import re
    skill = re.sub(r"[^\w\s+#.-]", "", skill)
    skill = skill.strip()
    # Check aliases
    if skill in SKILL_ALIASES:
        return SKILL_ALIASES[skill]
    return skill


def normalize_skills(skills: list[str]) -> list[str]:
    """Normalize a list of skills, removing duplicates and empty entries."""
    normalized = []
    seen = set()
    for skill in skills:
        normalized_skill = normalize_skill(skill)
        if normalized_skill and normalized_skill not in seen:
            seen.add(normalized_skill)
            normalized.append(normalized_skill)
    return normalized


def get_skill_category(skill: str) -> str | None:
    """Get the category of a skill."""
    normalized = normalize_skill(skill)
    for category, skills in SKILL_CATEGORIES.items():
        if normalized in skills:
            return category
    return None


def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    """Categorize a list of skills into their respective categories."""
    categorized: dict[str, list[str]] = {cat: [] for cat in SKILL_CATEGORIES}
    categorized["other"] = []
    
    for skill in skills:
        normalized = normalize_skill(skill)
        category = get_skill_category(skill)
        if category:
            categorized[category].append(normalized)
        else:
            categorized["other"].append(normalized)
    
    # Remove empty categories
    return {k: v for k, v in categorized.items() if v}


def extract_skill_tokens(text: str) -> set[str]:
    """Extract potential skill tokens from text."""
    import re
    # Common delimiters
    tokens = re.split(r"[,;|/\n\t\r]+", text.lower())
    tokens = {t.strip() for t in tokens if t.strip()}
    # Filter out very short tokens and common words
    stop_words = {"and", "or", "the", "a", "an", "in", "on", "at", "to", "for", "with", "of", "from", "by", "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their"}
    return {t for t in tokens if len(t) > 2 and t not in stop_words}