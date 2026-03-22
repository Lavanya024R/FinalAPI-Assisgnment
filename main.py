from math import ceil
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(title="Medical Appointment System")


# -----------------------------
# In-memory data
# -----------------------------
doctors = [
    {
        "id": 1,
        "name": "Dr. Asha Rao",
        "specialization": "Cardiologist",
        "fee": 800,
        "experience_years": 12,
        "is_available": True
    },
    {
        "id": 2,
        "name": "Dr. Kiran Mehta",
        "specialization": "Dermatologist",
        "fee": 600,
        "experience_years": 8,
        "is_available": True
    },
    {
        "id": 3,
        "name": "Dr. Neha Sharma",
        "specialization": "Pediatrician",
        "fee": 500,
        "experience_years": 10,
        "is_available": False
    },
    {
        "id": 4,
        "name": "Dr. Ravi Kulkarni",
        "specialization": "General",
        "fee": 400,
        "experience_years": 6,
        "is_available": True
    },
    {
        "id": 5,
        "name": "Dr. Priya Nair",
        "specialization": "Cardiologist",
        "fee": 900,
        "experience_years": 15,
        "is_available": True
    },
    {
        "id": 6,
        "name": "Dr. Suman Verma",
        "specialization": "General",
        "fee": 350,
        "experience_years": 5,
        "is_available": False
    }
]

appointments = []
appt_counter = 1
doctor_counter = 7


# -----------------------------
# Pydantic models
# -----------------------------
class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2)
    doctor_id: int = Field(..., gt=0)
    date: str = Field(..., min_length=8)
    reason: str = Field(..., min_length=5)
    appointment_type: str = Field(default="in-person")
    senior_citizen: bool = False


class NewDoctor(BaseModel):
    name: str = Field(..., min_length=2)
    specialization: str = Field(..., min_length=2)
    fee: int = Field(..., gt=0)
    experience_years: int = Field(..., gt=0)
    is_available: bool = True


# -----------------------------
# Helper functions
# -----------------------------
def find_doctor(doctor_id: int) -> Optional[Dict[str, Any]]:
    for doctor in doctors:
        if doctor["id"] == doctor_id:
            return doctor
    return None


def find_appointment(appointment_id: int) -> Optional[Dict[str, Any]]:
    for appt in appointments:
        if appt["appointment_id"] == appointment_id:
            return appt
    return None


def calculate_fee(base_fee: int, appointment_type: str, senior_citizen: bool = False) -> Dict[str, int]:
    original_fee = base_fee

    if appointment_type == "video":
        calculated_fee = int(base_fee * 0.8)
    elif appointment_type == "emergency":
        calculated_fee = int(base_fee * 1.5)
    else:
        calculated_fee = base_fee

    final_fee = calculated_fee
    if senior_citizen:
        final_fee = int(calculated_fee * 0.85)

    return {
        "original_fee": original_fee,
        "calculated_fee": final_fee
    }


def filter_doctors_logic(
    specialization: Optional[str] = None,
    max_fee: Optional[int] = None,
    min_experience: Optional[int] = None,
    is_available: Optional[bool] = None
) -> List[Dict[str, Any]]:
    filtered = doctors

    if specialization is not None:
        filtered = [
            doctor for doctor in filtered
            if doctor["specialization"].lower() == specialization.lower()
        ]

    if max_fee is not None:
        filtered = [
            doctor for doctor in filtered
            if doctor["fee"] <= max_fee
        ]

    if min_experience is not None:
        filtered = [
            doctor for doctor in filtered
            if doctor["experience_years"] >= min_experience
        ]

    if is_available is not None:
        filtered = [
            doctor for doctor in filtered
            if doctor["is_available"] == is_available
        ]

    return filtered


def paginate_items(items: List[Dict[str, Any]], page: int, limit: int) -> Dict[str, Any]:
    total = len(items)
    total_pages = ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    paginated = items[start:end]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "results": paginated
    }


# -----------------------------
# Basic routes
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to MediCare Clinic"}


# -----------------------------
# Doctors routes
# -----------------------------
@app.get("/doctors/summary")
def doctors_summary():
    if not doctors:
        return {
            "total_doctors": 0,
            "available_count": 0,
            "most_experienced_doctor": None,
            "cheapest_consultation_fee": None,
            "specialization_counts": {}
        }

    available_count = sum(1 for doctor in doctors if doctor["is_available"])
    most_experienced = max(doctors, key=lambda d: d["experience_years"])
    cheapest_fee = min(doctor["fee"] for doctor in doctors)

    specialization_counts = {}
    for doctor in doctors:
        spec = doctor["specialization"]
        specialization_counts[spec] = specialization_counts.get(spec, 0) + 1

    return {
        "total_doctors": len(doctors),
        "available_count": available_count,
        "most_experienced_doctor": most_experienced["name"],
        "cheapest_consultation_fee": cheapest_fee,
        "specialization_counts": specialization_counts
    }


@app.get("/doctors/filter")
def filter_doctors(
    specialization: Optional[str] = None,
    max_fee: Optional[int] = None,
    min_experience: Optional[int] = None,
    is_available: Optional[bool] = None
):
    filtered = filter_doctors_logic(specialization, max_fee, min_experience, is_available)
    return {
        "filters_applied": {
            "specialization": specialization,
            "max_fee": max_fee,
            "min_experience": min_experience,
            "is_available": is_available
        },
        "total": len(filtered),
        "doctors": filtered
    }


@app.get("/doctors/search")
def search_doctors(keyword: str):
    keyword_lower = keyword.lower()
    matched = [
        doctor for doctor in doctors
        if keyword_lower in doctor["name"].lower()
        or keyword_lower in doctor["specialization"].lower()
    ]

    if not matched:
        return {
            "message": f"No doctors found matching keyword '{keyword}'. Try another name or specialization.",
            "total_found": 0,
            "doctors": []
        }

    return {
        "keyword": keyword,
        "total_found": len(matched),
        "doctors": matched
    }


@app.get("/doctors/sort")
def sort_doctors(
    sort_by: str = "fee",
    order: str = "asc"
):
    allowed_sort_fields = ["fee", "name", "experience_years"]
    allowed_orders = ["asc", "desc"]

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Allowed values: {allowed_sort_fields}"
        )

    if order not in allowed_orders:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order. Allowed values: {allowed_orders}"
        )

    sorted_list = sorted(
        doctors,
        key=lambda d: d[sort_by],
        reverse=(order == "desc")
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "total": len(sorted_list),
        "doctors": sorted_list
    }


@app.get("/doctors/page")
def paginate_doctors(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1)
):
    data = paginate_items(doctors, page, limit)
    return data


@app.get("/doctors/browse")
def browse_doctors(
    keyword: Optional[str] = None,
    sort_by: str = "fee",
    order: str = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1)
):
    allowed_sort_fields = ["fee", "name", "experience_years"]
    allowed_orders = ["asc", "desc"]

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Allowed values: {allowed_sort_fields}"
        )

    if order not in allowed_orders:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order. Allowed values: {allowed_orders}"
        )

    filtered = doctors

    if keyword:
        keyword_lower = keyword.lower()
        filtered = [
            doctor for doctor in filtered
            if keyword_lower in doctor["name"].lower()
            or keyword_lower in doctor["specialization"].lower()
        ]

    sorted_list = sorted(
        filtered,
        key=lambda d: d[sort_by],
        reverse=(order == "desc")
    )

    paginated = paginate_items(sorted_list, page, limit)

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": paginated["page"],
        "limit": paginated["limit"],
        "total": paginated["total"],
        "total_pages": paginated["total_pages"],
        "results": paginated["results"]
    }


@app.get("/doctors")
def get_doctors():
    available_count = sum(1 for doctor in doctors if doctor["is_available"])
    return {
        "doctors": doctors,
        "total": len(doctors),
        "available_count": available_count
    }


@app.get("/doctors/{doctor_id}")
def get_doctor_by_id(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@app.post("/doctors", status_code=status.HTTP_201_CREATED)
def add_doctor(new_doctor: NewDoctor):
    global doctor_counter

    for doctor in doctors:
        if doctor["name"].lower() == new_doctor.name.lower():
            raise HTTPException(status_code=400, detail="Doctor with this name already exists")

    doctor_data = {
        "id": doctor_counter,
        "name": new_doctor.name,
        "specialization": new_doctor.specialization,
        "fee": new_doctor.fee,
        "experience_years": new_doctor.experience_years,
        "is_available": new_doctor.is_available
    }

    doctors.append(doctor_data)
    doctor_counter += 1

    return doctor_data


@app.put("/doctors/{doctor_id}")
def update_doctor(
    doctor_id: int,
    fee: Optional[int] = None,
    is_available: Optional[bool] = None
):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if fee is not None:
        doctor["fee"] = fee

    if is_available is not None:
        doctor["is_available"] = is_available

    return {
        "message": "Doctor updated successfully",
        "doctor": doctor
    }


@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    has_active_appointments = any(
        appt["doctor_id"] == doctor_id and appt["status"] == "scheduled"
        for appt in appointments
    )

    if has_active_appointments:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete doctor with active scheduled appointments"
        )

    doctors.remove(doctor)

    return {"message": "Doctor deleted successfully"}


# -----------------------------
# Appointment routes
# -----------------------------
@app.get("/appointments/active")
def get_active_appointments():
    active = [
        appt for appt in appointments
        if appt["status"] in ["scheduled", "confirmed"]
    ]
    return {
        "total": len(active),
        "appointments": active
    }


@app.get("/appointments/by-doctor/{doctor_id}")
def get_appointments_by_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_appts = [appt for appt in appointments if appt["doctor_id"] == doctor_id]

    return {
        "doctor_id": doctor_id,
        "doctor_name": doctor["name"],
        "total": len(doctor_appts),
        "appointments": doctor_appts
    }


@app.get("/appointments/search")
def search_appointments(patient_name: str):
    keyword = patient_name.lower()
    matched = [
        appt for appt in appointments
        if keyword in appt["patient"].lower()
    ]
    return {
        "patient_name": patient_name,
        "total_found": len(matched),
        "appointments": matched
    }


@app.get("/appointments/sort")
def sort_appointments(sort_by: str = "fee", order: str = "asc"):
    allowed_sort_fields = ["fee", "date"]
    allowed_orders = ["asc", "desc"]

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Allowed values: {allowed_sort_fields}"
        )

    if order not in allowed_orders:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order. Allowed values: {allowed_orders}"
        )

    sorted_list = sorted(
        appointments,
        key=lambda a: a[sort_by],
        reverse=(order == "desc")
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "total": len(sorted_list),
        "appointments": sorted_list
    }


@app.get("/appointments/page")
def paginate_appointments(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1)
):
    data = paginate_items(appointments, page, limit)
    return data


@app.get("/appointments")
def get_appointments():
    return {
        "appointments": appointments,
        "total": len(appointments)
    }


@app.post("/appointments")
def create_appointment(request: AppointmentRequest):
    global appt_counter

    doctor = find_doctor(request.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if not doctor["is_available"]:
        raise HTTPException(status_code=400, detail="Doctor is currently unavailable")

    fee_data = calculate_fee(
        base_fee=doctor["fee"],
        appointment_type=request.appointment_type,
        senior_citizen=request.senior_citizen
    )

    appointment = {
        "appointment_id": appt_counter,
        "patient": request.patient_name,
        "doctor_id": doctor["id"],
        "doctor_name": doctor["name"],
        "date": request.date,
        "reason": request.reason,
        "type": request.appointment_type,
        "original_fee": fee_data["original_fee"],
        "fee": fee_data["calculated_fee"],
        "senior_citizen": request.senior_citizen,
        "status": "scheduled"
    }

    appointments.append(appointment)
    appt_counter += 1

    doctor["is_available"] = False

    return {
        "message": "Appointment created successfully",
        "appointment": appointment
    }


@app.post("/appointments/{appointment_id}/confirm")
def confirm_appointment(appointment_id: int):
    appointment = find_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment["status"] = "confirmed"
    return {
        "message": "Appointment confirmed successfully",
        "appointment": appointment
    }


@app.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int):
    appointment = find_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment["status"] = "cancelled"

    doctor = find_doctor(appointment["doctor_id"])
    if doctor:
        doctor["is_available"] = True

    return {
        "message": "Appointment cancelled successfully",
        "appointment": appointment
    }


@app.post("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int):
    appointment = find_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment["status"] = "completed"

    doctor = find_doctor(appointment["doctor_id"])
    if doctor:
        doctor["is_available"] = True

    return {
        "message": "Appointment completed successfully",
        "appointment": appointment
    }
