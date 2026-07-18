"""Module 10: Billing & Administration tab (claims, invoices, payments, coding)."""
from __future__ import annotations

from tkinter import messagebox, simpledialog, ttk

from app.db.dao import billing as billing_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values


class BillingTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.balance_label = ttk.Label(self, text="Balance due: $0.00", font=("TkDefaultFont", 10, "bold"))
        self.balance_label.grid(row=0, column=0, sticky="w", padx=4, pady=4)

        sub_nb = ttk.Notebook(self)
        sub_nb.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        self.claims_panel = RecordPanel(
            sub_nb,
            columns=[("claim_date", "Date"), ("insurance_provider", "Insurer"),
                     ("amount_billed", "Billed"), ("status", "Status")],
            fields=[
                FieldSpec("claim_date", "Claim Date"),
                FieldSpec("insurance_provider", "Insurance Provider"),
                FieldSpec("cpt_codes", "CPT Codes"),
                FieldSpec("icd_codes", "ICD Codes"),
                FieldSpec("amount_billed", "Amount Billed"),
                FieldSpec("amount_paid", "Amount Paid"),
                FieldSpec("status", "Status", kind="combo",
                          options=["submitted", "paid", "denied", "appealed"]),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_claims,
            on_create=self._create_claim,
        )
        sub_nb.add(self.claims_panel, text="Insurance Claims")

        invoices_frame = ttk.Frame(sub_nb)
        invoices_frame.columnconfigure(0, weight=1)
        invoices_frame.rowconfigure(0, weight=1)
        self.invoices_panel = RecordPanel(
            invoices_frame,
            columns=[("invoice_date", "Date"), ("amount_due", "Due"),
                     ("amount_paid", "Paid"), ("status", "Status")],
            fields=[
                FieldSpec("invoice_date", "Invoice Date"),
                FieldSpec("amount_due", "Amount Due"),
                FieldSpec("due_date", "Due Date"),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_invoices,
            on_create=self._create_invoice,
            on_change=self._refresh_balance,
        )
        self.invoices_panel.grid(row=0, column=0, sticky="nsew")
        ttk.Button(invoices_frame, text="Record Payment on Selected Invoice",
                   command=self._record_payment).grid(row=1, column=0, sticky="w", pady=4)
        sub_nb.add(invoices_frame, text="Invoices & Payments")

    def load_patient(self):
        self.claims_panel.refresh()
        self.invoices_panel.refresh()
        self._refresh_balance()

    def _refresh_balance(self):
        pid = self.ctx.current_patient_id
        balance = billing_dao.balance_due(self.ctx.db, pid) if pid else 0
        self.balance_label.configure(text=f"Balance due: ${balance:.2f}")

    # ------------------------------------------------------------ claims
    def _list_claims(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return billing_dao.list_claims(self.ctx.db, pid)

    def _create_claim(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data, numeric_fields=["amount_billed", "amount_paid"])
        claim_id = billing_dao.create_claim(self.ctx.db, pid, **data)
        self.ctx.audit("CREATE_CLAIM", "billing_claim", claim_id)
        return claim_id

    # ---------------------------------------------------------- invoices
    def _list_invoices(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return billing_dao.list_invoices(self.ctx.db, pid)

    def _create_invoice(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data, numeric_fields=["amount_due"])
        amount_due = data.pop("amount_due")
        invoice_id = billing_dao.create_invoice(self.ctx.db, pid, amount_due, **data)
        self.ctx.audit("CREATE_INVOICE", "invoice", invoice_id)
        return invoice_id

    def _record_payment(self):
        selection = self.invoices_panel.tree.selection()
        if not selection:
            messagebox.showinfo("Select an invoice", "Select an invoice to record a payment.")
            return
        invoice_id = int(selection[0])
        pid = self.ctx.current_patient_id
        amount = simpledialog.askfloat("Record Payment", "Payment amount:", minvalue=0.01)
        if amount is None:
            return
        try:
            billing_dao.record_payment(self.ctx.db, invoice_id, pid, amount)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Could not record payment", str(exc))
            return
        self.ctx.audit("RECORD_PAYMENT", "invoice", invoice_id, str(amount))
        self.invoices_panel.refresh()
        self._refresh_balance()
