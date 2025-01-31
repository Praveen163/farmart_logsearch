import sys
from datetime import datetime
import mmap
from pathlib import Path

class LogExtractor:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.date_format = "%Y-%m-%d"
        self.timestamp_length = 10

    def find_approximate_position(self, mm, file_size, target_date):
        """
        Quick approximation of where the target date might be in the file
        based on the date's position in the year
        """
        try:
            target = datetime.strptime(target_date, self.date_format)
            year_start = datetime(target.year, 1, 1)
            days_diff = (target - year_start).days
            approx_pos = (days_diff * file_size) // 365
            
            # Adjust to nearest newline
            while approx_pos > 0 and mm[approx_pos-1:approx_pos] != b'\n':
                approx_pos -= 1
            
            return max(0, approx_pos)
        except ValueError:
            return 0

    def find_boundary(self, mm, target_date, approx_pos, file_size, search_forward=True):
        """
        Fast linear search from approximate position
        """
        step_size = 4096  # 4KB steps
        pos = approx_pos
        
        while 0 <= pos < file_size:
            # Adjust to nearest newline
            while pos > 0 and mm[pos-1:pos] != b'\n':
                pos -= 1
            
            try:
                current_date = mm[pos:pos+self.timestamp_length].decode()
                current = datetime.strptime(current_date, self.date_format)
                target = datetime.strptime(target_date, self.date_format)
                
                if current == target:
                    # Found a match, now find the boundary
                    if search_forward:
                        # Look for first non-matching date
                        while pos < file_size:
                            next_pos = mm.find(b'\n', pos) + 1
                            if next_pos == 0:  # No more newlines
                                return file_size
                            try:
                                next_date = mm[next_pos:next_pos+self.timestamp_length].decode()
                                if next_date != target_date:
                                    return pos
                            except:
                                return pos
                            pos = next_pos
                    else:
                        # Look backwards for first non-matching date
                        while pos > 0:
                            prev_pos = mm.rfind(b'\n', 0, pos - 1) + 1
                            if prev_pos <= 0:  # No more newlines
                                return 0
                            try:
                                prev_date = mm[prev_pos:prev_pos+self.timestamp_length].decode()
                                if prev_date != target_date:
                                    return pos
                            except:
                                return pos
                            pos = prev_pos
                
                if search_forward:
                    if current < target:
                        pos += step_size
                    else:
                        pos = mm.rfind(b'\n', pos - step_size, pos) + 1
                else:
                    if current > target:
                        pos -= step_size
                    else:
                        next_line = mm.find(b'\n', pos) + 1
                        if next_line == 0:
                            return file_size
                        pos = next_line
                
            except ValueError:
                if search_forward:
                    pos += step_size
                else:
                    pos -= step_size
            
            if pos < 0:
                return 0
            if pos >= file_size:
                return file_size
                
        return -1

    def extract_logs(self, target_date):
        """Extract logs for the specified date and save to output file."""
        parent_folder = Path(__file__).resolve().parent
        output_dir = parent_folder.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"output_{target_date}.txt"

        try:
            with open(self.log_file_path, 'rb') as f:
                file_size = Path(self.log_file_path).stat().st_size
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                
                # Get approximate position based on date
                approx_pos = self.find_approximate_position(mm, file_size, target_date)
                
                # Find start and end positions
                start_pos = self.find_boundary(mm, target_date, approx_pos, file_size, search_forward=False)
                if start_pos == -1:
                    print(f"No logs found for date: {target_date}")
                    mm.close()
                    return
                
                end_pos = self.find_boundary(mm, target_date, start_pos, file_size, search_forward=True)
                
                # Find the end of the last line
                end_pos = mm.find(b'\n', end_pos)
                if end_pos == -1:
                    end_pos = file_size
                else:
                    end_pos += 1  # Include the newline

                # Copy data in larger chunks (10MB)
                chunk_size = 10 * 1024 * 1024
                total_size = end_pos - start_pos

                with open(output_file, 'wb') as out_f:
                    current_pos = start_pos
                    while current_pos < end_pos:
                        chunk_end = min(current_pos + chunk_size, end_pos)
                        out_f.write(mm[current_pos:chunk_end])
                        current_pos = chunk_end

                mm.close()
                print(f"Logs extracted to: {output_file}")
                print(f"Extracted {total_size:,} bytes of log data")

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