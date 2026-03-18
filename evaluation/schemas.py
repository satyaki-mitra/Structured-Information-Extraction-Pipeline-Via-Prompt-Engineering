# DEPENDENCIES
import logging
import warnings
from typing import List
from pydantic import Field
from typing import Optional
from pydantic import BaseModel


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


# INPUT SCHEMA FOR LINKEDIN POST DATA
class LinkedInPostInput(BaseModel):
    """
    Pydantic model for validating input LinkedIn post data: all fields have default values making them optional but recommended
    """
    name           : str                 = Field(default = '', description = 'Name of the person posting')
    about          : str                 = Field(default = '', description = 'About section of the poster')
    description    : str                 = Field(default = '', description = 'Main post content/description')
    userProfileUrl : Optional[str]       = Field(default = None, description = 'LinkedIn profile URL')
    source         : str                 = Field(default = '', description = 'Data source identifier')
    searchJobTitle : Optional[str]       = Field(default = None, description = 'Job title used in search')
    companyLinks   : Optional[List[str]] = Field(default = None, description = 'List of company URLs')
    
    class Config:
        json_schema_extra = {"example": {"name"           : "John Doe",
                                         "about"          : "Senior Software Engineer at TechCorp",
                                         "description"    : "Excited to announce that I'm starting a new position as CTO at StartupXYZ!",
                                         "userProfileUrl" : "https://linkedin.com/in/johndoe",
                                         "source"         : "LinkedIn",
                                         "searchJobTitle" : "CTO",
                                         "companyLinks"   : ["https://startupxyz.com"],
                                        }
                            }


# EXTRACTED INFORMATION SCHEMA
class ExtractedJobInfo(BaseModel):
    """
    Pydantic model for individual extracted job information: represents a single job change/transition extracted from the post
    """
    person_name  : str = Field(description = 'Full name of the person mentioned')
    organization : str = Field(description = 'Organization/company name')
    new_role     : str = Field(description = 'New job title or role')
    
    class Config:
        json_schema_extra = {"example": {"person_name"  : "Sarah Johnson",
                                         "organization" : "TechCorp",
                                         "new_role"     : "Senior Data Scientist",
                                        }
                            }


# EXTRACTION RESULT SCHEMA
class ExtractionResult(BaseModel):
    """
    Pydantic model for the complete extraction result from LLM: contains classification, relevance, and all extracted information
    """
    poster_name    : str                    = Field(description = 'Name of the person who posted')
    post_category  : str                    = Field(description = 'Category number (1-5)')
    change_count   : int                    = Field(description = 'Number of job changes detected')
    relevant       : bool                   = Field(description = 'Whether the post is relevant')
    extracted_info : List[ExtractedJobInfo] = Field(default = [], description = 'List of extracted job information')
    
    class Config:
        json_schema_extra = {"example": {"poster_name"    : "John Doe",
                                         "post_category"  : "1",
                                         "change_count"   : 1,
                                         "relevant"       : True,
                                         "extracted_info" : [{"person_name"  : "Sarah Johnson",
                                                              "organization" : "TechCorp",
                                                              "new_role"     : "Senior Data Scientist",
                                                            }]
                                        }
                            }


# OUTPUT SCHEMA FOR API RESPONSE
class LinkedInPostOutput(BaseModel):
    """
    Pydantic model for API response output: combines input data with extraction results for comprehensive output
    """
    name           : str                 = Field(description = 'Name from input')
    about          : str                 = Field(description = 'About section from input')
    description    : str                 = Field(description = 'Description from input')
    source         : str                 = Field(description = 'Source from input')
    userProfileUrl : Optional[str]       = Field(default = '', description = 'Profile URL from input')
    searchJobTitle : Optional[str]       = Field(default = '', description = 'Search job title from input')
    companyLinks   : Optional[List[str]] = Field(default = [], description = 'Company links from input')
    jobPosterName  : Optional[str]       = Field(default = None, description = 'Extracted poster name')
    jobStarterName : Optional[str]       = Field(default = None, description = 'Person who got the new job')
    companyName    : Optional[str]       = Field(default = None, description = 'Company name')
    currentRole    : Optional[str]       = Field(default = None, description = 'Current/new role')
    classification : Optional[str]       = Field(default = None, description = 'Relevant or Irrelevant')
    error          : Optional[str]       = Field(default = None, description = 'Error message if any')
    
    class Config:
        json_schema_extra = {"example" : {"name"           : "John Doe",
                                          "about"          : "Senior Software Engineer",
                                          "description"    : "Excited to announce...",
                                          "source"         : "LinkedIn",
                                          "userProfileUrl" : "https://linkedin.com/in/johndoe",
                                          "searchJobTitle" : "CTO",
                                          "companyLinks"   : ["https://company.com"],
                                          "jobPosterName"  : "John Doe",
                                          "jobStarterName" : "Sarah Johnson",
                                          "companyName"    : "TechCorp",
                                          "currentRole"    : "Senior Data Scientist",
                                          "classification" : "Relevant",
                                          "error"          : None,
                                         }
                            }


# EVALUATION METRICS SCHEMA
class EvaluationMetrics(BaseModel):
    """
    Pydantic model for evaluation metrics: contains comprehensive performance metrics for model evaluation
    """
    accuracy        : float = Field(description = 'Overall accuracy')
    precision       : float = Field(description = 'Precision score')
    recall          : float = Field(description = 'Recall score')
    f1_score        : float = Field(description = 'F1 score')
    true_positives  : int   = Field(description = 'Number of true positives')
    true_negatives  : int   = Field(description = 'Number of true negatives')
    false_positives : int   = Field(description = 'Number of false positives')
    false_negatives : int   = Field(description = 'Number of false negatives')
    total_samples   : int   = Field(description = 'Total number of samples evaluated')
    
    class Config:
        json_schema_extra = {"example" : {"accuracy"        : 0.942,
                                          "precision"       : 0.918,
                                          "recall"          : 0.935,
                                          "f1_score"        : 0.926,
                                          "true_positives"  : 374,
                                          "true_negatives"  : 97,
                                          "false_positives" : 12,
                                          "false_negatives" : 17,
                                          "total_samples"   : 500,
                                         }
                            }


# GROUND TRUTH ANNOTATION SCHEMA
class GroundTruthAnnotation(BaseModel):
    """
    Pydantic model for ground truth annotations: used for creating annotated test datasets for evaluation
    """
    post_id             : str       = Field(description = 'Unique identifier for the post')
    name                : str       = Field(description = 'Poster name')
    description         : str       = Field(description = 'Post description')
    is_relevant         : bool      = Field(description = 'Whether post is relevant')
    category            : int       = Field(description = 'Post category (1-5)')
    extracted_people    : List[str] = Field(default = [], description = 'List of people mentioned')
    extracted_companies : List[str] = Field(default = [], description = 'List of companies mentioned')
    extracted_roles     : List[str] = Field(default = [], description = 'List of roles mentioned')
    annotator           : str       = Field(description = 'Person who annotated this sample')
    annotation_date     : str       = Field(description = 'Date of annotation')
    
    class Config:
        json_schema_extra = {"example" : {"post_id"             : "post_001",
                                          "name"                : "John Doe",
                                          "description"         : "Excited to announce...",
                                          "is_relevant"         : True,
                                          "category"            : 1,
                                          "extracted_people"    : ["Sarah Johnson"],
                                          "extracted_companies" : ["TechCorp"],
                                          "extracted_roles"     : ["Senior Data Scientist"],
                                          "annotator"           : "human_expert_1",
                                          "annotation_date"     : "2024-01-15",
                                         }
                            }