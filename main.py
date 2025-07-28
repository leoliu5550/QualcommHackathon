from lib.service.organize_service import Organizer


def main():
    org = Organizer()
    print(org.start_organize('./test/data'))

if __name__=="__main__":
    main()