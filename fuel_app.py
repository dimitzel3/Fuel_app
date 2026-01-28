import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# =========================
# ΡΥΘΜΙΣΕΙΣ / OPTIONS
# =========================

# Κοινή λίστα οχημάτων (μπορείς να την κάνεις import από κοινό αρχείο αν θέλεις)
VEHICLE_OPTIONS = [
    "ΙΚΑ-9999",
    "ΙΚΑ-5678",
    "ΙΚΑ-9012",
]

FUEL_TABLE = "fuel_refuels"  # όνομα πίνακα στη Supabase

# =========================
# Supabase client
# =========================

@st.cache_resource
def get_supabase_client():
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
):
    data = {
        "vehicle": vehicle,
        "driver_name": driver_name.strip() if driver_name else None,
        "liters": to_float_or_none(liters),
        "odometer_km": to_float_or_none(odometer_km),
        "fuel_cost": to_float_or_none(fuel_cost),
        "dt": created_at.date().isoformat(),
        "created_at": created_at.isoformat(),
    }
    supabase.table(FUEL_TABLE).insert(data).execute()


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

# Header (ίδια λογική με main app: τίτλος + υπότιτλος)
st.markdown(
    """
    <div style="padding: 0.5rem 0 1rem 0;">
      <h1 style="margin-bottom: 0.2rem;">⛽ Ανεφοδιασμοί Οχημάτων</h1>
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
            driver_name = st.text_input("Ονοματεπώνυμο οδηγού")

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

        fuel_cost = st.number_input(
            "Αξία καυσίμου (€)",
            min_value=0.0,
            step=0.5,
            format="%.2f",
        )

        submitted = st.form_submit_button("💾 Καταχώρηση ανεφοδιασμού")

        if submitted:
            errors = []

            if not driver_name.strip():
                errors.append("Το πεδίο «Ονοματεπώνυμο οδηγού» είναι υποχρεωτικό.")

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
                    )
                    st.success(
                        f"Ο ανεφοδιασμός καταχωρήθηκε επιτυχώς "
                        f"({now.strftime('%d/%m/%Y %H:%M')})."
                    )
                except Exception as ex:
                    st.error(f"Σφάλμα κατά την αποθήκευση: {ex}")

# -----------------------------
# TAB 2 – Ιστορικό & Αναφορές
# -----------------------------
with tab_history:
    st.subheader("Ιστορικό ανεφοδιασμών")

    df = get_all_refuels()

    if df.empty:
        st.info("Δεν υπάρχουν ακόμα καταχωρημένοι ανεφοδιασμοί.")
    else:
        if "created_at" in df.columns:
            df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
        else:
            df["created_at_dt"] = pd.NaT

        # Φίλτρα
        col1, col2, col3 = st.columns(3)

        with col1:
            vehicle_filter = st.selectbox(
                "Φίλτρο οχήματος",
                options=["(Όλα)"] + sorted(
                    df["vehicle"].dropna().astype(str).unique().tolist()
                ),
            )

        with col2:
            driver_filter = st.selectbox(
                "Φίλτρο οδηγού",
                options=["(Όλοι)"] + sorted(
                    df["driver_name"].dropna().astype(str).unique().tolist()
                ),
            )

        with col3:
            # Προαιρετικό: range ημερομηνίας
            min_date = df["dt"].min() if "dt" in df.columns else None
            max_date = df["dt"].max() if "dt" in df.columns else None
            date_range = st.date_input(
                "Φίλτρο ημερομηνίας (προαιρετικό)",
                value=None,
            )

        filtered_df = df.copy()

        if vehicle_filter != "(Όλα)":
            filtered_df = filtered_df[filtered_df["vehicle"] == vehicle_filter]

        if driver_filter != "(Όλοι)":
            filtered_df = filtered_df[filtered_df["driver_name"] == driver_filter]

        # Αν ο χρήστης επέλεξε ημερομηνία ή range
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range
            if start_date and end_date and "dt" in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df["dt"] >= start_date.isoformat())
                    & (filtered_df["dt"] <= end_date.isoformat())
                ]

        filtered_df = filtered_df.sort_values(by="created_at_dt", ascending=False)

        cols_to_show = [
            c
            for c in [
                "id",
                "dt",
                "created_at_dt",
                "vehicle",
                "driver_name",
                "liters",
                "odometer_km",
                "fuel_cost",
            ]
            if c in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[cols_to_show],
            use_container_width=True,
            hide_index=True,
        )

        # Μικρό summary
        total_liters = filtered_df["liters"].sum() if "liters" in filtered_df else 0
        total_cost = filtered_df["fuel_cost"].sum() if "fuel_cost" in filtered_df else 0

        st.markdown(
            f"""
            **Σύνολο λίτρων (φίλτρου):** {total_liters:.2f} L  
            **Συνολική αξία (φίλτρου):** {total_cost:.2f} €
            """
        )
