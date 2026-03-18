# DEPENDENCIES
import signal
import asyncio
import uvicorn
import warnings
from typing import List
from fastapi import Request
from fastapi import FastAPI
from fastapi import HTTPException
from config.settings import settings
from config.logging_config import logger
from fastapi.responses import JSONResponse
from config.schemas import LinkedInPostInput
from config.schemas import LinkedInPostOutput
from src.core.llm_extractor import LLMExtractor
from src.core.data_processor import DataProcessor
from src.core.spacy_extractor import SpacyNERExtractor
from src.core.rule_based_extractor import RuleBasedExtractor



# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# INITIALIZE FASTAPI APPLICATION
app = FastAPI(title       = "LinkedIn Job Information Extraction API",
              description = "Advanced prompt engineering pipeline with spaCy NER + rule-based fallback",
              version     = "1.0.0",
              docs_url    = "/docs",
              redoc_url   = "/redoc",
             )


# REQUEST ID MIDDLEWARE
class RequestIDMiddleware:
    """
    Middleware to add unique request IDs to each request
    """
    def __init__(self, app):
        self.app     = app
        self.counter = 0
    

    async def __call__(self, scope, receive, send):
        if (scope["type"] == "http"):
            self.counter  += 1
            scope["state"] = {"request_id": self.counter}

        await self.app(scope, receive, send)


# ADD MIDDLEWARE
app.add_middleware(RequestIDMiddleware)


# SHUTDOWN HANDLER
shutdown_event = asyncio.Event()


async def handle_shutdown():
    """
    Handle graceful shutdown
    """
    logger.info(msg   = "Initiating graceful shutdown",
                extra = {"request_id": "shutdown", "batch_id": "N/A", "batch_item_id": "N/A"},
               )

    shutdown_event.set()
    await asyncio.sleep(10)

    logger.info(msg   = "Shutdown complete",
                extra = {"request_id": "shutdown", "batch_id": "N/A", "batch_item_id": "N/A"},
               )


@app.on_event("shutdown")
async def shutdown():
    """
    Shutdown event handler
    """
    await handle_shutdown()


# SIGNAL HANDLERS
def signal_handler(signum, frame):
    """
    Handle OS signals for graceful shutdown
    """
    logger.info(msg   = f"Received signal {signum}",
                extra = {"request_id": "signal", "batch_id": "N/A", "batch_item_id": "N/A"},
               )

    asyncio.create_task(handle_shutdown())


# REGISTER SIGNAL HANDLERS
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# GLOBAL EXTRACTORS (initialized lazily)
llm_extractor        = None
spacy_extractor      = None
rule_based_extractor = None


def get_llm_extractor():
    """
    Get or create LLM extractor instance
    """
    global llm_extractor

    if llm_extractor is None:
        llm_extractor = LLMExtractor(prompt_version="v4")
        
        logger.info(msg   = "LLM extractor initialized",
                    extra = {"request_id": "init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )

    return llm_extractor


def get_spacy_extractor():
    """
    Get or create spaCy NER extractor instance
    """
    global spacy_extractor

    if spacy_extractor is None:
        try:
            spacy_extractor = SpacyNERExtractor()
            
            logger.info(msg   = "spaCy NER extractor initialized",
                        extra = {"request_id": "init", "batch_id": "N/A", "batch_item_id": "N/A"},
                       )

        except Exception as e:
            logger.error(msg   = f"Failed to initialize spaCy extractor: {e}",
                         extra = {"request_id": "init", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            spacy_extractor = None

    return spacy_extractor


def get_rule_based_extractor():
    """
    Get or create rule-based extractor instance
    """
    global rule_based_extractor

    if rule_based_extractor is None:
        rule_based_extractor = RuleBasedExtractor()
        
        logger.info(msg   = "Rule-based extractor initialized",
                    extra = {"request_id": "init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )

    return rule_based_extractor


async def extract_with_fallback(linkedin_post: dict, request_id: str) -> dict:
    """
    Extract with spaCy, fallback to rule-based if needed
    
    Fallback triggers:
    1. spaCy extraction fails
    2. Confidence score < 0.6
    3. No entities extracted
    """
    # Try spaCy first
    spacy_ext = get_spacy_extractor()
    
    if spacy_ext is not None:
        try:
            result       = await spacy_ext.extract(linkedin_post, request_id)
            
            # Check if spaCy succeeded
            confidence   = result.get('confidence', 0.0)
            has_entities = len(result.get('extracted_info', [])) > 0
            no_error     = result.get('error') is None
            
            if (no_error and ((confidence >= 0.6) or has_entities)):
                logger.info(msg   = f"spaCy extraction succeeded (confidence: {confidence:.2f})",
                            extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                           )

                result['extractor_used'] = 'spacy'

                return result
            
            else:
                logger.warning(msg   = f"spaCy low confidence ({confidence:.2f}), falling back to rule-based",
                               extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                              )

        except Exception as spacy_error:
            logger.warning(msg   = f"spaCy extraction failed: {spacy_error}, falling back to rule-based",
                           extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                          )
    
    # Fallback to rule-based
    rule_ext                 = get_rule_based_extractor()
    result                   = await rule_ext.extract(linkedin_post, request_id)
    result['extractor_used'] = 'rule_based_fallback'
    
    logger.info(msg   = "Using rule-based extractor (fallback)",
                extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
               )
    
    return result


######################### API ENDPOINTS #########################
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    logger.info(msg   = "Root endpoint accessed",
                extra = {"request_id": "root", "batch_id": "N/A", "batch_item_id": "N/A"},
               )
    
    return {"message"     : "LinkedIn Job Information Extraction API",
            "version"     : "1.0.0",
            "description" : "Advanced extraction with spaCy NER + rule-based fallback",
            "endpoints"   : {"docs"                 : "/docs",
                             "health"               : "/health",
                             "extract_llm"          : "/extract/llm",
                             "extract_hybrid"       : "/extract/hybrid",
                             "extract_batch_llm"    : "/extract/batch/llm",
                             "extract_batch_hybrid" : "/extract/batch/hybrid",
                            },
            "features"    : ["LLM-based extraction (GPT-3.5)",
                             "Hybrid: spaCy NER → Rule-based fallback",
                             "Batch processing support",
                             "Async processing",
                             "Comprehensive logging"
                            ]
           }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    logger.info(msg   = "Health check accessed",
                extra = {"request_id": "health", "batch_id": "N/A", "batch_item_id": "N/A"},
               )
    
    return {"status"  : "healthy",
            "service" : "LinkedIn Job Extraction API",
            "version" : "1.0.0",
           }


@app.post("/extract/llm", response_model = LinkedInPostOutput, response_model_exclude_none = True, summary = "Extract using LLM", description = "Extract using GPT-3.5 with optimized prompts")
async def extract_single_llm(post: LinkedInPostInput, request: Request):
    """
    Extract from single post using LLM
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        extractor = get_llm_extractor()
        result    = await extractor.extract(post.dict(), str(request_id))
        
        output    = LinkedInPostOutput(name           = post.name,
                                       about          = post.about,
                                       description    = post.description,
                                       userProfileUrl = post.userProfileUrl or "",
                                       source         = post.source,
                                       searchJobTitle = post.searchJobTitle or "",
                                       companyLinks   = post.companyLinks or [],
                                       classification = "Relevant" if result.get('relevant') else "Irrelevant",
                                       error          = result.get('error'),
                                      )
        
        if result.get('extracted_info'):
            info                  = result['extracted_info'][0]
            output.jobPosterName  = result.get('poster_name')
            output.jobStarterName = info.get('person_name')
            output.companyName    = info.get('organization')
            output.currentRole    = info.get('new_role')
        
        return output
    
    except Exception as e:
        logger.error(msg      = f"LLM extraction failed: {repr(e)}",
                     extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                     exc_info = True,
                    )

        raise HTTPException(status_code = 500, 
                            detail      = str(e),
                           )


@app.post("/extract/hybrid", response_model = LinkedInPostOutput, response_model_exclude_none = True, summary = "Extract using Hybrid (spaCy → Rule-based)", description = "Try spaCy NER first, fallback to rule-based if needed")
async def extract_single_hybrid(post: LinkedInPostInput, request: Request):
    """
    Extract from single post using hybrid approach
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        result = await extract_with_fallback(post.dict(), str(request_id))
        
        output = LinkedInPostOutput(name           = post.name,
                                    about          = post.about,
                                    description    = post.description,
                                    userProfileUrl = post.userProfileUrl or "",
                                    source         = post.source,
                                    searchJobTitle = post.searchJobTitle or "",
                                    companyLinks   = post.companyLinks or [],
                                    classification = "Relevant" if result.get('relevant') else "Irrelevant",
                                    error          = result.get('error'),
                                   )
        
        if result.get('extracted_info'):
            info                  = result['extracted_info'][0]
            output.jobPosterName  = result.get('poster_name')
            output.jobStarterName = info.get('person_name')
            output.companyName    = info.get('organization')
            output.currentRole    = info.get('new_role')
        
        # Add extractor info to response
        output.error = f"Extractor: {result.get('extractor_used', 'unknown')}"
        
        return output
    
    except Exception as e:
        logger.error(msg      = f"Hybrid extraction failed: {repr(e)}",
                     extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                     exc_info = True,
                    )

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/batch/llm", response_model = List[LinkedInPostOutput], response_model_exclude_none = True, summary = "Batch Extract using LLM")
async def extract_batch_llm(posts: List[LinkedInPostInput], request: Request):
    """
    Extract from multiple posts using LLM
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    if not posts:
        raise HTTPException(status_code = 400, 
                            detail      = "Empty input list",
                           )
    
    if (len(posts) > 100):
        raise HTTPException(status_code = 400,
                            detail      = f"Batch too large. Max 100, got {len(posts)}",
                           )
    
    try:
        extractor  = get_llm_extractor()
        processor  = DataProcessor(extractor  = extractor, 
                                   batch_size = settings.batch_size,
                                  )
        
        input_data = [post.dict() for post in posts]
        results    = await processor.process_all(input_data, str(request_id))
        
        logger.info(msg   = f"Batch LLM: {len(results)} outputs",
                    extra = {"request_id": request_id, "batch_id": "All", "batch_item_id": "N/A"},
                   )
        
        return results
    
    except Exception as e:
        logger.error(msg      = f"Batch LLM failed: {repr(e)}",
                     extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                     exc_info = True,
                    )

        raise HTTPException(status_code = 500, 
                            detail      = str(e),
                           )


@app.post("/extract/batch/hybrid", response_model = List[LinkedInPostOutput], response_model_exclude_none = True, summary = "Batch Extract using Hybrid")
async def extract_batch_hybrid(posts: List[LinkedInPostInput], request: Request):
    """
    Extract from multiple posts using hybrid approach with fallback
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    if not posts:
        raise HTTPException(status_code = 400, 
                            detail      = "Empty input list",
                           )
    
    if (len(posts) > 100):
        raise HTTPException(status_code = 400,
                            detail      = f"Batch too large. Max 100, got {len(posts)}",
                           )
    
    try:
        # Process each with fallback logic
        results = list()
        
        for idx, post in enumerate(posts):
            logger.info(msg   = f"Processing {idx+1}/{len(posts)}",
                        extra = {"request_id": request_id, "batch_id": "hybrid", "batch_item_id": idx},
                       )
            
            result = await extract_with_fallback(post.dict(), f"{request_id}_{idx}")
            
            output = LinkedInPostOutput(name           = post.name,
                                        about          = post.about,
                                        description    = post.description,
                                        userProfileUrl = post.userProfileUrl or "",
                                        source         = post.source,
                                        searchJobTitle = post.searchJobTitle or "",
                                        companyLinks   = post.companyLinks or [],
                                        classification = "Relevant" if result.get('relevant') else "Irrelevant",
                                       )
            
            if result.get('extracted_info'):
                info                  = result['extracted_info'][0]
                output.jobPosterName  = result.get('poster_name')
                output.jobStarterName = info.get('person_name')
                output.companyName    = info.get('organization')
                output.currentRole    = info.get('new_role')
            
            results.append(output)
        
        logger.info(msg   = f"Batch hybrid: {len(results)} outputs",
                    extra = {"request_id": request_id, "batch_id": "All", "batch_item_id": "N/A"},
                   )
        
        return results
    
    except Exception as e:
        logger.error(msg      = f"Batch hybrid failed: {repr(e)}",
                     extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                     exc_info = True,
                    )

        raise HTTPException(status_code = 500, 
                            detail      = str(e),
                           )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(msg      = f"Unhandled exception: {repr(exc)}",
                 extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                 exc_info = True,
                )
    
    return JSONResponse(status_code = 500,
                        content     = {"error"      : "Internal server error",
                                       "detail"     : str(exc),
                                       "request_id" : str(request_id),
                                      }
                       )


######################### RUN SERVER #########################
if __name__ == "__main__":
    logger.info(msg   = f"Starting server on {settings.app_host}:{settings.app_port}",
                extra = {"request_id": "startup", "batch_id": "N/A", "batch_item_id": "N/A"},
               )
    
    uvicorn.run(app,
                host      = settings.app_host,
                port      = settings.app_port,
                workers   = 1,
                log_level = settings.log_level.lower(),
               )
