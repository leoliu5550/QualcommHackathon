from lib.llm_model.llm_interface import get_llm
from lib.llm_model.mode_config import config
from lib.service.organize_service import Organizer
from lib.folder_namer.folder_namer import create_name
def main():
    orger = Organizer()
    summ_load = orger.start_organize("test//data//textIO")
    for summ in summ_load["summaries"]:
        print("Summary INTPUT-------------------")
        print(summ["summary"])
        print("LLM OUTPUT-------------------")
        print(create_name.create_folder_name(summ["summary"]))


if __name__=="__main__":
    main()