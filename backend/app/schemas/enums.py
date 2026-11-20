from enum import Enum


class ExperienceLevel(str, Enum):
    STUDENT = "student"
    FRESHER = "fresher"
    JUNIOR = "junior"
    EXPERIENCED = "experienced"


class OpportunityType(str, Enum):
    INTERNSHIP = "internship"
    FRESHER_JOB = "fresher_job"
    FULL_TIME_JOB = "full_time_job"
    FREELANCE_PROJECT = "freelance_project"


class RemotePreference(str, Enum):
    REMOTE_ONLY = "remote_only"
    HYBRID = "hybrid"
    ONSITE_ONLY = "onsite_only"
    NO_PREFERENCE = "no_preference"
