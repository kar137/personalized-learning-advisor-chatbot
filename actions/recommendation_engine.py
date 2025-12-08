from typing import List, Dict, Any

class RecommendationEngine:
    def __init__(self):
        # Mock database for recommendations
        self.courses = {
            "AI": [
                {"title": "Machine Learning by Andrew Ng", "platform": "Coursera", "level": "Beginner"},
                {"title": "Deep Learning Specialization", "platform": "Coursera", "level": "Intermediate"},
                {"title": "Fast.ai Practical Deep Learning", "platform": "Fast.ai", "level": "Advanced"}
            ],
            "Web Development": [
                {"title": "The Web Developer Bootcamp", "platform": "Udemy", "level": "Beginner"},
                {"title": "Full Stack Open", "platform": "University of Helsinki", "level": "Intermediate"},
                {"title": "Advanced React", "platform": "Frontend Masters", "level": "Advanced"}
            ],
            "Cybersecurity": [
                {"title": "Introduction to Cyber Security", "platform": "FutureLearn", "level": "Beginner"},
                {"title": "Cybersecurity Specialization", "platform": "Coursera", "level": "Intermediate"}
            ]
        }

        self.projects = {
            "AI": [
                "Build a Chatbot using Rasa",
                "Image Classification with CNN",
                "Predicting House Prices using Regression"
            ],
            "Web Development": [
                "Personal Portfolio Website",
                "E-commerce Store",
                "Task Management App"
            ],
            "Cybersecurity": [
                "Keylogger in Python",
                "Network Packet Sniffer",
                "Password Strength Checker"
            ]
        }

        self.career_paths = {
            "AI": ["Machine Learning Engineer", "Data Scientist", "AI Research Scientist"],
            "Web Development": ["Frontend Developer", "Backend Developer", "Full Stack Engineer"],
            "Cybersecurity": ["Security Analyst", "Penetration Tester", "Security Engineer"]
        }

    def get_learning_path(self, domain: str) -> str:
        paths = {
            "AI": "Start with Python -> Math for ML -> Basic ML Algorithms -> Deep Learning -> NLP/CV",
            "Web Development": "HTML/CSS -> JavaScript -> React/Vue -> Node.js -> Databases -> DevOps",
            "Cybersecurity": "Networking Basics -> Linux -> Scripting (Python/Bash) -> Ethical Hacking -> Cloud Security"
        }
        return paths.get(domain, "I recommend starting with the basics of Computer Science and then specializing.")

    def recommend_courses(self, domain: str, level: str = "Beginner") -> List[Dict[str, Any]]:
        domain_courses = self.courses.get(domain, [])
        # Filter by level if needed, for now return all for the domain
        return domain_courses

    def recommend_projects(self, domain: str) -> List[str]:
        return self.projects.get(domain, ["Build a simple To-Do App", "Create a Calculator"])

    def recommend_career(self, domain: str) -> List[str]:
        return self.career_paths.get(domain, ["Software Engineer", "Technical Consultant"])
