from pathlib import Path
import json
from typing import List
from lib.file_scanner import FileScanner
from lib.file_parser import parser_manager
from lib.file_parser.base_parser import ParseResult

class Organizer:
    def __init__(self):
        pass

    def start_organize(self,target_path:str):

        # step 1
        scanner_result = self._file_scanner(target_path)

        # step 2 
        file_parserd = self._file_parser(scanner_result,  save_result = True)
        return file_parserd
    
    def _file_scanner(self,target_path:str)->json:
        file_scanner = FileScanner(target_path=target_path)
        scanner_result = file_scanner.scan_with_details(save_result=False)
        scanner_result = [ file_path.get("path",None) for file_path in scanner_result.get("original_files",[])]
        return scanner_result
    
    def _file_parser(self, scanner_result:json, save_result :False)->json:
        file_parserd:List[ParseResult] = parser_manager.parse_multiple_files(scanner_result)
      
        parser_results = []
        for _file_path,result in zip(scanner_result,file_parserd):
            _temp = {}
            _temp["summary"] = result.content
            _temp["path"] = _file_path
            parser_results.append(_temp)
        if save_result:
            with open("summ_load.json", 'w', encoding='utf-8') as f:
                json.dump(parser_results, f, ensure_ascii=False, indent=4)
        return parser_results