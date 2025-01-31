import sys
import os
import mmap
from datetime import datetime
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
import queue

class LogExtractor:
    def __init__(self, log_file_path):
        """Initialize with log file path and constants"""
        self.log_file_path = log_file_path
        self.date_format = "%Y-%m-%d"
        self.timestamp_length = 10  # Length of YYYY-MM-DD
        self.chunk_size = 100 * 1024 * 1024  # 100MB chunks for reading
        self.output_queue = queue.Queue(maxsize=100)  # Buffer for matched lines
        
    def process_chunk(self, chunk, target_date):
        """Process a chunk of data and find matching lines"""
        matches = []
        start = 0
        while True:
            # Find next newline
            end = chunk.find(b'\n', start)
            if end == -1:
                # If no newline found, this might be a partial line
                return matches, chunk[start:] if start < len(chunk) else b''
            
            line = chunk[start:end+1]
            try:
                # Check if line starts with our target date
                if line[:self.timestamp_length].decode() == target_date:
                    matches.append(line)
            except (UnicodeDecodeError, IndexError):
                pass  # Skip invalid lines
                
            start = end + 1
            if start >= len(chunk):
                return matches, b''

    def write_output(self, output_file):
        """Write matched lines from queue to output file"""
        with open(output_file, 'wb') as out_f:
            while True:
                try:
                    chunk = self.output_queue.get()
                    if chunk is None:  # Sentinel value
                        break
                    out_f.write(chunk)
                except queue.Empty:
                    break

    def extract_logs(self, target_date):
        """Extract logs for the specified date and save to output file."""
        start_time = time.time()
        
        # Create output directory
        parent_folder = Path(__file__).resolve().parent
        output_dir = parent_folder.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"output_{target_date}.txt"

        try:
            file_size = os.path.getsize(self.log_file_path)
            print(f"Processing file of size: {file_size:,} bytes")
            
            # Start output writer thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.write_output, output_file)
            
                with open(self.log_file_path, 'rb') as f:
                    leftover = b''  # For handling lines split across chunks
                    total_matches = 0
                    processed_size = 0
                    
                    while True:
                        chunk = f.read(self.chunk_size)
                        if not chunk:
                            break
                            
                        # Process chunk with any leftover from previous chunk
                        full_chunk = leftover + chunk
                        matches, leftover = self.process_chunk(full_chunk, target_date)
                        
                        # Put matches in output queue
                        for match in matches:
                            self.output_queue.put(match)
                            total_matches += 1
                        
                        # Update progress
                        processed_size += len(chunk)
                        progress = (processed_size / file_size) * 100
                        print(f"\rProgress: {progress:.1f}% - Matches found: {total_matches}", 
                              end='', flush=True)
                    
                    # Process any remaining leftover
                    if leftover:
                        matches, _ = self.process_chunk(leftover, target_date)
                        for match in matches:
                            self.output_queue.put(match)
                            total_matches += 1
                    
                    # Signal completion to output writer
                    self.output_queue.put(None)
                
                # Wait for writer to finish
                future.result()
            
            elapsed_time = time.time() - start_time
            print(f"\nExtracted {total_matches:,} log entries in {elapsed_time:.2f} seconds")
            print(f"Output saved to: {output_file}")

        except FileNotFoundError:
            print(f"Error: Log file not found at {self.log_file_path}")
        except Exception as e:
            print(f"Error processing logs: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_logs.py YYYY-MM-DD")
        return

    target_date = sys.argv[1]
    log_file_path = "logs_2024.log"
    
    print(f"Searching for logs from date: {target_date}")
    extractor = LogExtractor(log_file_path)
    extractor.extract_logs(target_date)

if __name__ == "__main__":
    main()
