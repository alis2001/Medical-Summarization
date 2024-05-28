import os
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader
from datetime import datetime
import csv
from itertools import count
from codicefiscale import codicefiscale

def get_place_of_birth_code(codice_fiscale_str):
    try:
        if codicefiscale.is_valid(codice_fiscale_str):
            birth_place_info = codicefiscale.decode(codice_fiscale_str)['birthplace']
            birth_place_code = birth_place_info['code'] if isinstance(birth_place_info, dict) else "INVALID"
            return birth_place_code
        else:
            print(f"Invalid codice fiscale: {codice_fiscale_str}")
            return "INVALID"
    except Exception as e:
        print(f"Error in get_place_of_birth_code: {e}")
        return "INVALID"

def get_gender(codice_fiscale_str):
    try:
        if codicefiscale.is_valid(codice_fiscale_str):
            gender = codicefiscale.decode(codice_fiscale_str)['gender']
            return gender
        else:
            print(f"Invalid codice fiscale for gender: {codice_fiscale_str}")
            return "INVALID"
    except Exception as e:
        print(f"Error in get_gender: {e}")
        return "INVALID"

def get_birth_date_parts(codice_fiscale_str):
    try:
        if codicefiscale.is_valid(codice_fiscale_str):
            birth_date_str = codicefiscale.decode(codice_fiscale_str)['birthdate']
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            birth_year = birth_date.strftime("%Y")
            birth_month = birth_date.strftime("%m")
            return birth_year, birth_month
        else:
            print(f"Invalid codice fiscale for birth date: {codice_fiscale_str}")
            return "INVALID", "INVALID"
    except Exception as e:
        print(f"Error in get_birth_date_parts: {e}")
        return "INVALID", "INVALID"

patient_counter = count(start=1)
assigned_person_counter = count(start=1)

def generate_anonymized_code(gender, birth_month, birth_year, place_of_birth_code, is_patient=True):
    counter = patient_counter if is_patient else assigned_person_counter
    progressive_number = next(counter)
    progressive_str = str(progressive_number).zfill(6)
    gender_abbr = 'M' if gender == 'M' else 'F'
    birth_year_abbr = birth_year[-2:]
    anonymized_code = f"{gender_abbr}{birth_month}{birth_year_abbr}{place_of_birth_code}{progressive_str}"
    return anonymized_code

def extract_patient_info(xml_content):
    root = ET.fromstring(xml_content)
    ns = {"hl7": "urn:hl7-org:v3"}
    
    patient_id = root.find(".//hl7:patientRole/hl7:id", ns).attrib.get("extension", "")
    birth_date_str = root.find(".//hl7:patientRole/hl7:patient/hl7:birthTime", ns).attrib.get("value", "")
    date_str = root.find(".//hl7:effectiveTime", ns).attrib.get("value", "")
    title = root.find(".//hl7:title", ns).text
    
    assigned_person_id = root.find(".//hl7:assignedAuthor/hl7:id", ns).attrib.get("extension", "")
    exam_time = root.find(".//hl7:entry/hl7:act/hl7:effectiveTime", ns).attrib.get("value", "")
    
    last_paragraph = root.find(".//hl7:section[@ID='REFERTO']/hl7:text/hl7:paragraph[last()]", ns).text.strip()
    
    birth_date = datetime.strptime(birth_date_str, "%Y%m%d").strftime("%Y-%m-%d")
    birth_year = datetime.strptime(birth_date_str, "%Y%m%d").strftime("%Y")
    birth_month = datetime.strptime(birth_date_str, "%Y%m%d").strftime("%m")
    date = datetime.strptime(date_str, "%Y%m%d%H%M%S%z").strftime("%Y-%m-%d %H:%M:%S")
    
    place_of_birth_code = get_place_of_birth_code(patient_id)
    gender = get_gender(patient_id)
    
    if place_of_birth_code == "INVALID" or gender == "INVALID":
        print(f"Invalid patient info: patient_id={patient_id}, place_of_birth_code={place_of_birth_code}, gender={gender}")

    patient_id_anonymized = generate_anonymized_code(gender, birth_month, birth_year, place_of_birth_code, is_patient=True)
    
    assigned_person_birth_year, assigned_person_birth_month = get_birth_date_parts(assigned_person_id)
    assigned_person_place_of_birth_code = get_place_of_birth_code(assigned_person_id)
    assigned_person_gender = get_gender(assigned_person_id)
    
    if assigned_person_place_of_birth_code == "INVALID" or assigned_person_gender == "INVALID":
        print(f"Invalid assigned person info: assigned_person_id={assigned_person_id}, assigned_person_place_of_birth_code={assigned_person_place_of_birth_code}, assigned_person_gender={assigned_person_gender}")

    assigned_person_id_anonymized = generate_anonymized_code(assigned_person_gender, assigned_person_birth_month, assigned_person_birth_year, assigned_person_place_of_birth_code, is_patient=False)
    
    return {"patient_id": patient_id_anonymized, "birth_date": birth_date, "date": date, "title": title,
            "assigned_person_id": assigned_person_id_anonymized, "exam_time": exam_time,
            "last_paragraph": last_paragraph, "place_of_birth_code": place_of_birth_code, "gender": gender}

def get_attachments(reader):
    attachments_info = []
    catalog = reader.trailer["/Root"]
    if "/EmbeddedFiles" in catalog["/Names"]:
        file_names = catalog['/Names']['/EmbeddedFiles']['/Names']
        for f in file_names:
            if isinstance(f, str):
                name = f
                data_index = file_names.index(f) + 1
                f_dict = file_names[data_index].get_object()
                f_data = f_dict['/EF']['/F'].get_data()
                attachments_info.append({"name": name, "data": f_data})
    return attachments_info

folder_path = r"H:\Intern\data\EXPORT_REF\EXPORT_REF"
csv_file = "output.csv"

with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["PDF", "Attachment Name", "Patient ID", "Birth Date", "Date", "Title", 
                  "Assigned Person's ID", "Exam Time", "Place of Birth Code", "Gender", "Last Paragraph"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            full_path = os.path.join(folder_path, filename)
            with open(full_path, 'rb') as handler:
                reader = PdfReader(handler)
                attachments_info = get_attachments(reader)

                for attachment in attachments_info:
                    xml_content = attachment["data"]
                    patient_info = extract_patient_info(xml_content)
                    
                    writer.writerow({
                        "PDF": filename,
                        "Attachment Name": attachment["name"],
                        "Patient ID": patient_info["patient_id"],
                        "Birth Date": patient_info["birth_date"],
                        "Date": patient_info["date"],
                        "Title": patient_info["title"],
                        "Assigned Person's ID": patient_info["assigned_person_id"],
                        "Exam Time": patient_info["exam_time"],
                        "Place of Birth Code": patient_info["place_of_birth_code"],
                        "Gender": patient_info["gender"],
                        "Last Paragraph": patient_info["last_paragraph"]
                    })

print("CSV file created: output.csv")
