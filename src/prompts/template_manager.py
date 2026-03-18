# DEPENDENCIES
import logging
import warnings
from typing import Any
from typing import Dict
from typing import Optional
from datetime import datetime


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """
    Manager for prompt templates with versioning and formatting capabilities: handles creation, storage, and retrieval of prompt templates
    and supports multiple versions and template variables
    """
    def __init__(self):
        """
        Initialize the prompt template manager
        """
        self.templates       : Dict[str, Dict[str, Any]] = dict()
        self.current_version : str                       = "v4"
        
        # Load all predefined templates
        self._initialize_templates()
        
        logger.info(msg   = f"PromptTemplateManager initialized with {len(self.templates)} templates",
                    extra = {"request_id": "template_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
    
    
    def _initialize_templates(self) -> None:
        """
        Initialize all prompt templates with different versions
        """
        # V1: Baseline prompt (simple)
        self.templates["v1"] = {"version"      : "v1",
                                "name"         : "Baseline Simple Prompt",
                                "description"  : "Simple extraction prompt without advanced techniques",
                                "created_date" : "2024-01-01",
                                "template"     : """
                                                    Extract job change information from this LinkedIn post:

                                                    Post by: {poster_name}
                                                    About: {about}
                                                    Description: {description}

                                                    Extract: person name, company, and job title.

                                                    Return JSON with: poster_name, post_category (1-5), change_count, relevant (true/false), extracted_info (array).
                                                 """
                               }
        
        # V2: With chain-of-thought
        self.templates["v2"] = {"version"      : "v2",
                                "name"         : "Chain-of-Thought Prompt",
                                "description"  : "Adds step-by-step reasoning to improve accuracy",
                                "created_date" : "2024-01-10",
                                "template"     : """
                                                    Analyze this LinkedIn post step by step:

                                                    Post by: {poster_name}
                                                    About: {about}
                                                    Description: {description}

                                                    Step 1: Determine if this is about a job change (new job, promotion, or transition).
                                                    Step 2: If yes, extract the person's name, company, and role.

                                                    Categories:
                                                    1. New job joining
                                                    2. Job change/transition
                                                    3. Promotion
                                                    4. Leadership appointment
                                                    5. Not relevant

                                                    Return JSON with: poster_name, post_category, change_count, relevant, extracted_info.
                                                 """
                               }
        
        # V3: With few-shot learning (implicit)
        self.templates["v3"] = {"version"      : "v3",
                                "name"         : "Few-Shot Learning Prompt",
                                "description"  : "Includes detailed category descriptions as implicit examples",
                                "created_date" : "2024-01-20",
                                "template"     : """
                                                    Analyze this LinkedIn post and classify it:

                                                    Post by: {poster_name}
                                                    About: {about}
                                                    Description: {description}

                                                    Classification Categories:
                                                    1. New Job Joining: Someone started a new position (internal or external move)
                                                    - Example indicators: "starting a new position", "joined the team", "excited to announce"
                                                    
                                                    2. Job Change/Transition: Someone changed roles or companies
                                                    - Example indicators: "moved to", "transitioned to", "new role at"
                                                    
                                                    3. Internal Promotion: Someone promoted within same company
                                                    - Example indicators: "promoted to", "elevated to", "new responsibilities"
                                                    
                                                    4. Leadership Appointment: Board member, C-level, or director appointment
                                                    - Example indicators: "appointed as", "named to board", "elected as"
                                                    
                                                    5. Not Relevant: Hiring announcements, retirements only, unrelated content

                                                    Extract for categories 1-4:
                                                    - Person name (without titles like Mr., Dr., Prof.)
                                                    - Organization name
                                                    - New job title/role

                                                    Return JSON with: poster_name, post_category, change_count, relevant, extracted_info.
                                                 """
                               }
        
        # V4: Current optimized prompt
        self.templates["v4"] = {"version"      : "v4",
                                "name"         : "Optimized Production Prompt",
                                "description"  : "Full production prompt with all techniques and constraints",
                                "created_date" : "2024-02-01",
                                "template"     : """
                                                    Analyze the following LinkedIn post thoroughly and classify it based on job-related announcements:

                                                    Post by: {poster_name}
                                                    About: {about}
                                                    Description: {description}

                                                    Step 1: Classification
                                                    Determine if this post is about any of the following:
                                                    1. New job joining (either within the same company or a new company)
                                                    2. Job change or transition
                                                    3. Promotion within the same company
                                                    4. Leadership change or appointment
                                                    5. Other (not related to the above categories)

                                                    Step 2: Information Extraction
                                                    If the post falls into categories 1-4, extract the following information for each relevant mention:
                                                    - Remove any salutations eg: Mr. Mrs. Dr. Prof. or title or degree or something rather than the name
                                                    itself only, present after or before the name : {poster_name}
                                                    - Full name of the person mentioned (who got the new job, promotion, or new role), but exclude any 
                                                    salutations eg: Mr. Mrs. Dr. Prof.  or title or degree or something rather than the name itself only, 
                                                    present after or before the name
                                                    - Full name of the organization (current or new)
                                                    - New job title or role

                                                    Important Constraints:
                                                    - Ignore all kinds of hiring announcements for positions that are not filled yet or do not mention a
                                                    specific individual's job change. For example, if the post says "I am hiring for a Finance Manager," 
                                                    this should be ignored.
                                                    - Ignore those individuals or persons who are retiring or leaving job
                                                    - Include those who are leaving a role or position but joining another role or position.
                                                    - Ignore positions like "Shareholder", "Owner", "Proprietor", "Insider", or similar titles. 
                                                    - Specifically, exclude roles that do not indicate a significant change in responsibilities or title.

                                                    Format the response as a JSON object with the following structure:
                                                    {{
                                                        "poster_name": "[modified poster_name]",
                                                        "post_category": "[Category number from Step 1]",
                                                        "change_count": [number of changes],
                                                        "relevant": [true/false],
                                                        "extracted_info": [
                                                            {{
                                                                "person_name": "[Full Name of the person mentioned]",
                                                                "organization": "[Full Name of the Organization]",
                                                                "new_role": "[New Job Title or Role]"
                                                            }},
                                                            ...
                                                        ]
                                                    }}

                                                    Ensure high accuracy in classification and information extraction. If any information is
                                                    uncertain or not explicitly mentioned, use "Unknown" as the value.

                                                    Provide only the JSON object as your response, with no additional text before or after.
                                                 """
                               }
    
    
    def get_template(self, version: Optional[str] = None) -> str:
        """
        Get prompt template by version
        
        Arguments:
        ----------
            version { str } : Template version (defaults to current_version)
        
        Returns:
        --------
              { str }       : The template string
        
        Raises:
        -------
            ValueError      : If version doesn't exist
        """
        version = version or self.current_version
        
        if version not in self.templates:
            error_message = f"Template version '{version}' not found. Available versions: {list(self.templates.keys())}"
            
            logger.error(msg   = error_message,
                         extra = {"request_id": "template_get", "batch_id": "N/A", "batch_item_id": "N/A"}
                        )

            raise ValueError(error_message)
        
        return self.templates[version]["template"]
    
    
    def format_prompt(self, poster_name: str, about: str, description: str, version: Optional[str] = None) -> str:
        """
        Format prompt template with actual data
        
        Arguments:
        ----------
            poster_name { str } : Name of the person posting
            
            about       { str } : About section of the poster
            
            description { str } : Main post content
            
            version     { str } : Template version to use (defaults to current_version)
        
        Returns:
        --------
                { str }         : Formatted prompt ready to send to LLM
        
        Raises:
        -------
            ValueError          : If inputs are invalid or template version doesn't exist
        """
        # Input validation
        if not isinstance(poster_name, str):
            error_message = f"poster_name must be a string, got: {type(poster_name)}"
            
            logger.error(msg   = error_message,
                         extra = {"request_id": "prompt_format", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            raise ValueError(error_message)
        
        if not isinstance(about, str):
            error_message = f"about must be a string, got: {type(about)}"
            
            logger.error(msg   = error_message,
                         extra = {"request_id": "prompt_format", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            raise ValueError(error_message)
        
        if not isinstance(description, str):
            error_message = f"description must be a string, got: {type(description)}"
            
            logger.error(msg   = error_message,
                         extra = {"request_id": "prompt_format", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            raise ValueError(error_message)
        
        # Get template
        template          = self.get_template(version)
        
        # Clean inputs (remove newlines that might break formatting)
        poster_name_clean = poster_name.replace('\n', ' ').strip()
        about_clean       = about.replace('\n', ' ').strip()
        description_clean = description.replace('\n', ' ').strip()
        
        # Format template
        try:
            formatted_prompt = template.format(poster_name = poster_name_clean,
                                               about       = about_clean,
                                               description = description_clean,
                                              )
            
            logger.debug(msg   = f"Successfully formatted prompt using template version: {version or self.current_version}",
                         extra = {"request_id": "prompt_format", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )
            
            return formatted_prompt
        
        except Exception as format_error:
            error_message = f"Failed to format prompt: {repr(format_error)}"
            
            logger.error(msg      = error_message,
                         extra    = {"request_id": "prompt_format", "batch_id": "N/A", "batch_item_id": "N/A"},
                         exc_info = True,
                        )

            raise ValueError(error_message)
    
    
    def list_templates(self) -> Dict[str, Dict[str, str]]:
        """
        List all available templates with metadata
        
        Returns:
        --------
            { Dict } : Dictionary of template versions with their metadata
        """
        template_info = dict()
        
        for version, template_data in self.templates.items():
            template_info[version] = {"name"         : template_data["name"],
                                      "description"  : template_data["description"],
                                      "created_date" : template_data["created_date"],
                                     }
        
        return template_info
    
    
    def add_template(self, version: str, template: str, name: str, description: str) -> None:
        """
        Add a new template version
        
        Arguments:
        ----------
            version     { str } : Version identifier
            
            template    { str } : Template string with {variables}
            
            name        { str } : Template name
            
            description { str } : Template description
        
        Raises:
        -------
            ValueError          : If version already exists
        """
        if version in self.templates:
            error_message = f"Template version '{version}' already exists"
           
            logger.error(msg   = error_message,
                         extra = {"request_id": "template_add", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            raise ValueError(error_message)

        
        self.templates[version] = {"version"      : version,
                                   "name"         : name,
                                   "description"  : description,
                                   "created_date" : datetime.now().strftime("%Y-%m-%d"),
                                   "template"     : template,
                                  }
        
        logger.info(msg   = f"Added new template version: {version}",
                    extra = {"request_id": "template_add", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
            
