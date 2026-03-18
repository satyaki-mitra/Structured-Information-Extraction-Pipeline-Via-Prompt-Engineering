# DEPENDENCIES
import asyncio
import logging
import warnings
from typing import Any
from typing import List
from typing import Dict
from typing import Optional
from config.schemas import LinkedInPostInput
from config.schemas import LinkedInPostOutput
from src.core.base_extractor import BaseExtractor


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Handles batch processing of LinkedIn posts through extractors: manages concurrent processing, batching, and result aggregation
    """
    def __init__(self, extractor: BaseExtractor, batch_size: int = 20):
        """
        Initialize data processor
        
        Arguments:
        ----------
            extractor  { BaseExtractor } : Extractor instance to use for processing
            
            batch_size      { int }      : Number of items to process concurrently
        """
        self.extractor  = extractor
        self.batch_size = batch_size
        
        logger.info(msg   = f"DataProcessor initialized with {extractor.extractor_name}, batch_size={batch_size}",
                    extra = {"request_id": "processor_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
    
    
    async def process_single_item(self, item: Dict[str, Any], index: int, total_count: int, batch_id: int, batch_item_id: int, request_id: str) -> LinkedInPostOutput:
        """
        Process a single LinkedIn post
        
        Arguments:
        ----------
            item          { Dict }  : Input LinkedIn post data
            
            index         { int }   : Index in total input array
            
            total_count   { int }   : Total number of items in request
            
            batch_id      { int }   : Current batch identifier
            
            batch_item_id { int }   : Item identifier within batch
            
            request_id    { str }   : Request identifier
        
        Returns:
        --------
            { LinkedInPostOutput }  : Processed output
        """
        logger.info(msg   = f"Processing item {index + 1}/{total_count}",
                    extra = {"request_id": request_id, "batch_id": batch_id, "batch_item_id": batch_item_id},
                   )
        
        try:
            # Extract information using the configured extractor
            extraction_result = await self.extractor.extract(linkedin_post = item,
                                                             request_id    = request_id,
                                                            )
            
            # Check for extraction errors
            if (('error' in extraction_result) and (extraction_result['error'])):
                logger.warning(msg   = f"Extraction failed for item {index + 1}: {extraction_result['error']}",
                               extra = {"request_id": request_id, "batch_id": batch_id, "batch_item_id": batch_item_id},
                              )
                
                return LinkedInPostOutput(name           = item.get('name', ''),
                                          about          = item.get('about', ''),
                                          description    = item.get('description', ''),
                                          userProfileUrl = item.get('userProfileUrl', ''),
                                          source         = item.get('source', ''),
                                          searchJobTitle = item.get('searchJobTitle', ''),
                                          companyLinks   = item.get('companyLinks', []),
                                          classification = 'Irrelevant',
                                          error          = extraction_result['error'],
                                         )
            
            # Build base output
            base_output    = LinkedInPostOutput(name           = item.get('name', ''),
                                                about          = item.get('about', ''),
                                                description    = item.get('description', ''),
                                                userProfileUrl = item.get('userProfileUrl', ''),
                                                source         = item.get('source', ''),
                                                searchJobTitle = item.get('searchJobTitle', ''),
                                                companyLinks   = item.get('companyLinks', []),
                                                classification = 'Relevant' if extraction_result.get('relevant') else 'Irrelevant',
                                               )
            
            # Get extracted information
            extracted_info = extraction_result.get('extracted_info', [])
            
            # If no relevant information extracted
            if not extracted_info:
                return base_output
            
            # Create output items for each extracted job change
            output_items   = list()
            
            for info in extracted_info:
                output_item                = base_output.model_copy(deep = True)
                output_item.jobPosterName  = extraction_result.get('poster_name')
                output_item.jobStarterName = info.get('person_name')
                output_item.companyName    = info.get('organization')
                output_item.currentRole    = info.get('new_role')
                output_items.append(output_item)
            
            logger.info(msg   = f"Successfully processed item {index + 1}/{total_count}",
                        extra = {"request_id": request_id, "batch_id": batch_id, "batch_item_id": batch_item_id},
                       )
            
            return output_items if (len(output_items) > 1) else output_items[0]
        
        except Exception as process_error:
            error_message = f"Error processing item {index + 1}: {repr(process_error)}"
            
            logger.error(msg      = error_message,
                         extra    = {"request_id": request_id, "batch_id": batch_id, "batch_item_id": batch_item_id},
                         exc_info = True,
                        )
            
            return LinkedInPostOutput(name           = item.get('name', ''),
                                      about          = item.get('about', ''),
                                      description    = item.get('description', ''),
                                      userProfileUrl = item.get('userProfileUrl', ''),
                                      source         = item.get('source', ''),
                                      searchJobTitle = item.get('searchJobTitle', ''),
                                      companyLinks   = item.get('companyLinks', []),
                                      classification = 'Irrelevant',
                                      error          = error_message,
                                     )
    
    
    async def process_batch(self, batch: List[Dict[str, Any]], batch_id: int, total_items: int, request_id: str, start_index: int = 0) -> List[LinkedInPostOutput]:
        """
        Process a batch of LinkedIn posts concurrently
        
        Arguments:
        ----------
            batch        { List }        : List of input items to process
           
            batch_id     { int }         : Batch identifier
           
            total_items  { int }         : Total number of items in entire request
           
            request_id   { str }         : Request identifier
           
            start_index  { int }         : Starting index in total array
        
        Returns:
        --------
            { List[LinkedInPostOutput] } : List of processed outputs
        """
        logger.info(msg   = f"Processing batch {batch_id} with {len(batch)} items",
                    extra = {"request_id": request_id, "batch_id": batch_id, "batch_item_id": "N/A"},
                   )
        
        # Create tasks for concurrent processing
        tasks             = [self.process_single_item(item          = item,
                                                      index         = start_index + idx,
                                                      total_count   = total_items,
                                                      batch_id      = batch_id,
                                                      batch_item_id = idx + 1,
                                                      request_id    = request_id,
                                                     )
                             for idx, item in enumerate(batch)
                            ]
        
        # Execute all tasks concurrently
        results           = await asyncio.gather(*tasks, return_exceptions = True)
        
        # Handle any exceptions
        processed_results = list()

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(msg   = f"Task failed in batch {batch_id}, item {idx + 1}: {repr(result)}",
                             extra = {"request_id": request_id, "batch_id": batch_id, "batch_item_id": idx + 1},
                            )
                # Create error output
                processed_results.append(LinkedInPostOutput(name           = '',
                                                            about          = '',
                                                            description    = '',
                                                            source         = '',
                                                            classification = 'Irrelevant',
                                                            error          = f"Processing exception: {repr(result)}",
                                                           )
                                        )
            
            else:
                processed_results.append(result)
        
        logger.info(msg   = f"Batch {batch_id} completed: {len(processed_results)} items processed",
                    extra = {"request_id": request_id, "batch_id": batch_id, "batch_item_id": "N/A"},
                   )
        
        return processed_results
    
    
    async def process_all(self, input_data: List[Dict[str, Any]], request_id: str = "batch_process") -> List[LinkedInPostOutput]:
        """
        Process all input data in batches
        
        Arguments:
        ----------
            input_data     { List }      : List of LinkedIn post data to process
            
            request_id     { str }       : Request identifier
        
        Returns:
        --------
            { List[LinkedInPostOutput] } : List of all processed outputs
        """
        if not input_data:
            logger.warning(msg   = "Empty input data provided",
                           extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                          )
            return []
        
        total_items = len(input_data)
        all_results = list()
        
        logger.info(msg   = f"Starting batch processing: {total_items} items, batch_size={self.batch_size}",
                    extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
        
        # Process in batches
        for batch_id, i in enumerate(range(0, total_items, self.batch_size), start=1):
            batch         = input_data[i:i + self.batch_size]
            
            batch_results = await self.process_batch(batch       = batch,
                                                     batch_id    = batch_id,
                                                     total_items = total_items,
                                                     request_id  = request_id,
                                                     start_index = i,
                                                    )
            
            all_results.extend(batch_results)
        
        # Flatten results (handle cases where single item returns list)
        flattened_results = list()

        for result in all_results:
            if isinstance(result, list):
                flattened_results.extend(result)
            
            else:
                flattened_results.append(result)
        
        logger.info(msg   = f"Batch processing complete: {len(flattened_results)} total outputs",
                    extra = {"request_id": request_id, "batch_id": "All", "batch_item_id": "N/A"},
                   )
        
        return flattened_results