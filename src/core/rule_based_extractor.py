# DEPENDENCIES
import re
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


class RuleBasedExtractor(BaseExtractor):
    """
    Sophisticated rule-based extractor for LinkedIn posts: uses comprehensive regex patterns, keyword matching, and heuristic scoring
    to extract job information from unstructured posts and implements the BaseExtractor interface
    """
    def __init__(self):
        """
        Initialize sophisticated rule-based extractor
        """
        super().__init__(extractor_name = "RuleBasedExtractor")
        
        self.validator = DataValidator()
        
        # Comprehensive job transition patterns with confidence scores
        self.job_patterns        = {'new_job'     : {'high_confidence'   : [(r'(?:starting|started|begins|begun)\s+(?:a\s+)?new\s+(?:position|role|job)', 0.9),
                                                                            (r'(?:joined|joining)\s+(?:the\s+)?(?:team|company|organization|firm)', 0.9),
                                                                            (r'(?:happy|excited|thrilled|pleased|delighted)\s+to\s+(?:announce|share).*?(?:joined|joining)', 0.85),
                                                                            (r'(?:welcome|welcoming).*?(?:to\s+(?:our|the)\s+team)', 0.85),
                                                                           ],
                                                     'medium_confidence' : [(r'new\s+(?:chapter|journey|adventure)', 0.6),
                                                                            (r'first\s+day\s+at', 0.7),
                                                                            (r'(?:onboard|onboarding)', 0.6),
                                                                           ]
                                                    },
                                    'promotion'   : {'high_confidence'   : [(r'(?:promoted|elevated)\s+to', 0.95),
                                                                            (r'(?:congratulations|congrats).*?(?:promotion|advancement)', 0.9),
                                                                            (r'(?:new|expanded)\s+responsibilities.*?(?:as|to)', 0.8),
                                                                           ],
                                                     'medium_confidence' : [(r'(?:moving|stepped)\s+up\s+to', 0.65),
                                                                            (r'advancing\s+to', 0.7),
                                                                           ]
                                                    },
                                    'transition'  : {'high_confidence'   : [(r'(?:moved|moving|transitioning|transitioned)\s+to', 0.85),
                                                                            (r'(?:leaving|departing).*?(?:to\s+join|for\s+a\s+new)', 0.9),
                                                                           ],
                                                     'medium_confidence' : [(r'(?:changing|switched|switching)\s+(?:roles|positions)', 0.7),
                                                                            (r'new\s+opportunity\s+at', 0.65),
                                                                           ]
                                                    },
                                    'appointment' : {'high_confidence'    : [(r'(?:appointed|named|designated|elected)\s+(?:as|to)', 0.95),
                                                                             (r'(?:announcing|announces).*?(?:appointment|selection)\s+of', 0.9),
                                                                            ],
                                                     'medium_confidence' : [(r'selected\s+(?:as|to\s+serve\s+as)', 0.75),
                                                                            (r'assumes\s+(?:role|position)\s+of', 0.7),
                                                                           ]
                                                    }
                                   }
            
        # Irrelevant patterns (negative indicators)
        self.irrelevant_patterns = [(r'(?:hiring|recruiting|looking)\s+for', 0.9),
                                    (r'(?:seeking|searching\s+for).*?(?:candidate|applicant)', 0.9),
                                    (r'(?:open|available)\s+position', 0.85),
                                    (r'job\s+(?:opening|posting|vacancy)', 0.85),
                                    (r'(?:apply|applications).*?(?:now|today|here)', 0.8),
                                    (r'(?:retiring|retirement)(?!\s+(?:from.*?to|to))', 0.95),  # Retirement without transition
                                    (r'(?:leaving|stepping\s+down)(?!\s+(?:to|for))', 0.85),  # Leaving without new role
                                    (r'(?:we\'re|we\s+are)\s+hiring', 0.9),
                                    (r'interested\s+candidates', 0.85),
                                    (r'(?:shareholder|owner|proprietor)(?!\s+(?:and|,))', 0.8),
                                   ]
        
        # Comprehensive job title patterns
        self.title_patterns      = [# C-suite
                                    r'Chief\s+(?:Executive|Technology|Financial|Operating|Marketing|Data|Information|Product)\s+Officer',
                                    r'(?:CEO|CTO|CFO|COO|CMO|CDO|CIO|CPO)',
                                    # VP/Director level
                                    r'(?:Senior\s+)?Vice\s+President\s+of\s+[\w\s]+',
                                    r'(?:Senior\s+)?(?:Executive\s+)?Director\s+of\s+[\w\s]+',
                                    r'(?:VP|SVP)\s+(?:of\s+)?[\w\s]+',
                                    # Manager level
                                    r'(?:Senior\s+)?(?:General\s+)?Manager\s+(?:of\s+)?[\w\s]+',
                                    r'(?:Head|Lead)\s+of\s+[\w\s]+',
                                    # Individual contributors
                                    r'(?:Senior\s+|Lead\s+|Staff\s+|Principal\s+)?(?:Software|Data|Machine\s+Learning|DevOps|Cloud)\s+Engineer',
                                    r'(?:Senior\s+|Lead\s+)?(?:Data|Business|Financial|Systems|Security)\s+Analyst',
                                    r'(?:Senior\s+)?(?:Product|Project|Program)\s+Manager',
                                    r'(?:Senior\s+)?(?:Marketing|Sales|HR|Finance)\s+(?:Specialist|Coordinator|Associate)',
                                    r'(?:Technical\s+)?Consultant',
                                    r'Solutions\s+Architect',
                                    r'(?:Senior\s+)?Research\s+Scientist',
                                   ]
        
        # Company extraction patterns
        self.company_patterns    = [r'\bat\s+([A-Z][\w\s&\',.-]+?(?:Inc\.?|LLC|Ltd\.?|Corporation|Corp\.?|Company|Co\.?)?)\s*(?:\.|\,|!|\s+as\s|\s+in\s)',
                                    r'\bfor\s+([A-Z][\w\s&\',.-]+?(?:Inc\.?|LLC|Ltd\.?)?)\s*(?:\.|\,|!)',
                                    r'\bwith\s+([A-Z][\w\s&\',.-]+?)\s*(?:\.|\,|!|\s+as\s)',
                                    r'\b(?:joining|joined)\s+([A-Z][\w\s&\',.-]+?)\s*(?:\.|\,|!|\s+as\s)',
                                   ]
        
        # Stopwords to filter from extracted names
        self.name_stopwords      = {'The', 'This', 'That', 'These', 'Those', 'With', 'From', 'After', 'Before', 'Team', 'Company', 'Organization', 'Group', 'Department', 'Division'}
        
        logger.info(msg   = "Sophisticated RuleBasedExtractor initialized",
                    extra = {"request_id": "rule_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
    
    
    async def validate_input(self, linkedin_post: Dict[str, Any]) -> bool:
        """
        Validate input
        """
        is_valid, _ = self.validator.validate_linkedin_post(linkedin_post)
        return is_valid
    
    
    def _score_relevance(self, text: str) -> Tuple[float, str]:
        """
        Score text relevance with category detection
        
        Returns:
        --------
            (confidence_score, category)
        """
        text_lower    = text.lower()
        max_score     = 0.0
        best_category = "5"
        
        # Check positive patterns
        category_map  = {'new_job'     : '1', 
                         'transition'  : '2', 
                         'promotion'   : '3', 
                         'appointment' : '4',
                        }
        
        for cat_name, cat_num in category_map.items():
            for conf_level in ['high_confidence', 'medium_confidence']:
                if conf_level in self.job_patterns[cat_name]:
                    for pattern, score in self.job_patterns[cat_name][conf_level]:
                        if (re.search(pattern, text_lower, re.IGNORECASE)):
                            if (score > max_score):
                                max_score     = score
                                best_category = cat_num
        
        # Check negative patterns
        for pattern, neg_score in self.irrelevant_patterns:
            if (re.search(pattern, text_lower, re.IGNORECASE)):
                # Reduce confidence
                max_score -= neg_score  
        
        return max(0.0, max_score), best_category if (max_score > 0.5) else "5"
    
    
    def _extract_names(self, text: str, poster_name: str) -> List[str]:
        """
        Extract person names with better filtering
        """
        # Pattern for capitalized names
        name_pattern    = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        potential_names = re.findall(name_pattern, text)
        
        names           = list()

        for name in potential_names:
            # Filter stopwords
            if any(word in name for word in self.name_stopwords):
                continue
            
            # Skip if it's the poster
            if name.lower() in poster_name.lower():
                continue
            
            # Skip single words
            if (len(name.split()) < 2):
                continue
            
            names.append(name)
        
        # Top 3 unique names
        return list(set(names))[:3]  
    
    
    def _extract_job_titles(self, text: str) -> List[str]:
        """
        Extract job titles using comprehensive patterns
        """
        titles = list()
        
        for pattern in self.title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            titles.extend([m if isinstance(m, str) else m[0] for m in matches])
        
        # Also look for "as [TITLE]" pattern
        as_pattern     = r'\bas\s+((?:[A-Z][a-z]+\s+){1,4}(?:Manager|Director|Engineer|Analyst|Officer|President|Lead|Head))'
        as_matches     = re.findall(as_pattern, text)
        titles.extend(as_matches)
        
        # Clean and deduplicate
        cleaned_titles = list()

        for title in titles:
            title = title.strip()
            if ((len(title) > 3) and (title not in cleaned_titles)):
                cleaned_titles.append(title)
        
        # Top 3
        return cleaned_titles[:3]  
    
    
    def _extract_companies(self, text: str) -> List[str]:
        """
        Extract company names
        """
        companies = list()
        
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        
        # Clean companies
        cleaned = list()

        for comp in companies:
            comp = comp.strip()
            # Remove trailing punctuation
            comp = re.sub(r'[,\.\!]+$', '', comp)
            if ((len(comp) > 2) and (comp not in cleaned)):
                cleaned.append(comp)
        
        # Top 3
        return cleaned[:3]  
    
    
    async def extract(self, linkedin_post: Dict[str, Any], request_id: str = "rule_extract") -> Dict[str, Any]:
        """
        Extract information using rule-based approach
        """
        if not await self.validate_input(linkedin_post):
            return {"poster_name"    : linkedin_post.get('name', ''),
                    "post_category"  : "5",
                    "change_count"   : 0,
                    "relevant"       : False,
                    "extracted_info" : [],
                    "error"          : "Invalid input",
                   }
        
        try:
            poster_name         = linkedin_post.get('name', '').strip()
            description          = linkedin_post.get('description', '').strip()
            
            # Score relevance
            confidence, category = self._score_relevance(description)
            
            if ((confidence < 0.5) or (category == "5")):
                return {"poster_name"    : poster_name,
                        "post_category"  : "5",
                        "change_count"   : 0,
                        "relevant"       : False,
                        "extracted_info" : [],
                       }
            
            # Extract entities
            names          = self._extract_names(description, poster_name)
            titles         = self._extract_job_titles(description)
            companies      = self._extract_companies(description)
            
            # Build triplets
            extracted_info = list()
            
            if names and (companies or titles):
                for i, name in enumerate(names):
                    title   = titles[i] if i < len(titles) else (titles[0] if titles else "Unknown")
                    company = companies[i] if i < len(companies) else (companies[0] if companies else "Unknown")
                    
                    extracted_info.append({"person_name"  : name,
                                           "organization" : company,
                                           "new_role"     : title,
                                         })
            
            # Clean
            cleaned_info = self.validator.clean_extracted_info(extracted_info)
            
            result       = {"poster_name"    : poster_name,
                            "post_category"  : category,
                            "change_count"   : len(cleaned_info),
                            "relevant"       : len(cleaned_info) > 0,
                            "extracted_info" : cleaned_info,
                            "confidence"     : confidence,
                           }
            
            logger.info(msg   = f"Rule-based extraction: {result['change_count']} changes (confidence: {confidence:.2f})",
                        extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
            
            return result
        
        except Exception as e:
            logger.error(msg      = f"Rule-based error: {repr(e)}",
                         extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                         exc_info = True,
                        )
            
            return {"poster_name"    : linkedin_post.get('name', ''),
                    "post_category"  : "5",
                    "change_count"   : 0,
                    "relevant"       : False,
                    "extracted_info" : [],
                    "error"          : str(e),
                   }