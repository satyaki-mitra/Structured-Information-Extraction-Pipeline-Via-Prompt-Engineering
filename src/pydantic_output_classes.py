# DEPENDENCIES
import logging
import warnings
from pydantic import Field
from typing import Optional
from pydantic import BaseModel


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING 
logger = logging.getLogger(__name__)


# DEFINE PYDANTIC MODEL FOR RESPONSE TO GPT'S ENDPOINT
class OutputItemGpt(BaseModel):
    """
    Represents an output item for GPT model with required and optional fields

    Required fields do not have default values and must be provided

    Optional fields are initialized to None by default and will be excluded if None

    """
    name           : str                                                            # Name of the output item
    about          : str                                                            # Information about the output item    
    description    : str                                                            # Description of the output item 
    source         : str                                                            # Source of the output item
    userProfileUrl : Optional[str]   = Field(default = '', exclude_none = True)     # URL of the user profile
    searchJobTitle : Optional[str]   = Field(default = '', exclude_none = True)     # The job title which has been searched in LinkedIn
    companyLinks   : Optional[list]  = Field(default = [], exclude_none = True)     # Web Links for the company
    jobPosterName  : Optional[str]   = Field(default = None, exclude_none = True)   # Name of the job poster (optional)
    jobStarterName : Optional[str]   = Field(default = None, exclude_none = True)   # Name of the job starter (optional)
    companyName    : Optional[str]   = Field(default = None, exclude_none = True)   # Name of the company (optional)
    currentRole    : Optional[str]   = Field(default = None, exclude_none = True)   # Current role of the user (optional)
    classification : Optional[str]   = Field(default = None, exclude_none = True)   # Classification decision (optional)
    error          : Optional[str]   = Field(default = None, exclude_none = True)   # Error message, if any (optional)

    class Config:
        json_encoders = {Optional[str]   : lambda v: v or None,
                         Optional[float] : lambda v: v or None
                        }
    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(msg   = f"OutputItemGpt created: {self.dict()}", 
                     extra = {"request_id": "model_creation"})
