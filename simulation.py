import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import heapq
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import queue
import time
import seaborn as sns

# Set matplotlib style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class DisasterAllocationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Disaster Resource Allocation System")
        self.root.geometry("1400x900")
        self.root.state('zoomed')  

        # Initialize variables
        self.households = []
        self.allocations = []
        self.simulation_running = False
        self.result_queue = queue.Queue()

        # Resource definitions and budget 
        self.resources = {
            "Food Pack": {"cost": 500, "available": 100},
            "Hygiene Kit": {"cost": 300, "available": 80},
            "Medical Kit": {"cost": 400, "available": 50},
            "Shelter Kit": {"cost": 600, "available": 40}
        }
        self.budget = 150000

        # Priors and likelihoods
        self.vulnerability_priors = {"low": 0.3, "medium": 0.4, "high": 0.3}
        self.size_priors = {2: 0.113, 3: 0.169, 4: 0.452, 5: 0.226, 6: 0.03, 7: 0.01}
        self.vulnerability_likelihoods = {
            "low": {"low": 0.8, "medium": 0.15, "high": 0.05},
            "medium": {"low": 0.1, "medium": 0.8, "high": 0.1},
            "high": {"low": 0.05, "medium": 0.15, "high": 0.8}
        }
        self.vulnerability_weights = {"low": 1, "medium": 2, "high": 3}

        self.setup_gui()

    def setup_gui(self):
        # Create main container with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Configuration
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        self.setup_config_tab()

        # Tab 2: Simulation
        self.sim_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sim_frame, text="Simulation")
        self.setup_simulation_tab()

        # Tab 3: Results
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self.setup_results_tab()

        # Tab 4: Visualizations
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="Visualizations")
        self.setup_visualization_tab()

    def setup_config_tab(self):
        # Configuration panel
        config_panel = ttk.LabelFrame(self.config_frame, text="Simulation Configuration", padding=10)
        config_panel.pack(fill='x', padx=10, pady=10)

        # Number of households
        ttk.Label(config_panel, text="Number of Households:").grid(row=0, column=0, sticky='w', pady=5)
        self.num_households = tk.IntVar(value=100)
        households_spinbox = ttk.Spinbox(config_panel, from_=10, to=1000, textvariable=self.num_households, width=10)
        households_spinbox.grid(row=0, column=1, sticky='w', pady=5)

        # Budget
        ttk.Label(config_panel, text="Total Budget (₱):").grid(row=1, column=0, sticky='w', pady=5)
        self.budget_var = tk.IntVar(value=self.budget)
        budget_spinbox = ttk.Spinbox(config_panel, from_=50000, to=500000, textvariable=self.budget_var, width=10)
        budget_spinbox.grid(row=1, column=1, sticky='w', pady=5)

        # Resource configuration
        resource_panel = ttk.LabelFrame(self.config_frame, text="Resource Configuration", padding=10)
        resource_panel.pack(fill='both', expand=True, padx=10, pady=10)

        # Headers
        ttk.Label(resource_panel, text="Resource", font=('Arial', 10, 'bold')).grid(row=0, column=0, pady=5)
        ttk.Label(resource_panel, text="Cost (₱)", font=('Arial', 10, 'bold')).grid(row=0, column=1, pady=5)
        ttk.Label(resource_panel, text="Available", font=('Arial', 10, 'bold')).grid(row=0, column=2, pady=5)

        self.resource_vars = {}
        for i, (resource, data) in enumerate(self.resources.items(), 1):
            ttk.Label(resource_panel, text=resource).grid(row=i, column=0, sticky='w', pady=5)

            cost_var = tk.IntVar(value=data['cost'])
            cost_spinbox = ttk.Spinbox(resource_panel, from_=100, to=2000, textvariable=cost_var, width=10)
            cost_spinbox.grid(row=i, column=1, pady=5)

            avail_var = tk.IntVar(value=data['available'])
            avail_spinbox = ttk.Spinbox(resource_panel, from_=10, to=500, textvariable=avail_var, width=10)
            avail_spinbox.grid(row=i, column=2, pady=5)

            self.resource_vars[resource] = {'cost': cost_var, 'available': avail_var}

        # Update resources button
        ttk.Button(resource_panel, text="Update Configuration",
                  command=self.update_configuration).grid(row=len(self.resources)+1, column=0, columnspan=3, pady=10)

    def setup_simulation_tab(self):
        # Control panel
        control_panel = ttk.LabelFrame(self.sim_frame, text="Simulation Control", padding=10)
        control_panel.pack(fill='x', padx=10, pady=10)

        # Simulation buttons
        self.run_button = ttk.Button(control_panel, text="Run Simulation", command=self.run_simulation)
        self.run_button.pack(side='left', padx=5)

        self.stop_button = ttk.Button(control_panel, text="Stop Simulation", command=self.stop_simulation, state='disabled')
        self.stop_button.pack(side='left', padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(control_panel, mode='indeterminate')
        self.progress.pack(side='left', fill='x', expand=True, padx=10)

        # Status label
        self.status_label = ttk.Label(control_panel, text="Ready to simulate")
        self.status_label.pack(side='right', padx=5)

        # Real-time output
        output_panel = ttk.LabelFrame(self.sim_frame, text="Simulation Output", padding=10)
        output_panel.pack(fill='both', expand=True, padx=10, pady=10)

        self.output_text = scrolledtext.ScrolledText(output_panel, height=20)
        self.output_text.pack(fill='both', expand=True)

    def setup_results_tab(self):
        # Summary panel
        summary_panel = ttk.LabelFrame(self.results_frame, text="Allocation Summary", padding=10)
        summary_panel.pack(fill='x', padx=10, pady=10)

        # Summary labels
        self.summary_labels = {}
        summary_items = [
            "Total Households Served", "Remaining Budget", "Average Priority",
            "Average Items per Household", "Average Cost per Household",
            "Min Waiting Time", "Average Waiting Time", "Max Waiting Time"
        ]

        for i, item in enumerate(summary_items):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(summary_panel, text=f"{item}:", font=('Arial', 10, 'bold')).grid(row=row, column=col, sticky='w', padx=5, pady=5)
            label = ttk.Label(summary_panel, text="--")
            label.grid(row=row, column=col+1, sticky='w', padx=5, pady=5)
            self.summary_labels[item] = label

        # Detailed results table
        table_panel = ttk.LabelFrame(self.results_frame, text="Detailed Allocation Results", padding=10)
        table_panel.pack(fill='both', expand=True, padx=10, pady=10)

        # Create treeview for results
        columns = ["ID", "True Size", "Priority", "Food", "Hygiene", "Medical", "Shelter", "Total Cost"]
        self.results_tree = ttk.Treeview(table_panel, columns=columns, show='headings', height=15)

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=80)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_panel, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(table_panel, orient='horizontal', command=self.results_tree.xview)
        self.results_tree.configure(xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        table_panel.grid_rowconfigure(0, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)

        # Export button
        ttk.Button(table_panel, text="Export to CSV", command=self.export_results).grid(row=2, column=0, pady=10)

    def setup_visualization_tab(self):
        # Create frame for controls
        controls_frame = ttk.Frame(self.viz_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)

        # Control buttons
        ttk.Button(controls_frame, text="Generate All Plots", command=self.generate_plots).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Save Plots", command=self.save_plots).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Clear Plots", command=self.clear_plots).pack(side='left', padx=5)

        # Individual plot buttons
        ttk.Label(controls_frame, text=" | Individual Plots:").pack(side='left', padx=10)
        ttk.Button(controls_frame, text="Size Distribution", command=lambda: self.generate_single_plot('size')).pack(side='left', padx=2)
        ttk.Button(controls_frame, text="Priority vs Cost", command=lambda: self.generate_single_plot('priority')).pack(side='left', padx=2)
        ttk.Button(controls_frame, text="Resource Allocation", command=lambda: self.generate_single_plot('resources')).pack(side='left', padx=2)

        # Create matplotlib figure with proper size
        self.fig = Figure(figsize=(16, 12), dpi=80)
        self.canvas = FigureCanvasTkAgg(self.fig, self.viz_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

        # Add toolbar for navigation
        toolbar_frame = ttk.Frame(self.viz_frame)
        toolbar_frame.pack(fill='x', padx=10, pady=5)

        # Navigation toolbar (optional - requires matplotlib.backends.backend_tkagg.NavigationToolbar2Tk)
        try:
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()
        except ImportError:
            ttk.Label(toolbar_frame, text="Navigation toolbar not available").pack()

    def update_configuration(self):
        """Update resource configuration from GUI inputs"""
        self.budget = self.budget_var.get()
        for resource, vars_dict in self.resource_vars.items():
            self.resources[resource]['cost'] = vars_dict['cost'].get()
            self.resources[resource]['available'] = vars_dict['available'].get()

        self.log_output("Configuration updated successfully")
        messagebox.showinfo("Success", "Configuration updated successfully!")

    def log_output(self, message):
        """Add message to output text widget"""
        timestamp = time.strftime('%H:%M:%S')
        self.output_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def run_simulation(self):
        """Run the simulation in a separate thread"""
        if self.simulation_running:
            return

        self.simulation_running = True
        self.run_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress.start()
        self.status_label.config(text="Running simulation...")

        # Clear previous output
        self.output_text.delete(1.0, tk.END)

        # Start simulation in separate thread
        thread = threading.Thread(target=self.simulation_worker)
        thread.daemon = True
        thread.start()

        # Check for results periodically
        self.root.after(100, self.check_simulation_progress)

    def simulation_worker(self):
        """Worker function for simulation thread"""
        try:
            self.log_output("Starting simulation...")
            self.log_output(f"Budget: ₱{self.budget:,}")
            self.log_output(f"Number of households: {self.num_households.get()}")

            # Generate households
            self.log_output(f"Generating {self.num_households.get()} households...")
            households = self.generate_households(self.num_households.get())

            # Run allocation simulation
            self.log_output("Running allocation algorithm...")
            allocations, remaining = self.simulate_allocation(households)

            # Put results in queue
            self.result_queue.put(('success', allocations, remaining))
            self.log_output("Simulation completed successfully!")

        except Exception as e:
            self.result_queue.put(('error', str(e)))
            self.log_output(f"Simulation error: {str(e)}")

    def check_simulation_progress(self):
        """Check if simulation is complete"""
        try:
            result = self.result_queue.get_nowait()

            if result[0] == 'success':
                allocations, remaining = result[1], result[2]
                self.allocations = allocations
                self.display_results(allocations, remaining)
                self.simulation_complete()
            elif result[0] == 'error':
                messagebox.showerror("Simulation Error", result[1])
                self.simulation_complete()

        except queue.Empty:
            if self.simulation_running:
                self.root.after(100, self.check_simulation_progress)

    def simulation_complete(self):
        """Clean up after simulation"""
        self.simulation_running = False
        self.run_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress.stop()
        self.status_label.config(text="Simulation complete")

    def stop_simulation(self):
        """Stop the running simulation"""
        self.simulation_running = False
        self.simulation_complete()
        self.log_output("Simulation stopped by user")

    def display_results(self, allocations, remaining):
        """Display simulation results in the GUI"""
        df = pd.DataFrame(allocations)

        # Update summary
        total_served = len(df[df[['Food Pack', 'Hygiene Kit', 'Medical Kit', 'Shelter Kit']].sum(axis=1) > 0])
        avg_priority = df['Priority'].mean()
        avg_items = df[['Food Pack', 'Hygiene Kit', 'Medical Kit', 'Shelter Kit']].sum(axis=1).mean()
        avg_cost = df['Total Cost'].mean()
        min_wait = max(1, df['Waiting Time'].min()) * 10
        avg_wait = df['Waiting Time'].mean() 
        max_wait = df['Waiting Time'].max() 


        self.summary_labels["Total Households Served"].config(text=str(total_served))
        self.summary_labels["Remaining Budget"].config(text=f"₱{remaining:,}")
        self.summary_labels["Average Priority"].config(text=f"{avg_priority:.2f}")
        self.summary_labels["Average Items per Household"].config(text=f"{avg_items:.2f}")
        self.summary_labels["Average Cost per Household"].config(text=f"₱{avg_cost:,.2f}")
        self.summary_labels["Min Waiting Time"].config(text=f"{min_wait:.0f}")
        self.summary_labels["Average Waiting Time"].config(text=f"{avg_wait:.1f}")
        self.summary_labels["Max Waiting Time"].config(text=f"{max_wait:.0f}")
        # Clear and populate results tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        for _, row in df.iterrows():
            values = (
                row['Household ID'],
                row['True Size'],
                f"{row['Priority']:.1f}",
                row['Food Pack'],
                row['Hygiene Kit'],
                row['Medical Kit'],
                row['Shelter Kit'],
                f"₱{row['Total Cost']:,}"
            )
            self.results_tree.insert('', 'end', values=values)

        # Switch to results tab
        self.notebook.select(2)

        # Log completion
        self.log_output(f"Results displayed: {total_served} households served, ₱{remaining:,} remaining")

    def clear_plots(self):
        """Clear all plots"""
        self.fig.clear()
        self.canvas.draw()

    def generate_single_plot(self, plot_type):
        """Generate a single plot based on type"""
        if not self.allocations:
            messagebox.showwarning("No Data", "Please run a simulation first!")
            return

        df = pd.DataFrame(self.allocations)
        self.fig.clear()

        if plot_type == 'size':
            ax = self.fig.add_subplot(1, 1, 1)
            ax.hist(df['True Size'], bins=np.arange(1.5, 8.5, 1),
                   edgecolor='black', alpha=0.7, color='skyblue')
            ax.set_title('Household Size Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Household Size')
            ax.set_ylabel('Count')
            ax.grid(True, alpha=0.3)

        elif plot_type == 'priority':
            ax = self.fig.add_subplot(1, 1, 1)
            scatter = ax.scatter(df['Priority'], df['Total Cost'],
                               alpha=0.6, c=df['True Size'], cmap='viridis', s=50)
            ax.set_xlabel('Priority Score')
            ax.set_ylabel('Total Cost (₱)')
            ax.set_title('Priority vs Cost Allocation', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            cbar = self.fig.colorbar(scatter, ax=ax)
            cbar.set_label('Household Size')

        elif plot_type == 'resources':
            ax = self.fig.add_subplot(1, 1, 1)
            vuln_groups = df.groupby('Reported Vulnerability')[['Food Pack', 'Hygiene Kit', 'Medical Kit', 'Shelter Kit']].sum()
            vuln_groups.plot(kind='bar', ax=ax, stacked=True, width=0.8)
            ax.set_title('Resource Allocation by Vulnerability Level', fontsize=14, fontweight='bold')
            ax.set_xlabel('Vulnerability Level')
            ax.set_ylabel('Total Resources Allocated')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)

        self.fig.tight_layout()
        self.canvas.draw()

    def generate_plots(self):
        """Generate comprehensive visualization plots"""
        if not self.allocations:
            messagebox.showwarning("No Data", "Please run a simulation first!")
            return

        try:
            df = pd.DataFrame(self.allocations)

            # Clear previous plots
            self.fig.clear()

            # Create subplots with better spacing
            gs = self.fig.add_gridspec(3, 3, hspace=0.4, wspace=0.4,
                                     left=0.05, right=0.95, top=0.95, bottom=0.05)

            # Plot 1: Household size distribution
            ax1 = self.fig.add_subplot(gs[0, 0])
            counts, bins, patches = ax1.hist(df['True Size'], bins=np.arange(1.5, 8.5, 1),
                                           edgecolor='black', alpha=0.7, color='skyblue')
            ax1.set_title('Household Size Distribution', fontweight='bold')
            ax1.set_xlabel('Household Size')
            ax1.set_ylabel('Count')
            ax1.grid(True, alpha=0.3)

            # Add count labels on bars
            for count, patch in zip(counts, patches):
                if count > 0:
                    ax1.text(patch.get_x() + patch.get_width()/2, patch.get_height(),
                            f'{int(count)}', ha='center', va='bottom')

            # Plot 2: Priority vs Cost scatter
            ax2 = self.fig.add_subplot(gs[0, 1])
            scatter = ax2.scatter(df['Priority'], df['Total Cost'],
                                alpha=0.6, c=df['True Size'], cmap='viridis', s=50)
            ax2.set_xlabel('Priority Score')
            ax2.set_ylabel('Total Cost (₱)')
            ax2.set_title('Priority vs Cost Allocation', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            cbar1 = self.fig.colorbar(scatter, ax=ax2)
            cbar1.set_label('Household Size')

            # Plot 3: Resource allocation by vulnerability
            ax3 = self.fig.add_subplot(gs[0, 2])
            vuln_groups = df.groupby('Reported Vulnerability')[['Food Pack', 'Hygiene Kit', 'Medical Kit', 'Shelter Kit']].sum()
            vuln_groups.plot(kind='bar', ax=ax3, stacked=True, width=0.8)
            ax3.set_title('Resource Allocation by Vulnerability', fontweight='bold')
            ax3.set_xlabel('Vulnerability Level')
            ax3.set_ylabel('Total Resources Allocated')
            ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
            ax3.grid(True, alpha=0.3)
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=0)

            # Plot 4: Cost distribution
            ax4 = self.fig.add_subplot(gs[1, 0])
            ax4.hist(df['Total Cost'], bins=20, edgecolor='black', alpha=0.7, color='lightgreen')
            ax4.axvline(df['Total Cost'].mean(), color='red', linestyle='--',
                       label=f'Mean: ₱{df["Total Cost"].mean():.0f}')
            ax4.set_title('Cost Distribution', fontweight='bold')
            ax4.set_xlabel('Total Cost (₱)')
            ax4.set_ylabel('Number of Households')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

            # Plot 5: Items allocated vs household size
            ax5 = self.fig.add_subplot(gs[1, 1])
            df['Total Items'] = df[['Food Pack', 'Hygiene Kit', 'Medical Kit', 'Shelter Kit']].sum(axis=1)
            size_items = df.groupby('True Size')['Total Items'].mean()
            bars = ax5.bar(size_items.index, size_items.values, color='orange',
                          edgecolor='black', alpha=0.8)
            ax5.set_title('Average Items by Household Size', fontweight='bold')
            ax5.set_xlabel('Household Size')
            ax5.set_ylabel('Average Items Allocated')
            ax5.grid(True, alpha=0.3)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax5.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom')

            # Plot 6: Budget utilization pie chart
            ax6 = self.fig.add_subplot(gs[1, 2])
            total_cost = df['Total Cost'].sum()
            remaining = self.budget - total_cost
            utilization = (total_cost / self.budget) * 100

            sizes = [total_cost, remaining]
            labels = [f'Used Budget\n₱{total_cost:,}\n({utilization:.1f}%)',
                     f'Remaining Budget\n₱{remaining:,}\n({100-utilization:.1f}%)']
            colors = ['#ff9999', '#66b3ff']
            wedges, texts, autotexts = ax6.pie(sizes, labels=labels, autopct='',
                                             colors=colors, startangle=90)
            ax6.set_title('Budget Utilization', fontweight='bold')

            # Plot 7: Vulnerability score distribution
            ax7 = self.fig.add_subplot(gs[2, 0])
            vulnerability_mapping = {'low': 1, 'medium': 2, 'high': 3}
            df['Vulnerability_Numeric'] = df['Reported Vulnerability'].map(vulnerability_mapping)
            ax7.hist(df['Vulnerability_Numeric'], bins=[0.5, 1.5, 2.5, 3.5],
                    edgecolor='black', alpha=0.7, color='coral')
            ax7.set_xticks([1, 2, 3])
            ax7.set_xticklabels(['Low', 'Medium', 'High'])
            ax7.set_title('Vulnerability Distribution', fontweight='bold')
            ax7.set_xlabel('Vulnerability Level')
            ax7.set_ylabel('Count')
            ax7.grid(True, alpha=0.3)

            # Plot 8: Priority distribution by vulnerability
            ax8 = self.fig.add_subplot(gs[2, 1])
            for vuln in ['low', 'medium', 'high']:
                subset = df[df['Reported Vulnerability'] == vuln]['Priority']
                ax8.hist(subset, alpha=0.7, label=f'{vuln.capitalize()} ({len(subset)})', bins=15)
            ax8.set_title('Priority Score Distribution by Vulnerability', fontweight='bold')
            ax8.set_xlabel('Priority Score')
            ax8.set_ylabel('Count')
            ax8.legend()
            ax8.grid(True, alpha=0.3)

            # Plot 9: Resource efficiency (items per cost)
            ax9 = self.fig.add_subplot(gs[2, 2])
            df['Efficiency'] = df['Total Items'] / (df['Total Cost'] + 1)  # +1 to avoid division by zero
            efficiency_by_size = df.groupby('True Size')['Efficiency'].mean()
            bars = ax9.bar(efficiency_by_size.index, efficiency_by_size.values,
                          color='purple', alpha=0.7, edgecolor='black')
            ax9.set_title('Resource Efficiency by Household Size', fontweight='bold')
            ax9.set_xlabel('Household Size')
            ax9.set_ylabel('Items per ₱ Cost')
            ax9.grid(True, alpha=0.3)

            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax9.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=8)

            # Refresh canvas
            self.canvas.draw()

            # Switch to visualization tab
            self.notebook.select(3)
            self.log_output("Comprehensive visualizations generated successfully")

        except Exception as e:
            messagebox.showerror("Visualization Error", f"Failed to generate plots: {str(e)}")
            self.log_output(f"Visualization error: {str(e)}")

    def save_plots(self):
        """Save the current plots to file"""
        if not self.allocations:
            messagebox.showwarning("No Data", "Please generate plots first!")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")],
                title="Save Plots As..."
            )

            if filename:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Success", f"Plots saved as '{filename}'")
                self.log_output(f"Plots saved as: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save plots: {str(e)}")

    def export_results(self):
        """Export results to CSV file"""
        if not self.allocations:
            messagebox.showwarning("No Data", "Please run a simulation first!")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
                title="Export Results As..."
            )

            if filename:
                df = pd.DataFrame(self.allocations)
                if filename.endswith('.xlsx'):
                    df.to_excel(filename, index=False, engine='openpyxl')
                else:
                    df.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Results exported to '{filename}'")
                self.log_output(f"Results exported to: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {str(e)}")


    # Simulation methods (from original code)
    def bayesian_vulnerability_score(self, reported):
        """Calculate Bayesian vulnerability score based on reported level"""
        posterior = {}
        total = 0
        for true_level in self.vulnerability_priors:
            likelihood = self.vulnerability_likelihoods[true_level][reported]
            prior = self.vulnerability_priors[true_level]
            posterior[true_level] = likelihood * prior
            total += posterior[true_level]

        # Normalize posterior
        for k in posterior:
            posterior[k] /= total

        # Calculate expected vulnerability score
        return sum(self.vulnerability_weights[k] * posterior[k] for k in posterior)

    def size_likelihood(self, true_size, reported_size):
        """Calculate likelihood of reported size given true size"""
        diff = abs(true_size - reported_size)
        if diff == 0:
            return 0.7
        elif diff == 1:
            return 0.2
        elif diff == 2:
            return 0.1
        return 0.01

    def bayesian_expected_members(self, reported_size):
        """Calculate expected household members using Bayesian inference"""
        posterior = {}
        total = 0

        for true_size in self.size_priors:
            likelihood = self.size_likelihood(true_size, reported_size)
            prior = self.size_priors[true_size]
            posterior[true_size] = likelihood * prior
            total += posterior[true_size]

        # Normalize posterior
        for k in posterior:
            posterior[k] /= total

        # Calculate expected size
        return sum(k * posterior[k] for k in posterior)

    def generate_households(self, n):
        """Generate n households with realistic characteristics"""
        households = []
        possible_sizes = list(self.size_priors.keys())
        size_probs = list(self.size_priors.values())
        vulnerability_levels = list(self.vulnerability_priors.keys())
        vulnerability_probs = list(self.vulnerability_priors.values())

        for i in range(n):
            # Generate true household size based on priors
            true_size = np.random.choice(possible_sizes, p=size_probs)

            # Generate ages for household members
            ages = np.random.randint(1, 90, size=true_size).tolist()

            # Add reporting noise to size
            report_noise = np.random.choice([-1, 0, 1], p=[0.2, 0.6, 0.2])
            reported_size = max(2, min(7, true_size + report_noise))

            # Generate reported vulnerability level
            reported_vulnerability = np.random.choice(vulnerability_levels, p=vulnerability_probs)

            # Create household object
            households.append(self.Household(i + 1, ages, reported_size, reported_vulnerability, self))

        return households

    def simulate_allocation(self, households):
        """Simulate resource allocation using priority queue and track waiting time"""
        queue_heap = []
        for h in households:
            heapq.heappush(queue_heap, h)

        allocations = []
        remaining_budget = self.budget
        resource_state = {k: v['available'] for k, v in self.resources.items()}

        current_time = 0  # Simulated time step

        while queue_heap and remaining_budget > 0:
            h = heapq.heappop(queue_heap)
            h_alloc = {}
            total_cost = 0

            # Simulated waiting time (could be tied to position in queue)
            h.waiting_time = current_time

            food = max(1, int(round(h.expected_members / 3)))
            hygiene = max(1, int(round(h.expected_members / 4)))
            medical = 1 if h.elderly > 0 or h.children > 0 else 0
            shelter = 1 if h.expected_vulnerability_score >= 2.5 else 0

            needs = {
                "Food Pack": food,
                "Hygiene Kit": hygiene,
                "Medical Kit": medical,
                "Shelter Kit": shelter
            }

            for item, qty in needs.items():
                cost = qty * self.resources[item]["cost"]
                if qty <= resource_state[item] and remaining_budget >= cost:
                    h_alloc[item] = qty
                    resource_state[item] -= qty
                    remaining_budget -= cost
                    total_cost += cost
                else:
                    h_alloc[item] = 0

            allocation_record = {
                "Household ID": h.id,
                "True Ages": h.ages,
                "True Size": h.true_size,
                "Reported Size": h.reported_size,
                "Expected Size": round(h.expected_members, 2),
                "Children": h.children,
                "Elderly": h.elderly,
                "Reported Vulnerability": h.reported_vulnerability,
                "Expected Vulnerability Score": round(h.expected_vulnerability_score, 2),
                "Priority": round(h.priority, 2),
                **h_alloc,
                "Total Cost": total_cost,
                "Waiting Time": h.waiting_time  # Add this field
            }
            allocations.append(allocation_record)

            current_time += 1  # Increment simulated time step

        return allocations, remaining_budget

    class Household:
        """Household class representing a family unit in the disaster scenario"""

        def __init__(self, id, true_ages, reported_size, reported_vulnerability, parent):
            self.id = id
            self.ages = true_ages
            self.reported_size = reported_size
            self.true_size = len(true_ages)
            self.children = sum(1 for a in true_ages if a < 18)
            self.elderly = sum(1 for a in true_ages if a > 60)
            self.reported_vulnerability = reported_vulnerability

            # Calculate Bayesian estimates
            self.expected_members = parent.bayesian_expected_members(reported_size)
            self.expected_vulnerability_score = parent.bayesian_vulnerability_score(reported_vulnerability)

            # Calculate priority score
            self.priority = self.calculate_priority()

        def calculate_priority(self):
            """Calculate household priority based on multiple factors"""
            priority = (
                self.expected_members * 5 +      # Base need
                self.children * 10 +             # Children need extra care
                self.elderly * 15 +              # Elderly are vulnerable
                self.expected_vulnerability_score * 25  # Vulnerability multiplier
            )
            return priority

        def __lt__(self, other):
            """Comparison for heap (max heap behavior with negative priorities)"""
            return self.priority > other.priority

        def __repr__(self):
            return f"Household({self.id}, size={self.true_size}, priority={self.priority:.1f})"


# Main application runner
def main():
    """Main function to run the application"""
    try:
        # Create and configure the main window
        root = tk.Tk()

        # Set the application icon (optional)
        try:
            root.iconbitmap('disaster_icon.ico')  # Add icon if available
        except:
            pass

        # Create the application
        app = DisasterAllocationGUI(root)

        # Handle window closing
        def on_closing():
            if app.simulation_running:
                if messagebox.askokcancel("Quit", "Simulation is running. Do you want to quit?"):
                    app.stop_simulation()
                    root.destroy()
            else:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Start the GUI event loop
        root.mainloop()

    except Exception as e:
        print(f"Application error: {str(e)}")
        messagebox.showerror("Application Error", f"Failed to start application: {str(e)}")


# Entry point
if __name__ == "__main__":
    main()
