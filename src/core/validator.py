# DEPENDENCIES
import logging
import warnings
from typing import Any
from typing import List
from typing import Dict
from typing import Optional


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validator for input and output data: provides validation methods for LinkedIn posts and extraction results
    """
    @staticmethod
    def validate_linkedin_post(post: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate LinkedIn post data structure
        
        Arguments:
        ----------
            post { Dict[str, Any] } : LinkedIn post data to validate
        
        Returns:
        --------
                { tuple }           : (is_valid: bool, error_message: Optional[str])
        """
        # Check if input is a dictionary
        if not isinstance(post, dict):
            error_msg = f"Expected dictionary, got {type(post)}"
            
            logger.error(msg   = error_msg,
                         extra = {"request_id": "validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            return False, error_msg
        
        # Check required fields
        required_fields = ['name', 
                           'about', 
                           'description',
                          ]

        missing_fields  = [field for field in required_fields if field not in post]
        
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            
            logger.error(msg   = error_msg,
                         extra = {"request_id": "validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            return False, error_msg
        
        # Check field types
        for field in required_fields:
            if not isinstance(post[field], str):
                error_msg = f"Field '{field}' must be string, got {type(post[field])}"
               
                logger.error(msg   = error_msg,
                             extra = {"request_id": "validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                            )

                return False, error_msg
        
        # Check if required fields are not empty
        empty_fields = [field for field in required_fields if not post[field].strip()]
        
        if empty_fields:
            error_msg = f"Fields cannot be empty: {empty_fields}"
            
            logger.warning(msg   = error_msg,
                           extra = {"request_id": "validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                          )
            # This is a warning, not a hard error
        
        return True, None
    
    
    @staticmethod
    def validate_extraction_result(result: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate extraction result structure
        
        Arguments:
        ----------
            result { Dict[str, Any] } : Extraction result to validate
        
        Returns:
        --------
                   { tuple }          : (is_valid: bool, error_message: Optional[str])
        """
        # Check if input is a dictionary
        if not isinstance(result, dict):
            error_msg = f"Expected dictionary, got {type(result)}"
            
            logger.error(msg   = error_msg,
                         extra = {"request_id": "validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            return False, error_msg
        
        # Check required fields in result
        required_fields = ['poster_name', 
                           'post_category', 
                           'change_count', 
                           'relevant', 
                           'extracted_info',
                          ]

        missing_fields  = [field for field in required_fields if field not in result]
        
        if missing_fields:
            error_msg = f"Missing required fields in extraction result: {missing_fields}"
           
            logger.error(msg   = error_msg,
                         extra = {"request_id": "validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            return False, error_msg
        
        # Validate types
        if not isinstance(result['poster_name'], str):
            return False, "poster_name must be string"
        
        if not isinstance(result['post_category'], str):
            return False, "post_category must be string"
        
        if not isinstance(result['change_count'], int):
            return False, "change_count must be integer"
        
        if not isinstance(result['relevant'], bool):
            return False, "relevant must be boolean"
        
        if not isinstance(result['extracted_info'], list):
            return False, "extracted_info must be list"
        
        # Validate extracted_info items
        for idx, info in enumerate(result['extracted_info']):
            if not isinstance(info, dict):
                return False, f"extracted_info[{idx}] must be dictionary"
            
            required_info_fields = ['person_name', 
                                    'organization', 
                                    'new_role',
                                   ]

            missing_info_fields  = [field for field in required_info_fields if field not in info]
            
            if missing_info_fields:
                return False, f"extracted_info[{idx}] missing fields: {missing_info_fields}"
        
        return True, None
    
    
    @staticmethod
    def validate_post_category(category: str) -> bool:
        """
        Validate if post category is valid
        
        Arguments:
        ----------
            category { str } : Category number as string
        
        Returns:
        --------
             { bool }        : True if category is valid (1-5), False otherwise
        """
        valid_categories = ['1', '2', '3', '4', '5']
        
        return category in valid_categories
    
    
    @staticmethod
    def clean_extracted_info(extracted_info: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Clean and filter extracted information: removes entries with "Unknown" values or invalid data
        
        Arguments:
        ----------
            extracted_info { List[Dict[str, str]] } : List of extracted information
        
        Returns:
        --------
                  { List[Dict[str, str]] }          : Cleaned list
        """
        if not extracted_info:
            return []
        
        cleaned = list()
        
        for info in extracted_info:
            # Skip if any required field is "Unknown"
            if (any(info.get(key, "Unknown") == "Unknown" for key in ['person_name', 'organization', 'new_role'])):
                continue
            
            # Skip if new_role contains retirement/leaving keywords
            new_role = info.get('new_role', '').lower()

            if (('retiring' in new_role) or ('leaving' in new_role)):
                continue
            
            # Skip ownership roles
            ownership_roles = ['shareholder', 
                               'owner', 
                               'proprietor', 
                               'insider',
                              ]
            
            if any(role in new_role for role in ownership_roles):
                continue
            
            cleaned.append(info)
        
        logger.debug(msg   = f"Cleaned extracted_info: {len(extracted_info)} -> {len(cleaned)} items",
                     extra = {"request_id": "validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                    )
        
        return cleaned
