"""Module 10: Billing & Administration tab (claims, invoices, payments, coding)."""
from __future__ import annotations

from tkinter import messagebox, simpledialog, ttk

from app.db.dao import billing as billing_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.i18n import t


class BillingTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.balance_label = ttk.Label(self, font=("Helvetica", 11, "bold"))
        self.balance_label.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self._refresh_balance()

        sub_nb = ttk.Notebook(self)
        sub_nb.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

        self.claims_panel = RecordPanel(
            sub_nb,
            columns=[("claim_date", t("billing.col_date")), ("insurance_provider", t("billing.col_insurer")),
                     ("amount_billed", t("billing.col_billed")), ("status", t("billing.col_status"))],
            fields=[
                FieldSpec("claim_date", t("billing.claim_date")),
                FieldSpec("insurance_provider", t("billing.insurance_provider")),
                FieldSpec("cpt_codes", t("billing.cpt_codes")),
                FieldSpec("icd_codes", t("billing.icd_codes")),
                FieldSpec("amount_billed", t("billing.amount_billed")),
                FieldSpec("amount_paid", t("billing.amount_paid")),
                FieldSpec("status", t("billing.status"), kind="combo",
                          options=[t("claim_status.submitted"), t("claim_status.paid"),
                                   t("claim_status.denied"), t("claim_status.appealed")],
                          option_values=["submitted", "paid", "denied", "appealed"]),
                FieldSpec("notes", t("billing.notes"), kind="text"),
            ],
            on_list=self._list_claims,
            on_create=self._create_claim,
        )
        sub_nb.add(self.claims_panel, text=t("billing.tab_claims"))

        invoices_frame = ttk.Frame(sub_nb)
        invoices_frame.columnconfigure(0, weight=1)
        invoices_frame.rowconfigure(0, weight=1)
        self.invoices_panel = RecordPanel(
            invoices_frame,
            columns=[("invoice_date", t("billing.col_date")), ("amount_due", t("billing.col_due")),
                     ("amount_paid", t("billing.col_paid")), ("status", t("billing.col_status"))],
            fields=[
                FieldSpec("invoice_date", t("billing.invoice_date")),
                FieldSpec("amount_due", t("billing.amount_due")),
                FieldSpec("due_date", t("billing.due_date")),
                FieldSpec("notes", t("billing.notes"), kind="text"),
            ],
            on_list=self._list_invoices,
            on_create=self._create_invoice,
            on_change=self._refresh_balance,
        )
        self.invoices_panel.grid(row=0, column=0, sticky="nsew")
        ttk.Button(invoices_frame, text=t("billing.record_payment"), style="outline.TButton",
                   command=self._record_payment).grid(row=1, column=0, sticky="w", pady=6)
        sub_nb.add(invoices_frame, text=t("billing.tab_invoices"))

    def load_patient(self):
        self.claims_panel.refresh()
        self.invoices_panel.refresh()
        self._refresh_balance()

    def _refresh_balance(self):
        pid = self.ctx.current_patient_id
        balance = billing_dao.balance_due(self.ctx.db, pid) if pid else 0
        self.balance_label.configure(text=t("billing.balance_due", amount=f"{balance:.2f}"))

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
            messagebox.showinfo(t("billing.select_invoice_title"), t("billing.select_invoice_message"))
            return
        invoice_id = int(selection[0])
        pid = self.ctx.current_patient_id
        amount = simpledialog.askfloat(t("billing.payment_dialog_title"),
                                        t("billing.payment_dialog_prompt"), minvalue=0.01)
        if amount is None:
            return
        try:
            billing_dao.record_payment(self.ctx.db, invoice_id, pid, amount)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(t("common.error_save_title"), str(exc))
            return
        self.ctx.audit("RECORD_PAYMENT", "invoice", invoice_id, str(amount))
        self.invoices_panel.refresh()
        self._refresh_balance()
