from django.http import HttpResponseRedirect
from django.shortcuts import render
import openpyxl
from .forms import UploadResumeForm
import pdftotext


import re


def clean_text(text):
    # Remove non-printable characters
    cleaned_text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)
    return cleaned_text


def get_email_or_phone(content):
    # Regular expression patterns
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_number_pattern1 = r"\d{2}-\d{5}-\d{5}"
    phone_number_pattern2 = r"(?:\d{2}-)?\d{5}-\d{5}"

    # Find email addresses and phone numbers in the content
    emails = re.findall(email_pattern, content)
    phones = re.findall(phone_number_pattern1, content)
    # Extract phone numbers from the log pattern
    log_phones = re.findall(phone_number_pattern2, content)
    # Extend the phone numbers list with the ones from the log pattern
    phones.extend(log_phones)

    return emails, phones


def extract_resume_data(file_path):
    emails = []
    phones = []
    texts = []

    if file_path.endswith(".pdf"):
        with open(file_path, "rb") as pdf:
            content = pdftotext.PDF(pdf, physical=True)
            for page in content:
                email, phone = get_email_or_phone(page)
                texts.append(clean_text(page))
                emails.append(email)
                phones.append(phone)
    elif file_path.endswith(".docx"):
        try:
            with open(file_path, "rb") as doc:
                doc = docx.Document(doc)
                for paragraph in doc.paragraphs:
                    text = paragraph.text.strip()
                    texts.append(clean_text(text))
                    email, phone = get_email_or_phone(text)
                    emails.append(email)
                    phones.append(phone)
        except Exception as e:
            print(f"Error parsing DOCX: {e}")  # Log or handle the error

    return emails, phones, texts


def upload_file(request):
    if request.method == "POST":
        form = UploadResumeForm(request.POST, request.FILES)
        if form.is_valid():
            # Get the uploaded files as a list
            uploaded_files = request.FILES.getlist("file")

            for uploaded_file in uploaded_files:
                # Use the uploaded_file object directly
                with open("uploads/" + uploaded_file.name, "wb") as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                text, email, phone = extract_resume_data(
                    "uploads/" + uploaded_file.name
                )
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.append(["Text", "Email", "Phone"])  # Header row
                for i in range(len(text)):
                    # Join the lists of emails and phones into strings
                    email_str = ", ".join(email[i])
                    phone_str = ", ".join(phone[i])
                    ws.append([text[i], email_str, phone_str])
                filename = "extracted_data.xlsx"  # Adjust as needed
                wb.save(filename)

                return HttpResponseRedirect(f"/download/{filename}")
    else:
        form = UploadResumeForm()

    return render(request, "index.html", {"form": form})
