import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# =========================
# ΡΥΘΜΙΣΕΙΣ / OPTIONS
# =========================

VEHICLE_OPTIONS = [
    "ΔΕΞΑΜΕΝΗ",
    "BKT 9409",
    "NXY 3413",
    "ΒΜΗ 9889",
    "ΕΚΒ 4058",
    "ΙΑΕ 4351",
    "ΙΑΕ 6034",
    "ΙΕΜ 1356",
    "ΙΤΜ 3656",
    "ΚΙΕ 9263",
    "ΝΧΥ 3546",
    "ΝΧΥ 3547",
    "ΝΜΗ 5728",
]

FUEL_TYPE_OPTIONS = ["ΑΜΟΛΥΒΔΗ", "DIESEL", "AdBlue"]

FUEL_TABLE = "fuel_refuels"

# =========================
# Supabase client
# =========================

@st.cache_resource
def get_supabase_client():
    # Αν δεν έχεις βάλει σωστά secrets, θα σκάει εδώ
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)

supabase = get_supabase_client()

# =========================
# Helpers
# =========================

def to_float_or_none(x):
    if x in (None, ""):
        return None
    try:
        return float(x)
    except Exception:
        return None

def safe_str(x):
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None

# =========================
# CRUD
# =========================

def insert_refuel_record(
    vehicle: str,
    driver_name: str,
    liters: float,
    odometer_km: float,
    fuel_cost: float,
    created_at: datetime,
    receipt_invoice_no: str,
    fuel_type: str,
):
    data = {
        "vehicle": vehicle,
        "driver_name": safe_str(driver_name),
        "liters": to_float_or_none(liters),
        "odometer_km": to_float_or_none(odometer_km),
        "fuel_cost": to_float_or_none(fuel_cost),
        "dt": created_at.date().isoformat(),
        "created_at": created_at.isoformat(),
        # νέα πεδία
        "receipt_invoice_no": safe_str(receipt_invoice_no),
        "fuel_type": safe_str(fuel_type),
    }
    supabase.table(FUEL_TABLE).insert(data).execute()

def update_refuel_record(
    record_id: int,
    vehicle: str,
    driver_name: str,
    liters: float,
    odometer_km: float,
    fuel_cost: float,
    receipt_invoice_no: str,
    fuel_type: str,
):
    data = {
        "vehicle": vehicle,
        "driver_name": safe_str(driver_name),
        "liters": to_float_or_none(liters),
        "odometer_km": to_float_or_none(odometer_km),
        "fuel_cost": to_float_or_none(fuel_cost),
        "receipt_invoice_no": safe_str(receipt_invoice_no),
        "fuel_type": safe_str(fuel_type),
    }
    supabase.table(FUEL_TABLE).update(data).eq("id", record_id).execute()

def delete_refuel_record(record_id: int):
    supabase.table(FUEL_TABLE).delete().eq("id", record_id).execute()

def get_all_refuels() -> pd.DataFrame:
    res = (
        supabase.table(FUEL_TABLE)
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    return pd.DataFrame(res.data or [])

# =========================
# STREAMLIT UI
# =========================

st.set_page_config(
    page_title="Ανεφοδιασμοί Οχημάτων",
    page_icon="⛽",
    layout="wide",
)

st.markdown(
    """
    <div style="padding: 0.5rem 0 1rem 0;">
      <h1 style="margin-bottom: 0.2rem;">⛽ Gtrans Ανεφοδιασμοί Οχημάτων</h1>
      <p style="color: #6b7280; margin: 0;">
        Καταγραφή ανεφοδιασμών καυσίμου, με αυτόματη ημερομηνία & ώρα,
        ανά όχημα και οδηγό.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_new, tab_history = st.tabs(["Νέος Ανεφοδιασμός", "Ιστορικό & Αναφορές"])

# -----------------------------
# TAB 1 – Νέος Ανεφοδιασμός
# -----------------------------
with tab_new:
    st.subheader("Καταχώρηση νέου ανεφοδιασμού")

    with st.form("fuel_form", clear_on_submit=True):
        st.caption("Η ημερομηνία & ώρα καταγράφονται αυτόματα με την αποθήκευση.")

        col1, col2 = st.columns(2)

        with col1:
            vehicle = st.selectbox("Όχημα", options=VEHICLE_OPTIONS)
            driver_name = st.selectbox(
                "Ονοματεπώνυμο οδηγού",
                options=[
                    "(Επιλέξτε)",
                    "ΒΑΚΑΛΦΩΤΗΣ ΒΑΓΓΕΛΗΣ",
                    "ΒΑΚΑΛΦΩΤΗΣ ΓΡΗΓΟΡΗΣ",
                    "ΚΟΛΤΣΙΝΑΚΟΣ ΒΑΓΓΕΛΗΣ",
                    "ΙΜΠΑΣ ΙΟΡΔΑΝΗΣ",
                    "ΠΑΤΣΑΒΟΥΔΗΣ ΤΡΑΪΑΝΟΣ",
                ],
            )
            fuel_type = st.selectbox("Είδος Καυσίμου", options=["(Επιλέξτε)"] + FUEL_TYPE_OPTIONS)

        with col2:
            liters = st.number_input(
                "Λίτρα ανεφοδιασμού",
                min_value=0.0,
                step=0.1,
                format="%.2f",
            )
            odometer_km = st.number_input(
                "Χιλιομετρική ένδειξη (km) κατά τον ανεφοδιασμό",
                min_value=0.0,
                step=1.0,
                format="%.0f",
            )

        col3, col4 = st.columns(2)
        with col3:
            fuel_cost = st.number_input(
                "Αξία καυσίμου (€)",
                min_value=0.0,
                step=0.5,
                format="%.2f",
            )
        with col4:
            receipt_invoice_no = st.text_input("Αρ. Απόδειξης - Αρ. Τιμολογίου")

        submitted = st.form_submit_button("💾 Καταχώρηση ανεφοδιασμού")

        if submitted:
            errors = []

            if not driver_name or driver_name == "(Επιλέξτε)":
                errors.append("Το πεδίο «Ονοματεπώνυμο οδηγού» είναι υποχρεωτικό.")

            if not fuel_type or fuel_type == "(Επιλέξτε)":
                errors.append("Το πεδίο «Είδος Καυσίμου» είναι υποχρεωτικό.")

            if liters <= 0:
                errors.append("Τα λίτρα ανεφοδιασμού πρέπει να είναι μεγαλύτερα από 0.")

            if odometer_km <= 0:
                errors.append("Η χιλιομετρική ένδειξη πρέπει να είναι μεγαλύτερη από 0.")

            if fuel_cost <= 0:
                errors.append("Η αξία καυσίμου πρέπει να είναι μεγαλύτερη από 0.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                now = datetime.now()
                try:
                    insert_refuel_record(
                        vehicle=vehicle,
                        driver_name=driver_name,
                        liters=liters,
                        odometer_km=odometer_km,
                        fuel_cost=fuel_cost,
                        created_at=now,
                        receipt_invoice_no=receipt_invoice_no,
                        fuel_type=fuel_type,
                    )
                    st.success(
                        f"Ο ανεφοδιασμός καταχωρήθηκε επιτυχώς "
                        f"({now.strftime('%d/%m/%Y %H:%M')})."
                    )
                except Exception as ex:
                    st.error(f"Σφάλμα κατά την αποθήκευση: {ex}")

# -----------------------------
# TAB 2 – Ιστορικό & Αναφορές (+ ΕΠΕΞΕΡΓΑΣΙΑ)
# -----------------------------
with tab_history:
    st.subheader("Ιστορικό ανεφοδιασμών")

    df = get_all_refuels()

    if df.empty:
        st.info("Δεν υπάρχουν ακόμα καταχωρημένοι ανεφοδιασμοί.")
    else:
        # parsing created_at
        if "created_at" in df.columns:
            df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
        else:
            df["created_at_dt"] = pd.NaT

        # Φίλτρα
        col1, col2, col3 = st.columns(3)

        with col1:
            vehicle_filter = st.selectbox(
                "Φίλτρο οχήματος",
                options=["(Όλα)"] + sorted(df["vehicle"].dropna().astype(str).unique().tolist()),
                key="vehicle_filter",
            )

        with col2:
            driver_filter = st.selectbox(
                "Φίλτρο οδηγού",
                options=["(Όλοι)"] + sorted(df["driver_name"].dropna().astype(str).unique().tolist()),
                key="driver_filter",
            )

        with col3:
            date_range = st.date_input(
                "Φίλτρο ημερομηνίας (προαιρετικό)",
                value=None,
                key="date_filter",
            )

        filtered_df = df.copy()

        if vehicle_filter != "(Όλα)":
            filtered_df = filtered_df[filtered_df["vehicle"] == vehicle_filter]

        if driver_filter != "(Όλοι)":
            filtered_df = filtered_df[filtered_df["driver_name"] == driver_filter]

        # date range
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range
            if start_date and end_date and "dt" in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df["dt"] >= start_date.isoformat())
                    & (filtered_df["dt"] <= end_date.isoformat())
                ]

        filtered_df = filtered_df.sort_values(by="created_at_dt", ascending=False)

        # Προβολή
        cols_to_show = [
            c for c in [
                "id",
                "dt",
                "created_at_dt",
                "vehicle",
                "driver_name",
                "fuel_type",
                "receipt_invoice_no",
                "liters",
                "odometer_km",
                "fuel_cost",
            ] if c in filtered_df.columns
        ]

        st.dataframe(filtered_df[cols_to_show], use_container_width=True, hide_index=True)

        # Summary
        total_liters = filtered_df["liters"].sum() if "liters" in filtered_df else 0
        total_cost = filtered_df["fuel_cost"].sum() if "fuel_cost" in filtered_df else 0

        st.markdown(
            f"""
            **Σύνολο λίτρων (φίλτρου):** {total_liters:.2f} L  
            **Συνολική αξία (φίλτρου):** {total_cost:.2f} €
            """
        )

        st.divider()
        st.subheader("✏️ Επεξεργασία / Διαγραφή εγγραφής")

        # Επιλογή εγγραφής για edit
        edit_options = []
        for _, r in filtered_df.iterrows():
            rid = r.get("id")
            v = r.get("vehicle", "")
            d = r.get("driver_name", "")
            ts = r.get("created_at_dt")
            ts_txt = ts.strftime("%d/%m/%Y %H:%M") if pd.notna(ts) else ""
            edit_options.append((rid, f"#{rid} | {v} | {d} | {ts_txt}"))

        selected_label = st.selectbox(
            "Επίλεξε εγγραφή",
            options=[x[1] for x in edit_options],
            key="edit_select",
        )
        selected_id = None
        for rid, lbl in edit_options:
            if lbl == selected_label:
                selected_id = rid
                break

        row = filtered_df[filtered_df["id"] == selected_id].iloc[0]

        with st.form("edit_form"):
            colA, colB = st.columns(2)
            with colA:
                e_vehicle = st.selectbox("Όχημα", options=VEHICLE_OPTIONS, index=VEHICLE_OPTIONS.index(row.get("vehicle")) if row.get("vehicle") in VEHICLE_OPTIONS else 0)
                e_driver = st.text_input("Οδηγός", value=str(row.get("driver_name") or ""))
                e_fuel_type = st.selectbox(
                    "Είδος Καυσίμου",
                    options=FUEL_TYPE_OPTIONS,
                    index=FUEL_TYPE_OPTIONS.index(row.get("fuel_type")) if row.get("fuel_type") in FUEL_TYPE_OPTIONS else 0,
                )
            with colB:
                e_liters = st.number_input("Λίτρα", min_value=0.0, step=0.1, format="%.2f", value=float(row.get("liters") or 0.0))
                e_odometer = st.number_input("Χιλιομετρική ένδειξη (km)", min_value=0.0, step=1.0, format="%.0f", value=float(row.get("odometer_km") or 0.0))
                e_cost = st.number_input("Αξία καυσίμου (€)", min_value=0.0, step=0.5, format="%.2f", value=float(row.get("fuel_cost") or 0.0))

            e_receipt = st.text_input("Αρ. Απόδειξης - Αρ. Τιμολογίου", value=str(row.get("receipt_invoice_no") or ""))

            c1, c2 = st.columns(2)
            save_btn = c1.form_submit_button("💾 Αποθήκευση αλλαγών")
            delete_btn = c2.form_submit_button("🗑️ Διαγραφή εγγραφής")

            if save_btn:
                errs = []
                if not e_driver.strip():
                    errs.append("Ο οδηγός δεν μπορεί να είναι κενός.")
                if e_liters <= 0:
                    errs.append("Τα λίτρα πρέπει να είναι > 0.")
                if e_odometer <= 0:
                    errs.append("Το odometer πρέπει να είναι > 0.")
                if e_cost <= 0:
                    errs.append("Η αξία πρέπει να είναι > 0.")
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    try:
                        update_refuel_record(
                            record_id=int(selected_id),
                            vehicle=e_vehicle,
                            driver_name=e_driver,
                            liters=e_liters,
                            odometer_km=e_odometer,
                            fuel_cost=e_cost,
                            receipt_invoice_no=e_receipt,
                            fuel_type=e_fuel_type,
                        )
                        st.success("✅ Η εγγραφή ενημερώθηκε.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Σφάλμα κατά το update: {ex}")

            if delete_btn:
                try:
                    delete_refuel_record(int(selected_id))
                    st.success("🗑️ Η εγγραφή διαγράφηκε.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Σφάλμα κατά τη διαγραφή: {ex}")
