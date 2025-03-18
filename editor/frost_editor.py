import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import sys
import os
import random

class JSONEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Frost Editor")
        self.root.geometry("1000x700")
        self.json_data = []
        self.node_positions = {}
        self.custom_forms = {}
        self.indent_level = 4
        self.theme = "dark"  # Default theme
        
        # Set the window icon
        if getattr(sys, 'frozen', False):  # Running as compiled executable
            base_path = sys._MEIPASS  # Temp directory where PyInstaller extracts files
        else:  # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "1.png")
        try:
            icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, icon)
        except tk.TclError as e:
            print(f"Failed to load icon: {e}")

        # Configure styles for professional look
        self.style = ttk.Style()
        self.setup_themes()

        # Initialize category_menus for form submenus
        self.category_menus = {}  # Add this line

        # Menu bar
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.load_json)
        file_menu.add_command(label="Save", command=self.save_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)

        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Sort Tree", command=self.sort_tree)

        self.forms_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Forms", menu=self.forms_menu)
        self.forms_menu.add_command(label="Add Custom Form", command=self.add_custom_form)
        self.forms_menu.add_command(label="Load Saved Forms", command=self.load_saved_forms)

        theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Light Mode", command=lambda: self.switch_theme("light"))
        theme_menu.add_command(label="Dark Mode", command=lambda: self.switch_theme("dark"))

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Main layout with padding
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Paned window
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Treeview frame
        self.tree_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tree_frame, weight=1)
        self.tree = ttk.Treeview(self.tree_frame, style="Frost.Treeview")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree_context_menu = tk.Menu(self.root, tearoff=0)
        self.tree_context_menu.add_command(label="Open", command=self.open_in_text)
        self.tree_context_menu.add_command(label="Delete", command=self.delete_tree_item)
        self.tree.bind("<Button-3>", self.show_tree_context_menu)

        # Text frame
        self.text_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.text_frame, weight=1)
        self.text = tk.Text(self.text_frame, wrap="none", font=("Segoe UI", 10))
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text_context_menu = tk.Menu(self.root, tearoff=0)
        self.text_context_menu.add_command(label="Delete", command=self.delete_text_item)
        self.text.bind("<Button-3>", self.show_text_context_menu)

        # Search bar
        self.search_frame = ttk.Frame(self.main_frame, padding="5")
        self.search_frame.pack(fill=tk.X)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.search_tree())
        ttk.Button(self.search_frame, text="Search", command=self.search_tree).pack(side=tk.LEFT)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Forms folder setup
        script_dir = os.path.dirname(os.path.abspath(__file__))  # /home/mona/snowcaller/editor
        self.forms_folder = os.path.join(script_dir, "custom_forms")  # /home/mona/snowcaller/editor/custom_forms
        print(f"Forms folder set to: {self.forms_folder}")  # Debug to confirm
        if not os.path.exists(self.forms_folder):
            os.makedirs(self.forms_folder)
        self.load_saved_forms()

        # Apply theme AFTER all widgets are initialized
        self.apply_theme()

    def setup_themes(self):
        # Nicer Frosted Light Theme
        self.style.theme_create("frosted_light", parent="clam", settings={
            "TFrame": {"configure": {"background": "#ECF2FF"}},  # Softer blue-white
            "TPanedWindow": {"configure": {"background": "#D8E2FF"}},  # Gentle gradient effect
            "TLabel": {"configure": {"background": "#ECF2FF", "foreground": "#355070"}},  # Muted navy
            "TButton": {"configure": {"background": "#B8CCFF", "foreground": "#355070", "padding": 4}},  # Softer blue
            "TEntry": {"configure": {"fieldbackground": "#F8FAFF", "foreground": "#355070"}},
            "Frost.Treeview": {
                "configure": {"background": "#ECF2FF", "foreground": "#355070", "fieldbackground": "#ECF2FF"},
                "map": {"background": [("selected", "#A3BFFA")]}  # Light purple-blue selection
            }
        })

        # Nicer Frosted Dark Theme
        self.style.theme_create("frosted_dark", parent="clam", settings={
            "TFrame": {"configure": {"background": "#2A3555"}},  # Deep blue-gray
            "TPanedWindow": {"configure": {"background": "#3A4566"}},  # Slightly lighter
            "TLabel": {"configure": {"background": "#2A3555", "foreground": "#D9E0FF"}},  # Light purple-white
            "TButton": {"configure": {"background": "#4A5588", "foreground": "#D9E0FF", "padding": 4}},
            "TEntry": {"configure": {"fieldbackground": "#3E4A70", "foreground": "#D9E0FF"}},
            "Frost.Treeview": {
                "configure": {"background": "#2A3555", "foreground": "#D9E0FF", "fieldbackground": "#2A3555"},
                "map": {"background": [("selected", "#6B7FAA")]}  # Muted blue selection
            }
        })

    def apply_theme(self):
        self.style.theme_use(f"frosted_{self.theme}")
        self.root.configure(bg="#ECF2FF" if self.theme == "light" else "#2A3555")
        self.text.configure(bg="#F8FAFF" if self.theme == "light" else "#3E4A70",
                           fg="#355070" if self.theme == "light" else "#D9E0FF",
                           insertbackground="#355070" if self.theme == "light" else "#D9E0FF")  # Cursor color

    def switch_theme(self, theme):
        self.theme = theme
        self.apply_theme()
        self.status_var.set(f"Switched to Frosted {theme.capitalize()} Mode")

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About Frost Editor")
        about_window.geometry("400x400")
        about_window.configure(bg="#F0F6FF" if self.theme == "light" else "#2C3E50")

        canvas = tk.Canvas(about_window, width=400, height=200,
                          bg="#A9CCE3" if self.theme == "light" else "#34495E", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        snowflakes = []
        for _ in range(50):
            x = random.randint(0, 400)
            y = random.randint(0, 200)
            size = random.randint(2, 5)
            snowflakes.append(canvas.create_oval(x, y, x+size, y+size, fill="white"))

        def animate_snow():
            for flake in snowflakes:
                canvas.move(flake, random.randint(-1, 1), random.randint(1, 3))
                x1, y1, x2, y2 = canvas.coords(flake)
                if y2 > 200:
                    canvas.coords(flake, x1, -5, x2, -5 + (x2-x1))
            about_window.after(50, animate_snow)

        animate_snow()

        about_text = (
            "Frost Editor\n"
            "Version 0.0.6.3\n"
            "Created by Mona\n"
            "A JSON editor with a frosty twist.\n"
            "Credit to Elara for inspiration."
        )
        ttk.Label(about_window, text=about_text, justify=tk.CENTER,
                 background="#F0F6FF" if self.theme == "light" else "#2C3E50",
                 foreground="#2C3E50" if self.theme == "light" else "#ECF0F1").pack(pady=10)

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                self.detect_indent(lines)
                f.seek(0)
                self.json_data = json.load(f)
                self.update_views()
            self.current_file = file_path
            self.status_var.set(f"Loaded: {os.path.basename(file_path)}")

    def detect_indent(self, lines):
        for line in lines:
            stripped = line.lstrip()
            if stripped and stripped.startswith(('{', '[')):  # Look at first indented line
                indent = len(line) - len(stripped)
                if indent > 0:
                    self.indent_level = indent  # Set detected indent (e.g., 2 or 4 spaces)
                    break

    def save_json(self):
        json_text = self.text.get("1.0", tk.END).strip()  # Get raw text from widget
        try:
            # Validate JSON first
            self.json_data = json.loads(json_text)
            # If valid, proceed to save
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(self.json_data, f, indent=self.indent_level)
                messagebox.showinfo("Success", "JSON is valid and saved successfully!")
                self.current_file = file_path
                self.status_var.set(f"Saved: {os.path.basename(file_path)} - JSON Valid")
        except json.JSONDecodeError as e:
            # If invalid, show error with details
            error_msg = f"Invalid JSON: {str(e)}"
            messagebox.showerror("Validation Error", error_msg)
            self.status_var.set("Error: Invalid JSON - Save Failed")
        except Exception as e:
            # Catch other potential errors (e.g., file I/O issues)
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            self.status_var.set("Error: Save Failed")


    def update_views(self):
        self.tree.delete(*self.tree.get_children())
        self.text.delete("1.0", tk.END)
        self.node_positions.clear()
        json_text = json.dumps(self.json_data, indent=self.indent_level)
        self.text.insert("1.0", json_text)
    
        root_node = self.tree.insert("", "end", text="Root", values=("Object",))
        self.node_positions[root_node] = "1.0"
    
        if isinstance(self.json_data, dict):
            # Check for a primary list to prioritize (e.g., "monsters", "dialogue")
            primary_list = None
            primary_key = None
            for key, value in self.json_data.items():
                if isinstance(value, list) and len(value) > 0:
                    primary_list = value
                    primary_key = key
                    break
        
            if primary_list:
                list_node = self.tree.insert(root_node, "end", text=primary_key, values=("List",))
                self.node_positions[list_node] = self.text.search(f'"{primary_key}"', "1.0", tk.END) or "2.0"
                for i, item in enumerate(primary_list):
                    # Use "name", "quest", or similar as node text if available
                    node_text = item.get("name", item.get("quest", f"{primary_key} {i}")) if isinstance(item, dict) else f"{primary_key} {i}"
                    node = self.tree.insert(list_node, "end", text=node_text, values=(i,))
                    self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 3}.0"
                    self._populate_tree(node, item)
            else:
                # Fallback to full dictionary population
                self._populate_tree(root_node, self.json_data)
        elif isinstance(self.json_data, list):
            # Direct list at root
            for i, item in enumerate(self.json_data):
                node_text = item.get("name", item.get("quest", f"Item {i}")) if isinstance(item, dict) else f"Item {i}"
                node = self.tree.insert(root_node, "end", text=node_text, values=(i,))
                self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 2}.0"
                self._populate_tree(node, item)

    def show_tree_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_context_menu.post(event.x_root, event.y_root)

    def show_text_context_menu(self, event):
        self.text_context_menu.post(event.x_root, event.y_root)

    def open_in_text(self):
        item = self.tree.selection()[0]
        if item in self.node_positions:
            pos = self.node_positions[item]
            self.text.see(pos)
            self.text.mark_set("insert", pos)
            line_start = f"{pos.split('.')[0]}.0"
            line_end = f"{pos.split('.')[0]}.end"
            self.text.tag_remove("highlight", "1.0", tk.END)
            self.text.tag_add("highlight", line_start, line_end)
            self.text.tag_configure("highlight", background="yellow")

    def delete_tree_item(self):
        item = self.tree.selection()[0]
        parent = self.tree.parent(item)
        key = self.tree.item(item, "text")

        if parent == "":
            if key in self.json_data:
                del self.json_data[key]
        else:
            parent_data = self._get_data_from_path(parent)
            if isinstance(parent_data, dict) and key in parent_data:
                del parent_data[key]
            elif isinstance(parent_data, list) and key.startswith("["):
                index = int(key[1:-1])
                parent_data.pop(index)
        self.update_views()

    def delete_text_item(self):
        # Get the line under the cursor
        cursor_pos = self.text.index(tk.INSERT)
        line_start = f"{cursor_pos.split('.')[0]}.0"
        line_end = f"{cursor_pos.split('.')[0]}.end"
        line_text = self.text.get(line_start, line_end).strip()

        # Extract the key from the line (assumes format like "key": value)
        if '":' in line_text:
            key = line_text.split('":')[0].strip().strip('"')
            if key in self.json_data:
                del self.json_data[key]
                self.update_views()
            else:
                messagebox.showwarning("Warning", "Key not found at top level. Use tree view for nested items.")
        else:
            messagebox.showwarning("Warning", "Select a valid key-value line to delete.")

    def _get_data_from_path(self, node):
        path = []
        while node:
            path.append(self.tree.item(node, "text"))
            node = self.tree.parent(node)
        data = self.json_data
        for key in reversed(path[1:]):
            if key.startswith("["):
                data = data[int(key[1:-1])]
            else:
                data = data[key]
        return data

    def add_custom_form(self):
        print("Launching Add Custom Form window")  # Debug to confirm call
        form_window = tk.Toplevel(self.root)
        form_window.title("Design Custom Form")
        form_window.geometry("600x700")
        form_window.lift()
        form_window.focus_force()

        ttk.Label(form_window, text="Form Name:").pack(pady=5)
        name_entry = ttk.Entry(form_window)
        name_entry.pack(pady=5)

        ttk.Label(form_window, text="Category:").pack(pady=5)
        category_entry = ttk.Entry(form_window)
        category_entry.pack(pady=5)

        canvas = tk.Canvas(form_window, bg="#F8FAFF" if self.theme == "light" else "#3E4A70")
        scrollbar = ttk.Scrollbar(form_window, orient="vertical", command=canvas.yview)
        fields_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.create_window((0, 0), window=fields_frame, anchor="nw")

        fields = []

        def infer_type(value):
            if isinstance(value, str): return "text"
            elif isinstance(value, int): return "number"
            elif isinstance(value, float): return "number"
            elif isinstance(value, bool): return "yes/no"
            elif value is None: return "null"
            elif isinstance(value, dict): return "nested"
            elif isinstance(value, list): return "list"
            return "text"

        def add_field(name="", value=None):
            field_frame = ttk.Frame(fields_frame)
            field_frame.pack(fill=tk.X, pady=2)
            tk.Label(field_frame, text="Field Name:").pack(side=tk.LEFT, padx=5)
            field_name = ttk.Entry(field_frame)
            field_name.pack(side=tk.LEFT, padx=5)
            field_name.insert(0, name)
            tk.Label(field_frame, text="Type:").pack(side=tk.LEFT, padx=5)
            field_type = ttk.Combobox(field_frame, values=["text", "number", "yes/no", "null", "dropdown", "nested", "list"])
            field_type.pack(side=tk.LEFT, padx=5)
            field_type.set(infer_type(value) if value is not None else "text")
            options_entry = ttk.Entry(field_frame)
            options_entry.pack(side=tk.LEFT, padx=5)
            options_entry.insert(0, "Option1,Option2,Option3" if field_type.get() == "dropdown" else "")
            options_entry.config(state="disabled" if field_type.get() != "dropdown" else "normal")
            field_type.bind("<<ComboboxSelected>>", lambda e: options_entry.config(state="normal" if field_type.get() == "dropdown" else "disabled"))
            fields.append((field_name, field_type, options_entry))
            fields_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        if self.json_data and len(self.json_data) > 0:
            sample_item = self.json_data[0] if isinstance(self.json_data, list) else self.json_data
            for key, value in sample_item.items():
                add_field(key, value)

        ttk.Button(form_window, text="Add Field", command=lambda: add_field()).pack(pady=5)

        def save_form():
            form_name = name_entry.get().strip()
            category = category_entry.get() or "Uncategorized"
            if not form_name:
                messagebox.showerror("Error", "Form name is required!")
                return
            form_def = {"fields": [], "category": category}
            for field_name, field_type, options_entry in fields:
                field_def = {"name": field_name.get(), "type": field_type.get()}
                if field_type.get() == "dropdown":
                    field_def["options"] = options_entry.get().split(",")
                form_def["fields"].append(field_def)
            self.custom_forms[form_name] = form_def
            form_file = os.path.join(self.forms_folder, f"{form_name}.json")
            print(f"Saving form to: {os.path.abspath(form_file)}")  # Debug path
            try:
                with open(form_file, 'w') as f:
                    json.dump(form_def, f, indent=4)
                self.status_var.set(f"Saved form: {form_name}.json")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save form: {str(e)}")
                return
            self.update_forms_menu(category)
            form_window.destroy()

        ttk.Button(form_window, text="Save Form", command=save_form).pack(pady=10)

        form_window.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def load_saved_forms(self):
        self.custom_forms.clear()
        for filename in os.listdir(self.forms_folder):
            if filename.endswith(".json"):
                form_name = filename[:-5]
                with open(os.path.join(self.forms_folder, filename), 'r') as f:
                    self.custom_forms[form_name] = json.load(f)
        self.update_forms_menu()

    def update_forms_menu(self, category=None):
        self.forms_menu.delete(0, tk.END)
        self.forms_menu.add_command(label="Add Custom Form", command=self.add_custom_form)
        self.forms_menu.add_command(label="Load Saved Forms", command=self.load_saved_forms)
        self.forms_menu.add_separator()
        categorized_forms = {}
        for form_name in self.custom_forms.keys():
            form_file = os.path.join(self.forms_folder, f"{form_name}.json")
            if os.path.exists(form_file):
                with open(form_file, 'r') as f:
                    form_data = json.load(f)
                    cat = form_data.get("category", "Uncategorized")
                    if cat not in categorized_forms:
                        categorized_forms[cat] = []
                    categorized_forms[cat].append(form_name)
        for cat, forms in categorized_forms.items():
            if cat not in self.category_menus:
                self.category_menus[cat] = tk.Menu(self.forms_menu, tearoff=0)
                self.forms_menu.add_cascade(label=cat, menu=self.category_menus[cat])
            submenu = self.category_menus[cat]
            submenu.delete(0, tk.END)
            for form_name in forms:
                submenu.add_command(label=form_name, command=lambda fn=form_name: self.open_form(fn))

    def open_form(self, form_name):
        form_def = self.custom_forms[form_name]
        form_window = tk.Toplevel(self.root)
        form_window.title(f"Fill {form_name}")
    
        entries = {}
        for field in form_def["fields"]:
            ttk.Label(form_window, text=f"{field['name']}:").pack(pady=2)
            if field["type"] == "nested" and field["name"] == "level_range":
                # Special handling for level_range
                frame = ttk.Frame(form_window)
                frame.pack(pady=2)
                ttk.Label(frame, text="Min:").pack(side=tk.LEFT, padx=2)
                min_entry = ttk.Entry(frame, width=10)
                min_entry.pack(side=tk.LEFT, padx=2)
                ttk.Label(frame, text="Max:").pack(side=tk.LEFT, padx=2)
                max_entry = ttk.Entry(frame, width=10)
                max_entry.pack(side=tk.LEFT, padx=2)
                entries[field["name"]] = {"min": min_entry, "max": max_entry}
            elif field["type"] == "text":
                entry = ttk.Entry(form_window)
                entry.pack(pady=2)
                entries[field["name"]] = entry
            elif field["type"] == "number":
                entry = ttk.Entry(form_window)
                entry.pack(pady=2)
                entries[field["name"]] = entry
            elif field["type"] == "yes/no":
                var = tk.StringVar(value="No")
                ttk.Combobox(form_window, textvariable=var, values=["Yes", "No"]).pack(pady=2)
                entries[field["name"]] = var
            elif field["type"] == "dropdown":
                var = tk.StringVar()
                ttk.Combobox(form_window, textvariable=var, values=field["options"]).pack(pady=2)
                entries[field["name"]] = var
            elif field["type"] == "null":
                entry = ttk.Entry(form_window, state="disabled")
                entry.pack(pady=2)
                entries[field["name"]] = entry
            elif field["type"] == "nested":
                entry = ttk.Entry(form_window)  # Fallback for other nested fields
                entry.pack(pady=2)
                entries[field["name"]] = entry
            elif field["type"] == "list":
                entry = ttk.Entry(form_window)
                entry.pack(pady=2)
                entries[field["name"]] = entry

        ttk.Button(form_window, text="Save to JSON", command=lambda: self.inject_data(form_def, entries, form_window)).pack(pady=10)

    def inject_data(self, form_def, entries, form_window):
        new_item = {}
        for field in form_def["fields"]:
            entry = entries.get(field["name"])  # Safely get the entry
            if entry is None:
                messagebox.showerror("Error", f"No input found for {field['name']}")
                return
            # Handle both widgets and StringVars
            if isinstance(entry, (tk.Entry, ttk.Entry, ttk.Combobox)):
                value = entry.get()
            elif isinstance(entry, tk.StringVar):
                value = entry.get()
            elif isinstance(entry, dict):  # Handle old min/max dict format
                value = {
                    "min": entry["min"].get() if "min" in entry else "0",
                    "max": entry["max"].get() if "max" in entry else "0"
                }
            else:
                messagebox.showwarning("Warning", f"Unsupported input type for {field['name']}: {type(entry)}")
                value = ""  # Default to empty string
            
            if field["type"] == "yes/no":
                new_item[field["name"]] = (value == "Yes")
            elif field["type"] == "number":
                try:
                    new_item[field["name"]] = float(value) if "." in value else int(value)
                except ValueError:
                    new_item[field["name"]] = value if value else 0
            elif field["type"] == "null":
                new_item[field["name"]] = None
            elif field["type"] == "nested":
                if field["name"] == "level_range":
                    if isinstance(value, dict):  # From old min/max format
                        min_val = value.get("min", "0")
                        max_val = value.get("max", "0")
                    else:  # From single Entry
                        try:
                            parsed_value = json.loads(value) if value else {}
                            min_val = parsed_value.get("min", "0")
                            max_val = parsed_value.get("max", "0")
                        except json.JSONDecodeError:
                            # Handle space-separated numbers
                            if value and " " in value.strip():
                                try:
                                    min_val, max_val = map(int, value.strip().split())
                                except ValueError:
                                    min_val, max_val = 0, 0
                            else:
                                min_val, max_val = 0, 0
                    new_item[field["name"]] = {
                        "min": int(min_val) if str(min_val).isdigit() else 0,
                        "max": int(max_val) if str(max_val).isdigit() else 0
                    }
                else:
                    try:
                        new_item[field["name"]] = json.loads(value) if value else {}
                    except json.JSONDecodeError:
                        new_item[field["name"]] = value if value else {}
            elif field["type"] == "list":
                try:
                    new_item[field["name"]] = json.loads(value) if value else []
                except json.JSONDecodeError:
                    new_item[field["name"]] = value if value else []
            else:  # text, dropdown
                new_item[field["name"]] = value if value else ""

        if isinstance(self.json_data, list):
            self.json_data.append(new_item)
        else:
            self.json_data = [self.json_data, new_item] if self.json_data else [new_item]
        
        self.update_views()
        form_window.destroy()

    def search_tree(self):
        query = self.search_var.get().strip()  # Strip whitespace
        self.tree.delete(*self.tree.get_children())  # Clear current tree
        if not query:  # If empty, show full tree
            self.update_views()
        else:
            self._populate_tree_filtered("", self.json_data, query)  # Filter based on query

    def _populate_tree(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                # Only skip "name" if it's the top-level label already used
                if key not in ("name", "quest") or self.tree.item(parent, "text") not in (data.get("name"), data.get("quest")):
                    node = self.tree.insert(parent, "end", text=key, values=(str(value),))
                    self._populate_tree(node, value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                node_text = item.get("name", item.get("quest", f"[{i}]")) if isinstance(item, dict) else f"[{i}]"
                node = self.tree.insert(parent, "end", text=node_text, values=(str(item),))
                self._populate_tree(node, item)
        else:
            self.tree.insert(parent, "end", text=str(data))
            
    def _populate_tree_filtered(self, parent, data, query):
        if not query:  # If query is empty, show everything
            self._populate_tree(parent, data)
            return
        
        query = query.lower()  # Normalize query once
        
        def has_match(data, q):
            """Helper to check if data or its descendants match the query."""
            if isinstance(data, dict):
                return any(q in str(k).lower() or q in str(v).lower() or has_match(v, q) for k, v in data.items())
            elif isinstance(data, list):
                return any(q in str(item).lower() or has_match(item, q) for item in data)
            else:
                return q in str(data).lower()

        if isinstance(data, dict):
            for key, value in data.items():
                if query in str(key).lower() or query in str(value).lower() or has_match(value, query):
                    node = self.tree.insert(parent, "end", text=key, values=(str(value),))
                    self._populate_tree_filtered(node, value, query)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                node_text = item.get("name", f"Item {i}") if isinstance(item, dict) else f"Item {i}"
                if query in node_text.lower() or query in str(item).lower() or has_match(item, query):
                    node = self.tree.insert(parent, "end", text=node_text, values=(str(item),))
                    self._populate_tree_filtered(node, item, query)
        else:
            if query in str(data).lower():
                self.tree.insert(parent, "end", text=str(data))

    def sort_tree(self):
        def sort_dict(d):
            if isinstance(d, dict):
                return {k: sort_dict(v) for k, v in sorted(d.items(), key=lambda x: str(x[1]))}
            return d
        self.json_data = sort_dict(self.json_data)
        self.update_views()

if __name__ == "__main__":
    root = tk.Tk()
    app = JSONEditor(root)
    root.mainloop()
