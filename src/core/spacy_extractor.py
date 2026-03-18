# DEPENDENCIES
import re
import spacy
import logging
import warnings
from typing import Any
from typing import Set
from typing import List
from typing import Dict
from typing import Tuple
from src.core.validator import DataValidator
from src.core.base_extractor import BaseExtractor


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class SpacyNERExtractor(BaseExtractor):
    """
    spaCy NER + Dependency Parsing baseline extractor
    
    Uses spaCy's pretrained models for:
    - Named Entity Recognition (NER) for person names and organizations
    - Dependency parsing for relationship extraction
    - Part-of-speech tagging for job title identification
    
    Serves as a traditional NLP baseline for comparison with LLM-based approach
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize spaCy NER extractor
        
        Arguments:
        ----------
            model_name { str } : spaCy model name (default: en_core_web_sm)
        
        Note:
        -----
            Run 'python -m spacy download en_core_web_sm' to install the model
        """
        super().__init__(extractor_name = "SpacyNERExtractor")
        
        # Initialize validator
        self.validator = DataValidator()
        
        try:
            # Load spaCy model
            self.nlp = spacy.load(model_name)
            
            logger.info(msg   = f"Loaded spaCy model: {model_name}",
                        extra = {"request_id": "spacy_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
        
        except OSError as model_error:
            error_message = (f"spaCy model '{model_name}' not found. Install it with: python -m spacy download {model_name}")
            logger.error(msg   = error_message,
                         extra = {"request_id": "spacy_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            raise OSError(error_message)
        
        # Define job-related keywords for classification
        self.job_keywords        = {'new_job'     : ['starting', 'joined', 'new position', 'happy to announce', 'excited to share', 'pleased to announce', 'thrilled'],
                                    'promotion'   : ['promoted', 'elevated', 'advancement', 'risen to'],
                                    'transition'  : ['moved to', 'transitioned', 'changing roles', 'transferring'],
                                    'appointment' : ['appointed', 'named to', 'elected', 'designated', 'selected as'],
                                   }
        
        # Irrelevant patterns
        self.irrelevant_patterns = [r'hiring for', r'looking for', r'seeking.*candidate', r'open position', r'job opening', r'apply now', r'retiring', r'leaving.*position']
        
        # Job title indicators (common title words)
        self.title_indicators    = {'Chief', 'Senior', 'Vice', 'President', 'VP', 'Director', 'Manager', 'Head', 'Lead', 'Officer', 'CFO', 'CTO', 'CEO', 'COO', 'CMO', 'Analyst', 'Engineer', 'Specialist', 'Coordinator'}
        
        logger.info(msg   = "SpacyNERExtractor initialized with NER and dependency parsing",
                    extra = {"request_id": "spacy_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
    
    
    async def validate_input(self, linkedin_post: Dict[str, Any]) -> bool:
        """
        Validate input LinkedIn post data
        
        Arguments:
        ----------
            linkedin_post { Dict[str, Any] } : LinkedIn post data
        
        Returns:
        --------
                      { bool }               : True if valid, False otherwise
        """
        is_valid, error_message = self.validator.validate_linkedin_post(linkedin_post)
        
        if not is_valid:
            logger.error(msg   = f"Input validation failed: {error_message}",
                         extra = {"request_id": "spacy_extract", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )
        
        return is_valid
    
    
    def _is_irrelevant(self, text: str) -> bool:
        """
        Check if post contains irrelevant patterns
        
        Arguments:
        ----------
            text { str } : Post text to check
        
        Returns:
        --------
            { bool }     : True if irrelevant, False otherwise
        """
        text_lower = text.lower()
        
        for pattern in self.irrelevant_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    
    def _classify_post(self, text: str) -> str:
        """
        Classify post based on keyword patterns
        
        Arguments:
        ----------
            text { str } : Post text to classify
        
        Returns:
        --------
            { str }      : Category number (1-5)
        """
        text_lower = text.lower()
        
        # Check for new job
        if any(keyword in text_lower for keyword in self.job_keywords['new_job']):
            return "1"
        
        # Check for transition
        if any(keyword in text_lower for keyword in self.job_keywords['transition']):
            return "2"
        
        # Check for promotion
        if any(keyword in text_lower for keyword in self.job_keywords['promotion']):
            return "3"
        
        # Check for appointment
        if any(keyword in text_lower for keyword in self.job_keywords['appointment']):
            return "4"
        
        # Default to irrelevant
        return "5"
    
    
    def _extract_entities(self, doc: spacy.tokens.Doc) -> Dict[str, List[str]]:
        """
        Extract named entities using spaCy NER
        
        Arguments:
        ----------
            doc { spacy.tokens.Doc } : Processed spaCy document
        
        Returns:
        --------
            { Dict[str, List[str]] } : Dictionary with person names and organizations
        """
        entities = {'people'        : list(),
                    'organizations' : list(),
                   }
        
        for ent in doc.ents:
            if (ent.label_ == "PERSON"):
                # Clean person name (remove salutations)
                name = ent.text.strip()
                
                if not any(title in name for title in ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.']):
                    entities['people'].append(name)
            
            elif (ent.label_ == "ORG"):
                # Clean organization name
                org = ent.text.strip()
                
                entities['organizations'].append(org)
        
        return entities
    
    
    def _extract_job_titles(self, doc: spacy.tokens.Doc) -> List[str]:
        """
        Extract job titles using POS tagging and dependency parsing
        
        Arguments:
        ----------
            doc { spacy.tokens.Doc } : Processed spaCy document
        
        Returns:
        --------
                { List[str] }        : List of extracted job titles
        """
        job_titles = list()
        
        # Look for title indicator words followed by nouns
        for token in doc:
            if token.text in self.title_indicators:
                # Collect the title phrase (noun chunk)
                title_tokens = [token.text]
                
                # Look ahead for related nouns/adjectives
                for child in token.children:
                    if child.pos_ in ['NOUN', 'PROPN', 'ADJ']:
                        title_tokens.append(child.text)
                
                # Look at the token's head if it's a noun
                if token.head.pos_ in ['NOUN', 'PROPN']:
                    title_tokens.append(token.head.text)
                
                if (len(title_tokens) > 1):
                    job_titles.append(' '.join(title_tokens))
        
        # Look for patterns like "as [TITLE]"
        for i, token in enumerate(doc):
            if ((token.text.lower() == 'as') and (i + 1 < len(doc))):
                # Get the noun chunk after "as"
                next_token = doc[i + 1]
                
                if (next_token.pos_ in ['NOUN', 'PROPN', 'ADJ']):
                    title_parts = [next_token.text]
                    
                    # Extend to full noun phrase
                    for child in next_token.children:
                        if (child.pos_ in ['NOUN', 'PROPN', 'ADJ']):
                            title_parts.append(child.text)
                    
                    job_titles.append(' '.join(title_parts))
        
        # Use noun chunks that contain title indicators
        for chunk in doc.noun_chunks:
            if any(indicator in chunk.text for indicator in self.title_indicators):
                job_titles.append(chunk.text)
        
        # Remove duplicates
        return list(set(job_titles))  
    
    
    def _match_entities_to_jobs(self, people: List[str], organizations: List[str], job_titles: List[str]) -> List[Dict[str, str]]:
        """
        Match extracted people to organizations and job titles: uses heuristics to create person-organization-role triplets
        
        Arguments:
        ----------
            people        { List[str] } : Extracted person names
            
            organizations { List[str] } : Extracted organization names
            
            job_titles    { List[str] } : Extracted job titles
        
        Returns:
        --------
            { List[Dict[str, str]] }    : List of matched triplets
        """
        matched_info = list()
        
        # Pair each person with first organization and first job title
        if people and (organizations or job_titles):
            # Limit to first 3 people
            for person in people[:3]: 
                org  = organizations[0] if organizations else "Unknown"
                role = job_titles[0] if job_titles else "Unknown"
                
                matched_info.append({"person_name"  : person,
                                     "organization" : org,
                                     "new_role"     : role,
                                   })
        
        return matched_info
    
    
    async def extract(self, linkedin_post: Dict[str, Any], request_id: str = "spacy_extract") -> Dict[str, Any]:
        """
        Extract information from LinkedIn post using spaCy NER
        
        Arguments:
        ----------
            linkedin_post { Dict[str, Any] } : LinkedIn post data

            request_id    { str }            : Request identifier for logging
        
        Returns:
        --------
                { Dict[str, Any] }           : Extraction result
        """
        # Validate input
        if not await self.validate_input(linkedin_post):
            return {"poster_name"    : linkedin_post.get('name', ''),
                    "post_category"  : "5",
                    "change_count"   : 0,
                    "relevant"       : False,
                    "extracted_info" : [],
                    "error"          : "Invalid input data",
                   }
        
        try:
            # Extract fields
            poster_name = linkedin_post.get('name', '').strip()
            description = linkedin_post.get('description', '').strip()
            
            logger.info(msg   = f"spaCy NER extraction for post by: {poster_name[:50]}...",
                        extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
            
            # Check if irrelevant
            if self._is_irrelevant(description):
                return {"poster_name"    : poster_name,
                        "post_category"  : "5",
                        "change_count"   : 0,
                        "relevant"       : False,
                        "extracted_info" : [],
                       }
            
            # Classify post
            category = self._classify_post(description)
            
            if (category == "5"):
                return {"poster_name"    : poster_name,
                        "post_category"  : "5",
                        "change_count"   : 0,
                        "relevant"       : False,
                        "extracted_info" : [],
                       }
            
            # Process with spaCy
            doc            = self.nlp(description)
            
            # Extract entities
            entities       = self._extract_entities(doc)
            people         = entities['people']
            organizations  = entities['organizations']
            
            # Extract job titles
            job_titles     = self._extract_job_titles(doc)
            
            # Match entities to create triplets
            extracted_info = self._match_entities_to_jobs(people        = people,
                                                          organizations = organizations,
                                                          job_titles    = job_titles,
                                                         )
            
            # Clean extracted info
            cleaned_info   = self.validator.clean_extracted_info(extracted_info)
            
            result         = {"poster_name"    : poster_name,
                              "post_category"  : category,
                              "change_count"   : len(cleaned_info),
                              "relevant"       : len(cleaned_info) > 0,
                              "extracted_info" : cleaned_info,
                             }
            
            logger.info(msg   = f"spaCy extraction found {result['change_count']} job changes",
                        extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
            
            return result
        
        except Exception as extraction_error:
            error_message = f"spaCy extraction error: {repr(extraction_error)}"
            
            logger.error(msg      = error_message,
                         extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                         exc_info = True,
                        )
            
            return {"poster_name"    : linkedin_post.get('name', ''),
                    "post_category"  : "5",
                    "change_count"   : 0,
                    "relevant"       : False,
                    "extracted_info" : [],
                    "error"          : error_message,
                   }