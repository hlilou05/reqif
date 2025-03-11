import tkinter as tk
from tkinter import filedialog, messagebox
import os
import fitz  # PyMuPDF
import re
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

# Function to extract "3 Requirements" from the PDF
def extract_section_cleaned(pdf_path, start_keyword="3 Requirements", end_keyword="4 Notes"):
    """Extracts text from a PDF between the given start and end keywords, removing headers and footers."""
    doc = fitz.open(pdf_path)
    extracted_text = []
    capture = False  # Flag to start capturing text

    # Define patterns to remove headers, footers, and unwanted metadata
    unwanted_patterns = [
        r"^Page:\s*\d+\s*of\s*\d+", r"^\d+\s+of\s+\d+$", r"CYS1600:\s*Secure Storage Requirements",
        r"Group:\s*Product Cybersecurity", r"Release date:\s*\d{4}-\d{2}-\d{2}", r"Cadence:\s*\d+\.\d+\.\d+",
        r"ECCN:\s*.*", r"©\s*\d{4}\s*GM", r"GM Confidential"
    ]

    for page in doc:
        text = page.get_text("text")
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if any(re.match(pattern, line) for pattern in unwanted_patterns):
                continue
            cleaned_lines.append(line)

        for line in cleaned_lines:
            if start_keyword in line:
                capture = True
            if end_keyword in line and capture:
                capture = False
                break
            if capture:
                extracted_text.append(line)

    return "\n".join(extracted_text)

# Function to parse the extracted text and create a ReqIF file
def parse_requirements(input_text):
    requirements = []
    current_req = None

    for line in input_text.split("\n"):
        line = line.strip()
        full_match = re.match(r"ID:\s*(\d+)\s*/\s*Legacy GUID:\s*(\S+)?\s*/\s*CR:\s*(\d+)?", line)
        id_match = re.match(r"ID:\s*(\d+)", line)
        guid_match = re.match(r"Legacy GUID:\s*(\S+)", line)
        cr_match = re.match(r"CR:\s*(\d+)", line)

        if full_match:
            if current_req:
                requirements.append(current_req)
            current_req = {
                "req_id": full_match.group(1),
                "req_title": full_match.group(2) if full_match.group(2) else "N/A",
                "req_number": full_match.group(3) if full_match.group(3) else "N/A",
                "req_description": "",
            }
            continue

        if id_match:
            if current_req:
                requirements.append(current_req)
            current_req = {"req_id": id_match.group(1), "req_title": "N/A", "req_number": "N/A", "req_description": ""}
            continue

        if guid_match and current_req:
            current_req["req_title"] = guid_match.group(1)
            continue

        if cr_match and current_req:
            current_req["req_number"] = cr_match.group(1)
            continue

        if current_req and line:
            current_req["req_description"] += line + " "

    if current_req:
        requirements.append(current_req)

    return requirements

def generate_reqif(requirements, output_file):
    root = ET.Element("REQ-IF")
    core_content = ET.SubElement(root, "REQ-IF-CONTENT")
    spec_objects = ET.SubElement(core_content, "SPEC-OBJECTS")

    for req in requirements:
        spec_object = ET.SubElement(spec_objects, "SPEC-OBJECT")
        ET.SubElement(spec_object, "ID").text = req["req_id"]
        ET.SubElement(spec_object, "Legacy-GUID").text = req["req_title"]
        ET.SubElement(spec_object, "CR").text = req["req_number"]
        ET.SubElement(spec_object, "Description").text = req["req_description"].strip()

    pretty_xml = parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(indent="  ")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

# GUI Functions
def select_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        pdf_path_var.set(file_path)

def select_output():
    output_file = filedialog.asksaveasfilename(defaultextension=".reqif", filetypes=[("ReqIF Files", "*.reqif")])
    if output_file:
        output_path_var.set(output_file)

def convert_pdf():
    pdf_path = pdf_path_var.get()
    output_path = output_path_var.get()

    if not pdf_path:
        messagebox.showerror("Error", "Please select a PDF file.")
        return

    if cys_var.get() and not output_path:
        messagebox.showerror("Error", "Please select an output file location for CYS conversion.")
        return

    try:
        extracted_text = extract_section_cleaned(pdf_path)
        requirements = parse_requirements(extracted_text)
        generate_reqif(requirements, output_path)
        messagebox.showinfo("Success", f"✅ File converted successfully!\nOutput saved at: {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"❌ Conversion failed: {str(e)}")

# GUI Setup
root = tk.Tk()
root.title("PDF to ReqIF Converter")

# Variables
pdf_path_var = tk.StringVar()
output_path_var = tk.StringVar()
cys_var = tk.BooleanVar()
gb_var = tk.BooleanVar()

# File Selection
tk.Label(root, text="Select PDF File:").grid(row=0, column=0, padx=5, pady=5)
tk.Entry(root, textvariable=pdf_path_var, width=40).grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_pdf).grid(row=0, column=2, padx=5, pady=5)

# Checkbox (Only one can be selected)
def toggle_check(option):
    if option == "CYS":
        gb_var.set(False)
    else:
        cys_var.set(False)

tk.Checkbutton(root, text="CYS", variable=cys_var, command=lambda: toggle_check("CYS")).grid(row=1, column=0, padx=5, pady=5)
tk.Checkbutton(root, text="GB", variable=gb_var, command=lambda: toggle_check("GB")).grid(row=1, column=1, padx=5, pady=5)

# Output File Selection (only if CYS is checked)
tk.Label(root, text="Output File Location:").grid(row=2, column=0, padx=5, pady=5)
tk.Entry(root, textvariable=output_path_var, width=40).grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_output).grid(row=2, column=2, padx=5, pady=5)

# Convert Button
tk.Button(root, text="Convert", command=convert_pdf, bg="green", fg="white").grid(row=3, column=0, columnspan=3, pady=10)

# Run App
root.mainloop()
