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


# DEFINE PYDANTIC MODEL FOR REQUEST TO GPT'S ENDPOINT
class InputItemGpt(BaseModel):
    """
    Represents an input item with optional fields for GPT model
    
    All the fields have default empty strings, indicating they are optional
    
    """
    name           : str            = Field(default = '')   # Name of the input item
    about          : str            = Field(default = '')   # Information about the input item
    description    : str            = Field(default = '')   # Description of the input item
    source         : str            = Field(default = '')   # Source of the input item
    companyLinks   : Optional[list] = Field(default = None) # Web Links for the company
    userProfileUrl : Optional[str]  = Field(default = None) # URL of the user profile
    searchJobTitle : Optional[str]  = Field(default = None) # The job title using which data has been searched in LinkedIn

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(msg   = f"InputItemGpt created: {self.dict()}", 
                     extra = {"request_id": "model_creation"})