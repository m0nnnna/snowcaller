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
        self.current_outcomes = []
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
    
        # Handle nested key_items structure
        if isinstance(self.json_data, dict) and "key_items" in self.json_data:
            key_items = self.json_data["key_items"]
            if isinstance(key_items, list):
                for i, item in enumerate(key_items):
                    if isinstance(item, dict):
                        node_text = item.get("name", f"Item {i}")
                        node = self.tree.insert(root_node, "end", text=node_text, values=(i,))
                        self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 2}.0"
                        self._populate_tree(node, item)
            else:
                self._populate_tree(root_node, key_items)
        elif isinstance(self.json_data, dict):
            # Fallback for non-key_items dictionaries
            self._populate_tree(root_node, self.json_data)
        elif isinstance(self.json_data, list):
            # Direct list handling (e.g., gear.json)
            for i, item in enumerate(self.json_data):
                node_text = item.get("name", f"Item {i}") if isinstance(item, dict) else f"Item {i}"
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
            self.update_forms_menu()  # Update the full menu, no category filter
            form_window.destroy()

        ttk.Button(form_window, text="Save Form", command=save_form).pack(pady=10)

        form_window.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def load_saved_forms(self):
        # Clear and reload forms from disk
        self.custom_forms.clear()
        for filename in os.listdir(self.forms_folder):
            if filename.endswith(".json"):
                form_name = filename[:-5]
                try:
                    with open(os.path.join(self.forms_folder, filename), 'r') as f:
                        self.custom_forms[form_name] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading form {form_name}: {e}")
        self.update_forms_menu()  # Always update the menu after loading
        self.status_var.set(f"Loaded {len(self.custom_forms)} custom forms")

    def update_forms_menu(self, category=None):
        # Clear the entire forms menu and rebuild it
        self.forms_menu.delete(0, tk.END)
        self.category_menus.clear()  # Reset category submenus
        self.forms_menu.add_command(label="Add Custom Form", command=self.add_custom_form)
        self.forms_menu.add_command(label="Load Saved Forms", command=self.load_saved_forms)
        self.forms_menu.add_separator()
        
        # Organize forms by category
        categorized_forms = {}
        for form_name, form_data in self.custom_forms.items():
            cat = form_data.get("category", "Uncategorized")
            if cat not in categorized_forms:
                categorized_forms[cat] = []
            categorized_forms[cat].append(form_name)
        
        # Build category submenus
        for cat, forms in sorted(categorized_forms.items()):
            if cat not in self.category_menus:
                self.category_menus[cat] = tk.Menu(self.forms_menu, tearoff=0)
                self.forms_menu.add_cascade(label=cat, menu=self.category_menus[cat])
            submenu = self.category_menus[cat]
            submenu.delete(0, tk.END)  # Clear existing entries
            for form_name in sorted(forms):  # Sort forms alphabetically
                submenu.add_command(label=form_name, command=lambda fn=form_name: self.open_form(fn))

    def open_form(self, form_name):
        form_def = self.custom_forms[form_name]
        form_window = tk.Toplevel(self.root)
        form_window.title(f"Fill {form_name}")
    
        entries = {}
        self.current_outcomes = []  # Reset outcomes for this form instance
    
        for field in form_def["fields"]:
            ttk.Label(form_window, text=f"{field.get('label', field['name'])}:").pack(pady=2)
            if field["type"] == "nested" and "fields" in field:
                # General handling for nested fields with subfields
                frame = ttk.Frame(form_window)
                frame.pack(pady=2)
                sub_entries = {}
                for subfield in field["fields"]:
                    ttk.Label(frame, text=f"{subfield.get('label', subfield['name'])}:").pack(side=tk.LEFT, padx=2)
                    if subfield["type"] == "dropdown":
                        var = tk.StringVar(value=subfield.get("default", ""))
                        ttk.Combobox(frame, textvariable=var, values=subfield["options"]).pack(side=tk.LEFT, padx=2)
                        sub_entries[subfield["name"]] = var
                    else:
                        sub_entry = ttk.Entry(frame, width=10)
                        sub_entry.pack(side=tk.LEFT, padx=2)
                        sub_entries[subfield["name"]] = sub_entry
                entries[field["name"]] = sub_entries
            elif field["type"] == "list" and "item_template" in field:
                # Dynamic list handling (e.g., stages)
                list_frame = ttk.Frame(form_window)
                list_frame.pack(pady=2)
                list_entries = []
                max_items = field.get("max_items", 1)


                def add_list_item():
                    if len(list_entries) < max_items:
                        item_frame = ttk.Frame(list_frame)
                        item_frame.pack(pady=2)
                        item_entries = {}
                        for subfield in field["item_template"]["fields"]:
                            ttk.Label(item_frame, text=f"{subfield.get('label', subfield['name'])}:").pack(side=tk.LEFT, padx=2)
                            if subfield["type"] == "dropdown":
                                var = tk.StringVar(value=subfield.get("default", ""))
                                ttk.Combobox(item_frame, textvariable=var, values=subfield["options"]).pack(side=tk.LEFT, padx=2)
                                item_entries[subfield["name"]] = var
                            else:
                                sub_entry = ttk.Entry(item_frame, width=10)
                                sub_entry.pack(side=tk.LEFT, padx=2)
                                item_entries[subfield["name"]] = sub_entry
                        list_entries.append(item_entries)
                        if len(list_entries) >= max_items:
                            add_button.config(state="disabled")

                add_list_item()  # First stage by default
                add_button = ttk.Button(form_window, text=f"Add {field.get('label', field['name']).split()[0]}", command=add_list_item)
                add_button.pack(pady=2)
                entries[field["name"]] = list_entries
            elif field["type"] == "list":
                # Fallback for list without item_template
                entry = ttk.Entry(form_window)
                entry.pack(pady=2)
                entries[field["name"]] = entry
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
                var = tk.StringVar(value=field.get("default", ""))
                ttk.Combobox(form_window, textvariable=var, values=field["options"]).pack(pady=2)
                entries[field["name"]] = var
            elif field["type"] == "null":
                entry = ttk.Entry(form_window, state="disabled")
                entry.pack(pady=2)
                entries[field["name"]] = entry
            elif field["type"] == "nested":
                entry = ttk.Entry(form_window)  # Fallback for nested without subfields
                entry.pack(pady=2)
                entries[field["name"]] = entry
            elif field["type"] == "button":
                action = field.get("action")
                if action and hasattr(self, action):
                    ttk.Button(form_window, text=field.get("label", "Button"), 
                              command=getattr(self, action)).pack(pady=2)
                else:
                    ttk.Label(form_window, text=f"No action defined for {field['name']}").pack(pady=2)
                entries[field["name"]] = None

        ttk.Button(form_window, text="Save to JSON", command=lambda: self.inject_data(form_def, entries, form_window)).pack(pady=10)
        
    def open_outcome_editor(self):
        outcome_window = tk.Toplevel(self.root)
        outcome_window.title("Add Outcome")
        outcome_window.geometry("400x500")
    
        entries = {}
    
        # Outcome type dropdown
        ttk.Label(outcome_window, text="Reward Type:").pack(pady=2)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(outcome_window, textvariable=type_var, 
                                 values=["item", "gold", "merchant", "heal", "damage", "combat", "extend_encounters", "dialogue"])
        type_combo.pack(pady=2)
        entries["type"] = type_var
    
        # Common field: weight
        ttk.Label(outcome_window, text="Weight:").pack(pady=2)
        weight_entry = ttk.Entry(outcome_window)
        weight_entry.insert(0, "100")
        weight_entry.pack(pady=2)
        entries["weight"] = weight_entry
    
        # Type-specific fields
        field_frame = ttk.Frame(outcome_window)
        field_frame.pack(pady=5, fill=tk.BOTH, expand=True)
    
        def update_fields(*args):
            for widget in field_frame.winfo_children():
                widget.destroy()
            outcome_type = type_var.get()
        
            if outcome_type == "item":
                ttk.Label(field_frame, text="Source File:").pack(pady=2)
                source_entry = ttk.Entry(field_frame)
                source_entry.pack(pady=2)
                entries["source"] = source_entry
            
                ttk.Label(field_frame, text="Count Min:").pack(pady=2)
                count_min = ttk.Entry(field_frame)
                count_min.pack(pady=2)
                ttk.Label(field_frame, text="Count Max:").pack(pady=2)
                count_max = ttk.Entry(field_frame)
                count_max.pack(pady=2)
                entries["count"] = {"min": count_min, "max": count_max}
            
            elif outcome_type == "gold":
                ttk.Label(field_frame, text="Amount Min:").pack(pady=2)
                amount_min = ttk.Entry(field_frame)
                amount_min.pack(pady=2)
                ttk.Label(field_frame, text="Amount Max:").pack(pady=2)
                amount_max = ttk.Entry(field_frame)
                amount_max.pack(pady=2)
                entries["amount"] = {"min": amount_min, "max": amount_max}
            
            elif outcome_type == "heal" or outcome_type == "damage":
                ttk.Label(field_frame, text="Amount Min:").pack(pady=2)
                amount_min = ttk.Entry(field_frame)
                amount_min.pack(pady=2)
                ttk.Label(field_frame, text="Amount Max:").pack(pady=2)
                amount_max = ttk.Entry(field_frame)
                amount_max.pack(pady=2)
                entries["amount"] = {"min": amount_min, "max": amount_max}
            
                ttk.Label(field_frame, text="Requires Choice:").pack(pady=2)
                req_choice_var = tk.StringVar(value="false")
                ttk.Combobox(field_frame, textvariable=req_choice_var, values=["true", "false"]).pack(pady=2)
                entries["requires_choice"] = req_choice_var
            
            elif outcome_type == "combat":
                ttk.Label(field_frame, text="Monster:").pack(pady=2)
                monster_entry = ttk.Entry(field_frame)
                monster_entry.pack(pady=2)
                entries["monster"] = monster_entry
            
                ttk.Label(field_frame, text="Count:").pack(pady=2)
                count_entry = ttk.Entry(field_frame)
                count_entry.pack(pady=2)
                entries["count"] = count_entry
            
            elif outcome_type == "extend_encounters":
                ttk.Label(field_frame, text="Amount:").pack(pady=2)
                amount_entry = ttk.Entry(field_frame)
                amount_entry.pack(pady=2)
                entries["amount"] = amount_entry
            
                ttk.Label(field_frame, text="Max Limit:").pack(pady=2)
                max_limit_entry = ttk.Entry(field_frame)
                max_limit_entry.pack(pady=2)
                entries["max_limit"] = max_limit_entry
            
            elif outcome_type == "dialogue":
                ttk.Label(field_frame, text="NPC File:").pack(pady=2)
                npc_file_entry = ttk.Entry(field_frame)
                npc_file_entry.pack(pady=2)
                entries["npc_file"] = npc_file_entry
            
                ttk.Label(field_frame, text="Stage:").pack(pady=2)
                stage_entry = ttk.Entry(field_frame)
                stage_entry.pack(pady=2)
                entries["stage"] = stage_entry
            
                ttk.Label(field_frame, text="Requires Choice:").pack(pady=2)
                req_choice_var = tk.StringVar(value="false")
                ttk.Combobox(field_frame, textvariable=req_choice_var, values=["true", "false"]).pack(pady=2)
                entries["requires_choice"] = req_choice_var
    
        type_combo.bind("<<ComboboxSelected>>", update_fields)
    
        def save_outcome():
            outcome = {}
            for key, entry in entries.items():
                if isinstance(entry, tk.StringVar):
                    value = entry.get()
                elif isinstance(entry, ttk.Entry):
                    value = entry.get()
                elif isinstance(entry, dict):
                    value = {k: v.get() for k, v in entry.items()}
                else:
                    continue
                
                if key in ["weight"] and value:
                    outcome[key] = int(value)
                elif key in ["count"] and value and isinstance(value, dict):
                    outcome[key] = {k: int(v) for k, v in value.items()}
                elif key in ["amount"] and value and isinstance(value, dict):
                    outcome[key] = {k: float(v) if "." in v else int(v) for k, v in value.items()}
                elif key in ["amount", "count", "max_limit"] and value and not isinstance(value, dict):
                    outcome[key] = int(value)
                elif key == "requires_choice":
                    outcome[key] = value == "true"
                else:
                    outcome[key] = value if value else ""
        
            self.current_outcomes.append(outcome)
            outcome_window.destroy()
            self.status_var.set(f"Added outcome: {outcome['type']}")
    
        ttk.Button(outcome_window, text="Save Outcome", command=save_outcome).pack(pady=10)
    
        def update_fields(*args):
            for widget in field_frame.winfo_children():
                widget.destroy()
            outcome_type = type_var.get()
        
            if outcome_type == "item":
                ttk.Label(field_frame, text="Source File:").pack(pady=2)
                source_entry = ttk.Entry(field_frame)
                source_entry.pack(pady=2)
                entries["source"] = source_entry
            
                ttk.Label(field_frame, text="Count Min:").pack(pady=2)
                count_min = ttk.Entry(field_frame)
                count_min.pack(pady=2)
                ttk.Label(field_frame, text="Count Max:").pack(pady=2)
                count_max = ttk.Entry(field_frame)
                count_max.pack(pady=2)
                entries["count"] = {"min": count_min, "max": count_max}
            
            elif outcome_type == "gold":
                ttk.Label(field_frame, text="Amount Min:").pack(pady=2)
                amount_min = ttk.Entry(field_frame)
                amount_min.pack(pady=2)
                ttk.Label(field_frame, text="Amount Max:").pack(pady=2)
                amount_max = ttk.Entry(field_frame)
                amount_max.pack(pady=2)
                entries["amount"] = {"min": amount_min, "max": amount_max}
            
            elif outcome_type == "heal" or outcome_type == "damage":
                ttk.Label(field_frame, text="Amount Min:").pack(pady=2)
                amount_min = ttk.Entry(field_frame)
                amount_min.pack(pady=2)
                ttk.Label(field_frame, text="Amount Max:").pack(pady=2)
                amount_max = ttk.Entry(field_frame)
                amount_max.pack(pady=2)
                entries["amount"] = {"min": amount_min, "max": amount_max}
            
                ttk.Label(field_frame, text="Requires Choice:").pack(pady=2)
                req_choice_var = tk.StringVar(value="false")
                ttk.Combobox(field_frame, textvariable=req_choice_var, values=["true", "false"]).pack(pady=2)
                entries["requires_choice"] = req_choice_var
            
            elif outcome_type == "combat":
                ttk.Label(field_frame, text="Monster:").pack(pady=2)
                monster_entry = ttk.Entry(field_frame)
                monster_entry.pack(pady=2)
                entries["monster"] = monster_entry
            
                ttk.Label(field_frame, text="Count:").pack(pady=2)
                count_entry = ttk.Entry(field_frame)
                count_entry.pack(pady=2)
                entries["count"] = count_entry
            
            elif outcome_type == "extend_encounters":
                ttk.Label(field_frame, text="Amount:").pack(pady=2)
                amount_entry = ttk.Entry(field_frame)
                amount_entry.pack(pady=2)
                entries["amount"] = amount_entry
            
                ttk.Label(field_frame, text="Max Limit:").pack(pady=2)
                max_limit_entry = ttk.Entry(field_frame)
                max_limit_entry.pack(pady=2)
                entries["max_limit"] = max_limit_entry
            
            elif outcome_type == "dialogue":
                ttk.Label(field_frame, text="NPC File:").pack(pady=2)
                npc_file_entry = ttk.Entry(field_frame)
                npc_file_entry.pack(pady=2)
                entries["npc_file"] = npc_file_entry
            
                ttk.Label(field_frame, text="Stage:").pack(pady=2)
                stage_entry = ttk.Entry(field_frame)
                stage_entry.pack(pady=2)
                entries["stage"] = stage_entry
            
                ttk.Label(field_frame, text="Requires Choice:").pack(pady=2)
                req_choice_var = tk.StringVar(value="false")
                ttk.Combobox(field_frame, textvariable=req_choice_var, values=["true", "false"]).pack(pady=2)
                entries["requires_choice"] = req_choice_var
    
        type_combo.bind("<<ComboboxSelected>>", update_fields)
    
        def save_outcome():
            outcome = {}
            for key, entry in entries.items():
                if isinstance(entry, tk.StringVar):
                    value = entry.get()
                elif isinstance(entry, ttk.Entry):
                    value = entry.get()
                elif isinstance(entry, dict):
                    value = {k: v.get() for k, v in entry.items()}
                else:
                    continue
                
                if key in ["weight"] and value:
                    outcome[key] = int(value)
                elif key in ["count"] and value and isinstance(value, dict):
                    outcome[key] = {k: int(v) for k, v in value.items()}
                elif key in ["amount"] and value and isinstance(value, dict):
                    outcome[key] = {k: float(v) if "." in v else int(v) for k, v in value.items()}
                elif key in ["amount", "count", "max_limit"] and value and not isinstance(value, dict):
                    outcome[key] = int(value)
                elif key == "requires_choice":
                    outcome[key] = value == "true"
                else:
                    outcome[key] = value if value else ""
        
            self.current_outcomes.append(outcome)
            outcome_window.destroy()
            self.status_var.set(f"Added outcome: {outcome['type']}")
    
        ttk.Button(outcome_window, text="Save Outcome", command=save_outcome).pack(pady=10)

    def inject_data(self, form_def, entries, form_window):
        new_item = {}
        for field in form_def["fields"]:
            entry = entries.get(field["name"])
            if entry is None and field["name"] != "outcomes":  # Skip outcomes for now
                messagebox.showerror("Error", f"No input found for {field['name']}")
                return
        
            if field["name"] == "outcomes":
                new_item["outcomes"] = self.current_outcomes  # Inject collected outcomes
                continue
            
            if isinstance(entry, (tk.Entry, ttk.Entry, ttk.Combobox)):
                value = entry.get()
            elif isinstance(entry, tk.StringVar):
                value = entry.get()
            elif isinstance(entry, dict):  # Handle nested fields with sub-entries
                value = {}
                for sub_name, sub_entry in entry.items():
                    sub_value = sub_entry.get()
                    if sub_value:
                        try:
                            value[sub_name] = float(sub_value) if "." in sub_value else int(sub_value)
                        except ValueError:
                            value[sub_name] = sub_value
                    else:
                        value[sub_name] = 0 if sub_name in ["kill_count_required", "item_count_required"] else sub_value
            elif isinstance(entry, list):  # Handle list fields (e.g., stages)
                value = []
                for item_entries in entry:
                    item = {}
                    for sub_name, sub_entry in item_entries.items():
                        sub_value = sub_entry.get()
                        if sub_value:
                            try:
                                item[sub_name] = float(sub_value) if "." in sub_value else int(sub_value)
                            except ValueError:
                                item[sub_name] = sub_value
                    # Filter stages based on type
                    if item.get("type"):
                        filtered_item = {"type": item["type"]}
                        if item["type"] in ["kill", "boss"]:
                            if item.get("target_monster"):
                                filtered_item["target_monster"] = item["target_monster"]
                            if item.get("kill_count_required"):
                                filtered_item["kill_count_required"] = item["kill_count_required"]
                        elif item["type"] == "collect":
                            if item.get("target_item"):
                                filtered_item["target_item"] = item["target_item"]
                            if item.get("item_count_required"):
                                filtered_item["item_count_required"] = item["item_count_required"]
                        value.append(filtered_item)
            else:
                messagebox.showwarning("Warning", f"Unsupported input type for {field['name']}: {type(entry)}")
                value = ""
            
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
                new_item[field["name"]] = value  # Other nested fields (e.g., location)
            elif field["type"] == "list":
                new_item[field["name"]] = value  # List fields (e.g., stages)
            else:  # text, dropdown
                if field["name"] == "steps" and value:
                    new_item[field["name"]] = [step.strip() for step in value.split(",")]
                elif field["name"] in ["next_quest", "npc_trigger"]:
                    new_item[field["name"]] = None if value == "null" else value
                else:
                    new_item[field["name"]] = value if value else ""

        # Handle injection into json_data based on form category
        if form_def.get("category") == "Quests" and "quests" in self.json_data:
            quests = self.json_data.get("quests", [])
            if not isinstance(quests, list):
                quests = []
                self.json_data["quests"] = quests
            for i, item in enumerate(quests):
                if isinstance(item, dict) and item.get("quest_name") == new_item.get("quest_name"):
                    quests[i] = new_item
                    self.status_var.set(f"Updated quest: {new_item['quest_name']}")
                    break
            else:
                quests.insert(0, new_item)
                self.status_var.set(f"Added new quest at top: {new_item['quest_name']}")
        elif form_def.get("category") == "Random" and "monsters" in self.json_data:
            monsters = self.json_data.get("monsters", [])
            if not isinstance(monsters, list):
                monsters = []
                self.json_data["monsters"] = monsters
            for i, item in enumerate(monsters):
                if isinstance(item, dict) and item.get("name") == new_item.get("name"):
                    monsters[i] = new_item
                    self.status_var.set(f"Updated monster: {new_item['name']}")
                    break
            else:
                monsters.insert(0, new_item)
                self.status_var.set(f"Added new monster at top: {new_item['name']}")
        elif form_def.get("category") == "Lore" and "lore" in self.json_data:
            lore_items = self.json_data.get("lore", [])
            if not isinstance(lore_items, list):
                lore_items = []
                self.json_data["lore"] = lore_items
            for i, item in enumerate(lore_items):
                if isinstance(item, dict) and item.get("quest_name") == new_item.get("quest_name"):
                    lore_items[i] = new_item
                    self.status_var.set(f"Updated lore: {new_item['quest_name']}")
                    break
            else:
                lore_items.insert(0, new_item)
                self.status_var.set(f"Added new lore at top: {new_item['quest_name']}")
        elif form_def.get("category") == "Items" and "key_items" in self.json_data:
            key_items = self.json_data.get("key_items", [])
            if not isinstance(key_items, list):
                key_items = []
                self.json_data["key_items"] = key_items
            for i, item in enumerate(key_items):
                if isinstance(item, dict) and item.get("name") == new_item.get("name"):
                    key_items[i] = new_item
                    self.status_var.set(f"Updated key item: {new_item['name']}")
                    break
            else:
                key_items.insert(0, new_item)
                self.status_var.set(f"Added new key item at top: {new_item['name']}")
        elif isinstance(self.json_data, list):
            for i, item in enumerate(self.json_data):
                if isinstance(item, dict) and item.get("name") == new_item.get("name"):
                    self.json_data[i] = new_item
                    self.status_var.set(f"Updated item: {new_item['name']}")
                    break
            else:
                if len(self.json_data) >= 2:
                    try:
                        self.json_data.insert(0, new_item)
                        self.status_var.set(f"Added new item at top: {new_item['name']}")
                    except Exception as e:
                        self.json_data.insert(-1, new_item)
                        self.status_var.set(f"Added new item before last: {new_item['name']} (Top failed: {e})")
                elif len(self.json_data) == 1:
                    self.json_data.insert(0, new_item)
                    self.status_var.set(f"Added new item at top: {new_item['name']}")
                else:
                    self.json_data.append(new_item)
                    self.status_var.set(f"Added new item (empty list): {new_item['name']}")
        else:
            if not self.json_data:
                if form_def.get("category") == "Quests":
                    self.json_data = {"quests": [new_item]}
                    self.status_var.set(f"Created new quests list with: {new_item['quest_name']}")
                elif form_def.get("category") == "Random":
                    self.json_data = {"monsters": [new_item]}
                    self.status_var.set(f"Created new monsters list with: {new_item['name']}")
                elif form_def.get("category") == "Lore":
                    self.json_data = {"lore": [new_item]}
                    self.status_var.set(f"Created new lore list with: {new_item['quest_name']}")
                elif form_def.get("category") == "Items":
                    self.json_data = {"key_items": [new_item]}
                    self.status_var.set(f"Created new key items list with: {new_item['name']}")
                else:
                    self.json_data = [new_item]
                    self.status_var.set(f"Created new list with: {new_item.get('name', 'unnamed')}")
            else:
                self.json_data = [new_item, self.json_data]
                self.status_var.set(f"Created new list with: {new_item.get('name', 'unnamed')}")

        print("Post-injection self.json_data:", json.dumps(self.json_data, indent=2))  # Debug print
        self.update_views()
        form_window.destroy()

    def update_views(self):
        self.tree.delete(*self.tree.get_children())
        self.text.delete("1.0", tk.END)
        self.node_positions.clear()
        json_text = json.dumps(self.json_data, indent=self.indent_level)
        self.text.insert("1.0", json_text)
    
        root_node = self.tree.insert("", "end", text="Root", values=("Object",))
        self.node_positions[root_node] = "1.0"
    
        # Handle nested structures (quests, monsters, lore, or key_items)
        if isinstance(self.json_data, dict):
            if "quests" in self.json_data:
                quests = self.json_data["quests"]
                if isinstance(quests, list):
                    for i, item in enumerate(quests):
                        if isinstance(item, dict):
                            node_text = item.get("quest_name", f"Item {i}")
                            node = self.tree.insert(root_node, "end", text=node_text, values=(i,))
                            self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 2}.0"
                            self._populate_tree(node, item)
                else:
                    self._populate_tree(root_node, quests)
            elif "monsters" in self.json_data:
                monsters = self.json_data["monsters"]
                if isinstance(monsters, list):
                    for i, item in enumerate(monsters):
                        if isinstance(item, dict):
                            node_text = item.get("name", f"Item {i}")
                            node = self.tree.insert(root_node, "end", text=node_text, values=(i,))
                            self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 2}.0"
                            self._populate_tree(node, item)
                else:
                    self._populate_tree(root_node, monsters)
            elif "lore" in self.json_data:
                lore_items = self.json_data["lore"]
                if isinstance(lore_items, list):
                    for i, item in enumerate(lore_items):
                        if isinstance(item, dict):
                            node_text = item.get("quest_name", f"Item {i}")
                            node = self.tree.insert(root_node, "end", text=node_text, values=(i,))
                            self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 2}.0"
                            self._populate_tree(node, item)
                else:
                    self._populate_tree(root_node, lore_items)
            elif "key_items" in self.json_data:
                key_items = self.json_data["key_items"]
                if isinstance(key_items, list):
                    for i, item in enumerate(key_items):
                        if isinstance(item, dict):
                            node_text = item.get("name", f"Item {i}")
                            node = self.tree.insert(root_node, "end", text=node_text, values=(i,))
                            self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 2}.0"
                            self._populate_tree(node, item)
                else:
                    self._populate_tree(root_node, key_items)
            else:
                # Fallback for other dictionaries
                self._populate_tree(root_node, self.json_data)
        elif isinstance(self.json_data, list):
            # Direct list handling (e.g., gear.json)
            for i, item in enumerate(self.json_data):
                node_text = item.get("name", f"Item {i}") if isinstance(item, dict) else f"Item {i}"
                node = self.tree.insert(root_node, "end", text=node_text, values=(i,))
                self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 2}.0"
                self._populate_tree(node, item)

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

    def search_tree(self):
        search_term = self.search_entry.get().strip().lower()
        if not search_term:
            return
        
        # Clear current selection
        self.tree.selection_remove(self.tree.selection())
        
        # Search through tree items
        for item in self.tree.get_children(""):
            # Check top-level items (e.g., "Root")
            if search_term in self.tree.item(item, "text").lower():
                self.tree.selection_set(item)
                self.tree.see(item)
                return
            
            # Search children (e.g., quest_name, name)
            for child in self.tree.get_children(item):
                child_text = self.tree.item(child, "text").lower()
                if search_term in child_text:
                    self.tree.selection_set(child)
                    self.tree.see(child)
                    # Scroll to the position in the text widget if mapped
                    if child in self.node_positions:
                        self.text.see(self.node_positions[child])
                    return
        
        self.status_var.set(f"No match found for '{search_term}'")

if __name__ == "__main__":
    root = tk.Tk()
    app = JSONEditor(root)
    root.mainloop()
