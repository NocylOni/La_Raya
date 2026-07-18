"""Module 5: Orders & Results tab (labs, imaging, procedures, pathology,
with results and trend graphs)."""
from __future__ import annotations

from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.db.dao import orders as orders_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values


class OrdersTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._selected_order_id: int | None = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.orders_panel = RecordPanel(
            self,
            columns=[("order_type", "Type"), ("order_name", "Order"),
                     ("ordered_date", "Date"), ("status", "Status")],
            fields=[
                FieldSpec("order_type", "Type", kind="combo",
                          options=["lab", "imaging", "procedure", "pathology"]),
                FieldSpec("order_name", "Order Name"),
                FieldSpec("ordered_date", "Ordered Date"),
                FieldSpec("status", "Status", kind="combo",
                          options=["ordered", "completed", "cancelled"]),
                FieldSpec("ordered_by", "Ordered By"),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_orders,
            on_create=self._create_order,
            on_delete=orders_dao.delete_order,
        )
        self.orders_panel.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.orders_panel.tree.bind("<<TreeviewSelect>>", self._on_order_select, add="+")

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.results_panel = RecordPanel(
            right,
            columns=[("result_name", "Test"), ("value", "Value"),
                     ("abnormal_flag", "Flag"), ("result_date", "Date")],
            fields=[
                FieldSpec("result_name", "Test Name"),
                FieldSpec("value", "Value"),
                FieldSpec("numeric_value", "Numeric Value"),
                FieldSpec("unit", "Unit"),
                FieldSpec("reference_low", "Reference Low"),
                FieldSpec("reference_high", "Reference High"),
                FieldSpec("result_date", "Result Date"),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_results,
            on_create=self._create_result,
            on_delete=orders_dao.delete_result,
            on_change=self._refresh_graph,
        )
        self.results_panel.grid(row=0, column=0, sticky="nsew")

        graph_frame = ttk.LabelFrame(right, text="Result Trend")
        graph_frame.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(graph_frame)
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(toolbar, text="Test name:").pack(side="left")
        self.trend_combo = ttk.Combobox(toolbar, state="normal", width=25)
        self.trend_combo.pack(side="left", padx=4)
        ttk.Button(toolbar, text="Plot", command=self._refresh_graph).pack(side="left")

        self.figure = Figure(figsize=(4.2, 3), dpi=90)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    def load_patient(self):
        self._selected_order_id = None
        self.orders_panel.refresh()
        self.results_panel.refresh()
        self._refresh_graph()

    def _on_order_select(self, _event=None):
        selection = self.orders_panel.tree.selection()
        self._selected_order_id = int(selection[0]) if selection else None
        self.results_panel.refresh()

    # ------------------------------------------------------------ orders
    def _list_orders(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return orders_dao.list_orders(self.ctx.db, pid)

    def _create_order(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        order_type = data.pop("order_type")
        order_name = data.pop("order_name")
        order_id = orders_dao.create_order(self.ctx.db, pid, order_type, order_name, **data)
        self.ctx.audit("CREATE_ORDER", "order", order_id, order_name)
        return order_id

    # ------------------------------------------------------------ results
    def _list_results(self):
        if self._selected_order_id is None:
            return []
        return orders_dao.list_results(self.ctx.db, self.ctx.current_patient_id or 0,
                                        order_id=self._selected_order_id)

    def _create_result(self, data):
        pid = self.ctx.require_patient()
        if self._selected_order_id is None:
            raise ValueError("Select an order first")
        data = clean_form_values(
            data, numeric_fields=["numeric_value", "reference_low", "reference_high"]
        )
        result_name = data.pop("result_name")
        result_id = orders_dao.add_result(
            self.ctx.db, self._selected_order_id, pid, result_name, **data
        )
        self.ctx.audit("ADD_RESULT", "result", result_id, result_name)
        return result_id

    def _refresh_graph(self):
        self.ax.clear()
        pid = self.ctx.current_patient_id
        test_name = self.trend_combo.get()
        if pid is not None and test_name:
            trend = orders_dao.result_trend(self.ctx.db, pid, test_name)
            xs = [r["result_date"] for r in trend if r["numeric_value"] is not None]
            ys = [r["numeric_value"] for r in trend if r["numeric_value"] is not None]
            if xs:
                self.ax.plot(range(len(xs)), ys, marker="o", color="darkred")
                self.ax.set_xticks(range(len(xs)))
                self.ax.set_xticklabels([x[:10] for x in xs], rotation=45, ha="right", fontsize=7)
        self.ax.set_title(test_name or "Select a test")
        self.figure.tight_layout()
        self.canvas.draw_idle()
