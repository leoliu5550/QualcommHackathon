"""
usercli.py
FileOrg Terminal GUI Module

提供終端的圖形化界面，讓使用者透過箭頭鍵選擇選項
放置位置: fileorg/gui/usercli.py
"""

import sys
import os
import json
import time
from datetime import datetime
try:
    import msvcrt  # Windows
    WINDOWS = True
except ImportError:
    import termios
    import tty
    WINDOWS = False


class TerminalGUI:
    def __init__(self):
        self.history_file = os.path.expanduser("~/.fileorg_history.json")
        self.selected_index = 0
        
    def clear_screen(self):
        """清除螢幕"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_key(self):
        """跨平台的按鍵獲取"""
        if WINDOWS:
            key = msvcrt.getch()
            if key == b'\xe0':  # 方向鍵前綴
                key = msvcrt.getch()
                if key == b'H':  # 上箭頭
                    return 'UP'
                elif key == b'P':  # 下箭頭
                    return 'DOWN'
            elif key == b'\r':  # Enter
                return 'ENTER'
            elif key == b'\x1b':  # ESC
                return 'ESC'
            return key.decode('utf-8', errors='ignore')
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)
                if key == '\x1b':  # ESC 序列
                    key += sys.stdin.read(2)
                    if key == '\x1b[A':  # 上箭頭
                        return 'UP'
                    elif key == '\x1b[B':  # 下箭頭
                        return 'DOWN'
                    else:
                        return 'ESC'
                elif key == '\r' or key == '\n':
                    return 'ENTER'
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def show_menu(self, title, options):
        """顯示選單並處理選擇"""
        while True:
            self.clear_screen()
            print(f"\n{title}")
            print("=" * len(title))
            print()
            
            for i, option in enumerate(options):
                if i == self.selected_index:
                    print(f"► {option}")
                else:
                    print(f"  {option}")
            
            print("\n使用 ↑↓ 方向鍵選擇，Enter 確認，ESC 退出")
            
            key = self.get_key()
            
            if key == 'UP':
                self.selected_index = (self.selected_index - 1) % len(options)
            elif key == 'DOWN':
                self.selected_index = (self.selected_index + 1) % len(options)
            elif key == 'ENTER':
                return self.selected_index
            elif key == 'ESC':
                return None
    
    def input_path(self):
        """輸入檔案路徑的界面"""
        self.clear_screen()
        print("\n檔案路徑輸入")
        print("=" * 12)
        print()
        print("請輸入要整理的目錄路徑:")
        print("(可以直接貼上路徑)")
        print("提示: 在 Windows 中可以按 Ctrl+V 貼上")
        print("      在 Linux/Mac 中可以按 Shift+Ctrl+V 貼上")
        print()
        
        try:
            path = input("路徑: ").strip().strip('"').strip("'")
            if not path:
                return None
            
            # 正規化路徑
            path = os.path.normpath(os.path.abspath(path))
            
            if not os.path.exists(path):
                print(f"\n錯誤: 路徑 '{path}' 不存在")
                input("\n按 Enter 繼續...")
                return None
            
            if not os.path.isdir(path):
                print(f"\n錯誤: '{path}' 不是目錄")
                input("\n按 Enter 繼續...")
                return None
                
            return path
        except KeyboardInterrupt:
            return None
    
    def load_history(self):
        """載入歷史記錄"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    
    def save_history(self, path, report_path=None):
        """儲存歷史記錄"""
        try:
            history = self.load_history()
            record = {
                "timestamp": datetime.now().isoformat(),
                "path": path,
                "report_path": report_path
            }
            history.insert(0, record)  # 最新的在前面
            
            # 只保留最近 50 筆記錄
            history = history[:50]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存歷史記錄時發生錯誤: {e}")
    
    def show_history(self):
        """顯示歷史記錄"""
        history = self.load_history()
        
        if not history:
            self.clear_screen()
            print("\n歷史記錄")
            print("=" * 8)
            print("\n尚無歷史記錄")
            input("\n按 Enter 繼續...")
            return None
        
        options = []
        for record in history:
            timestamp = record.get("timestamp", "未知時間")
            path = record.get("path", "未知路徑")
            # 格式化時間顯示
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = timestamp[:16] if len(timestamp) > 16 else timestamp
            
            options.append(f"{time_str} - {path}")
        
        options.append("返回主選單")
        
        self.selected_index = 0
        choice = self.show_menu("歷史記錄", options)
        
        if choice is None or choice == len(options) - 1:
            return None
        
        return history[choice]["path"]
    
    def confirm_action(self, message, details=None):
        """確認對話框"""
        self.clear_screen()
        print(f"\n{message}")
        print("=" * len(message))
        
        if details:
            print(f"\n{details}")
        
        options = ["是", "否"]
        self.selected_index = 1  # 預設選擇 "否" 較安全
        
        choice = self.show_menu("", options)
        return choice == 0 if choice is not None else False
    
    def show_completion_report(self, target_path):
        """顯示完成後的報告資訊"""
        self.clear_screen()
        print("\n🎉 檔案整理完成！")
        print("=" * 20)
        
        print(f"\n⚠️  重要提醒:")
        print(f"   • 請勿刪除 .backup 資料夾，這是還原檔案的關鍵")
        print(f"   • 如需還原，可使用 'fileorg start' 再選擇還原模式")
        
        # 查找最近期報告
        latest_report_folder = self.find_latest_report_folder(target_path)
        has_report = latest_report_folder is not None

        options = []
        if has_report:
            options.append("查看最新報告")

        options.extend(["返回主選單", "退出程式"])

        self.selected_index = 0
        choice = self.show_menu("", options)

        if choice is not None:
            if has_report and choice == 0:  # 查看最新報告
                self.show_latest_report(latest_report_folder)
            elif choice == (1 if has_report else 0):  # 返回主選單
                return
            else:  # 退出程式
                self.clear_screen()
                print("\n感謝使用 FileOrg！")
                sys.exit(0)

    def show_latest_report(self, report_folder):
        """顯示最新報告內容"""
        try:
            # 優先查找 tree_structure.txt
            tree_file = os.path.join(report_folder, "tree_structure.txt")
            
            if os.path.exists(tree_file):
                with open(tree_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.clear_screen()
                print("\n📂 最新整理報告")
                print("=" * 16)
                print()
                print(content)
            else:
                self.clear_screen()
                print("\n📂 最新整理報告")
                print("=" * 16)
                print(f"\n報告資料夾: {os.path.basename(report_folder)}")
                print("找不到 tree_structure.txt 檔案")
            
            options = ["返回主選單", "退出程式"]
            self.selected_index = 0
            choice = self.show_menu("", options)
            
            if choice == 0:
                return  # 返回主選單
            else:
                self.clear_screen()
                print("\n感謝使用 FileOrg！")
                sys.exit(0)
                
        except Exception as e:
            self.clear_screen()
            print(f"\n❌ 無法讀取報告: {e}")
            input("\n按 Enter 繼續...")

    def find_latest_report_folder(self, target_path):
        """查找最近期的報告資料夾"""
        try:
            backup_dir = os.path.join(target_path, ".tidy_report")
            if not os.path.exists(backup_dir):
                return None
            
            # 找到所有時間戳記格式的資料夾
            timestamp_folders = []
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if os.path.isdir(item_path):
                    # 檢查是否是時間戳記格式 (例如: 20250827_143022)
                    if len(item) >= 8 and ('_' in item or item.replace('_', '').isdigit()):
                        timestamp_folders.append((item, item_path))
            
            if timestamp_folders:
                # 按時間戳記排序，取最新的
                latest_folder = sorted(timestamp_folders, reverse=True)[0][1]
                return latest_folder
        
        except Exception:
            pass
        
        return None

    def show_restore_completion(self, target_path):
        """顯示還原完成的資訊"""
        self.clear_screen()
        print("\n✅ 檔案還原完成！")
        print("=" * 16)
        
        print(f"\n📁 還原目錄: {target_path}")
        print("\n📋 已執行的操作:")
        print("   • 檔案已還原到整理前的原始位置")
        print("   • 自動建立的資料夾結構已清理")
        print("   • 備份檔案仍保留供日後參考")
        
        backup_dir = os.path.join(target_path, ".backup")
        if os.path.exists(backup_dir):
            print(f"\n💡 備份資料夾位置:")
            print(f"   {backup_dir}")
            print(f"   • 包含整理報告和操作記錄")
            print(f"   • 可安全刪除，但建議保留作為記錄")
        
        print(f"\n🔄 如需重新整理:")
        print(f"   • 可再次使用 'fileorg start' 進行整理")
        print(f"   • 或使用命令行: 'fileorg \"{target_path}\" --preview'")
    
    def show_preview_results(self, results):
        """顯示預覽結果"""
        self.clear_screen()
        print("\n預覽結果")
        print("=" * 8)
        
        folder_mappings = results.get("folder_mappings", {})
        
        print(f"\n建議分類為 {len(folder_mappings)} 個資料夾:")
        for folder, files in folder_mappings.items():
            print(f"\n📁 {folder} ({len(files)} 個檔案)")
            # 只顯示前 3 個檔案，避免螢幕過長
            for file in files[:3]:
                print(f"   • {os.path.basename(file)}")
            if len(files) > 3:
                print(f"   ... 還有 {len(files) - 3} 個檔案")
        
        print(f"\n分類時間: {results.get('classification_time', 'N/A')}")
        
        options = ["確認執行整理", "取消"]
        self.selected_index = 0
        
        choice = self.show_menu("", options)
        return choice == 0 if choice is not None else False

def start_gui():
    """啟動 GUI 模式"""
    gui = TerminalGUI()
    
    # 延遲載入主要模組
    # from fileorg.core.organizer import Organizer
    from fileorg.core.mock_organizer import MockOrganizer
    from fileorg.restore.restore_folder import restore_folder
    
    while True:
        # 檢查是否有歷史記錄
        history = gui.load_history()
        has_history = len(history) > 0
        
        # 主選單 - 根據歷史記錄動態調整選項
        main_options = ["輸入檔案路徑"]
        
        if has_history:
            main_options.append("選擇歷史路徑")
        
        main_options.append("退出程式")
        
        gui.selected_index = 0
        main_choice = gui.show_menu("FileOrg 智慧檔案整理工具", main_options)
        
        if main_choice is None or main_choice == len(main_options) - 1:  # 退出
            gui.clear_screen()
            print("\n感謝使用 FileOrg！")
            break
        
        target_path = None
        
        if main_choice == 0:  # 輸入路徑
            target_path = gui.input_path()
        elif has_history and main_choice == 1:  # 查看歷史
            target_path = gui.show_history()
        
        if target_path is None:
            continue
        
        # 檢查是否有備份可以還原
        backup_exists = False
        try:
            backup_file = os.path.join(target_path, ".backup", "file_paths.json")
            backup_exists = os.path.exists(backup_file)
        except:
            pass
        
        # 模式選單
        mode_options = ["預覽模式 (安全預覽，不移動檔案)", "確認執行整理"]
        
        if backup_exists:
            mode_options.append("還原到原始狀態")
        
        mode_options.append("返回主選單")
        
        gui.selected_index = 0
        mode_choice = gui.show_menu(f"選擇操作模式\n路徑: {target_path}", mode_options)
        
        if mode_choice is None or mode_choice == len(mode_options) - 1:
            continue
        
        try:
            if mode_choice == 0:  # 預覽模式
                gui.clear_screen()
                print("\n正在執行預覽模式...")
                print("掃描和分析檔案中，請稍候...")
                
                # 執行預覽
                # organizer = Organizer()
                organizer = MockOrganizer()
                organizer.target_path = target_path
                os.makedirs(os.path.join(target_path, ".backup"), exist_ok=True)
                
                # 掃描檔案
                scanner_result = organizer._file_scanner()
                print(f"找到 {len(scanner_result)} 個檔案")
                
                # 解析檔案
                file_parsed = organizer._file_parser(scanner_result=scanner_result, save_result=True)
                
                # 生成資料夾結構
                generate_result = organizer._generate_folder(
                    file_parsed, base_output_dir=target_path, save_result=True, generate_report=True
                )
                
                # 顯示預覽結果並確認
                if gui.show_preview_results(generate_result):
                    gui.clear_screen()
                    print("\n正在執行檔案整理...")
                    
                    # 套用備份結構
                    backup_data = None
                    backup_file = os.path.join(target_path, ".backup", "file_paths.json")
                    try:
                        with open(backup_file, "r", encoding="utf-8") as f:
                            backup_data = json.load(f)
                    except Exception as e:
                        print(f"載入備份資料時發生錯誤: {e}")
                        continue
                    
                    if backup_data:
                        file_paths = backup_data.get("file_paths", [])
                        moved_count = 0
                        
                        for file_info in file_paths:
                            original_path = os.path.normpath(file_info["original"])
                            new_path = os.path.normpath(file_info["new"])
                            
                            if os.path.exists(original_path):
                                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                                try:
                                    import shutil
                                    shutil.move(original_path, new_path)
                                    moved_count += 1
                                except Exception as e:
                                    print(f"移動失敗 {original_path}: {e}")
                        
                        print(f"\n✅ 檔案整理完成！已移動 {moved_count}/{len(file_paths)} 個檔案")
                        
                        # 顯示報告位置
                        gui.show_completion_report(target_path)
                        
                        # 儲存歷史記錄
                        report_path = os.path.join(target_path, ".backup", "organization_report.md")
                        gui.save_history(target_path, report_path if os.path.exists(report_path) else None)
                
                input("\n按 Enter 繼續...")
            
            elif mode_choice == 1:  # 直接執行
                if gui.confirm_action("確認執行檔案整理", f"路徑: {target_path}\n\n這將會移動檔案到新的資料夾結構中"):
                    gui.clear_screen()
                    print("\n正在執行檔案整理...")
                    
                    # organizer = Organizer()
                    organizer = MockOrganizer()
                    organizer.start_organize(target_path)
                    
                    print("\n✅ 檔案整理完成！")
                    
                    # 顯示報告位置
                    gui.show_completion_report(target_path)
                    
                    # 儲存歷史記錄
                    report_path = os.path.join(target_path, ".backup", "organization_report.md")
                    gui.save_history(target_path, report_path if os.path.exists(report_path) else None)
                    
                    input("\n按 Enter 繼續...")
            
            elif mode_choice == 2 and backup_exists:  # 還原
                if gui.confirm_action("確認還原檔案", f"路徑: {target_path}\n\n這將會把檔案還原到整理前的位置"):
                    gui.clear_screen()
                    print("\n正在還原檔案...")
                    
                    restore_folder(target_path)
                    
                    print("\n✅ 檔案還原完成！")
                    
                    # 顯示還原完成資訊
                    gui.show_restore_completion(target_path)
                    
                    input("\n按 Enter 繼續...")
        
        except Exception as e:
            gui.clear_screen()
            print(f"\n❌ 執行過程中發生錯誤: {str(e)}")
            input("\n按 Enter 繼續...")


if __name__ == "__main__":
    """
    使用範例:
    - GUI 模式: python -m fileorg.gui.usercli
    - 或透過主 CLI: fileorg start
    """
    start_gui()