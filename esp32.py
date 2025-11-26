import customtkinter
import esptool
import serial.tools.list_ports
import threading
import os

# --- UI এবং esptool এর কনফিগারেশন ---
customtkinter.set_appearance_mode("Dark") 
customtkinter.set_default_color_theme("blue") 

class ESPFlasherApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- উইন্ডো কনফিগারেশন ---
        self.title("✨ Futura ESP Flasher (Advanced)")
        self.geometry("900x700")
        
        # গ্রিড লেআউট কনফিগারেশন 
        self.grid_rowconfigure((0, 1), weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- ফ্রেম তৈরি ---
        
        # ১. সেটিংস ফ্রেম (পোর্ট, ফাইল, বাটন)
        self.settings_frame = customtkinter.CTkFrame(self)
        self.settings_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        self.settings_frame.columnconfigure((0, 1, 2, 3, 4, 5), weight=1) # 6 কলামে ভাগ

        # ২. লগ ফ্রেম
        self.log_frame = customtkinter.CTkFrame(self)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)

        self.setup_settings_widgets()
        self.setup_log_widgets()
        
    def setup_settings_widgets(self):
        # --- সেটিংস ফ্রেম উইজেটস ---
        
        # Row 0: পোর্ট সিলেক্টর এবং রিফ্রেশ
        self.port_label = customtkinter.CTkLabel(self.settings_frame, text="Serial Port:", font=("Roboto", 14, "bold"))
        self.port_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.port_var = customtkinter.StringVar(value="Select Port")
        self.port_menu = customtkinter.CTkOptionMenu(self.settings_frame, values=["No Ports Found"], variable=self.port_var)
        self.port_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.refresh_button = customtkinter.CTkButton(self.settings_frame, text="🔄 Refresh", command=self.refresh_ports)
        self.refresh_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        # New Feature: Chip Info Button
        self.chip_info_button = customtkinter.CTkButton(self.settings_frame, text="🔍 Get Chip Info", fg_color="#FFB300", hover_color="#CC8400", command=self.start_chip_info_thread)
        self.chip_info_button.grid(row=0, column=4, padx=10, pady=10, columnspan=2, sticky="e")

        # Row 1: ফাইল সিলেক্টর (ফার্মওয়্যার)
        self.file_label = customtkinter.CTkLabel(self.settings_frame, text="Firmware File:", font=("Roboto", 14, "bold"))
        self.file_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.file_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="Path/to/firmware.bin")
        self.file_entry.grid(row=1, column=1, padx=10, pady=10, columnspan=4, sticky="ew")
        
        self.browse_button = customtkinter.CTkButton(self.settings_frame, text="📁 Browse", command=self.browse_file)
        self.browse_button.grid(row=1, column=5, padx=10, pady=10, sticky="w")
        
        # Row 2: ফ্ল্যাশ অ্যাড্রেস
        self.addr_label = customtkinter.CTkLabel(self.settings_frame, text="Flash Address (Hex):", font=("Roboto", 14, "bold"))
        self.addr_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.addr_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="0x1000")
        self.addr_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self.addr_entry.insert(0, "0x1000") 

        # Row 3: অ্যাডভান্সড ফ্ল্যাশ অপশনস (Baud Rate, Mode, Freq)

        # Baud Rate
        self.baud_label = customtkinter.CTkLabel(self.settings_frame, text="Baud Rate:", font=("Roboto", 14, "bold"))
        self.baud_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.baud_var = customtkinter.StringVar(value="460800")
        self.baud_menu = customtkinter.CTkOptionMenu(self.settings_frame, values=["115200", "460800", "921600"], variable=self.baud_var)
        self.baud_menu.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        # Flash Mode
        self.mode_label = customtkinter.CTkLabel(self.settings_frame, text="Flash Mode:", font=("Roboto", 14, "bold"))
        self.mode_label.grid(row=3, column=2, padx=10, pady=10, sticky="w")
        self.mode_var = customtkinter.StringVar(value="dio")
        self.mode_menu = customtkinter.CTkOptionMenu(self.settings_frame, values=["dio", "qio", "dout", "qout"], variable=self.mode_var)
        self.mode_menu.grid(row=3, column=3, padx=10, pady=10, sticky="ew")

        # Flash Frequency
        self.freq_label = customtkinter.CTkLabel(self.settings_frame, text="Flash Freq:", font=("Roboto", 14, "bold"))
        self.freq_label.grid(row=3, column=4, padx=10, pady=10, sticky="w")
        self.freq_var = customtkinter.StringVar(value="40m")
        self.freq_menu = customtkinter.CTkOptionMenu(self.settings_frame, values=["40m", "80m"], variable=self.freq_var)
        self.freq_menu.grid(row=3, column=5, padx=10, pady=10, sticky="ew")

        # Row 4: ফ্ল্যাশ বাটন
        self.flash_button = customtkinter.CTkButton(self.settings_frame, 
                                                    text="⚡ Start Flash", 
                                                    font=("Roboto", 18, "bold"),
                                                    fg_color="#00AEEF", 
                                                    hover_color="#0080C0",
                                                    command=self.start_flashing_thread)
        self.flash_button.grid(row=4, column=0, columnspan=4, padx=10, pady=20, sticky="ew")

        # New Feature: Erase Button
        self.erase_button = customtkinter.CTkButton(self.settings_frame, 
                                                    text="⚠️ Erase Chip", 
                                                    font=("Roboto", 18, "bold"),
                                                    fg_color="#CC0000", 
                                                    hover_color="#990000",
                                                    command=self.start_erase_thread)
        self.erase_button.grid(row=4, column=4, columnspan=2, padx=10, pady=20, sticky="ew")

    def setup_log_widgets(self):
        # --- লগ ফ্রেম উইজেটস ---
        self.log_label = customtkinter.CTkLabel(self.log_frame, text="Activity Log", font=("Roboto", 16, "bold"))
        self.log_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # লগ টেক্সট বক্স
        self.log_text = customtkinter.CTkTextbox(self.log_frame, wrap="word", state="disabled", height=300)
        self.log_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    # --- ইউটিলিটি ফাংশন ---

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        if not port_list:
            return ["No Ports Found"]
        return port_list

    def refresh_ports(self):
        new_ports = self.get_serial_ports()
        self.port_menu.configure(values=new_ports)
        if new_ports and new_ports[0] != "No Ports Found":
             self.port_var.set(new_ports[0])
        else:
            self.port_var.set("No Ports Found")
        self.log_message("Port list refreshed.")
        
    def browse_file(self):
        import tkinter
        file_path = tkinter.filedialog.askopenfilename(
            defaultextension=".bin",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        if file_path:
            self.file_entry.delete(0, customtkinter.END)
            self.file_entry.insert(0, file_path)
            self.log_message(f"Firmware File Selected: {os.path.basename(file_path)}")

    def log_message(self, message, tag=None):
        self.log_text.configure(state="normal")
        
        # কালার কোডিং এর জন্য ট্যাগ সেটআপ (ফিউচারিস্টিক লুক)
        if tag == "SUCCESS":
            color = "#39FF14" # Neon Green
        elif tag == "ERROR":
            color = "#FF073A" # Bright Red
        elif tag == "INFO":
            color = "#00BFFF" # Deep Sky Blue
        else:
            color = "#FFFFFF" # Default White
            
        self.log_text.tag_config(tag or "default", foreground=color)
        self.log_text.insert("end", f"[{threading.current_thread().name}] {message}\n", tag or "default")
        
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # --- চিপ ইনফো লজিক ---

    def chip_info_worker(self):
        """চিপ তথ্য পড়ার জন্য esptool চালায়।"""
        port = self.port_var.get()

        if port in ("Select Port", "No Ports Found"):
            self.log_message("ERROR: Please select a valid port before reading chip info.", tag="ERROR")
            self.chip_info_button.configure(state="normal", text="🔍 Get Chip Info")
            return
            
        self.log_message("\n>>> Attempting to read Chip Info...", tag="INFO")
        
        try:
            # esptool.main() ব্যবহার করে flash_id এবং read_mac একসাথে চালানো
            args = [
                '--port', port,
                'flash_id' 
            ]
            
            # Note: The actual esptool.main() will print directly to the console (stdout/stderr).
            # For a fully contained GUI, you would need to redirect stdout/stderr.
            # Here we rely on the main function of esptool to execute the task.
            
            self.log_message("Executing 'esptool flash_id'...", tag="INFO")
            esptool.main(args)
            
            self.log_message("\n*** Chip Info Read Complete. Check your console output or log above. ***", tag="SUCCESS")

        except esptool.FatalError as e:
            self.log_message(f"\n!!! ERROR: Failed to connect or read chip info: {e} !!!", tag="ERROR")
        except Exception as e:
             self.log_message(f"\n!!! AN UNEXPECTED ERROR OCCURRED during Chip Info: {e} !!!", tag="ERROR")
        finally:
            self.chip_info_button.configure(state="normal", text="🔍 Get Chip Info")


    def start_chip_info_thread(self):
        """চিপ ইনফো পড়ার জন্য নতুন থ্রেড শুরু করে।"""
        self.chip_info_button.configure(state="disabled", text="Reading...")
        chip_thread = threading.Thread(target=self.chip_info_worker, name="ChipInfoThread")
        chip_thread.start()

    # --- ইরেজ লজিক ---

    def erase_worker(self):
        """সম্পূর্ণ চিপ মুছে ফেলার জন্য esptool চালায়।"""
        port = self.port_var.get()
        
        if port in ("Select Port", "No Ports Found"):
            self.log_message("ERROR: Please select a valid port before erasing.", tag="ERROR")
            self.erase_button.configure(state="normal", text="⚠️ Erase Chip")
            return
            
        self.log_message("\n>>> WARNING: Starting Full Chip Erase Process...", tag="ERROR")

        try:
            # esptool CLI কমান্ড আর্গুমেন্ট 
            args = [
                '--port', port,
                'erase_flash'
            ]
            
            self.log_message("Executing 'esptool erase_flash'...", tag="INFO")
            esptool.main(args)
            
            self.log_message("\n*** CHIP ERASE SUCCESSFUL! ***", tag="SUCCESS")

        except esptool.FatalError as e:
            self.log_message(f"\n!!! ERROR: Chip Erase FAILED: {e} !!!", tag="ERROR")
        except Exception as e:
             self.log_message(f"\n!!! AN UNEXPECTED ERROR OCCURRED during Erase: {e} !!!", tag="ERROR")
        finally:
            self.erase_button.configure(state="normal", text="⚠️ Erase Chip")
            self.log_message(">>> Erase process finished.")


    def start_erase_thread(self):
        """ইরেজ করার জন্য নতুন থ্রেড শুরু করে। (কনফার্মেশন যুক্ত করা উচিত)"""
        # Note: In a real app, a confirmation dialog (Tkinter messagebox) should be used here!
        self.erase_button.configure(state="disabled", text="Erasing...")
        erase_thread = threading.Thread(target=self.erase_worker, name="EraseThread")
        erase_thread.start()

    # --- ফ্ল্যাশিং লজিক ---

    def flash_worker(self):
        """ফ্ল্যাশিং এর জন্য esptool চালায়।"""
        port = self.port_var.get()
        firmware_file = self.file_entry.get()
        flash_addr = self.addr_entry.get()
        baud_rate = self.baud_var.get()
        flash_mode = self.mode_var.get()
        flash_freq = self.freq_var.get()

        if port in ("Select Port", "No Ports Found") or not firmware_file or not flash_addr:
            self.log_message("ERROR: Please select all required settings.", tag="ERROR")
            self.flash_button.configure(state="normal", text="⚡ Start Flash")
            return

        self.log_message(f"\n>>> Starting Flash Process...", tag="INFO")
        self.log_message(f"Baud: {baud_rate}, Mode: {flash_mode}, Freq: {flash_freq}", tag="INFO")
        
        try:
            # esptool CLI কমান্ড আর্গুমেন্ট 
            args = [
                '--port', port,
                '--baud', baud_rate,
                'write_flash',
                '--flash_mode', flash_mode,
                '--flash_freq', flash_freq,
                flash_addr, firmware_file
            ]
            
            self.log_message("Executing esptool.main()...", tag="INFO")
            esptool.main(args)
            
            self.log_message("\n*** FLASHING SUCCESSFUL! ***", tag="SUCCESS")

        except esptool.FatalError as e:
            self.log_message(f"\n!!! FLASHING FAILED: {e} !!!", tag="ERROR")
        except Exception as e:
             self.log_message(f"\n!!! AN UNEXPECTED ERROR OCCURRED: {e} !!!", tag="ERROR")
        finally:
            self.flash_button.configure(state="normal", text="⚡ Start Flash")
            self.log_message(">>> Flash process finished.")

    def start_flashing_thread(self):
        """UI ফ্রিজ না করে ফ্ল্যাশিং শুরু করার জন্য নতুন থ্রেড তৈরি করে।"""
        self.flash_button.configure(state="disabled", text="Flashing... Please Wait")
        flash_thread = threading.Thread(target=self.flash_worker, name="FlasherThread")
        flash_thread.start()


if __name__ == "__main__":
    app = ESPFlasherApp()
    app.refresh_ports()
    app.mainloop()