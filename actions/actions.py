from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
from .recommendation_engine import RecommendationEngine
from .utils import format_list, format_courses
from .db import Database

recommendation_engine = RecommendationEngine()
db = Database()

class ActionRecommendLearningPath(Action):
    def name(self) -> Text:
        return "action_recommend_learning_path"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        target_domain = tracker.get_slot("target_domain")
        interests = tracker.get_slot("interests")
        # Fallback: if target_domain is not set, use most recent interest
        if not target_domain and interests:
            target_domain = interests[-1]

        if not target_domain:
            dispatcher.utter_message(text="I need to know your area of interest to recommend a learning path. Could you tell me what you are interested in?")
            return []

        # Collect additional profile information to personalize timeline
        degree = tracker.get_slot("degree")
        semester = tracker.get_slot("semester")
        gpa = tracker.get_slot("gpa")
        skills = tracker.get_slot("skills") or []
        time_commitment = tracker.get_slot("time_commitment") or "1 hour"
        learning_goal = tracker.get_slot("learning_goal") or ""

        # Base path (short string) from recommendation engine
        base_path = recommendation_engine.get_learning_path(target_domain)

        # Parse time commitment (hours per day)
        import re
        hours_per_day = 1.0
        m = re.search(r"(\d+(?:\.\d+)?)", str(time_commitment))
        if m:
            try:
                hours_per_day = float(m.group(1))
            except Exception:
                hours_per_day = 1.0

        # Difficulty scaling: more hours -> faster progress
        if hours_per_day < 0.75:
            speed_factor = 1.8
        elif hours_per_day < 1.5:
            speed_factor = 1.2
        elif hours_per_day < 3:
            speed_factor = 1.0
        else:
            speed_factor = 0.8

        # Split the base path into stages
        stages = [s.strip() for s in base_path.split('->')]

        # If user already lists Python, remove Python stage entirely
        has_python = any('python' in (s or '').lower() for s in skills)
        if has_python:
            stages = [s for s in stages if 'python' not in s.lower()]

        # Assign estimated weeks per stage (base) and adjust by speed and existing skills
        base_weeks = {
            'python': 2,
            'math for ml': 4,
            'basic ml algorithms': 6,
            'deep learning': 10,
            'nlp/cv': 8,
            'html/css': 2,
            'javascript': 4,
            'react/vue': 6,
            'node.js': 6,
            'databases': 4,
            'devops': 6,
            'networking basics': 3,
            'linux': 3,
            'scripting (python/bash)': 4,
            'ethical hacking': 6,
            'cloud security': 6
        }

        timeline_lines = []
        total_weeks = 0
        for stage in stages:
            key = stage.lower()
            # normalize common variations
            key = key.replace('.', '').replace('  ', ' ').strip()
            weeks = None
            # try to match keywords
            for k in base_weeks:
                if k in key:
                    weeks = base_weeks[k]
                    break
            if weeks is None:
                # fallback default
                weeks = 6

            # reduce python time if user already knows python
            if 'python' in key and has_python:
                weeks = max(1, int(weeks * 0.5))

            # adjust by speed factor
            adj_weeks = max(1, int(weeks * speed_factor))
            total_weeks += adj_weeks
            timeline_lines.append(f"{stage}: ~{adj_weeks} week(s)")

        # Build a helpful explanation
        header = f"Here is a recommended learning path for {target_domain} based on your profile:\n"
        profile_summary = f"(Degree: {degree or 'N/A'}, Semester: {semester or 'N/A'}, GPA: {gpa or 'N/A'}, Daily study: {time_commitment})\n"
        goal_line = f"Primary goal: {learning_goal}\n\n" if learning_goal else ''

        timeline_text = '\n'.join(timeline_lines)
        timeline_note = f"\nEstimated total time: ~{total_weeks} week(s) (depends on consistency). These estimates scale with your daily study time.\n"

        actionable = "Tips:\n- Practice by building small projects after each stage.\n- Use curated courses (Coursera, fast.ai, Udemy) and official docs.\n- Pair learning with hands-on projects and version control (Git).\n"

        # Build display path from final stages (after any filtering)
        display_path = ' -> '.join(stages)

        message = header + profile_summary + goal_line + "Path: " + (display_path or base_path) + "\n\nTimeline:\n" + timeline_text + timeline_note + "\n" + actionable

        dispatcher.utter_message(text=message)

        return []

class ActionRecommendCourses(Action):
    def name(self) -> Text:
        return "action_recommend_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        target_domain = tracker.get_slot("target_domain")
        interests = tracker.get_slot("interests")
        
        if not target_domain and interests:
            target_domain = interests[-1]

        if not target_domain:
            dispatcher.utter_message(text="Please specify a domain for course recommendations (e.g., AI, Web Development).")
            return []

        courses = recommendation_engine.recommend_courses(target_domain)
        if courses:
            formatted_courses = format_courses(courses)
            dispatcher.utter_message(text=f"Here are some recommended courses for {target_domain}:\n{formatted_courses}")
        else:
            dispatcher.utter_message(text=f"I couldn't find specific courses for {target_domain}, but I suggest checking Coursera or Udemy.")

        return []

class ActionRecommendProjects(Action):
    def name(self) -> Text:
        return "action_recommend_projects"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        target_domain = tracker.get_slot("target_domain")
        interests = tracker.get_slot("interests")
        
        if not target_domain and interests:
            target_domain = interests[-1]

        if not target_domain:
            dispatcher.utter_message(text="I need to know your domain to suggest projects.")
            return []

        projects = recommendation_engine.recommend_projects(target_domain)
        formatted_projects = format_list(projects)
        dispatcher.utter_message(text=f"Here are some project ideas for {target_domain}:\n{formatted_projects}")

        return []

class ActionRecommendCareer(Action):
    def name(self) -> Text:
        return "action_recommend_career"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        target_domain = tracker.get_slot("target_domain")
        interests = tracker.get_slot("interests")
        
        if not target_domain and interests:
            target_domain = interests[-1]

        if not target_domain:
            dispatcher.utter_message(text="I need to know your domain to give career guidance.")
            return []

        careers = recommendation_engine.recommend_career(target_domain)
        formatted_careers = format_list(careers)
        dispatcher.utter_message(text=f"Here are some career paths in {target_domain}:\n{formatted_careers}")

        return []

class ActionShowProfile(Action):
    def name(self) -> Text:
        return "action_show_profile"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        name = tracker.get_slot("name")
        degree = tracker.get_slot("degree")
        semester = tracker.get_slot("semester")
        gpa = tracker.get_slot("gpa")
        interests = tracker.get_slot("interests")
        
        profile_text = f"Profile:\nName: {name}\nDegree: {degree}\nSemester: {semester}\nGPA: {gpa}\nInterests: {interests}"
        dispatcher.utter_message(text=profile_text)
        return []

class ActionResetAllSlots(Action):
    def name(self) -> Text:
        return "action_reset_all_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [AllSlotsReset()]

class ActionGreet(Action):
    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_greet")
        return [AllSlotsReset()]


class ValidateProfileForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_profile_form"

    async def validate_degree(self,
                              slot_value: Any,
                              dispatcher: CollectingDispatcher,
                              tracker: Tracker,
                              domain: DomainDict,) -> Dict[Text, Any]:
        if slot_value and isinstance(slot_value, str) and len(slot_value) > 1:
            return {"degree": slot_value}
        dispatcher.utter_message(text="I didn't get your degree clearly. Which degree are you pursuing?")
        return {"degree": None}

    async def validate_semester(self,
                                slot_value: Any,
                                dispatcher: CollectingDispatcher,
                                tracker: Tracker,
                                domain: DomainDict,) -> Dict[Text, Any]:
        import re

        # Accept numbers, ordinals (5th), or numeric words if simple digits present
        if slot_value is None:
            dispatcher.utter_message(text="Please provide your semester as a number, e.g. 5")
            return {"semester": None}

        text = str(slot_value).lower().strip()

        # Try to find a number in the text (e.g., '5', '5th')
        m = re.search(r"(\d{1,2})", text)
        if m:
            try:
                sem = int(m.group(1))
                if 1 <= sem <= 12:
                    return {"semester": str(sem)}
            except Exception:
                pass

        # fallback: map some common words
        words_to_num = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12
        }
        for word, num in words_to_num.items():
            if word in text:
                return {"semester": str(num)}

        dispatcher.utter_message(text="Please provide your semester as a number (for example: 5 or '5th').")
        return {"semester": None}

    async def validate_gpa(self,
                           slot_value: Any,
                           dispatcher: CollectingDispatcher,
                           tracker: Tracker,
                           domain: DomainDict,) -> Dict[Text, Any]:
        try:
            g = float(slot_value)
            # accept 0-10 or 0-4, normalize to string
            if 0.0 <= g <= 10.0:
                return {"gpa": str(g)}
        except Exception:
            pass
        dispatcher.utter_message(text="Please provide your GPA as a number (for example: 3.5 or 7.2).")
        return {"gpa": None}

    async def validate_skills(self,
                              slot_value: Any,
                              dispatcher: CollectingDispatcher,
                              tracker: Tracker,
                              domain: DomainDict,) -> Dict[Text, Any]:
        # normalize skills into a list
        if not slot_value:
            dispatcher.utter_message(text="Please list at least one technical skill you have.")
            return {"skills": None}
        if isinstance(slot_value, list):
            skills_list = slot_value
        else:
            skills_list = [s.strip() for s in str(slot_value).replace(';', ',').split(',') if s.strip()]
        return {"skills": skills_list}

    async def validate_time_commitment(self,
                                       slot_value: Any,
                                       dispatcher: CollectingDispatcher,
                                       tracker: Tracker,
                                       domain: DomainDict,) -> Dict[Text, Any]:
        if slot_value:
            return {"time_commitment": str(slot_value)}
        dispatcher.utter_message(text="How much time can you commit to learning daily? (e.g., 1 hour)")
        return {"time_commitment": None}

    async def validate_interests(self,
                                 slot_value: Any,
                                 dispatcher: CollectingDispatcher,
                                 tracker: Tracker,
                                 domain: DomainDict,) -> Dict[Text, Any]:
        if not slot_value:
            dispatcher.utter_message(text="What are your areas of interest? (e.g., AI, Web Development)")
            return {"interests": None}
        if isinstance(slot_value, list):
            interests_list = slot_value
        else:
            # Parse as comma-separated or single item
            text = str(slot_value).strip()
            if ',' in text:
                interests_list = [s.strip() for s in text.split(',') if s.strip()]
            else:
                interests_list = [text]
        
        # Ensure we have at least one valid interest
        if interests_list and len(interests_list) > 0:
            return {"interests": interests_list}
        
        dispatcher.utter_message(text="What are your areas of interest? (e.g., AI, Web Development)")
        return {"interests": None}

    async def validate_learning_goal(self,
                                     slot_value: Any,
                                     dispatcher: CollectingDispatcher,
                                     tracker: Tracker,
                                     domain: DomainDict,) -> Dict[Text, Any]:
        # Accept any non-empty string for learning goal
        if slot_value and len(str(slot_value).strip()) > 0:
            return {"learning_goal": str(slot_value).strip()}
        dispatcher.utter_message(text="Please tell me your learning goal (e.g., 'Learn AI', 'Become a web developer')")
        return {"learning_goal": None}

