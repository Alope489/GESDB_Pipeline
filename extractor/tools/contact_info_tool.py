# tools/contact_info_tool.py

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from langchain_core.tools import tool

class ContactInfoSchema(BaseModel):
    name: str = Field(..., description="Project contact's full name.")
    email: str = Field(..., description="Project contact's email address")
    phone_number: Optional[str] = Field(None, description="Project contact's phone number (optional).")

@tool
def extract_contact_info(contact_info: ContactInfoSchema):
    """
    Extract contact information including name, email, and optional phone number for the point of contact of the power plant or project if contained in the text, if not use the browser to look up the contact for that project.
    """
    return {
        "Name": contact_info.name,
        "Email": contact_info.email,
        "Phone Number": contact_info.phone_number or None
    }
