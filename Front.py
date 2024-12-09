import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk, filedialog, Frame
import subprocess
import json
import urllib.parse
import shutil
from ttkthemes import ThemedTk

systems_data = []
selected_file_path = ""

def run_curl():
    global systems_data 
    try:
        curl_path = shutil.which("curl")
        if curl_path is None:
            messagebox.showerror("Error", "CURL не встановлено або не знайдено.")
            return

        result = subprocess.run([curl_path, "http://127.0.0.1:5000/get_systems_list"], capture_output=True, text=True)

        output_display.delete(1.0, tk.END)
        if result.stdout:
            output_display.insert(tk.END, result.stdout)
            
            try:
                response_data = json.loads(result.stdout)
                if isinstance(response_data, dict) and "systems" in response_data:
                    systems_data = response_data["systems"]
                    systems_combobox['values'] = systems_data
                    if systems_data:
                        systems_combobox.current(0)
                else:
                    messagebox.showerror("Error", "Неправильний формат даних. Очікувався словник із ключем 'systems'.")
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Неможливо розпізнати відповідь як JSON.")
        else:
            output_display.insert(tk.END, "Систем з нечіткою логікою у базі даних не знайдено")
    except Exception as e:
        messagebox.showerror("Error", f"Помилка під час виконання запиту CURL: {e}")


def get_fml_file():
    selected_system = systems_combobox.get()  
    if selected_system:
        encoded_system = urllib.parse.quote(selected_system)  
        try:

            url = f"http://127.0.0.1:5000/get_fml_file/{encoded_system}"

            result = subprocess.run(["curl", url], capture_output=True, text=True)
            
            output_display.delete(1.0, tk.END)
            if result.stdout:
                output_display.insert(tk.END, result.stdout)
            else:
                output_display.insert(tk.END, "Систем з нечіткою логікою у базі даних не знайдено")
        except Exception as e:
            messagebox.showerror("Error", f"Помилка під час виконання запиту CURL: {e}")
    else:
        messagebox.showwarning("Warning", "Будь ласка, виберіть систему.")


def delete_one_system():
    selected_system = systems_combobox.get()  
    if selected_system:
        encoded_system = urllib.parse.quote(selected_system)  
        try:
            url = f"http://127.0.0.1:5000/delete_one_system/{encoded_system}"
            result = subprocess.run(["curl", "-X", "DELETE", url], capture_output=True, text=True)

            output_display.delete(1.0, tk.END)
            if result.stdout:
                output_display.insert(tk.END, result.stdout)
            else:
                output_display.insert(tk.END, "Error: No response from server.")
        except Exception as e:
            messagebox.showerror("Error", f"Помилка під час виконання запиту CURL: {e}")
    else:
        messagebox.showwarning("Warning", "Будь ласка, виберіть систему.")

def select_file():
    global selected_file_path 
    selected_file_path = filedialog.askopenfilename(
        title="Оберіть файл",
        filetypes=(("XML files", "*.xml"), ("All files", "*.*"))
    )
    if selected_file_path:
        output_display.delete(1.0, tk.END)
        output_display.insert(tk.END, f"обраний файл {selected_file_path}")

def save_to_file():
    file_path = filedialog.asksaveasfilename(
        title="Зберегти як",
        defaultextension=".txt",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(output_display.get(1.0, tk.END)) 
            messagebox.showinfo("Saving", "Файл успішно збережено.")
        except Exception as e:
            messagebox.showerror("Error", f"Не вдалось зберегти файл: {e}")

def upload_fml_file():
    if selected_file_path:
        try:
            url = "http://127.0.0.1:5000/put_fml_file"
            data = json.dumps({"file_path": selected_file_path})
            result = subprocess.run(
                ["curl", "-X", "PUT", "-H", "Content-Type: application/json", "-d", data, url],
                capture_output=True,
                text=True
            )
            output_display.delete(1.0, tk.END)
            output_display.insert(tk.END, f"завантажено файл {selected_file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Помилка під час виконання запиту CURL: {e}")
    else:
        messagebox.showwarning("Warning", "Виберіть файл.")

def delete_systems():
    selected_system = systems_combobox.get()
    
    if selected_system:
        confirm = messagebox.askyesno("Підтвердження видалення", "Ви впевнені, що хочете видалити всі системи?")
        
        if confirm:
            encoded_system = urllib.parse.quote(selected_system)
            try:
                url = f"http://127.0.0.1:5000/delete_systems_list"
                
                result = subprocess.run(["curl", "-X", "DELETE", url], capture_output=True, text=True)
                
                output_display.delete(1.0, tk.END)
                if result.stdout:
                    output_display.insert(tk.END, result.stdout)
                else:
                    output_display.insert(tk.END, "Помилка: Немає відповіді сервера.")
            except Exception as e:
                messagebox.showerror("Error", f"Помилка під час виконання CURL запиту: {e}")
    else:
        messagebox.showwarning("Warning", "Будь ласка, виберіть систему.")

root = ThemedTk(theme="scidpink")
root.config(bg="#2b2b2b") 
root.title("FML Manager")
root.minsize(800, 400)

button_width = 20
button_pady = 5
left_frame = Frame(root, bg="#2b2b2b")
right_frame = Frame(root, bg="#2b2b2b") 

output_display = scrolledtext.ScrolledText(left_frame, width=60, height=15)
output_display.pack(padx=10, pady=10, fill="both", expand=True)

systems_combobox = ttk.Combobox(right_frame, state="readonly", width=50)
systems_combobox.pack(pady=25, padx=10)

curl_button = ttk.Button(right_frame, text="Show systems", command=run_curl, width=button_width)
curl_button.pack(pady=button_pady, padx=10)

get_fml_button = ttk.Button(right_frame, text="Show current system", command=get_fml_file, width=button_width)
get_fml_button.pack(pady=button_pady, padx=10)

delete_button = ttk.Button(right_frame, text="Delete current system", command=delete_one_system, width=button_width)
delete_button.pack(pady=button_pady, padx=10)

delete_systems_button = ttk.Button(right_frame, text="Delete all systems", command=delete_systems, width=button_width)
delete_systems_button.pack(pady=button_pady, padx=10)

upload_button = ttk.Button(right_frame, text="Upload file", command=upload_fml_file, width=button_width)
upload_button.pack(pady=button_pady, padx=10)

select_file_button = ttk.Button(right_frame, text="File path", command=select_file, width=button_width)
select_file_button.pack(pady=button_pady, padx=10)

save_button = ttk.Button(right_frame, text="Download file", command=save_to_file, width=button_width)
save_button.pack(pady=button_pady, padx=10)

left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

run_curl()

root.mainloop()