# DEPENDENCIES
import os
import json
import asyncio
import argparse
import warnings
from typing import Any
from typing import List
from typing import Dict
from pathlib import Path
from datetime import datetime
from src.logging_config import setup_logging
from src.pydantic_input_classes import InputItemGpt
from src.pydantic_output_classes import OutputItemGpt
from src.processing_functions import process_item_gpt


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')

# CONFIGURE THE LOGGING
logger = setup_logging()

# DEFAULT CONFIGURATION
DEFAULT_INPUT_FILE = "data/sample_data.json"
DEFAULT_OUTPUT_DIR = "results"
DEFAULT_BATCH_SIZE = 5
REQUEST_ID         = "cli_processing"


class LinkedInJobExtractorCLI:
    """
    Command-line interface for LinkedIn job data extraction using prompt engineering
    for encapsulating the entire extraction workflow and provides a clean interface 
    for batch processing LinkedIn posts
    """
    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Initialize the CLI processor
        
        Arguments:
        ----------
            batch_size { int } : Number of items to process concurrently
        """
        self.batch_size      = batch_size
        self.processed_count = 0
        self.success_count   = 0
        self.error_count     = 0
        

    async def load_input_data(self, input_file: str) -> List[InputItemGpt]:
        """
        Load and validate input data from JSON file
        
        Arguments:
        ----------
            input_file { str }     : Path to input JSON file
            
        Returns:
        --------
            { List[InputItemGpt] } : Validated input items
            
        Raises:
        -------
            FileNotFoundError      : If input file doesn't exist

            ValueError             : If JSON is invalid or data doesn't match schema
        """
        try:
            input_path = Path(input_file)

            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
                
            logger.info(f"Loading input data from: {input_file}")
            
            with open(input_path, 'r', encoding = 'utf-8') as file:
                raw_data = json.load(file)
                
            if not isinstance(raw_data, list):
                raise ValueError("Input data must be a JSON array")
                
            # Validate and convert to Pydantic models
            input_items = list()

            for idx, item in enumerate(raw_data):
                try:
                    validated_item = InputItemGpt(**item)
                    input_items.append(validated_item)
                
                except Exception as validation_error:
                    logger.warning(f"Skipping invalid item at index {idx}: {validation_error}")
                    
            logger.info(f"Successfully loaded {len(input_items)} valid items from {len(raw_data)} total items")
            return input_items
            
        except json.JSONDecodeError as json_error:
            raise ValueError(f"Invalid JSON format in {input_file}: {json_error}")
        
        except Exception as load_error:
            logger.error(f"Error loading input data: {load_error}")
            raise
            

    async def process_batch(self, batch: List[InputItemGpt], batch_id: int, total_items: int) -> List[Dict[str, Any]]:
        """
        Process a single batch of input items concurrently
        
        Arguments:
        ----------
            batch       { List[InputItemGpt] } : Items to process in this batch

            batch_id            { int }        : Batch identifier for logging
            
            total_items         { int }        : Total number of items being processed
            
        Returns:
        --------
                { List[Dict[str, Any]] }        : Processed results as dictionaries
        """
        logger.info(f"Processing batch {batch_id} with {len(batch)} items")
        
        # Create tasks for concurrent processing
        tasks = list()

        for idx, item in enumerate(batch):
            global_idx    = (batch_id - 1) * self.batch_size + idx
            task          = process_item_gpt(item          = item,
                                             index         = global_idx,
                                             total_count   = total_items,
                                             batch_id      = batch_id,
                                             batch_item_id = idx + 1,
                                             request_id    = REQUEST_ID,
                                            )
            tasks.append(task)
            
        # Execute all tasks concurrently
        batch_results     = await asyncio.gather(*tasks, return_exceptions = True)
        
        # Process results and handle exceptions
        processed_results = list()

        for idx, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Error processing item {idx} in batch {batch_id}: {result}")
                
                self.error_count += 1
                
                # Create error response
                error_item        = batch[idx].dict()
                
                error_item.update({"classification" : "Error",
                                   "error"          : f"ProcessingError: {str(result)}"
                                 })

                processed_results.append(error_item)

            else:
                # Handle both single items and lists of items
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, OutputItemGpt):
                            processed_results.append(item.dict(exclude_none = True))
                        
                        else:
                            processed_results.append(item)
                        
                        self.success_count += 1
                else:
                    if isinstance(result, OutputItemGpt):
                        processed_results.append(result.dict(exclude_none=True))
                    
                    else:
                        processed_results.append(result)
                    
                    self.success_count += 1
                    
        return processed_results
        

    async def process_all_items(self, input_items: List[InputItemGpt]) -> List[Dict[str, Any]]:
        """
        Process all input items in batches with progress tracking
        
        Arguments:
        ----------
            input_items { List[InputItemGpt] } : All items to process
            
        Returns:
        --------
               { List[Dict[str, Any]] }        : All processed results
        """
        total_items = len(input_items)
        all_results = list()
        
        logger.info(f"Starting processing of {total_items} items in batches of {self.batch_size}")
        
        # Process items in batches
        for batch_id, i in enumerate(range(0, total_items, self.batch_size), start=1):
            batch = input_items[i:i + self.batch_size]
            
            try:
                batch_results = await self.process_batch(batch, batch_id, total_items)
                all_results.extend(batch_results)

                self.processed_count += len(batch)
                
                # Progress update
                progress              = (self.processed_count / total_items) * 100

                logger.info(f"Progress: {progress:.1f}% ({self.processed_count}/{total_items} items)")
                
            except Exception as batch_error:
                logger.error(f"Error processing batch {batch_id}: {batch_error}")
                self.error_count += len(batch)
                
        return all_results
        

    async def save_results(self, results: List[Dict[str, Any]], output_file: str) -> None:
        """
        Save processed results to JSON file with metadata
        
        Arguments:
        ----------
            results     { List[Dict[str, Any]] } : Processed results to save

            output_file        { str }           : Output file path
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_file)
            output_path.parent.mkdir(parents  = True, 
                                     exist_ok = True,
                                    )
            
            # Prepare output with metadata
            output_data = {"metadata" : {"timestamp"                : datetime.now().isoformat(),
                                         "total_processed"          : self.processed_count,
                                         "successful_extractions"   : self.success_count,
                                         "errors"                   : self.error_count,
                                         "batch_size"               : self.batch_size,
                                         "prompt_engineering_model" : "gpt-3.5-turbo-instruct",
                                         "processing_type"          : "CLI Batch Processing",
                                        },
                           "results"  : results,
                          }
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(obj          = output_data, 
                          fp           = file, 
                          indent       = 4, 
                          ensure_ascii = False)
                
            logger.info(f"Results saved to: {output_file}")
            logger.info(f"Total items processed: {self.processed_count}")
            logger.info(f"Successful extractions: {self.success_count}")
            logger.info(f"Errors encountered: {self.error_count}")
            
        except Exception as save_error:
            logger.error(f"Error saving results: {save_error}")
            raise
            

    async def run(self, input_file: str, output_file: str) -> None:
        """
        Main execution method for the CLI
        
        Arguments:
        ----------
            input_file  { str } : Path to input JSON file

            output_file { str } : Path to output JSON file
        """
        try:
            logger.info("Starting LinkedIn Job Data Extraction CLI")
            logger.info("Powered by Advanced Prompt Engineering Techniques")
            
            # Load input data
            input_items = await self.load_input_data(input_file)
            
            if not input_items:
                logger.warning("No valid input items found. Exiting.")
                return
                
            # Process all items
            results = await self.process_all_items(input_items)
            
            # Save results
            await self.save_results(results, output_file)
            
            logger.info("Processing completed successfully!")
            
        except Exception as main_error:
            logger.error(f"CLI execution failed: {main_error}")
            raise


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure command-line argument parser
    
    Returns:
    --------
        { argparse.ArgumentParser }    : Configured argument parser
    """
    parser = argparse.ArgumentParser(description     = "LinkedIn Job Data Extractor - CLI Utility",
                                     epilog          = """
                                                       Examples:
                                                            python main.py
                                                            python main.py --input data/custom_data.json
                                                            python main.py --output results/my_output.json --batch-size 10
                                                            python main.py --input data/test.json --output results/test_output.json --batch-size 3
                                                       """,
                                     formatter_class = argparse.RawDescriptionHelpFormatter
                                    )
    
    parser.add_argument('--input', 
                        '-i',
                        type    = str,
                        default = DEFAULT_INPUT_FILE,
                        help    = f'Input JSON file path (default: {DEFAULT_INPUT_FILE})',
                       )
    
    parser.add_argument('--output', 
                        '-o',
                        type = str,
                        help = 'Output JSON file path (default: auto-generated in results/ directory)',
                       )
    
    parser.add_argument('--batch-size', 
                        '-b',
                        type    = int,
                        default = DEFAULT_BATCH_SIZE,
                        help    = f'Number of items to process concurrently (default: {DEFAULT_BATCH_SIZE})',
                       )
    
    parser.add_argument('--verbose', 
                        '-v',
                        action = 'store_true',
                        help   = 'Enable verbose logging',
                       )
    
    return parser


def generate_output_filename(input_file: str) -> str:
    """
    Generate output filename based on input filename and timestamp
    
    Arguments:
    ----------
        input_file { str } : Input file path
        
    Returns:
    --------
            { str }        : Generated output file path
    """
    input_path      = Path(input_file)
    timestamp       = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_path.stem}_processed_{timestamp}.json"
    
    return str(Path(DEFAULT_OUTPUT_DIR) / output_filename)


async def main():
    """
    Main entry point for the CLI application
    """
    # Parse command-line arguments
    parser = create_argument_parser()
    args   = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel("DEBUG")
        
    # Generate output filename if not provided
    output_file = args.output or generate_output_filename(args.input)
    
    # Validate batch size
    if args.batch_size < 1:
        logger.error("Batch size must be at least 1")
        return
        
    try:
        # Create and run CLI processor
        cli_processor = LinkedInJobExtractorCLI(batch_size = args.batch_size)
        
        await cli_processor.run(args.input, 
                                output_file,
                               )
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    
    except FileNotFoundError as file_error:
        logger.error(f"File error: {file_error}")
    
    except ValueError as value_error:
        logger.error(f"Data error: {value_error}")
    
    except Exception as unexpected_error:
        logger.error(f"Unexpected error: {unexpected_error}")


if __name__ == "__main__":
    print("LinkedIn Job Data Extractor - Prompt Engineering CLI")
    print("=" * 60)
    
    # Run the async main function
    asyncio.run(main())