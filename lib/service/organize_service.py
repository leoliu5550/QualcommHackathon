import datetime
import json
import os
import sys
from typing import List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.file_scanner import FileScanner
from lib.file_parser import parser_manager
from lib.file_parser.base_parser import ParseResult
from lib.folder_namer.folder_namer import create_name

class Organizer:
    def __init__(self):
        pass

    def start_organize(self,target_path:str):

        # step 1
        scanner_result = self._file_scanner(target_path)

        # step 2 
        file_parserd = self._file_parser(scanner_result = scanner_result,  save_result = True)
        
        # step 2
        generate_result =self._generate_folder(file_parserd, base_output_dir=target_path,  save_result = True)
        
        return generate_result
    
    def _file_scanner(self,target_path:str)->json:
        file_scanner = FileScanner(target_path=target_path)
        scanner_result = file_scanner.scan_with_details(save_result=False)
        scanner_result = [ file_path.get("path",None) for file_path in scanner_result.get("original_files",[])]
        return scanner_result
    
    def _file_parser(self, scanner_result:json, save_result=False)->json:
        file_parserd:List[ParseResult] = parser_manager.parse_multiple_files(scanner_result)
        now = datetime.datetime.now()
        parser_results = {
            "scan_time": now.isoformat() ,
            "summaries":[],
        }
        for _file_path,result in zip(scanner_result,file_parserd):
            _temp = {}
            _temp["summary"] = result.content
            _temp["path"] = _file_path
            _temp["name"] = os.path.basename(_file_path)
            parser_results["summaries"].append(_temp)
        if save_result:
            os.makedirs(".backup", exist_ok=True)
            with open(".backup/summ_load.json", 'w', encoding='utf-8') as f:
                json.dump(parser_results, f, ensure_ascii=False, indent=4)
        return parser_results
    
    def _generate_folder(self,file_parserd:json,base_output_dir:str, save_result=False)->json:
        file_paths_dict = create_name.process_files(summaries_data=file_parserd,base_output_dir=base_output_dir)
        
        # Convert file_paths to folder_mappings
        folder_mappings = {}
        for file_info in file_paths_dict.get("file_paths", []):
            # Extract folder name from new path
            new_path = file_info["new"]
            folder_name = os.path.basename(os.path.dirname(new_path))
            file_name = os.path.basename(new_path)
            
            if folder_name not in folder_mappings:
                folder_mappings[folder_name] = []
            folder_mappings[folder_name].append(file_name)
        
        result = {
            "folder_mappings": folder_mappings,
            "file_paths": file_paths_dict.get("file_paths", []),
            "classification_time": datetime.datetime.now().isoformat()
        }

        if save_result:
            os.makedirs(".backup", exist_ok=True)
            with open(".backup/file_paths.json", 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
        return result

# 測試指令: python lib/service/organize_service.py test/data/textIO
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python organize_service.py <target_path>")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    if not os.path.exists(target_path):
        print(f"Error: Path '{target_path}' does not exist")
        sys.exit(1)
    
    print(f"Starting organization for: {target_path}")
    
    organizer = Organizer()
    
    try:
        os.makedirs(".backup", exist_ok=True)
        
        result = organizer.start_organize(target_path)
        
        print("\nOrganization completed!")
        print(f"Classification time: {result.get('classification_time', 'N/A')}")
        print(f"\nFolder mappings:")
        
        for folder, files in result.get("folder_mappings", {}).items():
            print(f"\n{folder}:")
            for file in files:
                print(f"  - {file}")
                
    except Exception as e:
        print(f"Error during organization: {str(e)}")
        sys.exit(1)