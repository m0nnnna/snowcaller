import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

class JSONEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Frost Editor")
        self.json_data = []
        self.node_positions = {}
        self.custom_forms = {}
        self.indent_level = 4  # New: Default indent, will be updated on load
        
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
        self.forms_menu.add_command(label="Load Saved Forms", command=self.load_saved_forms)  # Still available manually
        self.category_menus = {}

        # New: Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Paned window setup (unchanged)
        self.paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        self.tree_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tree_frame, weight=1)
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree_context_menu = tk.Menu(self.root, tearoff=0)
        self.tree_context_menu.add_command(label="Open", command=self.open_in_text)
        self.tree_context_menu.add_command(label="Delete", command=self.delete_tree_item)
        self.tree.bind("<Button-3>", self.show_tree_context_menu)
        self.text_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.text_frame, weight=1)
        self.text = tk.Text(self.text_frame, wrap="none")
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text_context_menu = tk.Menu(self.root, tearoff=0)
        self.text_context_menu.add_command(label="Delete", command=self.delete_text_item)
        self.text.bind("<Button-3>", self.show_text_context_menu)        

        # Search bar
        self.search_frame = ttk.Frame(root)
        self.search_frame.pack(fill=tk.X)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.search_entry.bind("<Return>", lambda event: self.search_tree())
        ttk.Button(self.search_frame, text="Search", command=self.search_tree).pack(side=tk.LEFT)
   
        # Forms folder setup
        self.forms_folder = "custom_forms"
        if not os.path.exists(self.forms_folder):
            os.makedirs(self.forms_folder)
    
        # Auto-load forms on startup
        self.load_saved_forms()  # New: Auto-load forms here

        # Initialize forms folder
        self.forms_folder = "custom_forms"
        if not os.path.exists(self.forms_folder):
            os.makedirs(self.forms_folder)

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                # Read raw text to detect indentation
                lines = f.readlines()
                self.detect_indent(lines)  # New: Detect indent from file
                f.seek(0)  # Reset to start for json.load
                loaded_data = json.load(f)
                if isinstance(loaded_data, list):
                    self.json_data = loaded_data
                    self.data_key = None
                elif isinstance(loaded_data, dict):
                    for key, value in loaded_data.items():
                        if isinstance(value, list):
                            self.json_data = value
                            self.data_key = key
                            break
                    else:
                        self.json_data = [loaded_data]
                        self.data_key = None
                self.update_views()
            self.current_file = file_path 

    def detect_indent(self, lines):
        for line in lines:
            stripped = line.lstrip()
            if stripped and stripped.startswith(('{', '[')):  # Look at first indented line
                indent = len(line) - len(stripped)
                if indent > 0:
                    self.indent_level = indent  # Set detected indent (e.g., 2 or 4 spaces)
                    break

    def save_json(self):
        try:
            self.json_data = json.loads(self.text.get("1.0", tk.END))
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                output_data = self.json_data if not hasattr(self, 'data_key') or not self.data_key else {self.data_key: self.json_data}
                with open(file_path, 'w') as f:
                    json.dump(output_data, f, indent=self.indent_level)  # Changed: Use detected indent
                messagebox.showinfo("Success", "JSON saved successfully!")
                self.current_file = file_path  # New: Update current file path
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON in text view!")


    def update_views(self):
        self.tree.delete(*self.tree.get_children())
        self.text.delete("1.0", tk.END)
        self.node_positions.clear()
        display_data = self.json_data if not hasattr(self, 'data_key') or not self.data_key else {self.data_key: self.json_data}
        json_text = json.dumps(display_data, indent=self.indent_level)  # Changed: Use detected indent
        self.text.insert("1.0", json_text)
        for i, item in enumerate(self.json_data):
            if isinstance(item, dict):
                node_text = item.get("quest_name", item.get("name", f"Item {i}"))
                node = self.tree.insert("", "end", text=node_text, values=(i,))
                self.node_positions[node] = self.text.search(f'"{node_text}"', "1.0", tk.END) or f"{i + 1}.0"
                self._populate_tree(node, item)

    def _populate_tree(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key not in ["name", "quest_name"]:  # Skip both "name" and "quest_name" to avoid duplication
                    node = self.tree.insert(parent, "end", text=key, values=(str(value),))
                    self._populate_tree(node, value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                node_text = item.get("name", f"[{i}]") if isinstance(item, dict) else f"[{i}]"
                node = self.tree.insert(parent, "end", text=node_text, values=(str(item),))
                self._populate_tree(node, item)
        else:
            self.tree.insert(parent, "end", text=str(data))


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
        form_window = tk.Toplevel(self.root)
        form_window.title("Design Custom Form")
        form_window.geometry("600x700")

        tk.Label(form_window, text="Form Name:").pack()
        name_entry = ttk.Entry(form_window)
        name_entry.pack()

        tk.Label(form_window, text="Category:").pack()
        category_entry = ttk.Entry(form_window)
        category_entry.pack()

        fields_frame = ttk.Frame(form_window)
        fields_frame.pack(fill=tk.BOTH, expand=True)
        fields = []  # Moved up to be available for all functions

        def infer_type(value):
            if isinstance(value, str):
                return "text"
            elif isinstance(value, int):
                return "number"
            elif isinstance(value, float):
                return "number"
            elif isinstance(value, bool):
                return "yes/no"
            elif value is None:
                return "null"
            elif isinstance(value, dict):
                return "nested"
            elif isinstance(value, list):
                return "list"
            return "text"

        def add_field(name="", value=None):  # Local function, not self.add_field
            field_frame = ttk.Frame(fields_frame)
            field_frame.pack(fill=tk.X, pady=2)
            tk.Label(field_frame, text="Field Name:").pack(side=tk.LEFT)
            field_name = ttk.Entry(field_frame)
            field_name.pack(side=tk.LEFT)
            field_name.insert(0, name)
            tk.Label(field_frame, text="Type:").pack(side=tk.LEFT)
            field_type = ttk.Combobox(field_frame, values=["text", "number", "yes/no", "null", "dropdown", "nested", "list"])
            field_type.pack(side=tk.LEFT)
            field_type.set(infer_type(value) if value is not None else "text")
            options_entry = ttk.Entry(field_frame)
            options_entry.pack(side=tk.LEFT)
            options_entry.insert(0, "Option1,Option2,Option3" if field_type.get() == "dropdown" else "")
            options_entry.config(state="disabled" if field_type.get() != "dropdown" else "normal")
            field_type.bind("<<ComboboxSelected>>", lambda e: options_entry.config(state="normal" if field_type.get() == "dropdown" else "disabled"))
            fields.append((field_name, field_type, options_entry))

        # Seed with example fields from json_data if available
        if self.json_data and len(self.json_data) > 0:
            sample_item = self.json_data[0]
            for key, value in sample_item.items():
                add_field(key, value)  # Changed: Call local add_field directly

        ttk.Button(form_window, text="Add Field", command=lambda: add_field()).pack()  # Fixed: No self., no extra args

        def save_form():
            form_name = name_entry.get()
            category = category_entry.get() or "Uncategorized"
            if not form_name:
                messagebox.showerror("Error", "Form name is required!")
                return
            form_def = {"fields": [], "category": category}  # Include category in form def
            for field_name, field_type, options_entry in fields:
                field_def = {"name": field_name.get(), "type": field_type.get()}
                if field_type.get() == "dropdown":
                    field_def["options"] = options_entry.get().split(",")
                form_def["fields"].append(field_def)
            self.custom_forms[form_name] = form_def
            form_file = os.path.join(self.forms_folder, f"{form_name}.json")
            with open(form_file, 'w') as f:
                json.dump(form_def, f, indent=4)
            self.update_forms_menu(category)
            form_window.destroy()

        ttk.Button(form_window, text="Save Form", command=save_form).pack(pady=10)  # Fixed: Direct call, no lambda

        name_entry = ttk.Entry(form_window)
        category_entry = ttk.Entry(form_window)
        fields = []
        conditions = []

    def load_saved_forms(self):
        self.custom_forms.clear()
        for filename in os.listdir(self.forms_folder):
            if filename.endswith(".json"):
                form_name = filename[:-5]
                with open(os.path.join(self.forms_folder, filename), 'r') as f:
                    self.custom_forms[form_name] = json.load(f)
        self.update_forms_menu()
        messagebox.showinfo("Success", "Loaded saved forms!") 

    # In update_forms_menu:
    def update_forms_menu(self, category=None):
        self.forms_menu.delete(0, tk.END)
        self.forms_menu.add_command(label="Add Custom Form", command=self.add_custom_form)
        self.forms_menu.add_command(label="Load Saved Forms", command=self.load_saved_forms)
        self.forms_menu.add_separator()
        # Group forms by category
        categorized_forms = {}
        for form_name in self.custom_forms.keys():
            form_file = os.path.join(self.forms_folder, f"{form_name}.json")
            if os.path.exists(form_file):
                with open(form_file, 'r') as f:
                    form_data = json.load(f)
                    cat = form_data.get("category", "Uncategorized")  # Assume category might be saved in JSON
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
            tk.Label(form_window, text=f"{field['name']}:").pack()
            if field["type"] == "text":
                entry = ttk.Entry(form_window)
                entry.pack()
                entries[field["name"]] = entry
            elif field["type"] == "dropdown":
                var = tk.StringVar()
                ttk.Combobox(form_window, textvariable=var, values=field["options"]).pack()
                entries[field["name"]] = var
            elif field["type"] == "yes/no":
                var = tk.StringVar(value="No")
                ttk.Combobox(form_window, textvariable=var, values=["Yes", "No"]).pack()
                entries[field["name"]] = var

    def inject_data(self, form_def, entries, form_window):
        new_item = {}
        for field in form_def["fields"]:
            value = entries[field["name"]].get()
            if field["type"] == "yes/no":
                new_item[field["name"]] = value == "Yes"
            elif field["type"] == "number":
                new_item[field["name"]] = float(value) if "." in value and value.replace(".", "").isdigit() else int(value) if value.isdigit() else value
            elif field["type"] == "null":
                new_item[field["name"]] = None
            elif field["type"] == "nested":
                new_item[field["name"]] = json.loads(value) if value else {}
            elif field["type"] == "list":
                new_item[field["name"]] = json.loads(value) if value else []
            else:
                new_item[field["name"]] = value
        self.json_data.append(new_item)
        self.update_views()
        form_window.destroy()

    def search_tree(self):
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        self._populate_tree_filtered("", self.json_data, query)

    def _populate_tree(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key != "name":  # Skip "name" to avoid duplication since it's the top-level node
                    node = self.tree.insert(parent, "end", text=key, values=(str(value),))
                    self._populate_tree(node, value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                node = self.tree.insert(parent, "end", text=f"[{i}]", values=(str(item),))
                self._populate_tree(node, item)
        else:
            self.tree.insert(parent, "end", text=str(data))

    def sort_tree(self):
        def sort_dict(d):
            if isinstance(d, dict):
                return {k: sort_dict(v) for k, v in sorted(d.items(), key=lambda x: str(x[1]))}
            return d
        self.json_data = sort_dict(self.json_data)
        self.update_views()

    def add_gear_form(self):
        gear_form = {
            "fields": [
                {"name": "name", "type": "text"},
                {"name": "level_range_min", "type": "number"},
                {"name": "level_range_max", "type": "number"},
                {"name": "slot", "type": "dropdown", "options": ["head", "chest", "legs", "weapon"]},
                {"name": "modifier", "type": "dropdown", "options": ["S", "A", "I", "W", "L"]},
                {"name": "stats_S", "type": "number"},
                {"name": "stats_A", "type": "number"},
                {"name": "stats_I", "type": "number"},
                {"name": "stats_W", "type": "number"},
                {"name": "stats_L", "type": "number"},
                {"name": "damage", "type": "null"},
                {"name": "armor_value", "type": "number"},
                {"name": "drop_rate", "type": "number"},
                {"name": "gold", "type": "number"},
                {"name": "boss_only", "type": "yes/no"}
            ],
            "conditions": []
        }  # New pre-built gear form
        self.custom_forms["Gear"] = gear_form
        form_file = os.path.join(self.forms_folder, "Gear.json")
        with open(form_file, 'w') as f:
            json.dump(gear_form, f, indent=4)
        self.update_forms_menu()
        messagebox.showinfo("Success", "Gear Form added! Find it under Forms > Gear.")

    def show_about(self):
        # You can customize this text below
        about_text = (
            "Frost Editor\n"
            "Version 0.0.5.9\n"
            "Created by Mona\n"
            "Credit to Elara for being such a complex file.\n"
            "A tool for editing JSON files with a tree view and custom forms.\n"
            "Built with Python and Tkinter.\n"
        )
        messagebox.showinfo("About", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = JSONEditor(root)
    root.mainloop()