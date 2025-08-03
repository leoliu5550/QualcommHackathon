import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python organize_service.py <target_path>")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    if not os.path.exists(target_path):
        print(f"Error: Path '{target_path}' does not exist")
        sys.exit(1)

    restore_mode = "--restore" in sys.argv[2:]

    if restore_mode:
        from lib.restore.restore_folder import restore_folder
        restore_folder(target_path)
    else:
        try:
            from lib.service.organize_service import Organizer
            
            os.makedirs(os.path.join(target_path,".backup"), exist_ok=True)
            
            organizer = Organizer()
            organizer.start_organize(target_path)
            
            # print("\nOrganization completed!")
            # print(f"Classification time: {result.get('classification_time', 'N/A')}")
            # print(f"\nFolder mappings:")
            # for folder, files in result.get("folder_mappings", {}).items():
            #     print(f"\n{folder}:")
            #     for file in files:
            #         print(f"  - {file}")
                    
        except Exception as e:
            print(f"Error during organization: {str(e)}")
            sys.exit(1)
        


if __name__=="__main__":
    """
    測試指令: 
    python main.py test/data/textIO
    python main.py test/data/textIO --restore"""
    main()