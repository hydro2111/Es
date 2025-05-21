import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
from datetime import datetime
import os
from functools import partial

COLORS = {
    "bg_white": "#FFFFFF",
    "dark_green": "#156064",
    "medium_green": "#00917C",
    "light_green": "#22BFA0",
    "very_light_green": "#D6F6E1",
    "text_black": "#333333",
    "priority_high": "#00917C",
    "priority_medium": "#7AE582",
    "priority_low": "#CCCCCC"
}

class ExpertSystem:
    def __init__(self):
        self.resources = {
            "Food Pack": {"cost": 500, "available": 200},
            "Hygiene Kit": {"cost": 300, "available": 200},
            "Medical Kit": {"cost": 400, "available": 200},
            "School Supplies": {"cost": 250, "available": 200}
        }

        self.households = []
        self.budget = 150000
        self.allocated_resources = {}
        self.total_cost = 0

        if not os.path.exists("data"):
            os.makedirs("data")

        self.load_data()

    def add_household(self, name, members, ages):
        household_id = len(self.households) + 1
        household = {
            "id": household_id,
            "name": name,
            "members": members,
            "ages": ages,
            "priority_score": 0,
            "allocations": {}
        }

        household["priority_score"] = self.calculate_priority(household)

        self.households.append(household)
        self.allocated_resources[household_id] = {}

        self.save_data()
        return household

    def calculate_priority(self, household):
        score = 0

        score += household["members"] * 10

        for age in household["ages"]:
            if age < 5:
                score += 30
            elif age < 18:
                score += 20
            elif age > 60:
                score += 25

        return score

    def allocate_resources(self):
        sorted_households = sorted(
            self.households,
            key=lambda h: h["priority_score"],
            reverse=True
        )

        self.allocated_resources = {h["id"]: {} for h in self.households}
        self.total_cost = 0

        remaining_budget = self.budget

        for household in sorted_households:
            h_id = household["id"]
            members = household["members"]
            ages = household["ages"]

            children_under_5 = sum(1 for age in ages if age < 5)
            school_age = sum(1 for age in ages if 5 <= age < 18)
            elderly = sum(1 for age in ages if age > 60)

            self.allocated_resources[h_id] = {}

            food_packs = (members + 2) // 3
            if self.check_resource_availability("Food Pack", food_packs, remaining_budget):
                self.allocated_resources[h_id]["Food Pack"] = food_packs
                remaining_budget -= food_packs * self.resources["Food Pack"]["cost"]
                self.total_cost += food_packs * self.resources["Food Pack"]["cost"]
                self.resources["Food Pack"]["available"] -= food_packs

            hygiene_kits = (members + 3) // 4
            if self.check_resource_availability("Hygiene Kit", hygiene_kits, remaining_budget):
                self.allocated_resources[h_id]["Hygiene Kit"] = hygiene_kits
                remaining_budget -= hygiene_kits * self.resources["Hygiene Kit"]["cost"]
                self.total_cost += hygiene_kits * self.resources["Hygiene Kit"]["cost"]
                self.resources["Hygiene Kit"]["available"] -= hygiene_kits

            vulnerable_count = children_under_5 + elderly
            medical_kits = min(1, vulnerable_count)
            if vulnerable_count >= 3:
                medical_kits = 2

            if medical_kits > 0 and self.check_resource_availability("Medical Kit", medical_kits, remaining_budget):
                self.allocated_resources[h_id]["Medical Kit"] = medical_kits
                remaining_budget -= medical_kits * self.resources["Medical Kit"]["cost"]
                self.total_cost += medical_kits * self.resources["Medical Kit"]["cost"]
                self.resources["Medical Kit"]["available"] -= medical_kits

            if school_age > 0 and self.check_resource_availability("School Supplies", school_age, remaining_budget):
                self.allocated_resources[h_id]["School Supplies"] = school_age
                remaining_budget -= school_age * self.resources["School Supplies"]["cost"]
                self.total_cost += school_age * self.resources["School Supplies"]["cost"]
                self.resources["School Supplies"]["available"] -= school_age

        self.save_data()
        return self.allocated_resources, remaining_budget

    def check_resource_availability(self, resource_type, quantity, budget):
        if quantity <= 0:
            return False

        cost = quantity * self.resources[resource_type]["cost"]
        return (quantity <= self.resources[resource_type]["available"] and cost <= budget)

    def update_budget(self, new_budget):
        self.budget = new_budget
        self.save_data()

    def save_data(self):
        with open("data/households.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "name", "members", "ages", "priority_score"])
            for household in self.households:
                writer.writerow([
                    household["id"],
                    household["name"],
                    household["members"],
                    ",".join(map(str, household["ages"])),
                    household["priority_score"]
                ])

        with open("data/resources.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["resource", "cost", "available"])
            for resource, data in self.resources.items():
                writer.writerow([resource, data["cost"], data["available"]])

        with open("data/allocations.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["household_id", "resource", "quantity"])
            for h_id, allocations in self.allocated_resources.items():
                for resource, quantity in allocations.items():
                    writer.writerow([h_id, resource, quantity])

        with open("data/budget.txt", "w") as file:
            file.write(str(self.budget))

    def load_data(self):
        try:
            if os.path.exists("data/households.csv"):
                self.households = []
                with open("data/households.csv", "r") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        household = {
                            "id": int(row["id"]),
                            "name": row["name"],
                            "members": int(row["members"]),
                            "ages": [int(age) for age in row["ages"].split(",") if age],
                            "priority_score": float(row["priority_score"]),
                            "allocations": {}
                        }
                        self.households.append(household)

            if os.path.exists("data/resources.csv"):
                with open("data/resources.csv", "r") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        resource = row["resource"]
                        if resource in self.resources:
                            self.resources[resource]["cost"] = int(row["cost"])
                            self.resources[resource]["available"] = int(row["available"])

            if os.path.exists("data/allocations.csv"):
                self.allocated_resources = {}
                with open("data/allocations.csv", "r") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        h_id = int(row["household_id"])
                        resource = row["resource"]
                        quantity = int(row["quantity"])

                        if h_id not in self.allocated_resources:
                            self.allocated_resources[h_id] = {}

                        self.allocated_resources[h_id][resource] = quantity

            if os.path.exists("data/budget.txt"):
                with open("data/budget.txt", "r") as file:
                    self.budget = int(file.read().strip())

        except Exception as e:
            print(f"Error loading data: {e}")


class BarangayResourceApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.expert_system = ExpertSystem()

        self.title("Barangay Resource Distribution Expert System")
        self.geometry("1100x700")
        self.configure(bg=COLORS["bg_white"])

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.setup_styles()

        self.create_header()

        self.create_input_frame()
        self.create_dashboard_frame()
        self.create_allocation_frame()

        self.update_household_list()
        self.update_budget_display()
        self.update_resource_display()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background=COLORS["bg_white"])
        style.configure("TLabel", background=COLORS["bg_white"], foreground=COLORS["text_black"])
        style.configure("TButton", background=COLORS["medium_green"], foreground=COLORS["bg_white"])
        style.configure("Header.TLabel", font=("Arial", 18, "bold"), foreground=COLORS["dark_green"])
        style.configure("Subheader.TLabel", font=("Arial", 14, "bold"), foreground=COLORS["medium_green"])

        style.configure("Green.TButton",
                        background=COLORS["medium_green"],
                        foreground=COLORS["text_black"],
                        font=("Arial", 10, "bold"))

        style.configure("Treeview",
                        background=COLORS["bg_white"],
                        foreground=COLORS["text_black"],
                        fieldbackground=COLORS["bg_white"])

        style.map("Treeview",
                  background=[("selected", COLORS["medium_green"])],
                  foreground=[("selected", COLORS["bg_white"])])

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ttk.Label(header_frame, text="Barangay Resource Distribution Expert System",
                               style="Header.TLabel")
        title_label.pack(side="left")

        self.budget_var = tk.StringVar()
        budget_frame = ttk.Frame(header_frame)
        budget_frame.pack(side="right")

        budget_label = ttk.Label(budget_frame, text="Budget: ")
        budget_label.pack(side="left")

        self.budget_display = ttk.Label(budget_frame, textvariable=self.budget_var,
                                       font=("Arial", 12, "bold"), foreground=COLORS["dark_green"])
        self.budget_display.pack(side="left", padx=(0, 10))

        update_budget_btn = ttk.Button(budget_frame, text="Update Budget",
                                      style="Green.TButton",
                                      command=self.update_budget)
        update_budget_btn.pack(side="left")

    def create_input_frame(self):
        input_frame = ttk.LabelFrame(self.main_frame, text="Household Information Input")
        input_frame.pack(fill="x", pady=(0, 20), padx=5)

        form_frame = ttk.Frame(input_frame)
        form_frame.pack(fill="x", padx=10, pady=10)

        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill="x", pady=5)

        name_label = ttk.Label(name_frame, text="Name of Household Head:")
        name_label.pack(side="left", padx=(0, 10))

        self.name_entry = ttk.Entry(name_frame, width=40)
        self.name_entry.pack(side="left", fill="x", expand=True)

        members_frame = ttk.Frame(form_frame)
        members_frame.pack(fill="x", pady=5)

        members_label = ttk.Label(members_frame, text="Number of Household Members:")
        members_label.pack(side="left", padx=(0, 10))

        self.members_var = tk.StringVar(value="1")
        members_spinbox = ttk.Spinbox(members_frame, from_=1, to=20, textvariable=self.members_var, width=5)
        members_spinbox.pack(side="left")

        ages_frame = ttk.Frame(form_frame)
        ages_frame.pack(fill="x", pady=5)

        ages_label = ttk.Label(ages_frame, text="Ages (comma-separated, e.g. 45,42,18,15,2):")
        ages_label.pack(side="left", padx=(0, 10))

        self.ages_entry = ttk.Entry(ages_frame, width=40)
        self.ages_entry.pack(side="left", fill="x", expand=True)

        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill="x", pady=(10, 0), anchor="e")

        add_btn = ttk.Button(button_frame, text="Add Household", style="Green.TButton",
                            command=self.add_household)
        add_btn.pack(side="right")

    def create_dashboard_frame(self):
        dashboard_frame = ttk.LabelFrame(self.main_frame, text="Households Dashboard")
        dashboard_frame.pack(fill="both", expand=True, pady=(0, 20), padx=5)

        list_frame = ttk.Frame(dashboard_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("id", "name", "members", "max_age", "priority")
        self.household_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        self.household_tree.heading("id", text="ID")
        self.household_tree.heading("name", text="Household Head")
        self.household_tree.heading("members", text="Members")
        self.household_tree.heading("max_age", text="Max Age")
        self.household_tree.heading("priority", text="Priority Score")

        self.household_tree.column("id", width=50, anchor="center")
        self.household_tree.column("name", width=200)
        self.household_tree.column("members", width=80, anchor="center")
        self.household_tree.column("max_age", width=80, anchor="center")
        self.household_tree.column("priority", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.household_tree.yview)
        self.household_tree.configure(yscrollcommand=scrollbar.set)

        self.household_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = ttk.Frame(dashboard_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        view_details_btn = ttk.Button(button_frame, text="View Household Details",
                                     style="Green.TButton",
                                     command=self.view_household_details)
        view_details_btn.pack(side="left", padx=(0, 10))

        remove_btn = ttk.Button(button_frame, text="Remove Household",
                               style="Green.TButton",
                               command=self.remove_household)
        remove_btn.pack(side="left")

        allocate_btn = ttk.Button(button_frame, text="Allocate Resources",
                                 style="Green.TButton",
                                 command=self.allocate_resources_gui)
        allocate_btn.pack(side="right")

    def create_allocation_frame(self):
        allocation_frame = ttk.LabelFrame(self.main_frame, text="Resource Allocation")
        allocation_frame.pack(fill="x", pady=(0, 20), padx=5)

        left_frame = ttk.Frame(allocation_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        right_frame = ttk.Frame(allocation_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        resource_label = ttk.Label(left_frame, text="Available Resources", style="Subheader.TLabel")
        resource_label.pack(anchor="w", pady=(0, 5))

        columns = ("resource", "cost", "available")
        self.resource_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=5)

        self.resource_tree.heading("resource", text="Resource")
        self.resource_tree.heading("cost", text="Cost (₱)")
        self.resource_tree.heading("available", text="Available")

        self.resource_tree.column("resource", width=150)
        self.resource_tree.column("cost", width=100, anchor="center")
        self.resource_tree.column("available", width=100, anchor="center")

        resource_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.resource_tree.yview)
        self.resource_tree.configure(yscrollcommand=resource_scrollbar.set)

        self.resource_tree.pack(side="left", fill="both", expand=True)
        resource_scrollbar.pack(side="right", fill="y")

        allocation_label = ttk.Label(right_frame, text="Resource Allocations", style="Subheader.TLabel")
        allocation_label.pack(anchor="w", pady=(0, 5))

        columns = ("household", "resource", "quantity", "cost")
        self.allocation_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=5)

        self.allocation_tree.heading("household", text="Household")
        self.allocation_tree.heading("resource", text="Resource")
        self.allocation_tree.heading("quantity", text="Quantity")
        self.allocation_tree.heading("cost", text="Cost (₱)")

        self.allocation_tree.column("household", width=150)
        self.allocation_tree.column("resource", width=150)
        self.allocation_tree.column("quantity", width=80, anchor="center")
        self.allocation_tree.column("cost", width=100, anchor="center")

        allocation_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.allocation_tree.yview)
        self.allocation_tree.configure(yscrollcommand=allocation_scrollbar.set)

        self.allocation_tree.pack(side="left", fill="both", expand=True)
        allocation_scrollbar.pack(side="right", fill="y")

        export_frame = ttk.Frame(allocation_frame)
        export_frame.pack(fill="x", padx=10, pady=(10, 0))

        export_btn = ttk.Button(export_frame, text="Export Distribution Plan",
                               style="Green.TButton",
                               command=self.export_distribution_plan)
        export_btn.pack(side="right")

    def add_household(self):
        name = self.name_entry.get().strip()

        try:
            members = int(self.members_var.get())
            ages_text = self.ages_entry.get().strip()

            if ages_text:
                ages = [int(age.strip()) for age in ages_text.split(",")]
            else:
                messagebox.showerror("Input Error", "Ages cannot be empty.")
                return

            if not ages:
                messagebox.showerror("Input Error", "Please provide valid ages.")
                return

            if not name:
                messagebox.showerror("Input Error", "Please enter the name of the household head.")
                return

            if len(ages) != members:
                messagebox.showerror("Input Error",
                                    f"The number of ages ({len(ages)}) doesn't match the number of members ({members}).")
                return

            household = self.expert_system.add_household(name, members, ages)

            self.update_household_list()

            self.name_entry.delete(0, tk.END)
            self.members_var.set("1")
            self.ages_entry.delete(0, tk.END)

            messagebox.showinfo("Success", f"Household '{name}' added successfully.")

        except ValueError:
            messagebox.showerror("Input Error", "Invalid input for ages. Please use comma-separated numbers (e.g., 30,25,5).")
        except Exception as e:
             messagebox.showerror("Input Error", f"An unexpected error occurred: {str(e)}")

    def update_household_list(self):
        for item in self.household_tree.get_children():
            self.household_tree.delete(item)

        sorted_display_households = sorted(
            self.expert_system.households,
            key=lambda h: h["priority_score"],
            reverse=True
        )
        for household in sorted_display_households:
            max_age = max(household["ages"]) if household["ages"] else "N/A"
            self.household_tree.insert("", tk.END, values=(
                household["id"],
                household["name"],
                household["members"],
                max_age,
                household["priority_score"]
            ))

    def update_budget_display(self):
        self.budget_var.set(f"₱{self.expert_system.budget:,}")

    def update_resource_display(self):
        for item in self.resource_tree.get_children():
            self.resource_tree.delete(item)

        for resource, data in self.expert_system.resources.items():
            self.resource_tree.insert("", tk.END, values=(
                resource,
                f"{data['cost']:,}",
                data["available"]
            ))

    def update_allocation_display(self):
        for item in self.allocation_tree.get_children():
            self.allocation_tree.delete(item)

        sorted_households_for_alloc_display = sorted(
            self.expert_system.households,
            key=lambda h: max(h["ages"]) if h["ages"] else 0,
            reverse=True
        )

        for household_data in sorted_households_for_alloc_display:
            h_id = household_data["id"]
            household_name = household_data["name"]
            allocations = self.expert_system.allocated_resources.get(h_id, {})

            if allocations:
                for resource, quantity in allocations.items():
                    cost = quantity * self.expert_system.resources[resource]["cost"]
                    self.allocation_tree.insert("", tk.END, values=(
                        household_name,
                        resource,
                        quantity,
                        f"{cost:,}"
                    ))

    def update_budget(self):
        try:
            new_budget = simpledialog.askinteger("Update Budget",
                                               "Enter new budget amount (₱):",
                                               parent=self,
                                               initialvalue=self.expert_system.budget,
                                               minvalue=0)

            if new_budget is not None:
                self.expert_system.update_budget(new_budget)
                self.update_budget_display()
                messagebox.showinfo("Budget Updated", f"Budget updated to ₱{new_budget:,}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update budget: {str(e)}")

    def view_household_details(self):
        selected_item = self.household_tree.selection()
        if not selected_item:
            messagebox.showinfo("Selection Required", "Please select a household to view details.")
            return

        item_data = self.household_tree.item(selected_item)
        h_id = int(item_data["values"][0])

        household = None
        for h in self.expert_system.households:
            if h["id"] == h_id:
                household = h
                break

        if household:
            detail_window = tk.Toplevel(self)
            detail_window.title(f"Household Details: {household['name']}")
            detail_window.geometry("500x450")
            detail_window.configure(bg=COLORS["bg_white"])

            frame = ttk.Frame(detail_window)
            frame.pack(fill="both", expand=True, padx=20, pady=20)

            ttk.Label(frame, text=f"Household Head: {household['name']}",
                     font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))

            ttk.Label(frame, text=f"Number of Members: {household['members']}").pack(anchor="w", pady=2)

            max_age_display = max(household["ages"]) if household["ages"] else "N/A"
            ttk.Label(frame, text=f"Maximum Age in Household: {max_age_display}").pack(anchor="w", pady=2)
            ttk.Label(frame, text=f"Calculated Priority Score: {household['priority_score']}").pack(anchor="w", pady=2)

            ttk.Label(frame, text="Ages:").pack(anchor="w", pady=(10, 5))

            ages_frame = ttk.Frame(frame)
            ages_frame.pack(fill="x", pady=(0, 10))

            children_under_5 = [age for age in household["ages"] if age < 5]
            school_age = [age for age in household["ages"] if 5 <= age < 18]
            adults = [age for age in household["ages"] if 18 <= age <= 60]
            elderly = [age for age in household["ages"] if age > 60]

            if children_under_5:
                ttk.Label(ages_frame, text=f"Children under 5: {', '.join(map(str, children_under_5))}",
                         foreground=COLORS["priority_high"]).pack(anchor="w")

            if school_age:
                ttk.Label(ages_frame, text=f"School-age children: {', '.join(map(str, school_age))}",
                         foreground=COLORS["priority_medium"]).pack(anchor="w")

            if adults:
                ttk.Label(ages_frame, text=f"Adults: {', '.join(map(str, adults))}").pack(anchor="w")

            if elderly:
                ttk.Label(ages_frame, text=f"Elderly (60+): {', '.join(map(str, elderly))}",
                         foreground=COLORS["priority_high"]).pack(anchor="w")

            ttk.Label(frame, text="Allocated Resources:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))

            allocations_display_frame = ttk.Frame(frame)
            allocations_display_frame.pack(fill="x")

            allocations = self.expert_system.allocated_resources.get(h_id, {})
            if allocations:
                total_cost = 0
                for resource, quantity in allocations.items():
                    cost = quantity * self.expert_system.resources[resource]["cost"]
                    total_cost += cost
                    ttk.Label(allocations_display_frame, text=f"{resource}: {quantity} units (₱{cost:,})").pack(anchor="w")

                ttk.Label(frame, text=f"Total allocation cost: ₱{total_cost:,}",
                         font=("Arial", 12, "bold")).pack(anchor="w", pady=(5, 0))
            else:
                ttk.Label(allocations_display_frame, text="No resources allocated yet.").pack(anchor="w")

            ttk.Button(frame, text="Close", style="Green.TButton",
                      command=detail_window.destroy).pack(pady=(20, 0))

    def remove_household(self):
        selected_item = self.household_tree.selection()
        if not selected_item:
            messagebox.showinfo("Selection Required", "Please select a household to remove.")
            return

        item_data = self.household_tree.item(selected_item)
        h_id = int(item_data["values"][0])
        name = item_data["values"][1]

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove household '{name}'?"):
            self.expert_system.households = [h for h in self.expert_system.households if h["id"] != h_id]

            if h_id in self.expert_system.allocated_resources:
                del self.expert_system.allocated_resources[h_id]

            self.expert_system.save_data()

            self.update_household_list()
            self.update_allocation_display()

            messagebox.showinfo("Household Removed", f"Household '{name}' has been removed.")

    def allocate_resources_gui(self):
        if not self.expert_system.households:
            messagebox.showinfo("No Households", "There are no households in the system. Please add households first.")
            return

        if messagebox.askyesno("Confirm Allocation",
                              "This will allocate resources based on the priorty in households. Continue?"):
            try:
                allocations, remaining_budget = self.expert_system.allocate_resources()

                self.update_household_list()
                self.update_resource_display()
                self.update_allocation_display()

                messagebox.showinfo("Allocation Complete",
                                  f"Resources have been allocated. Remaining budget: ₱{remaining_budget:,}")
            except Exception as e:
                messagebox.showerror("Allocation Error", f"Failed to allocate resources: {str(e)}")

    def export_distribution_plan(self):
        if not self.expert_system.allocated_resources:
            if self.expert_system.households and not any(self.expert_system.allocated_resources.values()):
                messagebox.showinfo("No Allocations", "Resources have not been allocated yet. Please allocate first.")
                return
            elif not self.expert_system.households:
                messagebox.showinfo("No Data", "There are no households or allocations to export.")
                return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_path = os.getcwd()
            filename = os.path.join(base_path, f"distribution_plan_sorted_by_max_age_{timestamp}.csv")
            summary_filename = os.path.join(base_path, f"distribution_summary_sorted_by_max_age_{timestamp}.txt")

            sorted_export_households = sorted(
                self.expert_system.households,
                key=lambda h: max(h["ages"]) if h["ages"] else 0,
                reverse=True
            )

            with open(filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Household ID", "Household Head", "Members", "Max Age",
                    "Priority Score", "Resource", "Quantity", "Cost (₱)"
                ])

                for household in sorted_export_households:
                    h_id = household["id"]
                    allocations = self.expert_system.allocated_resources.get(h_id, {})
                    max_age_val = max(household["ages"]) if household["ages"] else "N/A"

                    if allocations:
                        has_written = False
                        for resource, quantity in allocations.items():
                            if quantity > 0:
                                cost = quantity * self.expert_system.resources[resource]["cost"]
                                writer.writerow([
                                    h_id,
                                    household["name"],
                                    household["members"],
                                    max_age_val,
                                    household["priority_score"],
                                    resource,
                                    quantity,
                                    cost
                                ])
                                has_written = True
                        if not has_written:
                            writer.writerow([
                                h_id,
                                household["name"],
                                household["members"],
                                max_age_val,
                                household["priority_score"],
                                "No Allocation",
                                0,
                                0
                            ])
                    else:
                        writer.writerow([
                            h_id,
                            household["name"],
                            household["members"],
                            max_age_val,
                            household["priority_score"],
                            "No Allocation",
                            0,
                            0
                        ])

            with open(summary_filename, "w", encoding="utf-8") as file:
                file.write("BARANGAY RESOURCE DISTRIBUTION SUMMARY (Sorted by Priority)\n")
                file.write("=" * 60 + "\n\n")
                file.write(f"Date: {datetime.now().strftime('%B %d, %Y')}\n")
                file.write(f"Total Budget: ₱{self.expert_system.budget:,}\n")
                file.write(f"Total Cost of Allocations: ₱{self.expert_system.total_cost:,}\n")
                file.write(f"Remaining Budget: ₱{self.expert_system.budget - self.expert_system.total_cost:,}\n\n")

                file.write("RESOURCE SUMMARY (After Allocation)\n")
                file.write("-" * 40 + "\n")
                for resource, data in self.expert_system.resources.items():
                    file.write(f"{resource}: {data['available']} units remaining at ₱{data['cost']} each\n")

                file.write("\nHOUSEHOLD SUMMARY\n")
                file.write("-" * 40 + "\n")
                file.write(f"Total Households Processed: {len(self.expert_system.households)}\n")

                total_children_under_5 = 0
                total_school_age = 0
                total_elderly = 0

                for household_item in self.expert_system.households:
                    for age in household_item["ages"]:
                        if age < 5:
                            total_children_under_5 += 1
                        elif 5 <= age < 18:
                            total_school_age += 1
                        elif age >= 60:
                            total_elderly += 1

                file.write(f"Total Children Under 5: {total_children_under_5}\n")
                file.write(f"Total School-age Children: {total_school_age}\n")
                file.write(f"Total Elderly (60+): {total_elderly}\n\n")

                file.write("EXPERT TEAM NOTES (Allocation based on Priority)\n")
                file.write("-" * 60 + "\n")
                file.write("Barangay Captain (Kap. Rosalie Mauricio): Resources were allocated prioritizing\n")
                file.write("households with the eldest members first. Vulnerability factors like young children\n")
                file.write("and elderly members within those households were then considered for specific kit types.\n\n")

                file.write("Councilor for Distribution (Kgd. Romy Colubong): Distribution plan accounts for\n")
                file.write("household size for food packs, and specific needs (school supplies, medical kits)\n")
                file.write("after the primary sorting by max age.\n\n")

                file.write("Treas. (Weng Panganiban): The current allocation utilized a portion of the available budget for resource distribution.\n")

            messagebox.showinfo("Export Complete",
                f"Distribution plan exported to:\n{filename}\nand summary to:\n{summary_filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export distribution plan:\n{str(e)}")

class BarangayCaptain:
    @staticmethod
    def assess_vulnerability(household):
        score = 0

        children_under_5 = sum(1 for age in household["ages"] if age < 5)
        elderly = sum(1 for age in household["ages"] if age > 60)

        score += children_under_5 * 30
        score += elderly * 25

        return score


class DistributionCouncilor:
    @staticmethod
    def recommend_resources(household):
        members = household["members"]
        ages = household["ages"]

        children_under_5 = sum(1 for age in ages if age < 5)
        school_age = sum(1 for age in ages if 5 <= age < 18)
        elderly = sum(1 for age in ages if age > 60)

        recommendations = {}

        food_packs = max(1, members // 3)
        recommendations["Food Pack"] = food_packs

        recommendations["Hygiene Kit"] = 1

        if elderly > 0 or children_under_5 > 0:
            recommendations["Medical Kit"] = 1
        else:
            recommendations["Medical Kit"] = 0

        recommendations["School Supplies"] = school_age

        return recommendations


class Treasurer:
    @staticmethod
    def approve_budget(total_cost, budget):
        if total_cost <= budget:
            return True, budget - total_cost
        else:
            return False, "Total cost exceeds available budget"

    @staticmethod
    def calculate_total_cost(allocations, resource_costs):
        total = 0

        for household_alloc in allocations.values():
            for resource, quantity in household_alloc.items():
                if resource in resource_costs:
                     total += quantity * resource_costs[resource]["cost"]
                else:
                    print(f"Warning: Resource '{resource}' not found in resource_costs during total cost calculation.")

        return total


if __name__ == "__main__":
    app = BarangayResourceApp()
    app.mainloop()
