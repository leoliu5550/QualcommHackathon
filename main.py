import sys,os 
from lib.llm_model.llm_interface import get_llm
from lib.llm_model.mode_config import config
from lib.service.organize_service import Organizer
from lib.folder_namer.folder_namer import create_name
def main():
    if len(sys.argv) < 2:
        print("Usage: python organize_service.py <target_path>")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    if not os.path.exists(target_path):
        print(f"Error: Path '{target_path}' does not exist")
        sys.exit(1)

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
        
# 測試指令: python lib/service/organize_service.py test/data/textIO

if __name__=="__main__":
    main()