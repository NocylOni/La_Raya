"""Reusable Tkinter building blocks: a generic list+form CRUD panel used by
most tabs so each module doesn't need to hand-roll its own form/list code."""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from tkinter import messagebox, ttk
from typing import Callable, Optional

from app.i18n import t


@dataclass
class FieldSpec:
    name: str
    label: str
    kind: str = "entry"          # entry | text | combo | check | date | readonly
    options: list[str] = field(default_factory=list)   # display labels shown to the user
    option_values: list[str] | None = None              # canonical DB values, parallel to
                                                          # `options`; defaults to `options`
                                                          # itself when not given (untranslated
                                                          # combos where display == stored value)
    width: int = 30


class RecordPanel(ttk.Frame):
    """A Treeview list of records plus a below-list form to add/edit/delete
    one record at a time. Generic across most patient sub-modules."""

    def __init__(
        self,
        parent,
        columns: list[tuple[str, str]],   # (row_key, header) shown in the list
        fields: list[FieldSpec],          # editable form fields
        on_list: Callable[[], list[dict]],
        on_create: Callable[[dict], int],
        on_update: Optional[Callable[[int, dict], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
        id_key: str = "id",
        on_change: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.columns = columns
        self.fields = fields
        self.on_list = on_list
        self.on_create = on_create
        self.on_update = on_update
        self.on_delete = on_delete
        self.id_key = id_key
        self.on_change = on_change
        self._records: dict[int, dict] = {}
        self._selected_id: Optional[int] = None
        self._widgets: dict[str, tk.Widget] = {}

        self._build()

    # ------------------------------------------------------------- layout
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(self)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        col_ids = [c[0] for c in self.columns]
        self.tree = ttk.Treeview(list_frame, columns=col_ids, show="headings", height=8)
        for key, header in self.columns:
            self.tree.heading(key, text=header)
            self.tree.column(key, width=120, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        form_frame = ttk.LabelFrame(self, text=t("common.details"), padding=10)
        form_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        form_frame.columnconfigure(1, weight=1)

        for i, spec in enumerate(self.fields):
            ttk.Label(form_frame, text=spec.label + ":").grid(
                row=i, column=0, sticky="ne", padx=(2, 8), pady=4
            )
            widget = self._make_field_widget(form_frame, spec)
            widget.grid(row=i, column=1, sticky="ew", padx=2, pady=4)
            self._widgets[spec.name] = widget

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=10)
        ttk.Button(btn_frame, text=t("common.new"), style="secondary.TButton",
                   command=self.clear_form).pack(side="left", padx=3)
        ttk.Button(btn_frame, text=t("common.save"), style="success.TButton",
                   command=self._save).pack(side="left", padx=3)
        if self.on_delete:
            ttk.Button(btn_frame, text=t("common.delete"), style="danger.TButton",
                       command=self._delete).pack(side="left", padx=3)

    def _make_field_widget(self, parent, spec: FieldSpec):
        if spec.kind == "text":
            widget = tk.Text(parent, width=spec.width, height=4)
        elif spec.kind == "combo":
            widget = ttk.Combobox(parent, values=spec.options, width=spec.width, state="readonly")
        elif spec.kind == "check":
            var = tk.IntVar(value=0)
            widget = ttk.Checkbutton(parent, variable=var)
            widget.var = var  # type: ignore[attr-defined]
        elif spec.kind == "readonly":
            widget = ttk.Entry(parent, width=spec.width, state="readonly")
        else:
            widget = ttk.Entry(parent, width=spec.width)
        return widget

    # ------------------------------------------------------------- data io
    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._records.clear()
        self.tree.tag_configure("odd_row", background="#f4f6f8")
        field_by_name = {spec.name: spec for spec in self.fields}
        for i, record in enumerate(self.on_list()):
            record = dict(record)
            rid = record[self.id_key]
            self._records[rid] = record
            values = [self._display_value(field_by_name.get(key), record.get(key, ""))
                      for key, _ in self.columns]
            tag = "odd_row" if i % 2 else ""
            self.tree.insert("", "end", iid=str(rid), values=values, tags=(tag,))
        self.clear_form()

    @staticmethod
    def _display_value(spec: Optional[FieldSpec], raw):
        """List columns mirror form field values 1:1 by name - reuse the
        combo's value->label mapping so lists never show raw DB codes like
        'active' or '1' in an otherwise-translated UI."""
        if spec is None:
            return raw
        if spec.kind == "combo" and spec.option_values and raw in spec.option_values:
            return spec.options[spec.option_values.index(raw)]
        if spec.kind == "check":
            return t("common.yes") if raw else t("common.no")
        return raw

    def clear_form(self):
        self._selected_id = None
        self.tree.selection_remove(self.tree.selection())
        for spec in self.fields:
            self._set_field_value(spec, None)

    def _on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        rid = int(selection[0])
        self._selected_id = rid
        record = self._records.get(rid, {})
        for spec in self.fields:
            self._set_field_value(spec, record.get(spec.name))

    def _set_field_value(self, spec: FieldSpec, value):
        widget = self._widgets[spec.name]
        if spec.kind == "text":
            widget.delete("1.0", "end")
            if value is not None:
                widget.insert("1.0", str(value))
        elif spec.kind == "check":
            widget.var.set(1 if value else 0)  # type: ignore[attr-defined]
        elif spec.kind == "combo":
            values = spec.option_values or spec.options
            if value is not None and value in values:
                widget.set(spec.options[values.index(value)])
            else:
                widget.set(str(value) if value is not None else "")
        else:
            state = str(widget["state"])
            if state == "readonly":
                widget.configure(state="normal")
            widget.delete(0, "end")
            if value is not None:
                widget.insert(0, str(value))
            if state == "readonly":
                widget.configure(state="readonly")

    def _get_field_value(self, spec: FieldSpec):
        widget = self._widgets[spec.name]
        if spec.kind == "text":
            return widget.get("1.0", "end").strip()
        if spec.kind == "check":
            return bool(widget.var.get())  # type: ignore[attr-defined]
        if spec.kind == "combo":
            display = widget.get()
            values = spec.option_values or spec.options
            if display in spec.options:
                return values[spec.options.index(display)]
            return display
        return widget.get().strip()

    def apply_values(self, values: dict):
        """Programmatically fill form fields (e.g. from a template) without
        selecting/creating a record."""
        for spec in self.fields:
            if spec.name in values:
                self._set_field_value(spec, values[spec.name])

    def collect_form_data(self) -> dict:
        return {spec.name: self._get_field_value(spec) for spec in self.fields}

    def _save(self):
        data = self.collect_form_data()
        try:
            if self._selected_id is not None and self.on_update:
                self.on_update(self._selected_id, data)
            else:
                self.on_create(data)
        except Exception as exc:  # noqa: BLE001 - surfaced to the clinician
            messagebox.showerror(t("common.error_save_title"), str(exc))
            return
        self.refresh()
        if self.on_change:
            self.on_change()

    def _delete(self):
        if self._selected_id is None or not self.on_delete:
            return
        if not messagebox.askyesno(t("common.confirm_delete_title"), t("common.confirm_delete_message")):
            return
        try:
            self.on_delete(self._selected_id)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(t("common.error_delete_title"), str(exc))
            return
        self.refresh()
        if self.on_change:
            self.on_change()


def clean_form_values(data: dict, numeric_fields: list[str] | None = None) -> dict:
    """Turn empty-string form values into None, and cast numeric fields."""
    numeric_fields = numeric_fields or []
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str) and value == "":
            cleaned[key] = None
            continue
        if key in numeric_fields and value not in (None, ""):
            try:
                cleaned[key] = float(value) if "." in str(value) else int(value)
            except (ValueError, TypeError):
                cleaned[key] = value
            continue
        cleaned[key] = value
    return cleaned
