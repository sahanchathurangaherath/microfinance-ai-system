# ai_service/services/nic_validator.py
import re

def validate_sri_lankan_nic(nic: str, form_dob: str, form_gender: str) -> dict:
    """
    Validates a Sri Lankan NIC against form-submitted personal details.
    Returns flags if NIC data contradicts form data.
    """
    flags = []
    nic = nic.strip().upper()

    # Old format: 9 digits + V (e.g. 901234567V)
    old_format = re.match(r'^(\d{2})(\d{3})(\d{3})(\d)V$', nic)
    # New format: 12 digits (e.g. 199012345678)
    new_format = re.match(r'^(\d{4})(\d{3})(\d{3})(\d{2})$', nic)

    if not old_format and not new_format:
        return {
            "valid_format": False,
            "flags": ["NIC does not match Sri Lankan NIC format (old: 9+V, new: 12 digits)"]
        }

    if old_format:
        year_2digit = int(old_format.group(1))
        day_of_year = int(old_format.group(2))
        birth_year = 1900 + year_2digit if year_2digit > 24 else 2000 + year_2digit
    else:
        birth_year = int(new_format.group(1))
        day_of_year = int(new_format.group(2))

    # Gender from day_of_year (males: 1-366, females: 501-866)
    nic_gender = "F" if day_of_year > 500 else "M"

    # Compare birth year with form DOB
    if form_dob:
        try:
            form_year = int(form_dob[:4])
            if form_year != birth_year:
                flags.append(
                    f"Birth year mismatch: NIC indicates {birth_year}, form shows {form_year}"
                )
        except Exception:
            pass

    # Compare gender
    if form_gender and form_gender.upper() != nic_gender:
        flags.append(
            f"Gender mismatch: NIC indicates {nic_gender}, form shows {form_gender}"
        )

    return {
        "valid_format": True,
        "nic_birth_year": birth_year,
        "nic_gender": nic_gender,
        "flags": flags,
        "has_contradictions": len(flags) > 0
    }
